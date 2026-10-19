"""The user's HelixSR folder: the official release they downloaded and set up.

Scaler Assistant ships none of HelixSR's files. It only copies files from the
folder the user extracted HelixSR into, after HelixSR's own ``helixsr-setup``
has built the network into ``amd_fidelityfx_dx12.dll`` on their PC (that DLL
then carries NVIDIA's network and must never leave the user's computer).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

DLL = "amd_fidelityfx_dx12.dll"              # HelixSR (with the network after setup)
SETUP = "helixsr-setup.sh"
OPTI_DIR = "optiscaler"                      # official OptiScaler release in the HelixSR folder
OPTI_DLL = "OptiScaler.dll"
OPTI_INI = "OptiScaler.ini"
OPTI_EXTRA = ("fakenvapi.dll", "fakenvapi.ini")
AMD_DIR = "amd-fsr"
AMD_UPSCALER = "amd_fidelityfx_upscaler_dx12.dll"
AMD_FG = "amd_fidelityfx_framegeneration_dx12.dll"
LOADER_DIR = "dlss-loader"
LOADER = "dxgi.dll"
MY_FSR = "my-fsr"
# HelixSR 2.0 and newer: the DLL is built in HelixSR-fsrfg, games get HelixSR Scaler (HelixSR's own
# OptiScaler build, in helixsr-scaler) or the FSR drop-in, installed by the release's own installer
# (setup/helixsr_bridge.py, run as a separate program, never copied).
FSRFG = "HelixSR-fsrfg"
BRIDGE = "setup/helixsr_bridge.py"
SCALER_PKG = "helixsr-scaler"
SCALER_DLL = "OptiScaler.dll"
FG_DIR = "helixsr-fg"                         # HelixSR's frame generation, in HelixSR-fsrfg
# What the setup puts into helixsr-fg when it builds frame generation (the release only has
# the executor): NVIDIA's NGX core, NVIDIA's DLSS Frame Generation DLL and its data.
FG_BUILT = ("_nvngx.dll", "nvngx_dlssg.dll", "hxfg_data.bin")
_SCALER_VERSION = re.compile(rb"HelixSR Scaler v(\d+\.\d+\.\d+)")

NETWORK_TAG = b"HXSRNET1"                    # trailer of a DLL that carries the network
# One-file DLL (network inside), the f/o setup and the record format this tool writes.
MIN_VERSION = (1, 8, 0)
# Settings that only newer HelixSR versions read.
INT8_VERSION = (1, 9, 0)

_VERSION_EXACT = re.compile(rb"\x00HelixSR (\d+\.\d+\.\d+)\x00")
_VERSION_ANY = re.compile(rb"HelixSR (\d+\.\d+\.\d+)")
_SCAN_BYTES = 4 << 20


def parse_version(text: Optional[str]) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in str(text).split("."))
    except ValueError:
        return ()


_version_cache: dict[tuple[str, int, int], Optional[str]] = {}


def dll_version(path: Path) -> Optional[str]:
    """HelixSR's version if the file is a HelixSR DLL, else None (cached per file state)."""
    try:
        info = os.stat(path)
    except OSError:
        return None
    key = (str(path), info.st_size, info.st_mtime_ns)
    if key in _version_cache:
        return _version_cache[key]
    try:
        with open(path, "rb") as handle:
            head = handle.read(_SCAN_BYTES)
    except OSError:
        return None
    match = _VERSION_EXACT.search(head) or _VERSION_ANY.search(head)
    version = match.group(1).decode() if match else None
    if len(_version_cache) > 4096:
        _version_cache.clear()
    _version_cache[key] = version
    return version


def is_helixsr(path: Path) -> bool:
    return dll_version(path) is not None


def has_network(path: Path) -> bool:
    """True when helixsr-setup has appended the network to the DLL."""
    try:
        with open(path, "rb") as handle:
            handle.seek(-32, os.SEEK_END)
            return handle.read(8) == NETWORK_TAG
    except OSError:
        return False


def contains(path: Path, needle: bytes, limit: int = 32 << 20) -> bool:
    try:
        with open(path, "rb") as handle:
            return needle in handle.read(limit)
    except OSError:
        return False


def is_optiscaler(path: Path) -> bool:
    return contains(path, b"OptiScaler")


def is_loader(path: Path) -> bool:
    return contains(path, b"HelixSR DLSS loader", 1 << 20)


def is_fidelityfx(path: Path) -> bool:
    return contains(path, b"ffxCreateContext")


@dataclass
class HelixSRFolder:
    path: Path
    version: Optional[str]
    built: bool
    modern: bool = False          # HelixSR 2.0 layout (HelixSR-fsrfg, HelixSR Scaler, the bridge)

    @property
    def dll(self) -> Path:
        return self.path / FSRFG / DLL if self.modern else self.path / DLL

    @property
    def bridge(self) -> Path:
        return self.path / BRIDGE

    @property
    def scaler_pkg(self) -> Path:
        return self.path / SCALER_PKG

    @property
    def fg_ready(self) -> bool:
        """HelixSR's setup built frame generation (HelixSR 2.0 and newer)."""
        fg = self.path / FSRFG / FG_DIR
        if not self.modern or not (fg / "nvexec64.dll").is_file():
            return False
        names = {p.name.lower() for p in fg.rglob("*") if p.is_file()}
        return all(n.lower() in names for n in FG_BUILT)

    def scaler_version(self) -> Optional[str]:
        """HelixSR Scaler's version, from its DLL (HelixSR 2.0 and newer)."""
        try:
            with open(self.scaler_pkg / SCALER_DLL, "rb") as handle:
                match = _SCALER_VERSION.search(handle.read(64 << 20))
        except OSError:
            return None
        return match.group(1).decode() if match else None

    @property
    def version_tuple(self) -> tuple[int, ...]:
        return parse_version(self.version)

    @property
    def supported(self) -> bool:
        return bool(self.version) and self.version_tuple >= MIN_VERSION

    @property
    def ready(self) -> bool:
        return self.supported and self.built

    @property
    def problem(self) -> Optional[str]:
        """i18n key describing why the folder can't be used, or None."""
        if not self.version:
            return "hx_not_helixsr"
        if not self.supported:
            return "hx_too_old"
        if not self.built:
            return "hx_not_built"
        return None

    @property
    def has_loader(self) -> bool:
        return not self.modern and (self.path / LOADER_DIR / LOADER).is_file()

    @property
    def has_optiscaler(self) -> bool:
        if self.modern:
            return False
        base = self.path / OPTI_DIR
        return all((base / name).is_file() for name in (OPTI_DLL, OPTI_INI) + OPTI_EXTRA)

    def reads_int8(self) -> bool:
        return self.version_tuple >= INT8_VERSION

    def fsr_source(self) -> Path:
        """The FSR DLL OptiScaler lists next to HelixSR: one the user put into my-fsr, else AMD's."""
        mine = self.path / MY_FSR
        if mine.is_dir():
            for candidate in sorted(mine.iterdir()):
                if candidate.suffix.lower() == ".dll" and is_fidelityfx(candidate):
                    return candidate
        return self.path / AMD_DIR / AMD_UPSCALER

    def missing_for(self, route: str) -> list[Path]:
        """Files of this folder that a route copies but that are not there."""
        needed = [self.dll]
        if self.modern:
            needed.append(self.bridge)
            if route == "hscaler":
                needed.append(self.scaler_pkg / SCALER_DLL)
            return [p for p in needed if not p.is_file()]
        if route == "optiscaler":
            needed += [self.path / OPTI_DIR / n for n in (OPTI_DLL, OPTI_INI) + OPTI_EXTRA]
            needed += [self.fsr_source(), self.path / AMD_DIR / AMD_FG]
        elif route == "dlss":
            needed.append(self.path / LOADER_DIR / LOADER)
        return [p for p in needed if not p.is_file()]


def inspect(path: Path | str) -> HelixSRFolder:
    folder = Path(path).expanduser()
    modern = (folder / FSRFG / DLL).is_file()
    dll = folder / FSRFG / DLL if modern else folder / DLL
    return HelixSRFolder(folder, dll_version(dll), has_network(dll), modern)


def looks_like_helixsr(path: Path) -> bool:
    return (path / SETUP).is_file() and ((path / DLL).is_file() or (path / FSRFG / DLL).is_file())


def _search_roots() -> Iterable[tuple[Path, int]]:
    home = Path.home()
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    yield data / "scaler-assistant" / "helixsr", 1    # downloaded and built by Scaler Assistant
    yield home, 2
    for name in ("Downloads", "下載", "下载", "ダウンロード", "Desktop", "桌面", "デスクトップ",
                 "Games", "Applications", "Apps", "Programs", "Tools", "opt"):
        yield home / name, 2


def find_candidates() -> list[HelixSRFolder]:
    """HelixSR folders in the usual places, best first (set up, newest)."""
    found: dict[Path, HelixSRFolder] = {}
    for root, depth in _search_roots():
        todo = [(root, 0)]
        while todo:
            folder, level = todo.pop()
            try:
                entries = [e for e in os.scandir(folder) if e.is_dir(follow_symlinks=False)]
            except OSError:
                continue
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                path = Path(entry.path)
                if looks_like_helixsr(path):
                    key = path.resolve()
                    found.setdefault(key, inspect(key))
                elif level + 1 < depth:
                    todo.append((path, level + 1))
    return sorted(found.values(),
                  key=lambda f: (f.ready, f.supported, f.version_tuple), reverse=True)
