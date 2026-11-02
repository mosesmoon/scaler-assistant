"""Files Scaler Assistant downloads for FSR 4.1 and FSR 3: OptiScaler and the FSR 4.1 DLLs.

Every download is pinned to one release and checked by size and SHA-256
before anything is unpacked. Only the files games need are kept, in
``~/.local/share/scaler-assistant/components/<name>-<version>/``, with a
manifest of their SHA-256 (used to tell whether a game has the current copy).

HelixSR is not here: its licence allows using only the user's own set-up
HelixSR folder (see ``helixsr``).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

Progress = Callable[[int, int], None]   # (bytes done, bytes total)
MANIFEST = ".scaler-assistant.json"
SEVEN_ZIP_ENV = "SCALER_ASSISTANT_7Z"


class ComponentError(RuntimeError):
    pass


@dataclass(frozen=True)
class Component:
    key: str
    version: str
    url: str
    sha256: str
    size: int
    archive: str                       # "7z" or "zip"
    members: tuple[str, ...]           # files kept from the archive
    project: str
    licence: str
    notes: tuple[str, ...] = field(default_factory=tuple)   # files to show before first use


OPTISCALER = Component(
    key="optiscaler",
    version="0.9.4",
    url="https://github.com/optiscaler/OptiScaler/releases/download/v0.9.4/"
        "Optiscaler_0.9.4-final.20260718._MM.7z",
    sha256="575cb4df866116093df75af607e37fd70e10f5163e0f23fd5c804142e80ef0ad",
    size=55016448,
    archive="7z",
    members=(
        "OptiScaler.dll", "OptiScaler.ini", "fakenvapi.dll", "fakenvapi.ini",
        "amd_fidelityfx_dx12.dll", "amd_fidelityfx_upscaler_dx12.dll",
        "amd_fidelityfx_framegeneration_dx12.dll", "amd_fidelityfx_vk.dll",
        "Licenses/FidelityFX_v1_LICENSE.md", "Licenses/FidelityFX_v2_LICENSE.md",
    ),
    project="https://github.com/optiscaler/OptiScaler",
    licence="GPL-3.0 (OptiScaler), MIT (fakenvapi), AMD FidelityFX licence (AMD DLLs)",
)

_FSR4_RELEASE = "dll-2026-11-01"
_FSR4_BASE = ("https://github.com/zgauthier2000/fsr4-shader-performance-overrides/releases/download/"
              f"{_FSR4_RELEASE}/")
# Four builds in every archive: the full FSR 4 network (exact; lossy, retrained, network on every
# other frame) and AMD's smaller FSR 4.1.2 Lite network (4.1.2l-exact; 4.1.2l-lossy).
FSR4_FOLDERS = {"exact": "exact", "lossy": "lossy", "lite": "4.1.2l-exact",
                "lite_lossy": "4.1.2l-lossy"}
_FSR4_MEMBERS = ("NOTICE.md", "WHICH-SHOULD-I-CHOOSE.txt",
                 "exact/amd_fidelityfx_upscaler_dx12.dll",
                 "lossy/amd_fidelityfx_upscaler_dx12.dll", "lossy/WARNING.txt",
                 "4.1.2l-exact/amd_fidelityfx_upscaler_dx12.dll",
                 "4.1.2l-lossy/amd_fidelityfx_upscaler_dx12.dll", "4.1.2l-lossy/WARNING.txt")
# One build per kind of GPU (gpu.fsr4_pack): each carries only the shader changes that help it.
# Every build runs on every GPU before RDNA 4; the one for the GPU is the fastest there.
_FSR4_PACKS = {
    "rx7000": ("fsr4.1.2-cyboman-rx7000-2026-11-01.7z",
               "743adcd599dee3cbf6035ed08ceeced987b75178f74a22b945a421d030d8d34e", 9966908),
    "rx6000": ("fsr4.1.2-cyboman-rx6000-2026-11-01.7z",
               "c20ba73a9a5e6dc16ef7bf6329698541539cb1bc4a67846ef285c85676590315", 9978508),
    "igpu_rdna3": ("fsr4.1.2-igpu-cyboman-rdna3-2026-11-01.7z",
                   "76d23e608e42b3c1cc58d05c6efb4f522162896c0635719705e850a30d5c7658", 9922815),
    "igpu_rdna2": ("fsr4.1.2-igpu-cyboman-rdna2-2026-11-01.7z",
                   "258912efd91b95ac2bffdfb392375ba7b46bc67beefd0732ebe94a27ada17779", 9664389),
}
FSR4 = {
    pack: Component(
        key="fsr4-" + pack.replace("_", "-"), version=_FSR4_RELEASE, url=_FSR4_BASE + name,
        sha256=sha, size=size, archive="7z", members=_FSR4_MEMBERS,
        project="https://github.com/zgauthier2000/fsr4-shader-performance-overrides",
        licence="GPL-2.0-or-later, modified AMD DLL with AMD's notice",
        notes=("lossy/WARNING.txt", "4.1.2l-lossy/WARNING.txt"))
    for pack, (name, sha, size) in _FSR4_PACKS.items()
}
FSR4_PACKS = tuple(_FSR4_PACKS)
ALL = (OPTISCALER, *FSR4.values())


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "scaler-assistant" / "components"


def folder(component: Component, root: Optional[Path] = None) -> Path:
    return (root or data_dir()) / f"{component.key}-{component.version}"


def manifest(component: Component, root: Optional[Path] = None) -> dict[str, str]:
    """relative path -> sha256 of the kept files, or {} when not (completely) downloaded."""
    base = folder(component, root)
    try:
        data = json.loads((base / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, dict) or set(files) != set(component.members):
        return {}
    if not all((base / name).is_file() for name in files):
        return {}
    return files


def ready(component: Component, root: Optional[Path] = None) -> bool:
    return bool(manifest(component, root))


def path(component: Component, member: str, root: Optional[Path] = None) -> Path:
    return folder(component, root) / member


def sha256_file(file: Path) -> str:
    digest = hashlib.sha256()
    with open(file, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seven_zip() -> Optional[list[str]]:
    """A command that unpacks .7z with the BCJ2 filter OptiScaler's archive uses."""
    bundled = os.environ.get(SEVEN_ZIP_ENV)
    if bundled and os.access(bundled, os.X_OK):
        return [bundled, "x", "-y", "-bso0", "-bsp0"]
    for name in ("7zz", "7zzs", "7z", "7za"):
        found = shutil.which(name)
        if found:
            return [found, "x", "-y", "-bso0", "-bsp0"]
    found = shutil.which("bsdtar")
    if found:
        return [found]
    return None


# CA bundles of the common Linux distributions (SteamOS and Arch: the first and the last).
CA_FILES = (
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
    "/etc/ssl/ca-bundle.pem",
    "/etc/ssl/cert.pem",
    "/etc/ca-certificates/extracted/tls-ca-bundle.pem",
)
_context: Optional[ssl.SSLContext] = None


def tls_context() -> ssl.SSLContext:
    """A verifying TLS context that trusts the system's certificate authorities.

    A Python built elsewhere (Decky Loader runs plugins inside its own bundled Python)
    looks for them where its build machine kept them and finds none, so every HTTPS
    download fails with CERTIFICATE_VERIFY_FAILED. Then the system's bundle is loaded.
    Certificates are always checked."""
    global _context
    if _context is not None:
        return _context
    context = ssl.create_default_context()
    if not context.cert_store_stats().get("x509_ca"):
        paths = ssl.get_default_verify_paths()
        found = False
        for candidate in (os.environ.get("SSL_CERT_FILE"), paths.cafile, *CA_FILES):
            if candidate and os.path.isfile(candidate):
                try:
                    context.load_verify_locations(cafile=candidate)
                except (OSError, ssl.SSLError):
                    continue
                found = True
                break
        if not found and os.path.isdir("/etc/ssl/certs"):
            context.load_verify_locations(capath="/etc/ssl/certs")
    _context = context
    return context


def open_url(request, timeout: float):
    return urllib.request.urlopen(request, timeout=timeout, context=tls_context())


def _download(component: Component, target: Path, progress: Progress,
              opener: Callable = open_url) -> None:
    digest = hashlib.sha256()
    done = 0
    request = urllib.request.Request(component.url, headers={"User-Agent": "Scaler-Assistant"})
    try:
        with opener(request, timeout=60) as response, open(target, "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                progress(done, component.size)
    except OSError as error:
        raise ComponentError(f"{component.url}: {error}") from error
    if done != component.size or digest.hexdigest() != component.sha256:
        raise ComponentError(f"{component.url}: size or SHA-256 does not match")


def _extract(component: Component, archive: Path, into: Path) -> None:
    if component.archive == "zip":
        with zipfile.ZipFile(archive) as zipped:
            for member in component.members:
                target = into / member
                target.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(member) as source, open(target, "wb") as out:
                    shutil.copyfileobj(source, out)
        return
    command = seven_zip()
    if command is None:
        raise ComponentError("7z")
    if Path(command[0]).name == "bsdtar":
        args = [*command, "-x", "-f", str(archive), "-C", str(into), *component.members]
    else:
        args = [*command, f"-o{into}", str(archive), *component.members]
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise ComponentError(result.stdout.strip()[-400:] or f"exit {result.returncode}")


def fetch(component: Component, progress: Progress = lambda *_: None,
          root: Optional[Path] = None, opener: Callable = open_url) -> Path:
    """Download, verify and unpack a component (nothing is left half-done)."""
    if ready(component, root):
        return folder(component, root)
    base = folder(component, root)
    base.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=base.parent, prefix=".download-") as tmp:
        archive = Path(tmp) / f"archive.{component.archive}"
        _download(component, archive, progress, opener)
        staging = Path(tmp) / "files"
        staging.mkdir()
        _extract(component, archive, staging)
        missing = [m for m in component.members if not (staging / m).is_file()]
        if missing:
            raise ComponentError(f"{component.url}: missing {', '.join(missing)}")
        files = {m: sha256_file(staging / m) for m in component.members}
        (staging / MANIFEST).write_text(json.dumps(
            {"key": component.key, "version": component.version, "url": component.url,
             "files": files}, indent=1) + "\n", encoding="utf-8")
        if base.exists():
            shutil.rmtree(base)
        os.replace(staging, base)
    return base


def remove(component: Component, root: Optional[Path] = None) -> None:
    base = folder(component, root)
    if base.exists():
        shutil.rmtree(base)


def stale_folders(root: Optional[Path] = None) -> list[Path]:
    """Downloaded folders of versions this build no longer uses."""
    base = root or data_dir()
    current = {folder(c, base).name for c in ALL}
    try:
        return sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")
                      and p.name not in current)
    except OSError:
        return []
