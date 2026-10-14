"""Install, switch, update, repair and remove HelixSR in one game.

This is HelixSR Assistant's own code. It carries out the steps HelixSR's README
documents for installing by hand, and keeps HelixSR's install record
(``helixsr-install.json``), backups (``HelixSR/backup``, ``*.original.dll``)
and file names, so HelixSR's own setup and uninstaller recognise games set up
here, and HelixSR Assistant recognises games set up with HelixSR's setup.

Every file copied into a game comes from the user's HelixSR folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import settings
from .games import FOLDER, MARKER, OPTI_INI, GameLayout
from .helixsr import (
    AMD_DIR, AMD_FG, DLL, LOADER, LOADER_DIR, OPTI_DIR, OPTI_DLL, OPTI_EXTRA, HelixSRFolder,
    dll_version, has_network, is_helixsr, is_loader, is_optiscaler,
)
from .i18n import tr

BACKUP = "backup"
OWN = "helixsr.dll"                     # OptiScaler's FfxDx12Path
OWN_SR = "helixsr_upscaler.dll"         # OptiScaler's FfxDx12SRPath (must be a second file)
AMD_FSR_COPY = "amd_fidelityfx_upscaler_dx12.amd.dll"   # AMD's FSR, listed next to HelixSR
CORE = "nvngx.dll"                      # HelixSR under the DLSS core's name (DLSS way)
LOG = "helixsr.log"
LOADER_LOG = "helixsr_loader.log"
OPTI_LOG = "OptiScaler.log"
MY_FSR = "my-fsr"
MY_FSR_NOTE = "README.txt"
# The names OptiScaler can be loaded under (the game may already have one).
OPTI_NAMES = ("dxgi.dll", "winmm.dll", "version.dll", "dbghelp.dll", "d3d12.dll",
              "wininet.dll", "winhttp.dll", "OptiScaler.asi")
# Separate network files of HelixSR 1.4-1.7; one-file DLLs read their own copy.
NETWORK_FILES = ("helixsr_weights.bin", "helixsr_kernels.pak")
# HelixSR DLLs that older versions left in the game's HelixSR folder.
OLD_COPIES = (CORE, DLL, "amd_fidelityfx_upscaler_dx12.dll")
TEMP_SUFFIX = ".helixsr-assistant.tmp"

MY_FSR_TEXT = (
    "HelixSR Assistant made this folder for HelixSR.\r\n\r\n"
    "Put an FSR upscaler DLL here (for example FSR 4) and start the game again: OptiScaler lists\r\n"
    "it next to HelixSR (press Insert in the game: Upscaling > Upscalers > FFX Upscaler).\r\n"
    "Delete the DLL to go back. This folder is left in place on removal if you put files here.\r\n"
)


class InstallError(RuntimeError):
    pass


def original(target: Path) -> Path:
    return target.with_name(target.stem + ".original.dll")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_record(directory: Path) -> dict:
    try:
        data = json.loads((directory / MARKER).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_record(directory: Path, record: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / MARKER).write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


def copy_verified(src: Path, dst: Path) -> None:
    """Copy through a temporary file and check the result byte for byte."""
    tmp = dst.with_name(dst.name + TEMP_SUFFIX)
    try:
        shutil.copyfile(src, tmp)
        if tmp.stat().st_size != src.stat().st_size or sha256(tmp) != sha256(src):
            raise InstallError(tr("err_copy_changed", file=dst))
        os.replace(tmp, dst)
    finally:
        if tmp.exists():
            tmp.unlink()


def _remove(path: Path) -> bool:
    if path.exists() or path.is_symlink():
        path.unlink()
        return True
    return False


def _rmdir(path: Path) -> None:
    try:
        path.rmdir()
    except OSError:
        pass


def win_path(path: Path) -> str:
    """A path as OptiScaler (running under Proton) reads it: the Linux root is Z:."""
    return "Z:" + str(Path(path).resolve()).replace("/", "\\")


def set_ini_value(text: str, section: str, key: str, value: str) -> str:
    """Set ``key=value`` in an OptiScaler.ini, keeping every other line as it is."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    pattern = re.compile(r"^(\s*)%s(\s*)=" % re.escape(key))
    hits = [i for i, line in enumerate(lines) if pattern.match(line)]
    if len(hits) > 1:
        raise InstallError(tr("err_ini_duplicate", name=key, file=OPTI_INI))
    if hits:
        line = lines[hits[0]]
        ending = line[len(line.rstrip("\r\n")):] or newline
        lines[hits[0]] = f"{key}={value}{ending}"
        return "".join(lines)
    header = re.compile(r"^\s*\[%s\]\s*$" % re.escape(section), re.I)
    for i, line in enumerate(lines):
        if header.match(line):
            lines.insert(i + 1, f"{key}={value}{newline}")
            return "".join(lines)
    if lines and not lines[-1].endswith(("\n", "\r")):
        lines[-1] += newline
    lines.append(f"[{section}]{newline}{key}={value}{newline}")
    return "".join(lines)


def _read_text(path: Path) -> str:
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as handle:
        return handle.read()


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        handle.write(text)


# ---- state ------------------------------------------------------------------------

@dataclass
class InstallState:
    route: Optional[str] = None
    version: Optional[str] = None
    issues: list[str] = field(default_factory=list)     # i18n keys
    dll_files: list[Path] = field(default_factory=list)  # HelixSR's DLL(s) inside the game
    ini_dirs: list[Path] = field(default_factory=list)   # where helixsr.ini is read
    log_files: list[Path] = field(default_factory=list)
    chosen: bool = False                                 # OptiScaler picked for an FSR 3.1 game
    installed_by: str = ""

    @property
    def installed(self) -> bool:
        return self.route is not None

    def outdated(self, folder: Optional[HelixSRFolder]) -> bool:
        """True when the HelixSR folder holds a different build than the game."""
        if not self.installed or folder is None or not folder.ready:
            return False
        try:
            size = folder.dll.stat().st_size
        except OSError:
            return False
        for path in self.dll_files:
            try:
                if dll_version(path) != folder.version or path.stat().st_size != size:
                    return True
            except OSError:
                continue
        return False


def state(layout: GameLayout) -> InstallState:
    exe = Path(layout.exe_dir) if layout.exe_dir else None
    folder = exe / FOLDER if exe else None
    record = read_record(folder) if folder else {}
    if folder and record and record.get("route") == "dlss":
        core, loader = exe / CORE, exe / LOADER
        issues = [] if is_helixsr(core) and is_loader(loader) else ["is_files_replaced"]
        return InstallState("dlss", dll_version(core) or record.get("helixsr"), issues, [core],
                            [exe], [exe / LOG, exe / LOADER_LOG, folder / LOG],
                            installed_by=str(record.get("installed_by") or ""))
    if folder and (folder / MARKER).is_file():
        opti = exe / str(record.get("optiscaler") or "dxgi.dll")
        own = folder / OWN
        issues = []
        if not (is_optiscaler(opti) and is_helixsr(own)):
            issues.append("is_files_replaced")
        return InstallState("optiscaler", dll_version(own) or record.get("helixsr"), issues,
                            [own, folder / OWN_SR], [folder], [folder / LOG, exe / OPTI_LOG],
                            chosen=record.get("chosen") == "optiscaler",
                            installed_by=str(record.get("installed_by") or ""))
    targets = [Path(t) for t in layout.fsr_targets]
    dropped = [t for t in targets if original(t).exists() or is_helixsr(t)]
    if dropped:
        helixsr_files = [t for t in dropped if is_helixsr(t)]
        issues = []
        if any(original(t).exists() and not is_helixsr(t) for t in dropped):
            issues.append("is_game_updated")
        if any(is_helixsr(t) and not original(t).exists() for t in dropped):
            issues.append("is_no_backup")
        version = dll_version(helixsr_files[0]) if helixsr_files else None
        record = read_record(dropped[0].parent)
        return InstallState("direct", version, issues, helixsr_files or dropped,
                            sorted({t.parent for t in dropped}),
                            [t.parent / LOG for t in dropped],
                            installed_by=str(record.get("installed_by") or ""))
    return InstallState()


# ---- the FSR way (direct) ---------------------------------------------------------------

def _install_direct(layout: GameLayout, folder: HelixSRFolder, stamp: str) -> list[str]:
    notes = []
    targets = [Path(t) for t in layout.fsr_targets]
    if not targets:
        raise InstallError(tr("err_route_unavailable"))
    for target in targets:
        backup = original(target)
        if is_helixsr(target):
            if not backup.exists():
                notes.append(tr("in_fsr_no_backup", file=target))
            copy_verified(folder.dll, target)
            notes.append(tr("in_fsr_updated", file=target, version=folder.version))
        else:
            repaired = backup.exists()
            os.replace(target, backup)   # the game's file (after a game update: its new one)
            copy_verified(folder.dll, target)
            notes.append(tr("in_fsr_repaired" if repaired else "in_fsr_installed",
                            file=target, backup=backup.name, version=folder.version))
        for name in NETWORK_FILES:
            _remove(target.parent / name)
        record = read_record(target.parent)
        record.update({"helixsr": folder.version, "files": [target.name], "route": "direct",
                       "installed_by": stamp})
        record.setdefault("ini_made", None)
        write_record(target.parent, record)
    return notes


def _remove_direct(layout: GameLayout, remove_settings: bool | str) -> list[str]:
    notes = []
    for target in (Path(t) for t in layout.fsr_targets):
        backup = original(target)
        if not backup.exists():
            if is_helixsr(target):
                notes.append(tr("rm_fsr_no_backup", file=target))
            continue
        if target.exists() and not is_helixsr(target):
            notes.append(tr("rm_fsr_left", file=target, backup=backup.name))
        else:
            _remove(target)
            os.replace(backup, target)
            notes.append(tr("rm_fsr_restored", file=target))
        notes += _finish_settings(target.parent, read_record(target.parent), remove_settings)
        for name in (MARKER, LOG) + NETWORK_FILES:
            _remove(target.parent / name)
    return notes


# ---- the OptiScaler way -------------------------------------------------------------------

def _backup(exe: Path, name: str, record: dict) -> None:
    """Move the game's file into HelixSR/backup (a newer one replaces an older backup)."""
    source = exe / name
    if not (source.exists() or source.is_symlink()):
        return
    target = exe / FOLDER / BACKUP / name
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, target)
    moved = record.setdefault("moved", [])
    if name not in moved:
        moved.append(name)


def _copy_tracked(src: Path, dst: Path, record: dict, key: str, notes: list[str]) -> None:
    """Copy a file the user may have replaced by hand since: their copy is kept."""
    if dst.exists() and record.get(key) and sha256(dst) != record[key]:
        notes.append(tr("in_opti_kept_file", name=dst.name))
        return
    copy_verified(src, dst)
    record[key] = sha256(dst)


def _install_optiscaler(layout: GameLayout, folder: HelixSRFolder, stamp: str) -> list[str]:
    if not layout.exe_dir:
        raise InstallError(tr("err_route_unavailable"))
    exe = Path(layout.exe_dir)
    hx = exe / FOLDER
    record = read_record(hx)
    if "previous" in record:   # HelixSR 1.5 only edited an OptiScaler.ini the user had
        raise InstallError(tr("err_old_record", folder=hx))
    record.setdefault("moved", [])
    record.setdefault("created", [])
    hx.mkdir(exist_ok=True)
    notes = []
    opti = record.get("optiscaler") or next(
        (n for n in OPTI_NAMES if (exe / n).is_file() and is_optiscaler(exe / n)), "dxgi.dll")
    source = folder.path / OPTI_DIR
    if "optiscaler" not in record:   # first install: keep what the game had
        _backup(exe, opti, record)
        if (exe / OPTI_INI).is_file():
            (hx / BACKUP).mkdir(parents=True, exist_ok=True)
            shutil.copy2(exe / OPTI_INI, hx / BACKUP / OPTI_INI)
            record["ini"] = "edited"
        else:
            shutil.copyfile(source / OPTI_INI, exe / OPTI_INI)
            record["ini"] = "created"
        record["optiscaler"] = opti
    elif (exe / opti).exists() and not is_optiscaler(exe / opti):
        _backup(exe, opti, record)   # a game update put its own file back
        notes.append(tr("in_opti_repaired", name=opti))
    for name in OPTI_EXTRA:
        if not (exe / name).exists():
            shutil.copyfile(source / name, exe / name)
            if name not in record["created"]:
                record["created"].append(name)
    if (exe / opti).is_symlink():
        (exe / opti).unlink()
    copy_verified(source / OPTI_DLL, exe / opti)
    for name in OLD_COPIES:
        if is_helixsr(hx / name):
            _remove(hx / name)
    for name in NETWORK_FILES:
        _remove(hx / name)
    copy_verified(folder.dll, hx / OWN)
    copy_verified(folder.dll, hx / OWN_SR)
    (hx / MY_FSR).mkdir(exist_ok=True)
    (hx / MY_FSR / MY_FSR_NOTE).write_text(MY_FSR_TEXT, encoding="utf-8")
    _copy_tracked(folder.fsr_source(), hx / AMD_FSR_COPY, record, "amd_fsr", notes)
    _copy_tracked(folder.path / AMD_DIR / AMD_FG, hx / AMD_FG, record, "amd_fg", notes)
    if not (exe / OPTI_INI).is_file():   # deleted by hand since the last install
        shutil.copyfile(source / OPTI_INI, exe / OPTI_INI)
        notes.append(tr("in_opti_ini_new"))
    text = _read_text(exe / OPTI_INI)
    text = set_ini_value(text, "Upscalers", "Dx12Upscaler", "fsr31")
    text = set_ini_value(text, "Libraries", "FfxDx12Path", win_path(hx / OWN))
    text = set_ini_value(text, "Libraries", "FfxDx12SRPath", win_path(hx / OWN_SR))
    text = set_ini_value(text, "Libraries", "FfxDx12FGPath", win_path(hx / AMD_FG))
    _write_text(exe / OPTI_INI, text)
    record.update({"helixsr": folder.version, "route": "optiscaler", "installed_by": stamp})
    if layout.has_fsr31:
        record["chosen"] = "optiscaler"   # HelixSR's setup keeps this game on OptiScaler
    else:
        record.pop("chosen", None)
    record.setdefault("ini_made", None)
    write_record(hx, record)
    notes.insert(0, tr("in_opti_installed", name=opti, version=folder.version, folder=exe))
    if opti in record["moved"]:
        notes.insert(1, tr("in_opti_backup", name=opti))
    return notes


def _remove_optiscaler(exe: Path, remove_settings: bool | str) -> list[str]:
    hx = exe / FOLDER
    if not (hx / MARKER).is_file():
        return []
    record = read_record(hx)
    notes = []
    opti = str(record.get("optiscaler") or "dxgi.dll")
    replaced = (exe / opti).exists() and not is_optiscaler(exe / opti)
    if not replaced:
        _remove(exe / opti)
    if record.get("ini") == "created":
        _remove(exe / OPTI_INI)
        _remove(exe / OPTI_LOG)
    elif (hx / BACKUP / OPTI_INI).is_file():
        os.replace(hx / BACKUP / OPTI_INI, exe / OPTI_INI)
    for name in record.get("created") or []:
        _remove(exe / name)
    for name in record.get("moved") or []:
        saved = hx / BACKUP / name
        if not (saved.exists() or saved.is_symlink()):
            continue
        if (exe / name).exists():
            saved.unlink()      # the game has its current file in place already
        else:
            os.replace(saved, exe / name)
    for name in (OWN, OWN_SR, AMD_FSR_COPY, AMD_FG, LOG) + NETWORK_FILES:
        _remove(hx / name)
    for name in OLD_COPIES:
        if is_helixsr(hx / name):
            _remove(hx / name)
    notes += _finish_settings(hx, record, remove_settings)
    _remove(hx / MARKER)
    notes += _remove_my_fsr(hx)
    _rmdir(hx / BACKUP)
    _rmdir(hx)
    notes.insert(0, tr("rm_opti_done", folder=exe))
    return notes


def _remove_my_fsr(hx: Path) -> list[str]:
    directory = hx / MY_FSR
    note = directory / MY_FSR_NOTE
    try:
        if note.is_file():
            note.unlink()
        directory.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        return [tr("rm_my_fsr_kept", folder=directory)]
    return []


# ---- the DLSS way (experimental) ----------------------------------------------------------

def _install_dlss(layout: GameLayout, folder: HelixSRFolder, stamp: str) -> list[str]:
    if not layout.exe_dir:
        raise InstallError(tr("err_route_unavailable"))
    exe = Path(layout.exe_dir)
    hx = exe / FOLDER
    record = read_record(hx)
    record.setdefault("moved", [])
    hx.mkdir(exist_ok=True)
    for name, ours in ((LOADER, is_loader), (CORE, is_helixsr)):
        if (exe / name).exists() and not ours(exe / name):
            _backup(exe, name, record)
    copy_verified(folder.path / LOADER_DIR / LOADER, exe / LOADER)
    copy_verified(folder.dll, exe / CORE)
    record.update({"helixsr": folder.version, "route": "dlss", "files": [LOADER, CORE],
                   "installed_by": stamp})
    record.setdefault("ini_made", None)
    write_record(hx, record)
    notes = [tr("in_dlss_installed", version=folder.version, folder=exe)]
    if record["moved"]:
        notes.append(tr("in_dlss_backup", names=", ".join(record["moved"])))
    if (exe / OPTI_INI).is_file():
        notes.append(tr("in_dlss_foreign_opti"))
    return notes


def _remove_dlss(exe: Path, remove_settings: bool | str) -> list[str]:
    hx = exe / FOLDER
    record = read_record(hx)
    if record.get("route") != "dlss":
        return []
    for name, ours in ((LOADER, is_loader), (CORE, is_helixsr)):
        if ours(exe / name):
            _remove(exe / name)
    for name in record.get("moved") or []:
        saved = hx / BACKUP / name
        if not (saved.exists() or saved.is_symlink()):
            continue
        if (exe / name).exists():
            saved.unlink()
        else:
            os.replace(saved, exe / name)
    notes = _finish_settings(exe, record, remove_settings)
    for path in (hx / MARKER, hx / LOG, exe / LOG, exe / LOADER_LOG):
        _remove(path)
    _rmdir(hx / BACKUP)
    _rmdir(hx)
    notes.insert(0, tr("rm_dlss_done", folder=exe))
    return notes


# ---- settings follow the game ----------------------------------------------------------------

def _finish_settings(directory: Path, record: dict, remove_settings: bool | str) -> list[str]:
    """helixsr.ini on removal: HelixSR's untouched template goes, the user's settings stay
    unless they asked to remove them (or they move to another way: ``"moved"``)."""
    path = directory / settings.INI
    if not path.is_file():
        return []
    made = record.get("ini_made")
    if remove_settings or (made and sha256(path) == made) or settings.is_empty(path):
        path.unlink()
        return [tr("rm_settings_removed", file=path)] if remove_settings is True else []
    return [tr("rm_settings_kept", file=path)]


def _settings_of(current: InstallState) -> dict[str, str]:
    for directory in current.ini_dirs:
        values = settings.read(directory / settings.INI)
        if values:
            return values
    return {}


# ---- entry points ------------------------------------------------------------------------------

def install(layout: GameLayout, folder: HelixSRFolder, route: str, stamp: str) -> list[str]:
    """Install HelixSR the given way; also switches, updates and repairs."""
    if route not in layout.ways(folder.has_loader):
        raise InstallError(tr("err_route_unavailable"))
    missing = folder.missing_for(route)
    if missing:
        raise InstallError(tr("err_missing_files", files=", ".join(str(p) for p in missing)))
    if not has_network(folder.dll):
        raise InstallError(tr("hx_not_built", path=folder.path))
    current = state(layout)
    carried = _settings_of(current) if current.route not in (None, route) else {}
    notes: list[str] = []
    exe = Path(layout.exe_dir) if layout.exe_dir else None
    if current.route and current.route != route:
        notes.append(tr("sw_from", way=tr("way_" + current.route)))
        drop = "moved" if carried else False   # settings are written again below
        if current.route == "dlss" and exe:
            notes += _remove_dlss(exe, drop)
        elif current.route == "optiscaler" and exe:
            notes += _remove_optiscaler(exe, drop)
        elif current.route == "direct":
            notes += _remove_direct(layout, drop)
    if route == "direct":
        notes += _install_direct(layout, folder, stamp)
    elif route == "optiscaler":
        notes += _install_optiscaler(layout, folder, stamp)
    else:
        notes += _install_dlss(layout, folder, stamp)
    if carried:
        for directory in state(layout).ini_dirs:
            settings.write(directory / settings.INI, carried)
        notes.append(tr("sw_settings_moved"))
    if route == "direct" and exe and (exe / OPTI_INI).is_file():
        notes.append(tr("in_fsr_foreign_opti"))
    return notes


def remove(layout: GameLayout, remove_settings: bool) -> list[str]:
    current = state(layout)
    exe = Path(layout.exe_dir) if layout.exe_dir else None
    if current.route == "dlss" and exe:
        return _remove_dlss(exe, remove_settings)
    if current.route == "optiscaler" and exe:
        return _remove_optiscaler(exe, remove_settings)
    if current.route == "direct":
        return _remove_direct(layout, remove_settings)
    return [tr("rm_not_installed")]
