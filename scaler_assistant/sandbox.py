"""Running inside Flatpak: what the sandbox hides and how to reach the host.

The sandbox has its own process namespace, so Steam's and the games' processes are
not in its /proc. Inside Flatpak a small snapshot of the host's /proc (only what
``runtime`` and ``steam`` read: Steam's and the games' processes) is made through
``flatpak-spawn --host`` into the app's runtime folder, which host and sandbox see
at the same path. Programs that belong to the host (Steam, a terminal) are started
there too. Outside Flatpak everything is used directly.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

_SNAPSHOT_SECONDS = 2.0
_last: tuple[float, Optional[Path]] = (0.0, None)

# Copies /proc/stat and, for Steam and every process with a Steam app id, its comm,
# environ, stat, maps and exe link. Runs on the host with the user's own rights.
_SNAPSHOT = r'''
dest="$1"; tmp="$dest.new"
rm -rf "$tmp"; mkdir -p "$tmp" || exit 1
cp /proc/stat "$tmp/stat" 2>/dev/null
for d in /proc/[0-9]*; do
  p="${d#/proc/}"
  comm=$(cat "$d/comm" 2>/dev/null) || continue
  if [ "$comm" = steam ] || grep -qa 'SteamAppId=\|SteamGameId=\|STEAM_COMPAT_APP_ID=' "$d/environ" 2>/dev/null; then
    mkdir -p "$tmp/$p"
    printf '%s\n' "$comm" > "$tmp/$p/comm"
    cp "$d/environ" "$d/stat" "$tmp/$p/" 2>/dev/null
    cat "$d/maps" > "$tmp/$p/maps" 2>/dev/null
    exe=$(readlink "$d/exe" 2>/dev/null) && ln -s "$exe" "$tmp/$p/exe"
  fi
done
rm -rf "$dest"; mv "$tmp" "$dest"
'''


def in_flatpak() -> bool:
    return Path("/.flatpak-info").is_file() and bool(shutil.which("flatpak-spawn"))


def host(command: list[str]) -> list[str]:
    """The command line that runs ``command`` on the host (unchanged outside Flatpak)."""
    return ["flatpak-spawn", "--host", *command] if in_flatpak() else list(command)


def host_which(name: str) -> Optional[str]:
    if not in_flatpak():
        return shutil.which(name)
    try:
        done = subprocess.run(host(["sh", "-c", f'command -v "{name}"']), capture_output=True,
                              text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    found = done.stdout.strip()
    return found if done.returncode == 0 and found else None


def _snapshot_dir() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    app = os.environ.get("FLATPAK_ID") or "scaler-assistant"
    return Path(runtime) / "app" / app / "proc"


def proc_root() -> Path:
    """Where the host's processes can be read: /proc, or a fresh snapshot inside Flatpak."""
    global _last
    if not in_flatpak():
        return Path("/proc")
    stamp, path = _last
    if path is not None and time.monotonic() - stamp < _SNAPSHOT_SECONDS:
        return path
    dest = _snapshot_dir()
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(host(["sh", "-c", _SNAPSHOT, "snapshot", str(dest)]),
                       capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        pass
    if not dest.is_dir():
        return Path("/proc")
    _last = (time.monotonic(), dest)
    return dest
