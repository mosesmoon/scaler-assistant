"""Application logic for HelixSR Assistant, independent of the UI toolkit."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import __version__, helixsr, installer, settings
from .games import GameLayout, detect_layout
from .helixsr import HelixSRFolder
from .i18n import localized_name, tr
from .installer import InstallState
from .runtime import Watch, running_app_ids
from .steam import SteamGame, SteamInstallation

STAMP = f"HelixSR Assistant {__version__}"


def state_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "helixsr-assistant" / "state.json"


class GameRunningError(RuntimeError):
    """HelixSR's files can't be changed while the game has them loaded."""


@dataclass
class GameEntry:
    app_id: int
    name: str
    install_dir: str
    layout: GameLayout
    status: InstallState
    ways: list[str] = field(default_factory=list)
    outdated: bool = False
    names: dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return localized_name(self.name, self.names)

    @property
    def installed(self) -> bool:
        return self.status.installed

    @property
    def supported(self) -> bool:
        return bool(self.ways) or self.installed

    @property
    def needs_attention(self) -> bool:
        return self.outdated or bool(self.status.issues)

    def matches(self, query: str) -> bool:
        query = query.casefold()
        return (query in str(self.app_id)
                or any(query in n.casefold() for n in (self.name, *self.names.values())))

    def watch(self) -> Watch:
        status, layout = self.status, self.layout
        helpers: list[str] = []
        if status.route in ("optiscaler", "dlss") and layout.exe_dir:
            exe = Path(layout.exe_dir)
            record = installer.read_record(exe / "HelixSR")
            name = record.get("optiscaler") if status.route == "optiscaler" else installer.LOADER
            helpers.append(str(exe / str(name or "dxgi.dll")))
        return Watch([str(p) for p in status.dll_files], helpers,
                     [str(p) for p in status.log_files])


class AssistantService:
    def __init__(self, steam_root: Optional[Path] = None,
                 state_file: Optional[Path] = None,
                 proc: Path = Path("/proc")) -> None:
        self._steam_root = steam_root
        self.proc = proc
        self.state_file = state_file or state_path()
        self.state = self._load_state()

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
            raise FileNotFoundError(tr("hx_none"))
        problem = folder.problem
        if problem:
            raise FileNotFoundError(tr(problem, path=folder.path, version=folder.version or "?",
                                       minimum=".".join(map(str, helixsr.MIN_VERSION))))
        return folder

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

    def entries(self) -> list[GameEntry]:
        folder = self.helixsr()
        loader = folder.has_loader if folder and folder.version else True
        result = []
        for game in self.state.get("games", []):
            layout = GameLayout.from_json(game.get("layout"))
            status = installer.state(layout)
            result.append(GameEntry(
                app_id=int(game["app_id"]),
                name=game["name"],
                install_dir=game["install_dir"],
                layout=layout,
                status=status,
                ways=layout.ways(loader),
                outdated=status.outdated(folder),
                names=dict(game.get("names") or {}),
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

    # ---- actions ------------------------------------------------------------------------

    def install(self, app_id: int, route: str) -> str:
        folder = self.require_helixsr()   # before any change: nothing is touched without it
        cached, layout = self._refresh_game(app_id)
        name = self._name(cached)
        self._ensure_closed(app_id, name)
        before = installer.state(layout)
        notes = installer.install(layout, folder, route, STAMP)
        after = installer.state(layout)
        if before.route == route:
            head = tr("svc_updated", name=name, version=folder.version, way=tr("way_" + route))
        elif before.route:
            head = tr("svc_switched", name=name, way=tr("way_" + route))
        else:
            head = tr("svc_installed", name=name, version=folder.version, way=tr("way_" + route))
        lines = [head, *("  " + n for n in notes), tr("svc_pick_" + route)]
        if after.issues:
            lines += [tr(i) for i in after.issues]
        return "\n".join(lines)

    def uninstall(self, app_id: int, remove_settings: bool) -> str:
        cached, layout = self._refresh_game(app_id)
        name = self._name(cached)
        self._ensure_closed(app_id, name)
        notes = installer.remove(layout, remove_settings)
        return "\n".join([tr("svc_removed", name=name), *("  " + n for n in notes)])

    def update_all(self) -> str:
        """Bring every game with an older HelixSR build to the HelixSR folder's build."""
        folder = self.require_helixsr()
        lines = []
        running = running_app_ids(self.proc)
        for entry in self.entries():
            if not (entry.installed and entry.outdated):
                continue
            if entry.app_id in running:
                lines.append(tr("err_game_running", name=entry.display_name))
                continue
            try:
                lines.append(self.install(entry.app_id, entry.status.route))
            except (OSError, RuntimeError, LookupError) as error:
                lines.append(tr("svc_update_failed", name=entry.display_name, error=error))
        return "\n".join(lines) if lines else tr("svc_all_current", version=folder.version)

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
        if not entry.installed:
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
