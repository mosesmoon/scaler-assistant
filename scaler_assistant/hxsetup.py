"""Download HelixSR and build its network on this PC, in one step.

HelixSR's network is NVIDIA's (it is made from NVIDIA's DLSS DLL), so it can't be shipped
built: HelixSR's own setup has to make it on the user's computer. This module does what a
user would otherwise do by hand, the way HelixSR's own desktop app does it:

1. the newest HelixSR release (2.0 and newer) from HelixSR's GitHub releases, checked by the
   SHA-256 GitHub lists for it, unpacked unchanged into Scaler Assistant's data folder;
2. the build tools the setup needs: a Python 3 with numpy (a portable Python 3.14 when the
   system's can't unpack NVIDIA's zstd package for frame generation) and Microsoft's DirectX
   Shader Compiler, run through Steam's Proton (or Wine);
3. HelixSR's build program ``setup/helixsr_setup.py`` (run, never copied), after the user has
   agreed to NVIDIA's downloads in Scaler Assistant. It only builds: the games step of
   ``helixsr-setup.sh`` is not run, games stay Scaler Assistant's choice.

Inside Flatpak the build runs on the host (Proton and Wine live there); every path it uses is
in the home folder, which host and sandbox share.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from . import sandbox
from .components import open_url
from .helixsr import FSRFG, HelixSRFolder, inspect, parse_version

API = "https://api.github.com/repos/lonewolf0622/HelixSR/releases?per_page=10"
RELEASES = "https://github.com/lonewolf0622/HelixSR/releases"
MIN_AUTO = (2, 0, 0)          # the HelixSR-fsrfg layout with setup/helixsr_setup.py
_ZIP = re.compile(r"^HelixSR-(\d+\.\d+\.\d+)\.zip$")

# A portable Python 3.14 (python-build-standalone): it unpacks NVIDIA's zstd package itself.
PYTHON_URL = ("https://github.com/astral-sh/python-build-standalone/releases/download/20261003/"
              "cpython-3.14.8%2B20261003-x86_64-unknown-linux-gnu-install_only.tar.gz")
PYTHON_SHA = "371b6c281bbb09b29279e9e3a2996bab4ae2ea03cca52bf869f8bd89286b0ae8"
PYTHON_SIZE = 75007267
# Microsoft's DirectX Shader Compiler (Windows build; HelixSR's setup verifies with it).
DXC_URL = ("https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.9.2607/"
           "dxc_2026_07_29.zip")
DXC_SHA = "a1dfb116ba3eeae6a1582291b53a8e7bf65ad760676bd3194685c8f7367cd241"

NVIDIA_LICENSES = ("https://github.com/NVIDIA/DLSS/blob/v310.7.0/LICENSE.txt",
                   "https://github.com/NVIDIAGameWorks/Streamline/blob/main/license.txt")
_PROGRESS = re.compile(r"\]\s+(\d+)%\s+\S+\s+(.*)$")

# (stage, done, total, text): stage is release / python / numpy / dxc / build; done and total
# are bytes for downloads and percent for the build (total 100)
Report = Callable[[str, int, int, str], None]


class SetupError(RuntimeError):
    pass


@dataclass
class Release:
    version: str
    url: str
    sha256: str
    size: int

    @property
    def version_tuple(self) -> tuple[int, ...]:
        return parse_version(self.version)


def data_root() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "scaler-assistant" / "helixsr"


def tools_dir() -> Path:
    return data_root() / "tools"


def release_dir(version: str) -> Path:
    return data_root() / f"HelixSR-{version}"


# ---- the release ------------------------------------------------------------------------------

def _get_json(url: str, opener=None):
    request = urllib.request.Request(url, headers={
        "User-Agent": "Scaler-Assistant", "Accept": "application/vnd.github+json"})
    try:
        with (opener or open_url)(request, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError) as error:
        raise SetupError(f"{url}: {error}") from error


def latest_release(opener=None) -> Release:
    """The newest published HelixSR release (2.0 or newer) with its HelixSR-X.Y.Z.zip."""
    best: Optional[Release] = None
    for item in _get_json(API, opener) or []:
        if item.get("draft") or item.get("prerelease"):
            continue
        for asset in item.get("assets") or []:
            match = _ZIP.match(str(asset.get("name") or ""))
            digest = str(asset.get("digest") or "")
            if not match or not digest.startswith("sha256:"):
                continue
            found = Release(match.group(1), str(asset["browser_download_url"]),
                            digest.split(":", 1)[1].lower(), int(asset.get("size") or 0))
            if found.version_tuple >= MIN_AUTO and (best is None
                                                    or found.version_tuple > best.version_tuple):
                best = found
    if best is None:
        raise SetupError(f"no HelixSR release 2.0 or newer found at {RELEASES}")
    return best


def _download(url: str, target: Path, sha256: str, size: int, stage: str, report: Report,
              opener=None) -> None:
    digest = hashlib.sha256()
    done = 0
    request = urllib.request.Request(url, headers={"User-Agent": "Scaler-Assistant"})
    try:
        with (opener or open_url)(request, timeout=60) as response, open(target, "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                report(stage, done, size, "")
    except OSError as error:
        raise SetupError(f"{url}: {error}") from error
    if digest.hexdigest() != sha256.lower():
        target.unlink(missing_ok=True)
        raise SetupError(f"{url}: SHA-256 does not match")


def _safe_members(names: Iterable[str]) -> None:
    for name in names:
        parts = Path(name.replace("\\", "/")).parts
        if name.startswith(("/", "\\")) or ".." in parts:
            raise SetupError(f"unsafe path in the download: {name}")


def get_release(release: Release, report: Report, opener=None) -> Path:
    """The release unpacked unchanged into data_root(); kept when it is there already."""
    target = release_dir(release.version)
    if (target / FSRFG).is_dir() and (target / "setup" / "helixsr_setup.py").is_file():
        return target
    data_root().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=data_root(), prefix=".download-") as tmp:
        archive = Path(tmp) / "helixsr.zip"
        _download(release.url, archive, release.sha256, release.size, "release", report, opener)
        unpacked = Path(tmp) / "files"
        with zipfile.ZipFile(archive) as zipped:
            _safe_members(zipped.namelist())
            zipped.extractall(unpacked)
            for info in zipped.infolist():   # keep the scripts' execute bits
                mode = info.external_attr >> 16
                if mode & 0o111:
                    path = unpacked / info.filename
                    if path.is_file():
                        path.chmod(path.stat().st_mode | 0o111)
        tops = list(unpacked.iterdir())
        root = tops[0] if len(tops) == 1 and tops[0].is_dir() else unpacked
        if not (root / "setup" / "helixsr_setup.py").is_file() or not (root / FSRFG).is_dir():
            raise SetupError(f"HelixSR {release.version}: not a HelixSR 2.0 release")
        shutil.rmtree(target, ignore_errors=True)
        os.replace(root, target)
    return target


# ---- build tools ------------------------------------------------------------------------------

def _host_run(command: list[str], timeout: float = 120, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(sandbox.host(command), capture_output=True, text=True,
                          timeout=timeout, stdin=subprocess.DEVNULL, **kwargs)


def _python_ok(python: str, need_zstd: bool) -> bool:
    check = ("import sys, numpy\n"
             "ok = sys.version_info >= (3, 8)\n")
    if need_zstd:
        check += ("try:\n    import compression.zstd\nexcept ImportError:\n"
                  "    import shutil\n    ok = ok and shutil.which('zstd') is not None\n")
    check += "sys.exit(0 if ok else 1)\n"
    try:
        return _host_run([python, "-c", check], timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def portable_python() -> Path:
    return tools_dir() / "python" / "bin" / "python3"


def find_python() -> Optional[str]:
    """A Python with numpy that can also unpack NVIDIA's zstd package (frame generation):
    the portable one Scaler Assistant set up, HelixSR's own setup's, or the system's."""
    data = Path(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"))
    for candidate in (str(portable_python()), str(data / "HelixSR" / "python" / "bin" / "python3"),
                      "python3"):
        if candidate != "python3" and not Path(candidate).is_file():
            continue
        if _python_ok(candidate, need_zstd=True):
            return candidate
    return None


def get_python(report: Report, opener=None) -> str:
    found = find_python()
    if found:
        return found
    python = portable_python()
    if not python.is_file():
        tools_dir().mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tools_dir(), prefix=".download-") as tmp:
            archive = Path(tmp) / "python.tar.gz"
            _download(PYTHON_URL, archive, PYTHON_SHA, PYTHON_SIZE, "python", report, opener)
            with tarfile.open(archive) as tar:
                _safe_members(tar.getnames())
                tar.extractall(tmp, filter="data") if hasattr(tarfile, "data_filter") \
                    else tar.extractall(tmp)
            shutil.rmtree(tools_dir() / "python", ignore_errors=True)
            os.replace(Path(tmp) / "python", tools_dir() / "python")
    report("numpy", 0, 0, "")
    try:
        done = _host_run([str(python), "-m", "pip", "install", "--quiet",
                          "--disable-pip-version-check", "numpy"], timeout=900)
    except (OSError, subprocess.SubprocessError) as error:
        raise SetupError(f"numpy: {error}") from error
    if done.returncode != 0 or not _python_ok(str(python), need_zstd=True):
        raise SetupError("numpy could not be installed: " + (done.stderr or done.stdout).strip()[-300:])
    return str(python)


def find_wine() -> Optional[str]:
    """Steam's Proton first (official, then custom builds), then a system Wine."""
    home = Path.home()
    patterns = (home / ".local/share/Steam/steamapps/common", home / ".steam/steam/steamapps/common",
                home / ".local/share/Steam/compatibilitytools.d", home / ".steam/root/compatibilitytools.d")
    for index, base in enumerate(patterns):
        try:
            names = sorted(os.listdir(base), reverse=True)
        except OSError:
            continue
        for name in names:
            if index < 2 and not name.startswith("Proton"):
                continue
            wine = base / name / "files" / "bin" / "wine"
            if wine.is_file() and os.access(wine, os.X_OK):
                return str(wine)
    return sandbox.host_which("wine") or sandbox.host_which("wine64")


def get_dxc(wine: str, report: Report, opener=None) -> Path:
    """Microsoft's DXC and a wrapper that runs it through Proton / Wine with Z:\\ paths."""
    tools = tools_dir()
    exe = tools / "dxc-win" / "bin" / "x64" / "dxc.exe"
    if not exe.is_file():
        tools.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tools, prefix=".download-") as tmp:
            archive = Path(tmp) / "dxc.zip"
            _download(DXC_URL, archive, DXC_SHA, 0, "dxc", report, opener)
            out = Path(tmp) / "dxc-win"
            count = 0
            with zipfile.ZipFile(archive) as zipped:   # Windows paths: bin\x64\dxc.exe
                for name in zipped.namelist():
                    rel = name.replace("\\", "/")
                    if rel.startswith("bin/x64/") and not rel.endswith("/") and ".." not in rel:
                        path = out / rel
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(zipped.read(name))
                        count += 1
            if not count:
                raise SetupError("the shader compiler download has no bin/x64")
            shutil.rmtree(tools / "dxc-win", ignore_errors=True)
            os.replace(out, tools / "dxc-win")
    wrapper = tools / "dxc-wine.sh"
    wrapper.write_text(
        "#!/bin/sh\n"
        "# Microsoft's DXC through Proton / Wine: absolute Linux paths become Z:\\ paths\n"
        "first=1\n"
        "for a in \"$@\"; do\n"
        "  [ $first = 1 ] && { set --; first=0; }\n"
        "  case \"$a\" in /*) a=\"Z:$(printf '%s' \"$a\" | tr / '\\\\')\" ;; esac\n"
        "  set -- \"$@\" \"$a\"\n"
        "done\n"
        f"WINEPREFIX={_sh(str(tools / 'wineprefix'))} WINEDEBUG=-all exec {_sh(wine)} "
        f"{_sh(str(exe))} \"$@\"\n")
    wrapper.chmod(0o755)
    return wrapper


def _sh(text: str) -> str:
    return "'" + text.replace("'", "'\\''") + "'"


# ---- the build --------------------------------------------------------------------------------

def status(python: str, folder: Path) -> tuple[bool, bool]:
    """(network built, frame generation built) as HelixSR's setup reports them."""
    try:
        done = _host_run([python, str(folder / "setup" / "helixsr_setup.py"),
                          str(folder / FSRFG), "--status"], timeout=300,
                         env=_env(), cwd=str(folder))
    except (OSError, subprocess.SubprocessError):
        return False, False
    match = re.search(r"network=([01])\s+fg=([01])", done.stdout)
    return (match.group(1) == "1", match.group(2) == "1") if match else (False, False)


def _env() -> dict:
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH", "LD_PRELOAD"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def build(python: str, folder: Path, dxc: Path, report: Report,
          fg_only: bool = False) -> tuple[list[str], int]:
    """Run HelixSR's build program; (its last lines, exit code)."""
    tmp = tools_dir() / "tmp"   # in the home folder: the host and Flatpak's sandbox share it
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    command = ["env", "-u", "PYTHONHOME", "-u", "PYTHONPATH", f"TMPDIR={tmp}",
               python, str(folder / "setup" / "helixsr_setup.py"), str(folder / FSRFG),
               "--dxc", str(dxc), "--yes", *(["--fg-only"] if fg_only else [])]
    lines: list[str] = []
    try:
        process = subprocess.Popen(sandbox.host(command), stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   cwd=str(folder), env=_env())
    except OSError as error:
        raise SetupError(str(error)) from error
    buffer = b""
    assert process.stdout is not None
    while True:
        chunk = process.stdout.read1(4096) if hasattr(process.stdout, "read1") \
            else process.stdout.read(4096)
        if not chunk:
            break
        buffer += chunk
        *complete, buffer = re.split(rb"[\r\n]", buffer)
        for raw in complete:
            line = raw.decode(errors="replace").strip()
            if not line:
                continue
            lines = (lines + [line])[-40:]
            match = _PROGRESS.search(line)
            if match:
                report("build", int(match.group(1)), 100, match.group(2).strip())
            else:
                report("build", -1, 100, line.removeprefix("[helixsr-setup]").strip())
    code = process.wait()
    shutil.rmtree(tools_dir() / "wineprefix", ignore_errors=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return lines, code


@dataclass
class Result:
    folder: HelixSRFolder
    network: bool
    fg: bool
    lines: list[str]


def install(report: Report, release: Optional[Release] = None, opener=None) -> Result:
    """Everything: the release, the tools, the build. Only call it after the user agreed to
    NVIDIA's downloads (the build passes --yes to HelixSR's setup)."""
    started = time.monotonic()
    release = release or latest_release(opener)
    folder = get_release(release, report, opener)
    python = get_python(report, opener)
    network, fg = status(python, folder)
    lines: list[str] = []
    if not (network and fg):
        wine = find_wine()
        if not wine:
            from .i18n import tr
            raise SetupError(tr("hxa_no_wine"))
        dxc = get_dxc(wine, report, opener)
        lines, code = build(python, folder, dxc, report, fg_only=network)
        network, fg = status(python, folder)
        if not network:
            raise SetupError("\n".join(lines[-8:]) or f"exit code {code}")
    for old in data_root().glob("HelixSR-*"):   # earlier versions this module downloaded
        if old.is_dir() and old.resolve() != folder.resolve():
            shutil.rmtree(old, ignore_errors=True)
    report("done", 1, 1, f"{time.monotonic() - started:.0f}s")
    return Result(inspect(folder), network, fg, lines)


def is_managed(folder: Optional[HelixSRFolder]) -> bool:
    try:
        return folder is not None and data_root().resolve() in folder.path.resolve().parents
    except OSError:
        return False
