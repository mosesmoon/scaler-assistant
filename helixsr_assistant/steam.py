"""Discover the local Steam installation, its libraries and installed games."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import vdf_text
from .appinfo import AppInfoError, read_appinfo

_STEAM_ROOT_CANDIDATES = (
    "~/.local/share/Steam",
    "~/.steam/steam",
    "~/.steam/root",
    "~/.var/app/com.valvesoftware.Steam/.local/share/Steam",
    "~/snap/steam/common/.local/share/Steam",
)

# Shown in Steam's library but never real games.
_TOOL_NAME_PREFIXES = (
    "proton", "steam linux runtime", "steamworks common redistributables",
    "steamvr", "steam audio",
)


@dataclass
class SteamGame:
    app_id: int
    name: str
    install_dir: Path
    library: Path
    app_type: str = "game"
    appinfo: dict = field(default_factory=dict, repr=False)
    # Steam language key (tchinese, japanese, …) -> localized store name.
    names: dict = field(default_factory=dict)

    @property
    def installed(self) -> bool:
        return self.install_dir.is_dir()


class SteamInstallation:
    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root) if root else self.find_root()
        if self.root is None:
            raise FileNotFoundError("Steam installation not found")

    @staticmethod
    def find_root() -> Optional[Path]:
        for candidate in _STEAM_ROOT_CANDIDATES:
            path = Path(os.path.expanduser(candidate))
            if (path / "steamapps").is_dir():
                return path.resolve()
        return None

    def library_folders(self) -> list[Path]:
        folders = [self.root]
        config = self.root / "steamapps" / "libraryfolders.vdf"
        try:
            data = vdf_text.loads(config.read_text(encoding="utf-8", errors="replace"))
        except (OSError, vdf_text.VdfError):
            data = {}
        root_map = vdf_text.get_ci(data, "libraryfolders") or {}
        for value in root_map.values():
            path = value.get("path") if isinstance(value, dict) else value
            if isinstance(path, str) and path:
                folders.append(Path(path))
        unique: list[Path] = []
        seen = set()
        for folder in folders:
            try:
                key = folder.resolve()
            except OSError:
                key = folder
            if key not in seen and (folder / "steamapps").is_dir():
                seen.add(key)
                unique.append(folder)
        return unique

    def scan_games(self) -> list[SteamGame]:
        manifests: dict[int, SteamGame] = {}
        for library in self.library_folders():
            steamapps = library / "steamapps"
            for manifest in steamapps.glob("appmanifest_*.acf"):
                try:
                    data = vdf_text.loads(manifest.read_text(encoding="utf-8", errors="replace"))
                except (OSError, vdf_text.VdfError):
                    continue
                state = vdf_text.get_ci(data, "AppState") or {}
                try:
                    app_id = int(state.get("appid", ""))
                except ValueError:
                    continue
                installdir = state.get("installdir") or ""
                if not installdir:
                    continue
                manifests[app_id] = SteamGame(
                    app_id=app_id,
                    name=state.get("name") or str(app_id),
                    install_dir=steamapps / "common" / installdir,
                    library=library,
                )

        try:
            infos = read_appinfo(self.root / "appcache" / "appinfo.vdf", manifests)
        except (OSError, AppInfoError):
            infos = {}

        games = []
        for app_id, game in manifests.items():
            info = infos.get(app_id) or {}
            common = info.get("common") or {}
            game.appinfo = info
            game.app_type = str(common.get("type") or "").lower()
            if common.get("name"):
                game.name = str(common["name"])
            localized = common.get("name_localized")
            if isinstance(localized, dict):
                game.names = {str(k): str(v).strip() for k, v in localized.items()
                              if isinstance(v, str) and v.strip()}
            if game.app_type and game.app_type not in ("game", "demo", "mod"):
                continue
            if not game.app_type and game.name.lower().startswith(_TOOL_NAME_PREFIXES):
                continue
            if not game.installed:
                continue
            games.append(game)
        games.sort(key=lambda g: g.name.casefold())
        return games

    def header_image(self, app_id: int) -> Optional[Path]:
        cache = self.root / "appcache" / "librarycache"
        folder = cache / str(app_id)
        for pattern in ("**/library_header*.jpg", "header*.jpg", "**/library_capsule*.jpg"):
            match = next(iter(sorted(folder.glob(pattern))), None) if folder.is_dir() else None
            if match:
                return match
        legacy = cache / f"{app_id}_header.jpg"
        return legacy if legacy.is_file() else None
