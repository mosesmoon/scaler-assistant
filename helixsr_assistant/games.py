"""What a game folder offers HelixSR: its upscaler DLLs and the folder of its .exe.

HelixSR gets into a game one of three ways (the names are the ``route`` values
HelixSR's own setup records, so both tools understand each other's installs):

* ``direct`` (f, "FSR way"): the game's FSR 3.1 DLL is replaced by HelixSR.
* ``optiscaler`` (o): OptiScaler next to the game's .exe hands DLSS, XeSS or
  FSR 2 inputs to HelixSR.
* ``dlss`` (d, experimental): HelixSR's DLSS loader and HelixSR as nvngx.dll
  next to the game's .exe.
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from .executables import JUNK_EXE, detect_executables

ROUTES = ("direct", "optiscaler", "dlss")
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
OPTI_INI = "OptiScaler.ini"

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

    @property
    def has_fsr31(self) -> bool:
        return bool(self.fsr_targets)

    def ways(self, loader_available: bool = True) -> list[str]:
        """Routes that work for this game, the default first (FSR way when the game has FSR 3.1)."""
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
        return cls(inputs=list(data.get("inputs") or []),
                   fsr_targets=list(data.get("fsr_targets") or []),
                   exe_dir=data.get("exe_dir"),
                   anti_cheat=list(data.get("anti_cheat") or []))


def walk(folder: Path, depth: int = _WALK_DEPTH) -> list[tuple[Path, list[str], list[str]]]:
    """(directory, sub-directory names, file names) under folder, without following links.

    HelixSR's own folders are skipped: what is inside them belongs to HelixSR.
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
            todo += [(directory / name, level + 1) for name in dirs if name != FOLDER]
    return out


def _largest_exe_dir(tree) -> Optional[Path]:
    best, size = None, -1
    for directory, _, files in tree:
        for name in files:
            if not name.lower().endswith(".exe") or JUNK_EXE.search(name):
                continue
            try:
                current = (directory / name).stat().st_size
            except OSError:
                continue
            if name.lower().endswith("-win64-shipping.exe"):
                current += 1 << 40   # Unreal Engine: always the game itself
            if current > size:
                best, size = directory, current
    return best


def find_exe_dir(install_dir: Path, tree, appinfo: Optional[dict]) -> Optional[Path]:
    """The folder of the game's main .exe, where OptiScaler or the DLSS loader must go."""
    for directory, dirs, files in tree:   # a folder that already has HelixSR or OptiScaler wins
        if (FOLDER in dirs and (directory / FOLDER / MARKER).is_file()) or OPTI_INI in files:
            return directory
    for path in detect_executables(install_dir, appinfo):
        if path.suffix.lower() == ".exe":
            return path.parent
    return _largest_exe_dir(tree)


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
    exe_dir = find_exe_dir(install_dir, tree, appinfo) if (inputs or targets) else None
    return GameLayout(
        inputs=[label for label in INPUT_ORDER if label in inputs],
        fsr_targets=[str(p) for p in targets],
        exe_dir=str(exe_dir) if exe_dir else None,
        anti_cheat=sorted(anti_cheat),
    )
