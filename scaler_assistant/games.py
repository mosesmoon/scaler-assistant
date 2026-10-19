"""What a game folder offers: its upscaler DLLs, the folder of its .exe and its graphics API.

HelixSR gets into a game one of three ways (the names are the ``route`` values
HelixSR's own setup records, so both tools understand each other's installs):

* ``direct`` (f, "FSR way"): the game's FSR 3.1 DLL is replaced by HelixSR.
* ``optiscaler`` (o): OptiScaler next to the game's .exe hands DLSS, XeSS or
  FSR 2 inputs to HelixSR.
* ``dlss`` (d, experimental): HelixSR's DLSS loader and HelixSR as nvngx.dll
  next to the game's .exe.

HelixSR 2.0 and newer has two ways, installed by HelixSR's own installer:

* ``hscaler``: HelixSR Scaler (HelixSR's OptiScaler build) next to the .exe; the game's
  DLSS option runs HelixSR (Direct3D 12, 11 and Vulkan).
* ``direct``: the FSR drop-in, as before.

FSR 4.1 and FSR 3 always go through OptiScaler (see ``installer``).
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from .executables import JUNK_EXE, detect_executables
from .pe import graphics_api

ROUTES = ("direct", "optiscaler", "dlss", "hscaler")
FSR_UPSCALER = "amd_fidelityfx_upscaler_dx12.dll"
FSR_COMBINED = "amd_fidelityfx_dx12.dll"
INPUTS = {
    "nvngx_dlss.dll": "DLSS",
    "libxess.dll": "XeSS",
    "ffx_fsr2_api_x64.dll": "FSR 2",
    "ffx_fsr2_api_dx12_x64.dll": "FSR 2",
}
INPUT_ORDER = ("DLSS", "XeSS", "FSR 2")
FOLDER = "HelixSR"                    # HelixSR's folder next to the .exe (OptiScaler / DLSS ways)
MARKER = "helixsr-install.json"       # HelixSR's install record
SCALER_FOLDER = "ScalerAssistant"     # this tool's folder next to the .exe (FSR 4.1 / FSR 3)
SCALER_MARKER = "scaler-install.json"
OPTI_INI = "OptiScaler.ini"
HX_FSRFG = "HelixSR-fsrfg"            # HelixSR 2.0 in a game with HelixSR Scaler
HX_SCALER_FILES = "HelixSR-Scaler.files"   # HelixSR Scaler's install record
HX_SCALER_BACKUP = "HelixSR-Scaler-backup"
HX_SCALER_SUB = "OptiScaler"          # HelixSR Scaler's own FidelityFX / XeSS DLLs
APIS = ("dx12", "dx11", "vulkan")

_ANTI_CHEAT_DIRS = {"easyanticheat": "Easy Anti-Cheat", "battleye": "BattlEye"}
_ANTI_CHEAT_FILES = (
    (re.compile(r"^start_protected_game\.exe$", re.I), "Easy Anti-Cheat"),
    (re.compile(r"^easyanticheat.*\.(exe|dll|sys)$", re.I), "Easy Anti-Cheat"),
    (re.compile(r"^(beservice|battleye).*\.(exe|dll|sys)$", re.I), "BattlEye"),
)
_WALK_DEPTH = 7
_WALK_MAX_DIRS = 20000


@dataclass
class GameLayout:
    inputs: list[str] = field(default_factory=list)       # DLSS, XeSS, FSR 2
    fsr_targets: list[str] = field(default_factory=list)  # the game's FSR 3.1 DLLs
    exe_dir: Optional[str] = None
    anti_cheat: list[str] = field(default_factory=list)
    api: str = ""                                         # dx12, dx11, vulkan or "" (unknown)
    exe: Optional[str] = None                             # the main .exe in exe_dir

    @property
    def has_fsr31(self) -> bool:
        return bool(self.fsr_targets)

    @property
    def helixsr_possible(self) -> bool:
        """HelixSR is Direct3D 12 only (an unknown API gets the benefit of the doubt)."""
        return self.api in ("dx12", "")

    @property
    def optiscaler_possible(self) -> bool:
        """FSR 4.1 and FSR 3 go through OptiScaler, which needs an upscaler the game already has."""
        return bool(self.exe_dir and (self.inputs or self.fsr_targets))

    def ways(self, loader_available: bool = True, modern: bool = False) -> list[str]:
        """HelixSR routes that work for this game, the default first (FSR way when the game has FSR 3.1).
        modern: HelixSR 2.0 and newer (HelixSR Scaler or the FSR drop-in)."""
        if modern:
            ways = ["hscaler"] if self.exe_dir and (self.inputs or self.fsr_targets) else []
            if self.fsr_targets and self.helixsr_possible:
                ways.insert(0 if self.anti_cheat else len(ways), "direct")
            return ways
        if not self.helixsr_possible:
            return []
        ways = []
        if self.fsr_targets:
            ways.append("direct")
        if self.inputs and self.exe_dir:
            ways.append("optiscaler")
        if "DLSS" in self.inputs and self.exe_dir and loader_available:
            ways.append("dlss")
        return ways

    @property
    def upscalers(self) -> list[str]:
        """Every upscaler the game ships, for display."""
        return [*self.inputs, *(["FSR 3.1"] if self.fsr_targets else [])]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Optional[dict]) -> "GameLayout":
        data = data or {}
        api = data.get("api") or ""
        return cls(inputs=list(data.get("inputs") or []),
                   fsr_targets=list(data.get("fsr_targets") or []),
                   exe_dir=data.get("exe_dir"),
                   anti_cheat=list(data.get("anti_cheat") or []),
                   api=api if api in APIS else "",
                   exe=data.get("exe"))


def walk(folder: Path, depth: int = _WALK_DEPTH) -> list[tuple[Path, list[str], list[str]]]:
    """(directory, sub-directory names, file names) under folder, without following links.

    HelixSR's and this tool's own folders are skipped: what is inside them is not the game's.
    """
    out: list[tuple[Path, list[str], list[str]]] = []
    todo = [(Path(folder), 0)]
    while todo and len(out) < _WALK_MAX_DIRS:
        directory, level = todo.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError:
            continue
        dirs = [e.name for e in entries if e.is_dir(follow_symlinks=False)]
        files = [e.name for e in entries if e.is_file(follow_symlinks=False) or e.is_symlink()]
        out.append((directory, dirs, files))
        if level < depth:
            hx_scaler = HX_SCALER_FILES in files
            todo += [(directory / name, level + 1) for name in dirs
                     if name not in (FOLDER, SCALER_FOLDER, HX_FSRFG, HX_SCALER_BACKUP)
                     and not (hx_scaler and name == HX_SCALER_SUB)]
    return out


def _largest_exe(tree, directory: Optional[Path] = None) -> Optional[Path]:
    best, size = None, -1
    for folder, _, files in tree:
        if directory is not None and folder != directory:
            continue
        for name in files:
            if not name.lower().endswith(".exe") or JUNK_EXE.search(name):
                continue
            try:
                current = (folder / name).stat().st_size
            except OSError:
                continue
            if name.lower().endswith("-win64-shipping.exe"):
                current += 1 << 40   # Unreal Engine: always the game itself
            if current > size:
                best, size = folder / name, current
    return best


def find_exe(install_dir: Path, tree, appinfo: Optional[dict]) -> Optional[Path]:
    """The game's main .exe; its folder is where OptiScaler or the DLSS loader must go."""
    for directory, dirs, files in tree:   # a folder that already has HelixSR, us or OptiScaler wins
        if ((FOLDER in dirs and (directory / FOLDER / MARKER).is_file())
                or (SCALER_FOLDER in dirs and (directory / SCALER_FOLDER / SCALER_MARKER).is_file())
                or HX_SCALER_FILES in files or OPTI_INI in files):
            return _largest_exe(tree, directory) or directory / "?"
    for path in detect_executables(install_dir, appinfo):
        if path.suffix.lower() == ".exe":
            return path
    return _largest_exe(tree)


def detect_api(exe: Optional[Path], tree, exe_dir: Optional[Path]) -> str:
    """The graphics API from the main .exe's imports, with fallbacks for games that load
    their renderer at run time.

    Many games link D3D11 (or Vulkan) statically and load D3D12 only when they start
    rendering with it, so the import table alone can say "DX11" for a DX12 game. Proof
    of a D3D12 renderer wins: the FSR 3.1 DLLs (they only have a D3D12 back end), the
    D3D12 Agility SDK next to the .exe, or (for a D3D11 import) the .exe naming
    d3d12.dll itself.
    """
    exes = [exe] if exe and exe.is_file() else []
    api = graphics_api(exes)
    if api == "dx12":
        return api
    names = {n.lower() for d, _, files in tree for n in files}
    agility = exe_dir is not None and (exe_dir / "D3D12" / "D3D12Core.dll").is_file()
    if agility or names & {FSR_UPSCALER, FSR_COMBINED, "ffx_fsr2_api_dx12_x64.dll"}:
        return "dx12"   # a D3D12 renderer is certainly there
    if api == "dx11" or not api:
        for path in exes:
            if _mentions(path, rb"d3d12\.dll"):
                return "dx12"   # loads D3D12 at run time
    if api:
        return api
    if "libxess.dll" in names:
        return "dx12"   # XeSS's D3D12 DLL
    if "libxess_dx11.dll" in names:
        return "dx11"
    return ""


def _mentions(path: Path, pattern: bytes) -> bool:
    """True when the file contains the pattern (searched in place, never copied)."""
    import mmap
    try:
        with open(path, "rb") as handle:
            if os.fstat(handle.fileno()).st_size == 0:
                return False
            with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
                return re.compile(b"(?i)" + pattern).search(data) is not None
    except (OSError, ValueError):
        return False


def detect_layout(install_dir: Path | str, appinfo: Optional[dict] = None) -> GameLayout:
    install_dir = Path(install_dir)
    tree = walk(install_dir)
    inputs: set[str] = set()
    upscaler: list[Path] = []
    combined: list[Path] = []
    anti_cheat: set[str] = set()
    for directory, dirs, files in tree:
        for name in dirs:
            label = _ANTI_CHEAT_DIRS.get(name.lower())
            if label:
                anti_cheat.add(label)
        for name in files:
            lower = name.lower()
            if lower in INPUTS:
                inputs.add(INPUTS[lower])
            elif lower == FSR_UPSCALER:
                upscaler.append(directory / name)
            elif lower == FSR_COMBINED:
                combined.append(directory / name)
            for pattern, label in _ANTI_CHEAT_FILES:
                if pattern.match(name):
                    anti_cheat.add(label)
    # HelixSR replaces the upscaler DLL; only games without one use the combined DLL.
    targets = sorted(upscaler or combined)
    exe = find_exe(install_dir, tree, appinfo) if (inputs or targets) else None
    exe_dir = exe.parent if exe else None
    return GameLayout(
        inputs=[label for label in INPUT_ORDER if label in inputs],
        fsr_targets=[str(p) for p in targets],
        exe_dir=str(exe_dir) if exe_dir else None,
        anti_cheat=sorted(anti_cheat),
        api=detect_api(exe, tree, exe_dir) if exe else "",
        exe=str(exe) if exe and exe.is_file() else None,
    )
