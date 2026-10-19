"""Application logic for Scaler Assistant, independent of the UI toolkit.

Choices per game (``installer.CHOICES``):

* ``helixsr:direct`` / ``helixsr:optiscaler`` / ``helixsr:dlss`` — DLSS 3.7 (HelixSR)
  from the user's own HelixSR folder, the ways HelixSR documents.
* ``fsr4:exact`` / ``fsr4:lossy`` — FSR 4.1 through OptiScaler with the modified
  DLLs from zgauthier2000/fsr4-shader-performance-overrides (GPUs before RDNA 4).
* ``fsr4:native`` — FSR 4.1 through OptiScaler with AMD's own DLL (RDNA 4).
* ``fsr3`` — FSR 3 through OptiScaler.

Steam launch options are only touched when OptiScaler needs a file name other
than dxgi.dll / d3d12.dll, and then only the one entry Scaler Assistant adds
is inserted and later taken out again (see ``launch_options``).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import __version__, components, gpu, helixsr, installer, settings
from . import launch_options as lo
from . import optiscaler
from .components import Component
from .games import GameLayout, detect_layout
from .helixsr import HelixSRFolder
from .i18n import localized_name, tr
from .installer import InstallState, ScalerPlan
from .runtime import Watch, running_app_ids
from .steam import SteamGame, SteamInstallation
from .steam_cef import CefError, SteamCef

STAMP = f"Scaler Assistant {__version__}"
FSR4_BUILDS = ("auto", "dgpu", "igpu", "native")


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "scaler-assistant"


def state_path() -> Path:
    return config_dir() / "state.json"


def _migrate(state_file: Path) -> None:
    """Take over the settings of HelixSR Assistant (this program's former name) once."""
    if state_file.exists() or state_file != state_path():
        return
    old = state_file.parent.parent / "helixsr-assistant" / "state.json"
    if old.is_file():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(old, state_file)


class GameRunningError(RuntimeError):
    """The upscaler's files can't be changed while the game has them loaded."""


class SteamMustCloseError(RuntimeError):
    """Steam runs without a reachable CEF port; localconfig.vdf can't be edited live."""


class NeedsDownloadError(RuntimeError):
    def __init__(self, missing: list[Component]) -> None:
        super().__init__(", ".join(c.key for c in missing))
        self.missing = missing


class NeedsHelixSRError(FileNotFoundError):
    """No HelixSR folder that can be installed from."""


def upscaler_of(choice: Optional[str]) -> str:
    return (choice or "").partition(":")[0]


def uses_optiscaler(choice: Optional[str]) -> bool:
    return upscaler_of(choice) in ("fsr4", "fsr3") or choice in ("helixsr:optiscaler",
                                                                  "helixsr:hscaler")


@dataclass
class GameEntry:
    app_id: int
    name: str
    install_dir: str
    layout: GameLayout
    status: InstallState
    ways: list[str] = field(default_factory=list)          # HelixSR ways
    choices: list[str] = field(default_factory=list)       # every choice this game offers
    outdated: bool = False
    names: dict[str, str] = field(default_factory=dict)
    launch_options: str = ""
    launch_missing: bool = False                            # OptiScaler's override is gone
    blocked: dict[str, str] = field(default_factory=dict)   # choice -> i18n key: why not here
    recommended: Optional[str] = None                       # the choice to suggest for this PC

    @property
    def display_name(self) -> str:
        return localized_name(self.name, self.names)

    @property
    def installed(self) -> bool:
        return self.status.installed

    @property
    def supported(self) -> bool:
        return bool(self.choices) or self.installed

    @property
    def issues(self) -> list[str]:
        return self.status.issues + (["is_launch_missing"] if self.launch_missing else [])

    @property
    def needs_attention(self) -> bool:
        return self.outdated or bool(self.issues)

    def matches(self, query: str) -> bool:
        query = query.casefold()
        return (query in str(self.app_id)
                or any(query in n.casefold() for n in (self.name, *self.names.values())))

    def watch(self) -> Watch:
        status = self.status
        logs = status.log_files if status.upscaler == "helixsr" else []   # helixsr.log only
        return Watch([str(p) for p in status.dll_files], [str(p) for p in status.helper_files],
                     [str(p) for p in logs])


@dataclass
class ChoicePlan:
    """What applying a choice to a game needs, for the UI to ask before anything happens."""
    app_id: int
    choice: str
    downloads: list[Component] = field(default_factory=list)
    needs_helixsr: bool = False
    opti_name: Optional[str] = None
    opti_reason: str = ""
    launch_before: str = ""
    launch_after: str = ""
    lossy_warning: bool = False          # Lossy's WARNING.txt has not been accepted yet
    anti_cheat: list[str] = field(default_factory=list)

    @property
    def launch_change(self) -> bool:
        return self.launch_before != self.launch_after


class AssistantService:
    def __init__(self, steam_root: Optional[Path] = None,
                 state_file: Optional[Path] = None,
                 proc: Path = Path("/proc"),
                 cef: Optional[SteamCef] = None,
                 components_root: Optional[Path] = None,
                 sys_root: Path = Path("/sys")) -> None:
        self._steam_root = steam_root
        self.proc = proc
        self.state_file = state_file or state_path()
        _migrate(self.state_file)
        self.state = self._load_state()
        self.cef = cef or SteamCef()
        self.components_root = components_root
        self.sys_root = sys_root
        self._gpus: Optional[list[gpu.Gpu]] = None

    # ---- state ----------------------------------------------------------------

    def _load_state(self) -> dict:
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                state.setdefault("games", [])
                return state
        except (OSError, ValueError):
            pass
        return {"games": [], "scanned": False}

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, self.state_file)

    @property
    def has_scanned(self) -> bool:
        return bool(self.state.get("scanned"))

    def steam(self) -> SteamInstallation:
        return SteamInstallation(self._steam_root)

    # ---- the GPU and FSR 4.1 ------------------------------------------------------------

    def gpus(self) -> list[gpu.Gpu]:
        if self._gpus is None:
            self._gpus = gpu.detect(self.sys_root)
        return self._gpus

    def main_gpu(self) -> Optional[gpu.Gpu]:
        return gpu.main_gpu(self.gpus())

    @property
    def fsr4_build_setting(self) -> str:
        value = self.state.get("fsr4_build")
        return value if value in FSR4_BUILDS else "auto"

    @fsr4_build_setting.setter
    def fsr4_build_setting(self, value: str) -> None:
        self.state["fsr4_build"] = value if value in FSR4_BUILDS else "auto"
        self._save_state()

    def fsr4_build(self) -> str:
        """'dgpu' / 'igpu' (FSR 4.1 Exact and Lossy) or 'native' (AMD's own FSR 4.1, RDNA 4)."""
        setting = self.fsr4_build_setting
        if setting != "auto":
            return setting
        return gpu.fsr4_pack(self.main_gpu()) or "native"

    def fsr4_choices(self) -> list[str]:
        return ["fsr4:native"] if self.fsr4_build() == "native" else ["fsr4:exact", "fsr4:lossy"]

    def force_int8(self) -> bool:
        """FSR 4 needs its INT8 model on everything but RDNA 4."""
        return self.fsr4_build() != "native"

    def _fsr4_component(self) -> Component:
        return components.FSR4["igpu" if self.fsr4_build() == "igpu" else "dgpu"]

    # ---- downloads ------------------------------------------------------------------------

    def needed_components(self, choice: str) -> list[Component]:
        if upscaler_of(choice) not in ("fsr4", "fsr3"):
            return []
        needed = [components.OPTISCALER]
        if choice in ("fsr4:exact", "fsr4:lossy"):
            needed.append(self._fsr4_component())
        return needed

    def missing_components(self, choice: str) -> list[Component]:
        return [c for c in self.needed_components(choice)
                if not components.ready(c, self.components_root)]

    def component_ready(self, component: Component) -> bool:
        return components.ready(component, self.components_root)

    def download(self, wanted: list[Component],
                 progress: Callable[[Component, int, int], None] = lambda *_: None) -> str:
        lines = []
        for component in wanted:
            try:
                components.fetch(component,
                                 lambda done, total, c=component: progress(c, done, total),
                                 self.components_root)
            except components.ComponentError as error:
                if str(error) == "7z":
                    raise RuntimeError(tr("err_no_7z")) from error
                raise RuntimeError(tr("err_download", name=component_label(component),
                                      error=error)) from error
            lines.append(tr("svc_downloaded", name=component_label(component),
                            version=component.version))
        in_use = {e.status.source for e in self.entries()}
        for stale in components.stale_folders(self.components_root):
            if stale.name not in in_use:
                shutil.rmtree(stale, ignore_errors=True)
        return "\n".join(lines)

    def remove_downloads(self) -> str:
        for component in components.ALL:
            components.remove(component, self.components_root)
        return tr("svc_downloads_removed")

    def lossy_warning_text(self) -> str:
        path = components.path(self._fsr4_component(), "lossy/WARNING.txt", self.components_root)
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def accept_lossy(self) -> None:
        self.state["lossy_accepted"] = True
        self._save_state()

    def _source_for(self, choice: str) -> tuple[Component, Path]:
        """The component the upscaler DLL of a choice comes from, and the DLL in it."""
        if choice in ("fsr4:exact", "fsr4:lossy"):
            component = self._fsr4_component()
            member = f"{choice.partition(':')[2]}/{installer.FFX_FILES['upscaler']}"
        else:
            component = components.OPTISCALER
            member = installer.FFX_FILES["upscaler"]
        return component, components.path(component, member, self.components_root)

    def expected_source(self, choice: Optional[str]) -> str:
        if upscaler_of(choice) not in ("fsr4", "fsr3"):
            return ""
        component, _ = self._source_for(str(choice))
        return f"{component.key}-{component.version}"

    # ---- the HelixSR folder ------------------------------------------------------

    def helixsr(self) -> Optional[HelixSRFolder]:
        """The HelixSR folder in use. The first time, the usual places are searched."""
        saved = self.state.get("helixsr_folder")
        if saved and helixsr.looks_like_helixsr(Path(saved)):
            return helixsr.inspect(saved)
        # Not chosen yet, or the folder is gone (e.g. replaced by a newer release): look around.
        if saved or not self.state.get("helixsr_searched"):
            self.state["helixsr_searched"] = True
            candidates = helixsr.find_candidates()
            if candidates:
                self.state["helixsr_folder"] = str(candidates[0].path)
            self._save_state()
            if candidates:
                return candidates[0]
            if saved:
                return HelixSRFolder(Path(saved), None, False)
        return None

    def newer_helixsr(self) -> Optional[HelixSRFolder]:
        """A set-up HelixSR folder in the usual places that is newer than the one in use
        (each one is offered once)."""
        current = self.helixsr()
        offered = set(self.state.get("offered_folders") or [])
        for candidate in helixsr.find_candidates():
            if not candidate.ready or str(candidate.path) in offered:
                continue
            if current is None or not current.ready or candidate.version_tuple > current.version_tuple:
                self.state["offered_folders"] = sorted(offered | {str(candidate.path)})
                self._save_state()
                return candidate
        return None

    def set_helixsr_folder(self, path: Path | str) -> HelixSRFolder:
        path = Path(path).expanduser()
        if path.name == helixsr.FSRFG and helixsr.looks_like_helixsr(path.parent):
            path = path.parent   # HelixSR 2.0: its HelixSR-fsrfg folder was picked
        folder = helixsr.inspect(path)
        if not folder.version and not helixsr.looks_like_helixsr(folder.path):
            # A parent folder holding one extracted release (HelixSR-1.9.0/HelixSR-1.9.0)
            inner = [p for p in sorted(folder.path.glob("*/")) if helixsr.looks_like_helixsr(p)]
            if len(inner) == 1:
                folder = helixsr.inspect(inner[0])
        if not folder.version:
            raise FileNotFoundError(tr("hx_not_helixsr_path", path=folder.path))
        self.state["helixsr_folder"] = str(folder.path.resolve())
        self._save_state()
        return folder

    def require_helixsr(self) -> HelixSRFolder:
        """A HelixSR folder that can be installed from, or an error saying what's missing."""
        folder = self.helixsr()
        if folder is None:
            raise NeedsHelixSRError(tr("hx_none"))
        problem = folder.problem
        if problem:
            raise NeedsHelixSRError(tr(problem, path=folder.path, version=folder.version or "?",
                                       minimum=".".join(map(str, helixsr.MIN_VERSION))))
        return folder

    # ---- launch options -------------------------------------------------------

    def _live_launch_options(self, app_ids: list[int]) -> Optional[dict[int, str]]:
        if not app_ids:
            return {}
        script = """(async () => {
  const ids = %s; const out = {};
  await Promise.all(ids.map(id => new Promise(resolve => {
    const d = appDetailsStore.GetAppDetails(id);
    if (d && d.strLaunchOptions !== undefined) { out[id] = d.strLaunchOptions; return resolve(); }
    let done = false, handle;
    const finish = v => { if (done) return; done = true;
      try { handle && handle.unregister(); } catch (e) {}
      if (v !== undefined) out[id] = v; resolve(); };
    handle = SteamClient.Apps.RegisterForAppDetails(id, dd => finish(dd && dd.strLaunchOptions));
    setTimeout(() => finish(undefined), 4000);
  })));
  return JSON.stringify(out);
})()""" % json.dumps(app_ids)
        try:
            raw = self.cef.evaluate(script)
            return {int(k): v for k, v in json.loads(raw).items()}
        except (CefError, OSError, ValueError, TypeError):
            return None

    def read_launch_options(self, app_ids: list[int], live: bool = True) -> dict[int, str]:
        steam = self.steam()
        on_disk = steam.read_launch_options()
        if live and steam.is_running():
            current = self._live_launch_options(app_ids)
            if current is not None:
                on_disk.update(current)
        return on_disk

    def can_write_launch_options(self) -> bool:
        return not self.steam().is_running() or self.cef.available()

    def apply_launch_options(self, changes: dict[int, str]) -> str:
        """Save launch options. Returns 'live' or 'file' describing how."""
        steam = self.steam()
        if steam.is_running():
            try:
                for app_id, options in changes.items():
                    self.cef.set_launch_options(app_id, options)
                live = self._live_launch_options(list(changes))
                if live is not None:
                    failed = [a for a, o in changes.items() if a in live and live[a] != o]
                    if failed:
                        raise CefError(tr("svc_steam_rejected", ids=failed))
                return "live"
            except (CefError, OSError) as error:
                raise SteamMustCloseError(str(error)) from error
        steam.write_launch_options_offline(changes)
        return "file"

    def _launch_records(self) -> dict[str, dict]:
        records = self.state.get("launch")
        return dict(records) if isinstance(records, dict) else {}

    def launch_record(self, app_id: int) -> Optional[dict]:
        return self._launch_records().get(str(app_id))

    def _plan_launch(self, app_id: int, current: str,
                     opti_name: Optional[str]) -> tuple[str, Optional[dict], bool]:
        """(new options, record to keep, record changed) for OptiScaler under ``opti_name``
        (None: no OptiScaler). Only text Scaler Assistant added is ever taken out."""
        record = self.launch_record(app_id)
        options = current
        want = opti_name if opti_name and lo.needs_override(opti_name) else None
        changed = False
        if record and (want is None or record.get("dll") != lo.base(want)):
            options = lo.remove(options, record)
            record, changed = None, True
        if want and (record is None or not lo.has_override(options, want)):
            options, added = lo.add(options, want)
            if added is not None:
                record, changed = added, True
        return options, record, changed

    def _store_launch_record(self, app_id: int, record: Optional[dict]) -> None:
        records = self._launch_records()
        if record:
            records[str(app_id)] = record
        else:
            records.pop(str(app_id), None)
        self.state["launch"] = records
        self._save_state()

    def _write_launch(self, app_id: int, before: str, after: str, record: Optional[dict],
                      changed: bool) -> list[str]:
        lines = []
        if after != before:
            how = self.apply_launch_options({app_id: after})
            lines.append(tr("svc_launch_set", options=after or tr("empty"))
                         + ("" if how == "live" else " " + tr("svc_launch_file")))
        if changed:
            self._store_launch_record(app_id, record)
        return lines

    # ---- scanning -----------------------------------------------------------------

    def scan(self, rescan_library: bool = True) -> list[GameEntry]:
        cached = self.state.get("games")
        if rescan_library or not cached:
            steam = self.steam()
            games = steam.scan_games()
            self.state["games"] = [self._cache(game) for game in games]
            self.state["scanned"] = True
            self._save_state()
        return self.entries()

    @staticmethod
    def _cache(game: SteamGame) -> dict:
        layout = detect_layout(game.install_dir, game.appinfo)
        return {"app_id": game.app_id, "name": game.name, "names": game.names,
                "install_dir": str(game.install_dir), "layout": layout.to_json()}

    def gpu_kind(self) -> str:
        """nvidia / amd / amd_apu / intel / unknown, for the GPU games run on."""
        main = self.main_gpu()
        if main is None:
            return "unknown"
        if main.vendor == "NVIDIA":
            return "nvidia"
        if main.vendor == "Intel":
            return "intel"
        return "amd_apu" if main.apu else "amd"

    def _ways(self, layout: GameLayout, folder: Optional[HelixSRFolder]) -> list[str]:
        modern = bool(folder and folder.modern)
        loader = folder.has_loader if folder and folder.version and not modern else True
        return layout.ways(loader, modern)

    def blocked_choices(self, ways: list[str]) -> dict[str, str]:
        """HelixSR ways this PC's GPU can't use. The DLSS way needs a GeForce: with an AMD or
        Intel GPU games don't offer DLSS to select (no NVIDIA driver answers them)."""
        blocked = {}
        if "dlss" in ways and self.gpu_kind() in ("amd", "amd_apu", "intel"):
            blocked["helixsr:dlss"] = "blk_dlss_gpu"
        return blocked

    def recommended_choice(self, choices: list[str]) -> Optional[str]:
        """Built-in graphics (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) and Intel GPUs: Lossy."""
        if self.gpu_kind() in ("amd_apu", "intel") and "fsr4:lossy" in choices:
            return "fsr4:lossy"
        return None

    def choices_for(self, layout: GameLayout, folder: Optional[HelixSRFolder] = None,
                    ways: Optional[list[str]] = None) -> list[str]:
        ways = self._ways(layout, folder) if ways is None else ways
        blocked = self.blocked_choices(ways)
        result = [f"helixsr:{way}" for way in ways if f"helixsr:{way}" not in blocked]
        if layout.optiscaler_possible:
            result += self.fsr4_choices() + ["fsr3"]
        return result

    def modern_choice(self, choice: str, folder: Optional[HelixSRFolder]) -> str:
        """With HelixSR 2.0 an earlier way (OptiScaler, DLSS loader) is updated to HelixSR Scaler."""
        if folder is not None and folder.modern and choice in ("helixsr:optiscaler", "helixsr:dlss"):
            return "helixsr:hscaler"
        return choice

    def entries(self, live: bool = False) -> list[GameEntry]:
        folder = self.helixsr()
        games = self.state.get("games", [])
        try:
            options = self.read_launch_options([int(g["app_id"]) for g in games], live)
        except OSError:
            options = {}
        result = []
        for game in games:
            app_id = int(game["app_id"])
            layout = GameLayout.from_json(game.get("layout"))
            status = installer.state(layout)
            current = options.get(app_id, "")
            missing = bool(status.opti_name and lo.needs_override(status.opti_name)
                           and not lo.has_override(current, status.opti_name))
            if status.route == "scaler":
                outdated = status.source != self.expected_source(status.choice)
            else:
                outdated = status.outdated(folder)
            ways = self._ways(layout, folder)
            choices = self.choices_for(layout, folder, ways)
            result.append(GameEntry(
                app_id=app_id,
                name=game["name"],
                install_dir=game["install_dir"],
                layout=layout,
                status=status,
                ways=ways,
                choices=choices,
                blocked=self.blocked_choices(ways),
                recommended=self.recommended_choice(choices),
                outdated=outdated,
                names=dict(game.get("names") or {}),
                launch_options=current,
                launch_missing=missing,
            ))
        return result

    def _refresh_game(self, app_id: int) -> tuple[dict, GameLayout]:
        """Look at one game's folder again right before changing it."""
        steam = self.steam()
        game = next((g for g in steam.scan_games() if g.app_id == app_id), None)
        if game is None:
            raise LookupError(tr("svc_app_missing", app_id=app_id))
        cached = self._cache(game)
        games = self.state.setdefault("games", [])
        for i, item in enumerate(games):
            if int(item["app_id"]) == app_id:
                games[i] = cached
                break
        else:
            games.append(cached)
        self._save_state()
        return cached, GameLayout.from_json(cached["layout"])

    def _name(self, cached: dict) -> str:
        return localized_name(cached["name"], cached.get("names") or {})

    def _ensure_closed(self, app_id: int, name: str) -> None:
        if app_id in running_app_ids(self.proc):
            raise GameRunningError(tr("err_game_running", name=name))

    # ---- OptiScaler's file name ---------------------------------------------------------

    def opti_name_setting(self, app_id: int) -> Optional[str]:
        value = (self.state.get("opti_names") or {}).get(str(app_id))
        return value if value in optiscaler.NAMES else None

    def set_opti_name(self, app_id: int, name: Optional[str]) -> None:
        names = dict(self.state.get("opti_names") or {})
        if name in optiscaler.NAMES:
            names[str(app_id)] = name
        else:
            names.pop(str(app_id), None)
        self.state["opti_names"] = names
        self._save_state()

    def _opti_name(self, cached: dict, layout: GameLayout, status: InstallState,
                   choice: str, options: str) -> tuple[Optional[str], str]:
        """OptiScaler's file name for a choice in this game, and why (see choose_name)."""
        if not uses_optiscaler(choice) or not layout.exe_dir:
            return None, ""
        chosen = self.opti_name_setting(int(cached["app_id"]))
        if chosen:
            return chosen, "user"
        same = ((choice == "helixsr:optiscaler" and status.route == "optiscaler")
                or (choice == "helixsr:hscaler" and status.route == "hscaler")
                or (upscaler_of(choice) in ("fsr4", "fsr3") and status.route == "scaler"))
        blocked = lo.blocked_names(options)
        if status.opti_name:
            if same or not status.opti_over_foreign:
                return status.opti_name, "installed"   # an install keeps its name
            # Switching away from an install that put OptiScaler in place of the game's file:
            # that file comes back, so OptiScaler gets another name.
            blocked.add(status.opti_name.lower())
        names = [cached["name"], *(cached.get("names") or {}).values()]
        return optiscaler.choose_name(Path(layout.exe_dir), layout.api, names, None, blocked)

    def opti_name_auto(self, app_id: int) -> tuple[str, str]:
        """The name OptiScaler would get without a choice by hand, and why (for the UI)."""
        game = next((g for g in self.state.get("games", []) if int(g["app_id"]) == app_id), None)
        if game is None:
            raise LookupError(tr("svc_app_missing", app_id=app_id))
        layout = GameLayout.from_json(game.get("layout"))
        if not layout.exe_dir:
            return "dxgi.dll", "default"
        status = installer.state(layout)
        if status.opti_name:
            return status.opti_name, "installed"
        options = self.read_launch_options([app_id]).get(app_id, "")
        names = [game["name"], *(game.get("names") or {}).values()]
        return optiscaler.choose_name(Path(layout.exe_dir), layout.api, names, None,
                                      lo.blocked_names(options))

    # ---- actions ------------------------------------------------------------------------

    def plan(self, app_id: int, choice: str) -> ChoicePlan:
        """What ``apply`` will need; nothing is changed."""
        if choice not in installer.CHOICES:
            raise LookupError(choice)
        choice = self.modern_choice(choice, self.helixsr())
        cached, layout = self._refresh_game(app_id)
        self._check_blocked(layout, choice)
        status = installer.state(layout)
        options = self.read_launch_options([app_id]).get(app_id, "")
        name, reason = self._opti_name(cached, layout, status, choice, options)
        try:
            after, _, _ = self._plan_launch(app_id, options, name)
        except lo.OverrideConflict:
            after = options
        needs_helixsr = False
        if upscaler_of(choice) == "helixsr":
            try:
                self.require_helixsr()
            except NeedsHelixSRError:
                needs_helixsr = True
        return ChoicePlan(
            app_id=app_id, choice=choice, downloads=self.missing_components(choice),
            needs_helixsr=needs_helixsr, opti_name=name, opti_reason=reason,
            launch_before=options, launch_after=after,
            lossy_warning=choice == "fsr4:lossy" and not self.state.get("lossy_accepted"),
            anti_cheat=list(layout.anti_cheat))

    def _check_blocked(self, layout: GameLayout, choice: str) -> None:
        reason = self.blocked_choices(self._ways(layout, self.helixsr())).get(choice)
        if reason:
            raise installer.InstallError(tr(reason))

    def apply(self, app_id: int, choice: str) -> str:
        """Install, switch to, update or repair a choice in one game."""
        if choice not in installer.CHOICES:
            raise LookupError(choice)
        upscaler = upscaler_of(choice)
        folder = self.require_helixsr() if upscaler == "helixsr" else None
        choice = self.modern_choice(choice, folder)
        missing = self.missing_components(choice)
        if missing:
            raise NeedsDownloadError(missing)
        cached, layout = self._refresh_game(app_id)
        self._check_blocked(layout, choice)
        name = self._name(cached)
        self._ensure_closed(app_id, name)
        before = installer.state(layout)
        options = self.read_launch_options([app_id]).get(app_id, "")
        opti_name, _ = self._opti_name(cached, layout, before, choice, options)
        try:
            new_options, record, changed = self._plan_launch(app_id, options, opti_name)
        except lo.OverrideConflict as error:
            raise installer.InstallError(
                tr("err_override_conflict", name=f"{error}.dll")) from error
        if new_options != options and not self.can_write_launch_options():
            raise SteamMustCloseError(tr("steam_close_q"))   # before any file is changed
        if folder is not None:
            route = choice.partition(":")[2]
            notes = installer.install_helixsr(layout, folder, route, STAMP,
                                              opti_name if route in ("optiscaler", "hscaler")
                                              else None, cached["install_dir"])
        else:
            component, dll = self._source_for(choice)
            plan = ScalerPlan(
                choice=choice, opti_name=str(opti_name),
                optiscaler=components.folder(components.OPTISCALER, self.components_root),
                optiscaler_version=components.OPTISCALER.version, upscaler_dll=dll,
                force_int8=upscaler == "fsr4" and self.force_int8(),
                source=f"{component.key}-{component.version}")
            notes = installer.install_scaler(layout, plan, STAMP)
        after = installer.state(layout)
        label = choice_label(choice)
        if before.choice == choice:
            head = tr("svc_updated", name=name, choice=label)
        elif before.installed:
            head = tr("svc_switched", name=name, choice=label)
        else:
            head = tr("svc_installed", name=name, choice=label)
        lines = [head, *("  " + n for n in notes)]
        lines += self._write_launch(app_id, options, new_options, record, changed)
        lines.append(tr("svc_pick_" + choice.replace(":", "_")))
        if after.issues:
            lines += [tr(i) for i in after.issues]
        return "\n".join(lines)

    def uninstall(self, app_id: int, remove_settings: bool) -> str:
        cached, layout = self._refresh_game(app_id)
        name = self._name(cached)
        self._ensure_closed(app_id, name)
        options = self.read_launch_options([app_id]).get(app_id, "")
        new_options, record, changed = self._plan_launch(app_id, options, None)
        if new_options != options and not self.can_write_launch_options():
            raise SteamMustCloseError(tr("steam_close_q"))
        notes = installer.remove(layout, remove_settings)
        lines = [tr("svc_removed", name=name), *("  " + n for n in notes)]
        lines += self._write_launch(app_id, options, new_options, record, changed)
        return "\n".join(lines)

    def outdated_entries(self) -> list[GameEntry]:
        return [e for e in self.entries() if e.installed and e.outdated]

    def missing_for_update(self) -> list[Component]:
        missing: list[Component] = []
        for entry in self.outdated_entries():
            for component in self.missing_components(str(entry.status.choice)):
                if component not in missing:
                    missing.append(component)
        return missing

    def update_all(self) -> str:
        """Bring every game to the current HelixSR build and the current downloads."""
        lines = []
        running = running_app_ids(self.proc)
        for entry in self.outdated_entries():
            if entry.app_id in running:
                lines.append(tr("err_game_running", name=entry.display_name))
                continue
            try:
                lines.append(self.apply(entry.app_id, str(entry.status.choice)))
            except NeedsDownloadError as error:
                names = ", ".join(component_label(c) for c in error.missing)
                lines.append(tr("svc_update_failed", name=entry.display_name,
                                error=tr("svc_needs_download", names=names)))
            except SteamMustCloseError:
                raise
            except (OSError, RuntimeError, LookupError) as error:
                lines.append(tr("svc_update_failed", name=entry.display_name, error=error))
        return "\n".join(lines) if lines else tr("svc_all_current")

    # ---- settings and logs ---------------------------------------------------------------

    def _entry(self, app_id: int) -> GameEntry:
        entry = next((e for e in self.entries() if e.app_id == app_id), None)
        if entry is None:
            raise LookupError(tr("svc_app_missing", app_id=app_id))
        return entry

    def read_settings(self, app_id: int) -> dict[str, str]:
        entry = self._entry(app_id)
        for directory in entry.status.ini_dirs:
            values = settings.read(directory / settings.INI)
            if values:
                return values
        return {}

    def write_settings(self, app_id: int, values: dict[str, Optional[str]]) -> str:
        entry = self._entry(app_id)
        if not entry.installed or entry.status.upscaler != "helixsr":
            raise LookupError(tr("rm_not_installed"))
        paths = [d / settings.INI for d in entry.status.ini_dirs]
        for path in paths:
            settings.write(path, values)
        shown = {k: v for k, v in self.read_settings(app_id).items()}
        summary = ", ".join(f"{k} = {v}" for k, v in shown.items()) or tr("set_all_default")
        return "\n".join([tr("svc_settings_saved", name=entry.display_name, settings=summary),
                          *(f"  {p}" for p in paths), tr("svc_settings_restart")])

    def fix_wave_size(self, app_id: int) -> str:
        return self.write_settings(app_id, {"WaveSize": "64"})

    def log_text(self, app_id: int) -> tuple[Optional[Path], str]:
        entry = self._entry(app_id)
        existing = [p for p in entry.status.log_files if p.is_file()]
        if not existing:
            return None, ""
        newest = max(existing, key=lambda p: p.stat().st_mtime)
        from .hxlog import read_text
        return newest, read_text(newest)

    def game_folder(self, app_id: int) -> Path:
        entry = self._entry(app_id)
        exe = entry.layout.exe_dir
        if entry.status.route == "direct" and entry.status.ini_dirs:
            return entry.status.ini_dirs[0]
        return Path(exe) if exe else Path(entry.install_dir)

    # ---- outside programs ------------------------------------------------------------------

    @staticmethod
    def open_path(path: Path) -> None:
        subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)

    def _steam_command(self) -> str:
        return shutil.which("steam") or str(self.steam().root / "steam.sh")

    def shutdown_steam(self) -> bool:
        subprocess.Popen([self._steam_command(), "-shutdown"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        return self.steam().wait_until_closed(90)

    def start_steam(self) -> None:
        subprocess.Popen([self._steam_command()], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)

    def launch_game(self, app_id: int) -> None:
        """Ask Steam to start the game (it forwards to a running client)."""
        url = f"steam://rungameid/{int(app_id)}"
        steam_bin = shutil.which("steam")
        command = [steam_bin, url] if steam_bin else ["xdg-open", url]
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except OSError as error:
            raise RuntimeError(tr("svc_launch_failed", error=error)) from error

    @property
    def language(self) -> Optional[str]:
        return self.state.get("language")

    @language.setter
    def language(self, code: str) -> None:
        self.state["language"] = code
        self._save_state()

    @property
    def overlay_enabled(self) -> bool:
        return bool(self.state.get("overlay", True))

    @overlay_enabled.setter
    def overlay_enabled(self, enabled: bool) -> None:
        self.state["overlay"] = bool(enabled)
        self._save_state()

    @property
    def theme(self) -> str:
        value = self.state.get("theme", "auto")
        return value if value in ("auto", "dark", "light") else "auto"

    @theme.setter
    def theme(self, choice: str) -> None:
        self.state["theme"] = choice if choice in ("auto", "dark", "light") else "auto"
        self._save_state()


def choice_label(choice: Optional[str]) -> str:
    return tr("choice_" + (choice or "none").replace(":", "_"))


def component_label(component: Component) -> str:
    if component.key == "optiscaler":
        return "OptiScaler"
    return tr("comp_" + component.key.replace("-", "_"))
