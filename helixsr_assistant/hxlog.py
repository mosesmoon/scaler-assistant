"""Read HelixSR's helixsr.log: what HelixSR reported the last time a game ran.

HelixSR writes helixsr.log next to its DLL (the game's HelixSR folder, next to
the game's FSR DLL, or next to the .exe for the DLSS way). Its README points at
two things: the ``wave size:`` line (which lane count the network kernels run
with) and the reason when the network is not running. Lines are matched
loosely so a later HelixSR version with different wording still shows up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

_VERSION = re.compile(r"HelixSR (\d+\.\d+\.\d+)")
_WAVE = re.compile(r"wave\s*size\s*:", re.I)
_WAVE32 = re.compile(r"network kernels\s+wave\s*32", re.I)
_WAVE64 = re.compile(r"network kernels\s+wave\s*64", re.I)
_PROBLEM = re.compile(r"\berror\b|\bfailed\b|not running|red frame|red border", re.I)
_TAIL_BYTES = 256 * 1024
_MAX_PROBLEMS = 4


@dataclass
class LogSummary:
    path: Path
    mtime: float
    version: Optional[str] = None
    wave_line: str = ""
    wave: Optional[int] = None      # lanes of the network kernels: 32 or 64
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def read_text(path: Path) -> str:
    try:
        with open(path, "rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - _TAIL_BYTES))
            data = handle.read()
    except OSError:
        return ""
    return data.decode("utf-8", errors="replace")


def summarize(path: Path) -> Optional[LogSummary]:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    summary = LogSummary(path, mtime)
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line:
            continue
        if summary.version is None:
            match = _VERSION.search(line)
            if match:
                summary.version = match.group(1)
        if _WAVE.search(line):
            summary.wave_line = line
            summary.wave = 32 if _WAVE32.search(line) else 64 if _WAVE64.search(line) else None
        if _PROBLEM.search(line) and line not in summary.problems:
            summary.problems.append(line)
    summary.problems = summary.problems[-_MAX_PROBLEMS:]
    return summary


def newest(paths: Iterable[Path]) -> Optional[LogSummary]:
    best = None
    for path in paths:
        summary = summarize(path)
        if summary and (best is None or summary.mtime > best.mtime):
            best = summary
    return best
