"""Install, switch, update, repair and remove an upscaler in one game.

Two families, both written by Scaler Assistant itself:

* **DLSS 3.7 (HelixSR)** in HelixSR's three ways. It carries out the steps
  HelixSR's README documents for installing by hand, and keeps HelixSR's
  install record (``helixsr-install.json``), backups (``HelixSR/backup``,
  ``*.original.dll``) and file names, so HelixSR's own setup and uninstaller
  recognise games set up here, and the other way round. Every HelixSR file
  comes from the user's own HelixSR folder.
  HelixSR 2.0 and newer (HelixSR Scaler or the FSR drop-in) is installed by
  the release's own installer instead (``hxbridge``); its removal is done here
  from HelixSR Scaler's install record when that installer is not at hand.
* **FSR 4.1 and FSR 3** through OptiScaler. OptiScaler goes next to the game's
  .exe under the name ``optiscaler.choose_name`` picked, and the FFX DLLs it
  uses go into a ``ScalerAssistant`` folder beside it; OptiScaler.ini points
  at them. Switching between FSR 4.1 Exact, Lossy and FSR 3 only swaps the
  upscaler DLL and changes OptiScaler.ini. Everything replaced is kept in
  ``ScalerAssistant/backup`` and put back on removal.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import hxbridge, optiscaler, settings
from .games import (
    FOLDER, HX_FSRFG, HX_SCALER_BACKUP, HX_SCALER_FILES, MARKER, OPTI_INI, SCALER_FOLDER,
    SCALER_MARKER, GameLayout,
)
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
OPTI_LOG = optiscaler.LOG
MY_FSR = "my-fsr"
MY_FSR_NOTE = "README.txt"
# The names OptiScaler can be loaded under (the game may already have one).
OPTI_NAMES = optiscaler.NAMES + ("OptiScaler.asi",)
# Separate network files of HelixSR 1.4-1.7; one-file DLLs read their own copy.
NETWORK_FILES = ("helixsr_weights.bin", "helixsr_kernels.pak")
# HelixSR DLLs that older versions left in the game's HelixSR folder.
OLD_COPIES = (CORE, DLL, "amd_fidelityfx_upscaler_dx12.dll")
TEMP_SUFFIX = ".scaler-assistant.tmp"

# FSR 4.1 / FSR 3: the files in the game's ScalerAssistant folder, by OptiScaler.ini role.
FFX_FILES = {
    "loader": "amd_fidelityfx_dx12.dll",
    "upscaler": "amd_fidelityfx_upscaler_dx12.dll",
    "framegeneration": "amd_fidelityfx_framegeneration_dx12.dll",
    "vulkan": "amd_fidelityfx_vk.dll",
}
SCALER_NOTE = "README.txt"
SCALER_NOTE_TEXT = (
    "Scaler Assistant made this folder: the FidelityFX DLLs OptiScaler uses in this game\r\n"
    "(OptiScaler.ini points at them) and, in backup, the files OptiScaler replaced.\r\n"
    "Remove the upscaler in Scaler Assistant to put everything back.\r\n"
)
CHOICES = ("helixsr:hscaler", "helixsr:direct", "helixsr:optiscaler", "helixsr:dlss",
           "fsr4:exact", "fsr4:lossy", "fsr4:lossy2", "fsr4:native", "fsr3")

MY_FSR_TEXT = (
    "Scaler Assistant made this folder for HelixSR.\r\n\r\n"
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


def read_record(directory: Path, marker: str = MARKER) -> dict:
    try:
        data = json.loads((directory / marker).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_record(directory: Path, record: dict, marker: str = MARKER) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / marker).write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


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


win_path = optiscaler.win_path


def set_ini_value(text: str, section: str, key: str, value: str) -> str:
    """Set ``key=value`` in an OptiScaler.ini, keeping every other line as it is."""
    try:
        return optiscaler.set_value(text, section, key, value)
    except optiscaler.IniError as error:
        raise InstallError(tr("err_ini_duplicate", name=str(error), file=OPTI_INI)) from error


def _read_text(path: Path) -> str:
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as handle:
        return handle.read()


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        handle.write(text)


# ---- state ------------------------------------------------------------------------

@dataclass
class InstallState:
    route: Optional[str] = None          # HelixSR: direct / optiscaler / dlss; FSR: "scaler"
    version: Optional[str] = None        # HelixSR's version, or OptiScaler's for FSR 4.1 / FSR 3
    issues: list[str] = field(default_factory=list)     # i18n keys
    dll_files: list[Path] = field(default_factory=list)  # the upscaler DLL(s) inside the game
    ini_dirs: list[Path] = field(default_factory=list)   # where helixsr.ini is read (HelixSR)
    log_files: list[Path] = field(default_factory=list)
    chosen: bool = False                                 # OptiScaler picked for an FSR 3.1 game
    installed_by: str = ""
    upscaler: Optional[str] = None       # helixsr / fsr4 / fsr3
    variant: Optional[str] = None        # fsr4: exact / lossy / lossy2 / native
    opti_name: Optional[str] = None      # OptiScaler's file name next to the .exe
    files: dict[str, str] = field(default_factory=dict)  # FSR: sha256 of the copies made
    helper_files: list[Path] = field(default_factory=list)   # OptiScaler or the DLSS loader
    source: str = ""                     # FSR: the download the upscaler DLL came from
    opti_over_foreign: bool = False      # OptiScaler took the name of a file that was not OptiScaler
    fg: Optional[bool] = None            # HelixSR Scaler: HelixSR's frame generation on / off
    fg_files: bool = False               # HelixSR Scaler: frame generation's files are in the game

    @property
    def installed(self) -> bool:
        return self.route is not None

    @property
    def choice(self) -> Optional[str]:
        if self.upscaler == "helixsr":
            return f"helixsr:{self.route}"
        if self.upscaler == "fsr4":
            return f"fsr4:{self.variant or 'exact'}"
        return self.upscaler


    def outdated(self, folder: Optional[HelixSRFolder]) -> bool:
        """HelixSR only: True when the HelixSR folder holds a different build than the game."""
        if self.upscaler != "helixsr" or folder is None or not folder.ready:
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


def _over_foreign(record: dict, store: Path, name: str) -> bool:
    saved = store / name
    return name in (record.get("moved") or []) and saved.exists() and not is_optiscaler(saved)


# HelixSR Scaler (HelixSR 2.0): files it makes while the game runs, removed with it.
HX_MADE = ("OptiScaler.log", f"{HX_FSRFG}/helixsr.log", f"{HX_FSRFG}/helixsr.ini",
           f"{HX_FSRFG}/helixsr-fg/nvexec.log", f"{HX_FSRFG}/amd_fidelityfx_upscaler_dx12.amd.dll",
           "HelixSR-Scaler-remove.sh", "HelixSR-previous.zip")
HX_DLL = f"{HX_FSRFG}/{DLL}"


def hscaler_record(exe: Path) -> Optional[dict]:
    """HelixSR Scaler's install record (HelixSR-Scaler.files): name, version, files, by."""
    try:
        text = (exe / HX_SCALER_FILES).read_text(errors="replace")
    except OSError:
        return None
    record = {"name": "dxgi.dll", "version": None, "files": [], "by": ""}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# version="):
            record["version"] = line.split("=", 1)[1].strip() or None
        elif line.startswith("# HelixSR Scaler, installed by "):
            record["by"] = line.split(" by ", 1)[1].strip()
        elif line.startswith("name="):
            record["name"] = line.split("=", 1)[1].strip()
        elif line and not line.startswith("#"):
            record["files"].append(line)
    return record


def hscaler_fg(exe: Path) -> tuple[bool, bool]:
    """(on, files in the game) for HelixSR's frame generation with HelixSR Scaler: on when
    OptiScaler.ini's [FrameGen] picks it (FGInput = nvngxfg with FGNvngxReplacement = HelixSR)
    and its files are in HelixSR-fsrfg/helixsr-fg."""
    fg = exe / HX_FSRFG / "helixsr-fg"
    files = fg.is_dir() and any(fg.glob("*.dll"))
    try:
        text = _read_text(exe / OPTI_INI)
    except OSError:
        return False, files
    frame_gen = optiscaler.section_text(text, "FrameGen")
    picked = ((optiscaler.get_value(frame_gen, "FGInput") or "").lower() == "nvngxfg"
              and (optiscaler.get_value(frame_gen, "FGNvngxReplacement") or "").lower() == "helixsr")
    return picked and files, files


def _remove_hscaler(exe: Path) -> list[str]:
    """Take HelixSR Scaler out the way its record describes and put the game's files back."""
    record = hscaler_record(exe)
    if record is None:
        return []
    for rel in record["files"] + list(HX_MADE):
        target = exe / rel
        if target.is_file() or target.is_symlink():
            target.unlink()
    shutil.rmtree(exe / HX_FSRFG / "helixsr-fg.off", ignore_errors=True)
    backup = exe / HX_SCALER_BACKUP
    if backup.is_dir():
        for item in sorted(backup.rglob("*")):
            if item.is_file() or item.is_symlink():
                target = exe / item.relative_to(backup)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(item, target)
        shutil.rmtree(backup, ignore_errors=True)
    _remove(exe / HX_SCALER_FILES)
    folders = {(exe / rel).parent for rel in record["files"]} | {exe / HX_FSRFG}
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        while folder != exe and folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
            folder = folder.parent
    return [tr("rm_hscaler", folder=exe)]


def state(layout: GameLayout) -> InstallState:
    exe = Path(layout.exe_dir) if layout.exe_dir else None
    hx = hscaler_record(exe) if exe else None
    if exe and hx is not None:
        dll, name = exe / HX_DLL, hx["name"]
        issues = [] if is_optiscaler(exe / name) and is_helixsr(dll) else ["is_files_replaced"]
        fg, fg_files = hscaler_fg(exe)
        return InstallState("hscaler", dll_version(dll), issues, [dll], [],
                            [exe / HX_FSRFG / LOG, exe / OPTI_LOG], installed_by=hx["by"],
                            upscaler="helixsr", opti_name=name, helper_files=[exe / name],
                            fg=fg, fg_files=fg_files)
    folder = exe / FOLDER if exe else None
    record = read_record(folder) if folder else {}
    if folder and record and record.get("route") == "dlss":
        core, loader = exe / CORE, exe / LOADER
        issues = [] if is_helixsr(core) and is_loader(loader) else ["is_files_replaced"]
        return InstallState("dlss", dll_version(core) or record.get("helixsr"), issues, [core],
                            [exe], [exe / LOG, exe / LOADER_LOG, folder / LOG],
                            installed_by=str(record.get("installed_by") or ""),
                            upscaler="helixsr", helper_files=[loader])
    if folder and (folder / MARKER).is_file():
        name = str(record.get("optiscaler") or "dxgi.dll")
        opti = exe / name
        own = folder / OWN
        issues = []
        if not (is_optiscaler(opti) and is_helixsr(own)):
            issues.append("is_files_replaced")
        return InstallState("optiscaler", dll_version(own) or record.get("helixsr"), issues,
                            [own, folder / OWN_SR], [folder], [folder / LOG, exe / OPTI_LOG],
                            chosen=record.get("chosen") == "optiscaler",
                            installed_by=str(record.get("installed_by") or ""),
                            upscaler="helixsr", opti_name=name, helper_files=[opti],
                            opti_over_foreign=_over_foreign(record, folder / BACKUP, name))
    scaler = exe / SCALER_FOLDER if exe else None
    if scaler and (scaler / SCALER_MARKER).is_file():
        record = read_record(scaler, SCALER_MARKER)
        name = str(record.get("optiscaler") or "dxgi.dll")
        upscaler = record.get("upscaler") if record.get("upscaler") in ("fsr4", "fsr3") else "fsr3"
        dll = scaler / FFX_FILES["upscaler"]
        issues = []
        # HelixSR's own setup takes the FSR DLL here for a game's FSR 3.1 DLL and replaces it.
        if not (is_optiscaler(exe / name) and dll.is_file()) or is_helixsr(dll):
            issues.append("is_files_replaced")
        return InstallState("scaler", str(record.get("optiscaler_version") or ""), issues, [dll],
                            [], [exe / OPTI_LOG],
                            installed_by=str(record.get("installed_by") or ""),
                            upscaler=upscaler,
                            variant=record.get("variant") if upscaler == "fsr4" else None,
                            opti_name=name, files=dict(record.get("files") or {}),
                            helper_files=[exe / name], source=str(record.get("source") or ""),
                            opti_over_foreign=_over_foreign(record, scaler / BACKUP, name))
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
                            installed_by=str(record.get("installed_by") or ""),
                            upscaler="helixsr")
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
        for name in (MARKER, LOG, "HelixSR-previous.zip") + NETWORK_FILES:
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


def _install_optiscaler(layout: GameLayout, folder: HelixSRFolder, stamp: str,
                        name: Optional[str] = None) -> list[str]:
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
    opti = record.get("optiscaler") or name or next(
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


# ---- FSR 4.1 and FSR 3 (through OptiScaler) ---------------------------------------------------

@dataclass
class ScalerPlan:
    """What an FSR 4.1 / FSR 3 install copies, prepared by the service from the downloads."""
    choice: str                  # fsr4:exact / fsr4:lossy / fsr4:lossy2 / fsr4:native / fsr3
    opti_name: str               # OptiScaler's file name next to the .exe
    optiscaler: Path             # the downloaded OptiScaler folder
    optiscaler_version: str
    upscaler_dll: Path           # the amd_fidelityfx_upscaler_dx12.dll to use
    force_int8: bool             # FSR 4 on a GPU before RDNA 4
    source: str = ""             # "<download>-<version>" the upscaler DLL comes from

    @property
    def upscaler(self) -> str:
        return self.choice.partition(":")[0]

    @property
    def variant(self) -> Optional[str]:
        return self.choice.partition(":")[2] or None


def _put_back(exe: Path, store: Path, name: str) -> None:
    """Return a file moved into ``store`` (unless the game has its own there again)."""
    saved = store / name
    if not (saved.exists() or saved.is_symlink()):
        return
    if (exe / name).exists() or (exe / name).is_symlink():
        saved.unlink()
    else:
        os.replace(saved, exe / name)


def _clear_helixsr_dropin(sc: Path) -> list[str]:
    """HelixSR's own setup (FSR way) may have replaced the FSR DLL in the ScalerAssistant
    folder, taking it for a game's FSR 3.1 DLL: take its files out again."""
    record = read_record(sc)
    upscaler = sc / FFX_FILES["upscaler"]
    if record.get("route") != "direct" and not original(upscaler).exists():
        return []
    notes = _finish_settings(sc, record, False)
    for path in (original(upscaler), sc / MARKER, sc / LOG, *(sc / n for n in NETWORK_FILES)):
        _remove(path)
    if is_helixsr(upscaler):
        _remove(upscaler)
    return [tr("in_sc_helixsr_removed")] + notes


def _install_scaler(layout: GameLayout, plan: ScalerPlan, stamp: str) -> list[str]:
    if not layout.exe_dir:
        raise InstallError(tr("err_route_unavailable"))
    exe = Path(layout.exe_dir)
    sc = exe / SCALER_FOLDER
    store = sc / BACKUP
    record = read_record(sc, SCALER_MARKER)
    record.setdefault("moved", [])
    record.setdefault("created", [])
    sc.mkdir(exist_ok=True)
    notes: list[str] = []
    name = plan.opti_name
    previous = record.get("optiscaler")
    if previous and previous != name:   # another file name for OptiScaler: undo the old one
        if is_optiscaler(exe / previous):
            _remove(exe / previous)
        if previous in record["moved"]:
            _put_back(exe, store, previous)
            record["moved"].remove(previous)
        notes.append(tr("in_sc_renamed", old=previous, name=name))
    if "ini" not in record:   # first install: keep what the game had
        if (exe / OPTI_INI).is_file():
            store.mkdir(parents=True, exist_ok=True)
            shutil.copy2(exe / OPTI_INI, store / OPTI_INI)
            record["ini"] = "edited"
        else:
            shutil.copyfile(plan.optiscaler / OPTI_INI, exe / OPTI_INI)
            record["ini"] = "created"
    target = exe / name
    ours = previous == name and is_optiscaler(target)
    if (target.exists() or target.is_symlink()) and not ours:
        # the game's own file, another mod's, or an OptiScaler set up by hand: kept aside
        if previous == name:   # a game update put its own file back
            notes.append(tr("in_opti_repaired", name=name))
        store.mkdir(parents=True, exist_ok=True)
        os.replace(target, store / name)
        if name not in record["moved"]:
            record["moved"].append(name)
    record["optiscaler"] = name
    notes += _clear_helixsr_dropin(sc)
    for extra in OPTI_EXTRA:
        if not (exe / extra).exists():
            shutil.copyfile(plan.optiscaler / extra, exe / extra)
            if extra not in record["created"]:
                record["created"].append(extra)
    copy_verified(plan.optiscaler / OPTI_DLL, target)
    files = {OPTI_DLL: sha256(target)}
    paths: dict[str, Path] = {}
    for role, file_name in FFX_FILES.items():
        source = plan.upscaler_dll if role == "upscaler" else plan.optiscaler / file_name
        copy_verified(source, sc / file_name)
        files[file_name] = sha256(sc / file_name)
        paths[role] = sc / file_name
    (sc / SCALER_NOTE).write_text(SCALER_NOTE_TEXT, encoding="utf-8")
    if not (exe / OPTI_INI).is_file():   # deleted by hand since the last install
        shutil.copyfile(plan.optiscaler / OPTI_INI, exe / OPTI_INI)
        notes.append(tr("in_opti_ini_new"))
    try:
        text = optiscaler.configure(_read_text(exe / OPTI_INI), plan.upscaler, paths,
                                    plan.force_int8)
    except optiscaler.IniError as error:
        raise InstallError(tr("err_ini_duplicate", name=str(error), file=OPTI_INI)) from error
    _write_text(exe / OPTI_INI, text)
    record.update({"tool": "Scaler Assistant", "installed_by": stamp, "upscaler": plan.upscaler,
                   "variant": plan.variant, "optiscaler_version": plan.optiscaler_version,
                   "source": plan.source, "files": files})
    write_record(sc, record, SCALER_MARKER)
    notes.insert(0, tr("in_sc_installed", name=name, folder=exe))
    if name in record["moved"]:
        notes.insert(1, tr("in_sc_backup", name=name, folder=f"{SCALER_FOLDER}/{BACKUP}"))
    if record["ini"] == "edited":
        notes.append(tr("in_sc_ini_edited"))
    return notes


def _remove_scaler(exe: Path) -> list[str]:
    sc = exe / SCALER_FOLDER
    if not (sc / SCALER_MARKER).is_file():
        return []
    record = read_record(sc, SCALER_MARKER)
    store = sc / BACKUP
    notes: list[str] = []
    name = str(record.get("optiscaler") or "dxgi.dll")
    if is_optiscaler(exe / name) or not (exe / name).exists():
        _remove(exe / name)
    else:
        notes.append(tr("rm_sc_replaced", name=name))
    if record.get("ini") == "created":
        _remove(exe / OPTI_INI)
        _remove(exe / OPTI_LOG)
    elif (store / OPTI_INI).is_file():
        os.replace(store / OPTI_INI, exe / OPTI_INI)
    for extra in record.get("created") or []:
        _remove(exe / extra)
    for moved in record.get("moved") or []:
        _put_back(exe, store, moved)
    notes += _clear_helixsr_dropin(sc)
    for file_name in (*FFX_FILES.values(), SCALER_NOTE, SCALER_MARKER):
        _remove(sc / file_name)
    _rmdir(store)
    _rmdir(sc)
    notes.insert(0, tr("rm_sc_done", folder=exe))
    if sc.exists():
        notes.append(tr("rm_sc_kept", folder=sc))
    return notes


# ---- entry points ------------------------------------------------------------------------------

def _remove_current(layout: GameLayout, current: InstallState,
                    remove_settings: bool | str) -> list[str]:
    exe = Path(layout.exe_dir) if layout.exe_dir else None
    if current.route == "hscaler" and exe:
        return _remove_hscaler(exe)
    if current.route == "scaler" and exe:
        return _remove_scaler(exe)
    if current.route == "dlss" and exe:
        return _remove_dlss(exe, remove_settings)
    if current.route == "optiscaler" and exe:
        return _remove_optiscaler(exe, remove_settings)
    if current.route == "direct":
        return _remove_direct(layout, remove_settings)
    return []


def _label(current: InstallState) -> str:
    return tr("choice_" + (current.choice or "").replace(":", "_"))


def _install_modern(layout: GameLayout, folder: HelixSRFolder, route: str,
                    opti_name: Optional[str], game_dir: Optional[str]) -> list[str]:
    """HelixSR 2.0 and newer: HelixSR's own installer puts it in (HelixSR Scaler or the FSR
    drop-in). What Scaler Assistant installed itself (FSR 4.1 / FSR 3, earlier HelixSR ways) is
    taken out first, so the installer finds the game as the game ships."""
    if route not in layout.ways(modern=True) or not game_dir:
        raise InstallError(tr("err_route_unavailable"))
    missing = folder.missing_for(route)
    if missing:
        raise InstallError(tr("err_missing_files", files=", ".join(str(p) for p in missing)))
    if not has_network(folder.dll):
        raise InstallError(tr("hx_not_built", path=folder.path))
    current = state(layout)
    keep_fg = route == "hscaler" and current.route == "hscaler" and bool(current.fg)
    notes: list[str] = []
    if current.installed and current.route != route:
        notes.append(tr("sw_from", way=_label(current)))
        notes += _remove_current(layout, current, False)
    elif current.route == "hscaler" and route == "hscaler" and opti_name \
            and current.opti_name != opti_name:
        notes += _remove_hscaler(Path(str(layout.exe_dir)))   # a new file name: in again fresh
    try:
        answer = hxbridge.install(folder, game_dir, "scaler" if route == "hscaler" else "fsr",
                                  opti_name if route == "hscaler" else None,
                                  anti_cheat_ok=bool(layout.anti_cheat),
                                  fg=True if keep_fg else None)
    except hxbridge.BridgeError as error:
        raise InstallError("\n".join([tr("err_bridge", error=error), *error.messages])) from error
    after = state(layout)
    where = (f"{layout.exe_dir} ({after.opti_name})" if route == "hscaler"
             else ", ".join(str(Path(t).parent) for t in layout.fsr_targets))
    notes.append(tr("in_modern", way=tr("way_" + route), version=folder.version, folder=where))
    notes += ["HelixSR: " + m for m in answer.get("messages", [])]
    return notes


def set_frame_generation(layout: GameLayout, folder: HelixSRFolder, on: bool,
                         game_dir: str) -> list[str]:
    """HelixSR's frame generation on or off in a game with HelixSR Scaler, through HelixSR's
    own installer (it only changes OptiScaler.ini's [FrameGen] choice and, when they are
    missing, copies frame generation's files from the HelixSR folder)."""
    if not folder.modern:
        raise InstallError(tr("fg_no_folder"))
    current = state(layout)
    if current.route != "hscaler":
        raise InstallError(tr("rm_not_installed"))
    if not layout.dlss_fg:
        raise InstallError(tr("fg_no_dlssg"))
    if on and not current.fg_files and not folder.fg_ready:
        raise InstallError(tr("fg_not_built", path=folder.path))
    try:
        answer = hxbridge.run(folder, "scaler-fg", "--game", game_dir,
                              "--on", "true" if on else "false")
    except hxbridge.BridgeError as error:
        raise InstallError("\n".join([tr("err_bridge", error=error), *error.messages])) from error
    return ["HelixSR: " + m for m in answer.get("messages", [])]


def install_helixsr(layout: GameLayout, folder: HelixSRFolder, route: str, stamp: str,
                    opti_name: Optional[str] = None, game_dir: Optional[str] = None) -> list[str]:
    """Install HelixSR the given way; also switches, updates and repairs."""
    if folder.modern:
        return _install_modern(layout, folder, route, opti_name, game_dir)
    if route not in layout.ways(folder.has_loader):
        raise InstallError(tr("err_route_unavailable"))
    missing = folder.missing_for(route)
    if missing:
        raise InstallError(tr("err_missing_files", files=", ".join(str(p) for p in missing)))
    if not has_network(folder.dll):
        raise InstallError(tr("hx_not_built", path=folder.path))
    current = state(layout)
    renamed = (route == "optiscaler" and current.route == "optiscaler" and opti_name
               and current.opti_name != opti_name)
    switching = current.route not in (None, route) or renamed
    carried = _settings_of(current) if switching and current.upscaler == "helixsr" else {}
    notes: list[str] = []
    exe = Path(layout.exe_dir) if layout.exe_dir else None
    if switching:
        if current.upscaler == "helixsr" and not renamed:
            notes.append(tr("sw_from", way=tr("way_" + str(current.route))))
        elif current.upscaler != "helixsr":
            notes.append(tr("sw_from", way=_label(current)))
        drop = "moved" if carried else False   # settings are written again below
        notes += _remove_current(layout, current, drop)
    if route == "direct":
        notes += _install_direct(layout, folder, stamp)
    elif route == "optiscaler":
        notes += _install_optiscaler(layout, folder, stamp, opti_name)
    else:
        notes += _install_dlss(layout, folder, stamp)
    if carried:
        for directory in state(layout).ini_dirs:
            settings.write(directory / settings.INI, carried)
        notes.append(tr("sw_settings_moved"))
    if route == "direct" and exe and (exe / OPTI_INI).is_file():
        notes.append(tr("in_fsr_foreign_opti"))
    return notes


def install_scaler(layout: GameLayout, plan: ScalerPlan, stamp: str) -> list[str]:
    """Install FSR 4.1 or FSR 3 through OptiScaler; also switches between them, updates and repairs."""
    if plan.choice not in CHOICES or plan.upscaler == "helixsr":
        raise InstallError(tr("err_route_unavailable"))
    if not layout.optiscaler_possible:
        raise InstallError(tr("err_route_unavailable"))
    needed = [plan.optiscaler / n for n in (OPTI_DLL, OPTI_INI, *OPTI_EXTRA)]
    needed += [plan.optiscaler / n for r, n in FFX_FILES.items() if r != "upscaler"]
    needed.append(plan.upscaler_dll)
    missing = [p for p in needed if not p.is_file()]
    if missing:
        raise InstallError(tr("err_missing_files", files=", ".join(str(p) for p in missing)))
    current = state(layout)
    notes: list[str] = []
    if current.installed and current.route != "scaler":
        notes.append(tr("sw_from", way=tr("way_" + str(current.route))))
        notes += _remove_current(layout, current, False)
    elif current.route == "scaler" and current.choice != plan.choice:
        notes.append(tr("sw_from", way=_label(current)))
    notes += _install_scaler(layout, plan, stamp)
    return notes


def install(layout: GameLayout, folder: HelixSRFolder, route: str, stamp: str,
            opti_name: Optional[str] = None) -> list[str]:
    """HelixSR the given way (kept for callers of the HelixSR-only versions)."""
    return install_helixsr(layout, folder, route, stamp, opti_name)


def remove(layout: GameLayout, remove_settings: bool) -> list[str]:
    current = state(layout)
    if not current.installed:
        return [tr("rm_not_installed")]
    return _remove_current(layout, current, remove_settings)
