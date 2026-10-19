"""HelixSR 2.0 and newer install into games through the release's own installer.

Every HelixSR 2.0 release carries ``setup/helixsr_bridge.py``, the program HelixSR's
own desktop app runs: one command per call, one JSON object as the answer. Scaler
Assistant runs it the same way, as a separate program from the user's HelixSR
folder (HelixSR's setup scripts may be run, never copied), so HelixSR's own setup,
its app and Scaler Assistant install the same files and can update or remove what
the others installed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .helixsr import HelixSRFolder

TIMEOUT = 900   # an install copies a few hundred MB at most; a full game scan is part of each call


# Runs the installer as `python -I script ...` would, except that a file or folder the user may
# not read counts as not there (as os.path.exists does). HelixSR's scan looks into every game's
# folders, and one folder elsewhere without read permission (a mod's, a root-owned one) would
# otherwise stop it with PermissionError before it reaches the game being installed.
_RUNNER = r"""
import pathlib, runpy, sys
def _tolerant(name):
    original = getattr(pathlib.Path, name)
    def method(self, *args, **kwargs):
        try:
            return original(self, *args, **kwargs)
        except PermissionError:
            return False
    method.__name__ = name
    setattr(pathlib.Path, name, method)
for _name in ("exists", "is_file", "is_dir", "is_symlink"):
    _tolerant(_name)
del _tolerant, _name
script = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(script, run_name="__main__")
"""


class BridgeError(RuntimeError):
    def __init__(self, message: str, messages: Optional[list[str]] = None) -> None:
        super().__init__(message)
        self.messages = list(messages or [])


def python() -> str:
    """A Python to run HelixSR's installer with: this one, unless it is a frozen program
    (Decky Loader runs plugins inside its own executable)."""
    exe = sys.executable or ""
    if exe and not getattr(sys, "frozen", False) and "python" in Path(exe).name.lower():
        return exe
    return shutil.which("python3") or shutil.which("python") or "python3"


def run(folder: HelixSRFolder, command: str, *args: str) -> dict:
    """Run one bridge command; its JSON answer, or BridgeError with HelixSR's own message."""
    script = folder.bridge
    if not script.is_file():
        raise BridgeError(f"{script} is missing")
    env = dict(os.environ)
    for name in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(name, None)
    try:
        done = subprocess.run([python(), "-I", "-c", _RUNNER, str(script), str(folder.path),
                               command, *args],
                              capture_output=True, text=True, timeout=TIMEOUT, env=env,
                              cwd=str(folder.path), stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as error:
        raise BridgeError(str(error)) from error
    answer = None
    for line in reversed(done.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                answer = json.loads(line)
                break
            except ValueError:
                continue
    if not isinstance(answer, dict):
        tail = (done.stderr or done.stdout).strip().splitlines()[-3:]
        raise BridgeError(" ".join(tail) or f"exit code {done.returncode}")
    messages = [str(m) for m in answer.get("messages") or []]
    if not answer.get("ok"):
        raise BridgeError(str(answer.get("error") or "failed"), messages)
    answer["messages"] = messages
    return answer


def install(folder: HelixSRFolder, game_dir: str, way: str, name: Optional[str] = None,
            anti_cheat_ok: bool = False, fg: Optional[bool] = None) -> dict:
    """way: 'scaler' (HelixSR Scaler) or 'fsr' (the FSR drop-in). fg: HelixSR's frame
    generation on or off (HelixSR Scaler; None: an update keeps it as it was, new is off)."""
    args = ["--game", game_dir, "--way", way]
    if way == "scaler":
        args += ["--scaler", str(folder.scaler_pkg)]
        version = folder.scaler_version()
        if version:
            args += ["--scaler-version", version]
        if name:
            args += ["--scaler-name", name]
        if anti_cheat_ok:
            args += ["--anticheat-ok", "yes"]
        if fg is not None:
            args += ["--fg", "on" if fg else "off"]
    return run(folder, "install", *args)


def remove(folder: HelixSRFolder, game_dir: str) -> dict:
    return run(folder, "remove", "--game", game_dir)
