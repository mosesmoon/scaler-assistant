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

    @property
    def dll(self) -> Path:
        return self.path / DLL

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
        return (self.path / LOADER_DIR / LOADER).is_file()

    @property
    def has_optiscaler(self) -> bool:
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
        if route == "optiscaler":
            needed += [self.path / OPTI_DIR / n for n in (OPTI_DLL, OPTI_INI) + OPTI_EXTRA]
            needed += [self.fsr_source(), self.path / AMD_DIR / AMD_FG]
        elif route == "dlss":
            needed.append(self.path / LOADER_DIR / LOADER)
        return [p for p in needed if not p.is_file()]


def inspect(path: Path | str) -> HelixSRFolder:
    folder = Path(path).expanduser()
    dll = folder / DLL
    return HelixSRFolder(folder, dll_version(dll), has_network(dll))


def looks_like_helixsr(path: Path) -> bool:
    return (path / SETUP).is_file() and (path / DLL).is_file()


def _search_roots() -> Iterable[tuple[Path, int]]:
    home = Path.home()
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
