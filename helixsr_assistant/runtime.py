"""Detect what HelixSR is *actually* doing inside running Steam games.

* ``/proc/<pid>/environ``: ``SteamAppId`` & co. tie a process to a Steam app.
* ``/proc/<pid>/maps``: Proton (Wine) maps Windows DLLs from their files, so a
  game that has loaded HelixSR (or OptiScaler, or HelixSR's DLSS loader) shows
  the DLL's path there. The DLL is only loaded once the game uses the upscaler,
  so "installed but not loaded" usually means the game has not been switched to
  AMD FSR (or DLSS) in its graphics settings yet.
* ``helixsr.log``: written by HelixSR when it starts in the game; only counted
  when it is newer than the game's processes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import hxlog

_APP_ID_ENV_KEYS = ("SteamAppId", "SteamGameId", "STEAM_COMPAT_APP_ID")


@dataclass
class Watch:
    """The files to look for in one game's processes."""
    helixsr: list[str] = field(default_factory=list)   # HelixSR's DLL(s) in the game
    helpers: list[str] = field(default_factory=list)   # OptiScaler / DLSS loader
    logs: list[str] = field(default_factory=list)


@dataclass
class RunningGame:
    app_id: int
    pids: list[int] = field(default_factory=list)
    started: float = 0.0               # epoch seconds of the oldest process
    helixsr_loaded: bool = False
    helper_loaded: bool = False
    log: Optional[hxlog.LogSummary] = None


def _read_environ(pid_dir: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in (pid_dir / "environ").read_bytes().split(b"\0"):
        key, sep, value = item.partition(b"=")
        if sep:
            values[key.decode(errors="ignore")] = value.decode(errors="ignore")
    return values


def _boot_time(proc: Path) -> float:
    try:
        for line in (proc / "stat").read_text().splitlines():
            if line.startswith("btime "):
                return float(line.split()[1])
    except (OSError, ValueError):
        pass
    return 0.0


def _start_time(pid_dir: Path, boot: float) -> float:
    try:
        stat = (pid_dir / "stat").read_text()
        ticks = int(stat.rsplit(")", 1)[-1].split()[19])   # field 22: starttime
    except (OSError, IndexError, ValueError):
        return 0.0
    return boot + ticks / os.sysconf("SC_CLK_TCK")


def _suffixes(paths: list[str]) -> list[bytes]:
    """Match on the end of the path (from steamapps/common on), lower case: the
    game may see its library under another prefix inside Steam's runtime container."""
    out = []
    for path in paths:
        text = path.replace("\\", "/")
        marker = text.lower().find("/steamapps/common/")
        tail = text[marker:] if marker >= 0 else text
        out.append(tail.lower().encode())
    return out


def _maps_has(pid_dir: Path, needles: list[bytes]) -> bool:
    if not needles:
        return False
    try:
        with (pid_dir / "maps").open("rb") as handle:
            for line in handle:
                lowered = line.rstrip().lower()
                if any(lowered.endswith(needle) for needle in needles):
                    return True
    except OSError:
        pass
    return False


def running_app_ids(proc: Path = Path("/proc")) -> dict[int, list[int]]:
    """Steam app id -> pids of the user's processes that belong to it."""
    uid = os.getuid()
    found: dict[int, list[int]] = {}
    try:
        entries = list(proc.iterdir())
    except OSError:
        return {}
    for pid_dir in entries:
        if not pid_dir.name.isdigit():
            continue
        try:
            if pid_dir.stat().st_uid != uid:
                continue
            env = _read_environ(pid_dir)
        except OSError:
            continue
        app_id = next((env[k].strip() for k in _APP_ID_ENV_KEYS
                       if env.get(k, "").strip().isdigit() and env[k].strip() != "0"), None)
        if app_id is not None:
            found.setdefault(int(app_id), []).append(int(pid_dir.name))
    return found


def detect_running(watch: dict[int, Watch], proc: Path = Path("/proc")) -> dict[int, RunningGame]:
    boot = _boot_time(proc)
    games: dict[int, RunningGame] = {}
    for app_id, pids in running_app_ids(proc).items():
        game = RunningGame(app_id, sorted(pids))
        starts = [t for t in (_start_time(proc / str(pid), boot) for pid in pids) if t]
        game.started = min(starts) if starts else 0.0
        files = watch.get(app_id)
        if files:
            helixsr, helpers = _suffixes(files.helixsr), _suffixes(files.helpers)
            for pid in pids:
                pid_dir = proc / str(pid)
                game.helixsr_loaded = game.helixsr_loaded or _maps_has(pid_dir, helixsr)
                game.helper_loaded = game.helper_loaded or _maps_has(pid_dir, helpers)
                if game.helixsr_loaded and (game.helper_loaded or not helpers):
                    break
            log = hxlog.newest(Path(p) for p in files.logs)
            if log and (not game.started or log.mtime >= game.started - 2):
                game.log = log
        games[app_id] = game
    return games
