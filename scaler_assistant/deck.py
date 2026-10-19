"""The Steam Deck (Decky Loader) plugin's view of Scaler Assistant.

Everything here is plain JSON-ready data for the plugin's React panel; the work is
done by ``AssistantService`` exactly as in the desktop app, so both share their
state, downloads and launch-option records.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any, Callable, Optional

from . import __version__, components, gpu, i18n, optiscaler, settings
from .helixsr import MIN_VERSION
from .i18n import tr
from .launch_options import needs_override
from .runtime import RunningGame, detect_running
from .service import (
    AssistantService, GameEntry, GameRunningError, NeedsDownloadError, NeedsHelixSRError,
    SteamMustCloseError, choice_label, component_label, upscaler_of,
)
from .status import describe

API_LABELS = {"dx12": "DX12", "dx11": "DX11", "vulkan": "Vulkan"}
# Steam's own language names -> Scaler Assistant's languages.
STEAM_LANGUAGES = {
    "tchinese": "zh_TW", "schinese": "zh_CN", "english": "en", "japanese": "ja", "german": "de",
    "french": "fr", "spanish": "es", "latam": "es", "italian": "it", "thai": "th",
    "vietnamese": "vi",
}
LOG_LINES = 300


def plain(text: str) -> str:
    """The desktop strings carry a little HTML; the Deck shows plain text."""
    text = re.sub(r"<br\s*/?>|</p>|</li>|<ul>", "\n", text)
    text = re.sub(r"<li>", "• ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def steam_language(name: str) -> str:
    return STEAM_LANGUAGES.get((name or "").lower(), i18n.match_language(name or ""))


class DeckBridge:
    def __init__(self, service: Optional[AssistantService] = None) -> None:
        self.service = service or AssistantService()
        self.steam_language = "en"
        self.log: list[str] = []
        i18n.set_language(self.service.language)

    # ---- language and text ----------------------------------------------------------------

    def set_steam_language(self, name: str) -> str:
        self.steam_language = steam_language(name)
        return i18n.set_language(self.service.language or self.steam_language)

    def set_language(self, code: Optional[str]) -> str:
        """None / "" follows Steam's language."""
        if code in i18n.CODES:
            self.service.language = code
            return i18n.set_language(code)
        self.service.state.pop("language", None)
        self.service._save_state()
        return i18n.set_language(self.steam_language)

    def strings(self) -> dict[str, str]:
        return {key: plain(value) if "<" in value or "&" in value else value
                for key, value in i18n.STRINGS[i18n.current()].items()}

    def _note(self, text: str) -> str:
        for line in str(text).splitlines():
            self.log.append(line)
        del self.log[:-LOG_LINES]
        return text

    # ---- overview -------------------------------------------------------------------------

    def overview(self, rescan: bool = False) -> dict[str, Any]:
        service = self.service
        if rescan or not service.has_scanned:
            entries = service.scan(rescan_library=True)
        else:
            entries = service.entries(live=True)
        running = detect_running({e.app_id: e.watch() for e in entries if e.installed},
                                 service.proc)
        rdna3 = any(g.rdna3_or_newer for g in service.gpus())
        games = [self.game(e, running.get(e.app_id), rdna3) for e in entries if e.supported]
        games.sort(key=lambda g: (g["app_id"] not in running, not g["installed"],
                                  g["name"].casefold()))
        main = service.main_gpu()
        return {
            "version": __version__,
            "language": service.language or "",
            "languages": [[code, native] for code, native, _ in i18n.LANGUAGES],
            "games": games,
            "unsupported": sum(1 for e in entries if not e.supported),
            "running": sorted(running),
            "outdated": sum(1 for e in entries if e.installed and e.outdated),
            "helixsr": self.helixsr(),
            "downloads": self.downloads(),
            "gpu": tr("gpu_pill", gpu=main.label()) if main else tr("gpu_unknown"),
            "toast": service.overlay_enabled,
            "home": str(Path.home()),
            "log": self.log[-60:],
        }

    def game(self, entry: GameEntry, game: Optional[RunningGame] = None,
             rdna3: bool = False) -> dict[str, Any]:
        status, layout = entry.status, entry.layout
        if status.installed:
            tone = "warn" if entry.issues else "info" if entry.outdated else "ok"
            label = choice_label(status.choice)
            if status.upscaler == "helixsr":
                detail = tr("st_helixsr", version=status.version or "?")
                if status.opti_name:
                    detail += " · " + tr("st_opti", name=status.opti_name)
            else:
                detail = tr("st_opti_version", version=status.version or "?", name=status.opti_name)
        else:
            tone, label, detail = "idle", plain(tr("st_not_installed")).lstrip("○ "), ""
        notes = []
        if entry.outdated:
            folder = self.service.helixsr() if status.upscaler == "helixsr" else None
            notes.append(tr("st_outdated", version=folder.version if folder else "?")
                         if status.upscaler == "helixsr" else tr("st_outdated_fsr"))
        live = None
        if game is not None:
            if entry.installed:
                headline, live_tone, lines, problems = describe(entry, game, rdna3)
                live = {"headline": headline, "tone": live_tone,
                        "lines": [{"label": a, "detail": b, "active": c} for a, b, c in lines],
                        "notes": problems, "loaded": game.helixsr_loaded}
            else:
                live = {"headline": tr("rt_running_without"), "tone": "idle", "lines": [],
                        "notes": [], "loaded": False}
        return {
            "app_id": entry.app_id,
            "name": entry.display_name,
            "installed": entry.installed,
            "choice": status.choice,
            "label": label,
            "tone": tone,
            "detail": detail,
            "upscaler": status.upscaler,
            "api": API_LABELS.get(layout.api, ""),
            "upscalers": list(layout.upscalers),
            "anti_cheat": list(layout.anti_cheat),
            "outdated": entry.outdated,
            "issues": [plain(tr(i)) for i in entry.issues],
            "notes": notes,
            "hint": plain(tr("svc_pick_" + str(status.choice).replace(":", "_")))
                    if status.installed else "",
            "opti_name": status.opti_name or "",
            "opti_possible": layout.optiscaler_possible,
            "launch_options": entry.launch_options,
            "shows_launch": bool(status.opti_name and needs_override(status.opti_name)
                                 or entry.launch_options),
            "has_log": entry.installed,
            # HelixSR frame generation: null = not offered (HelixSR Scaler + DLSS Frame Generation only)
            "fg": entry.fg,
            "fg_block": plain(tr(entry.fg_block)) if entry.fg_block else "",
            "choices": self.choices(entry, self.service.helixsr()),
            "running": live,
        }

    @staticmethod
    def choices(entry: GameEntry, folder=None) -> list[dict[str, Any]]:
        """Every choice for the game: ways this GPU can't use come without an id (shown greyed
        out, with the reason), the one recommended for this PC is marked."""
        result = []
        order = [f"helixsr:{way}" for way in entry.ways]
        order += [c for c in entry.choices if c not in order]
        for choice in order:
            if upscaler_of(choice) == "helixsr":
                way = choice.partition(":")[2]
                text = f"{tr('menu_helixsr')} · {tr('way_' + way)}"
                hint = tr("menu_install_" + way)
            else:
                text = choice_label(choice)
                hint = tr("menu_" + choice.replace(":", "_"))
            reason = entry.blocked.get(choice)
            if reason:
                result.append({"id": "", "label": f"{text} ({tr(reason + '_short')})",
                               "hint": tr(reason), "current": False, "recommended": False})
                continue
            recommended = choice == entry.recommended
            if recommended:
                text = f"{text}  {tr('rec_suffix')}"
                hint = f"{hint}\n{tr('rec_lossy')}"
            result.append({"id": choice, "label": text, "hint": hint,
                           "current": choice == entry.status.choice, "recommended": recommended})
        layout = entry.layout
        if layout.optiscaler_possible and not entry.ways:
            result.insert(0, {"id": "", "label": tr("menu_helixsr"), "current": False,
                              "recommended": False,
                              "hint": tr("menu_helixsr_api_hx2", version=folder.version,
                                         api=API_LABELS.get(layout.api, "?"))
                              if folder is not None and folder.version and not folder.modern
                              else tr("menu_helixsr_api", api=API_LABELS.get(layout.api, "?"))})
        return result

    def helixsr(self) -> dict[str, Any]:
        folder = self.service.helixsr()
        minimum = ".".join(map(str, MIN_VERSION))
        if folder is None:
            return {"ready": False, "pill": tr("hx_pill_none"), "path": "",
                    "message": plain(tr("hx_none"))}
        if folder.ready:
            return {"ready": True, "pill": tr("hx_pill_ready", version=folder.version),
                    "path": str(folder.path), "message": ""}
        problem = folder.problem or "hx_not_helixsr"
        return {"ready": False, "pill": tr("hx_pill_problem", version=folder.version or "?"),
                "path": str(folder.path),
                "message": plain(tr(problem, path=folder.path, version=folder.version or "?",
                                    minimum=minimum))}

    def downloads(self) -> dict[str, Any]:
        service = self.service
        build = service.fsr4_build()
        main = service.main_gpu()
        auto = tr("dl_build_auto", build=tr("dl_build_" + (gpu.fsr4_pack(main) or "native")),
                  gpu=main.label() if main else "?")
        wanted = [components.OPTISCALER]
        if build != "native":
            wanted += service.needed_components("fsr4:exact")[1:]
        items = []
        for component in components.ALL:
            items.append({
                "key": component.key, "name": component_label(component),
                "version": component.version, "size": round(component.size / 1_000_000),
                "ready": service.component_ready(component),
                "wanted": component in wanted,
                "description": tr("dl_desc_" + component.key.replace("-", "_")),
                "licence": tr("dl_licence", licence=component.licence),
                "project": component.project,
            })
        return {
            "items": items,
            "missing": [c.key for c in wanted if not service.component_ready(c)],
            "build": service.fsr4_build_setting,
            "builds": [["auto", auto], ["dgpu", tr("dl_build_dgpu")],
                       ["igpu", tr("dl_build_igpu")], ["native", tr("dl_build_native")]],
            "intro": plain(tr("dl_intro", folder=service.components_root
                              or components.data_dir())),
        }

    # ---- choosing --------------------------------------------------------------------------

    def _entry(self, app_id: int) -> GameEntry:
        entry = next((e for e in self.service.entries() if e.app_id == app_id), None)
        if entry is None:
            raise LookupError(tr("svc_app_missing", app_id=app_id))
        return entry

    def plan(self, app_id: int, choice: str) -> dict[str, Any]:
        """What has to be confirmed before ``apply``, in the order to ask."""
        entry = self._entry(app_id)
        plan = self.service.plan(app_id, choice)
        same = entry.status.choice == choice
        steps: list[dict[str, Any]] = []
        if plan.needs_helixsr:
            steps.append({"kind": "helixsr", "title": tr("hx_title"),
                          "text": self.helixsr()["message"] or plain(tr("hx_none"))})
            return {"choice": choice, "label": choice_label(choice), "steps": steps}
        if not same and choice == "helixsr:dlss":
            steps.append({"kind": "confirm", "title": tr("warn_dlss_title"),
                          "text": plain(tr("warn_dlss", name=entry.display_name)),
                          "ok": tr("btn_install_anyway")})
        if not same and plan.anti_cheat and not entry.installed:
            steps.append({"kind": "confirm", "title": tr("warn_ac_title"),
                          "text": plain(tr("warn_ac", name=entry.display_name,
                                           ac=", ".join(plan.anti_cheat))),
                          "ok": tr("btn_install_anyway")})
        if plan.downloads:
            items = "".join(f"<li>{component_label(c)} {c.version} ({round(c.size / 1_000_000)} MB)"
                            f" — {c.licence}</li>" for c in plan.downloads)
            steps.append({"kind": "download", "title": tr("dl_title"),
                          "text": plain(tr("dl_confirm", what=choice_label(choice), items=items)),
                          "ok": tr("dl_confirm_ok"), "keys": [c.key for c in plan.downloads]})
        if plan.lossy_warning:
            steps.append({"kind": "lossy", "title": tr("lossy_title"),
                          "text": plain(tr("lossy_intro")), "ok": tr("lossy_accept"),
                          "body": None})
        return {"choice": choice, "label": choice_label(choice), "steps": steps}

    def lossy_text(self) -> str:
        return self.service.lossy_warning_text() or tr("lossy_missing")

    def accept_lossy(self) -> None:
        self.service.accept_lossy()

    def _run(self, fn: Callable[[], str]) -> dict[str, Any]:
        try:
            return {"ok": True, "message": self._note(fn())}
        except SteamMustCloseError as error:
            message = tr("deck_steam_rejected") + (f"\n{error}" if str(error) else "")
            return {"ok": False, "kind": "steam", "message": self._note(message)}
        except GameRunningError as error:
            return {"ok": False, "kind": "running", "message": self._note(str(error))}
        except NeedsHelixSRError as error:
            return {"ok": False, "kind": "helixsr", "message": self._note(str(error))}
        except NeedsDownloadError as error:
            return {"ok": False, "kind": "download", "keys": [c.key for c in error.missing],
                    "message": tr("svc_needs_download",
                                  names=", ".join(component_label(c) for c in error.missing))}
        except (OSError, RuntimeError, LookupError, ValueError) as error:
            return {"ok": False, "kind": "error",
                    "message": self._note(tr("log_error", error=error))}

    def apply(self, app_id: int, choice: str) -> dict[str, Any]:
        return self._run(lambda: self.service.apply(app_id, choice))

    def set_frame_generation(self, app_id: int, on: bool) -> dict[str, Any]:
        return self._run(lambda: self.service.set_frame_generation(app_id, on))

    def uninstall(self, app_id: int, remove_settings: bool = False) -> dict[str, Any]:
        return self._run(lambda: self.service.uninstall(app_id, remove_settings))

    def update_all(self) -> dict[str, Any]:
        missing = self.service.missing_for_update()
        if missing:
            return {"ok": False, "kind": "download", "keys": [c.key for c in missing],
                    "message": tr("svc_needs_download",
                                  names=", ".join(component_label(c) for c in missing))}
        return self._run(self.service.update_all)

    def removal(self, app_id: int) -> dict[str, Any]:
        """The removal question for one game."""
        entry = self._entry(app_id)
        text = plain(tr("remove_body", name=entry.display_name,
                        choice=choice_label(entry.status.choice)))
        if (entry.launch_options and entry.status.opti_name
                and needs_override(entry.status.opti_name)):
            text += "\n\n" + plain(tr("remove_launch"))
        has_settings = entry.status.upscaler == "helixsr" and any(
            (d / settings.INI).is_file() for d in entry.status.ini_dirs)
        return {"title": tr("remove_title"), "text": text, "ok": tr("btn_remove"),
                "settings": tr("remove_settings") if has_settings else ""}

    # ---- downloads -------------------------------------------------------------------------

    def download(self, keys: list[str],
                 progress: Callable[[str, int, int], None] = lambda *_: None) -> dict[str, Any]:
        wanted = [c for c in components.ALL if c.key in keys]
        return self._run(lambda: self.service.download(
            wanted, lambda c, done, total: progress(component_label(c), done, total)))

    def remove_downloads(self) -> dict[str, Any]:
        return self._run(self.service.remove_downloads)

    def set_fsr4_build(self, value: str) -> None:
        self.service.fsr4_build_setting = value

    # ---- OptiScaler's name, HelixSR, logs ---------------------------------------------------

    def opti_names(self, app_id: int) -> dict[str, Any]:
        entry = self._entry(app_id)
        name, reason = self.service.opti_name_auto(app_id)
        options = [["", tr("on_auto", name=name, reason=tr("on_reason_" + reason))]]
        for item in optiscaler.NAMES:
            note = f"  {tr('on_needs_launch')}" if needs_override(item) else ""
            options.append([item, item + note])
        return {"title": tr("on_title", name=entry.display_name),
                "intro": plain(tr("on_intro")), "hint": plain(tr("on_launch_hint")),
                "current": entry.status.opti_name or "",
                "chosen": self.service.opti_name_setting(app_id) or "",
                "auto": name, "options": options}

    def set_opti_name(self, app_id: int, name: str) -> dict[str, Any]:
        """Save the choice; OptiScaler is moved right away when it is installed."""
        entry = self._entry(app_id)
        automatic, _ = self.service.opti_name_auto(app_id)
        self.service.set_opti_name(app_id, name or None)
        self._note(tr("log_opti_name", name=entry.display_name,
                      file=name or tr("on_auto_short", name=automatic)))
        wanted = name or automatic
        if entry.status.opti_name and wanted != entry.status.opti_name:
            return self.apply(app_id, str(entry.status.choice))
        return {"ok": True, "message": ""}

    def set_helixsr_folder(self, path: str) -> dict[str, Any]:
        try:
            folder = self.service.set_helixsr_folder(path)
        except FileNotFoundError as error:
            return {"ok": False, "kind": "error", "message": str(error)}
        message = tr("log_folder", path=folder.path, version=folder.version or "?")
        return {"ok": True, "message": self._note(message), "helixsr": self.helixsr()}

    def log_text(self, app_id: int) -> dict[str, Any]:
        path, text = self.service.log_text(app_id)
        lines = text.splitlines()[-400:]
        return {"path": str(path or ""), "text": "\n".join(lines)}

    def set_toast(self, enabled: bool) -> None:
        self.service.overlay_enabled = bool(enabled)

    def runtime(self, app_id: int) -> Optional[dict[str, Any]]:
        """The live state of one running game (for the notification when it starts)."""
        try:
            entry = self._entry(app_id)
        except LookupError:
            return None
        if not entry.installed:
            return None
        running = detect_running({app_id: entry.watch()}, self.service.proc).get(app_id)
        if running is None:
            return None
        rdna3 = any(g.rdna3_or_newer for g in self.service.gpus())
        return self.game(entry, running, rdna3)
