"""HelixSR's settings file (helixsr.ini), next to HelixSR's DLL in each game.

Only the settings HelixSR's README documents are offered. Editing keeps every
other line (comments, sections and settings this tool does not know) exactly
as it was. A setting left at "default" has no line at all, so HelixSR uses its
own default for it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

INI = "helixsr.ini"
HEADER = "; HelixSR settings (edited with HelixSR Assistant). HelixSR reads this file next to its DLL."


@dataclass(frozen=True)
class Setting:
    section: str
    key: str
    choices: tuple[str, ...] = ()        # empty: a number from 0.0 to 1.0
    min_version: tuple[int, ...] = ()


SETTINGS: tuple[Setting, ...] = (
    Setting("Sharpening", "Sharpener", ("off", "nvidia", "rcas")),
    Setting("Sharpening", "Sharpness"),
    Setting("Sharpening", "UseGameSlider", ("true", "false")),
    Setting("Upscaling", "Int8", ("auto", "on", "off"), (1, 9, 0)),
    Setting("Upscaling", "UpscaleFilter", ("lanczos", "easu"), (1, 9, 0)),
    Setting("Compatibility", "WaveSize", ("64", "32")),
)
BY_KEY = {s.key.lower(): s for s in SETTINGS}

_SECTION = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_ENTRY = re.compile(r"^(\s*)([A-Za-z0-9_]+)(\s*)=(\s*)(.*?)(\s*)$")


def _lines(path: Path) -> tuple[list[str], str]:
    try:
        with open(path, encoding="utf-8", errors="surrogateescape", newline="") as handle:
            text = handle.read()
    except FileNotFoundError:
        return [], "\r\n"
    newline = "\r\n" if "\r\n" in text or not text else "\n"
    return text.splitlines(), newline


def _entries(lines: list[str]):
    """(line index, section, key, value) for every active ``key = value`` line."""
    section = ""
    for index, line in enumerate(lines):
        match = _SECTION.match(line)
        if match:
            section = match.group(1).strip()
            continue
        if line.lstrip().startswith((";", "#")):
            continue
        entry = _ENTRY.match(line)
        if entry:
            yield index, section, entry.group(2), entry.group(5)


def read(path: Path) -> dict[str, str]:
    """The known settings that are set in the file: {key: value}."""
    values: dict[str, str] = {}
    lines, _ = _lines(path)
    for _, section, key, value in _entries(lines):
        setting = BY_KEY.get(key.lower())
        if setting and setting.section.lower() == section.lower() and value:
            values[setting.key] = value
    return values


def normalize(setting: Setting, value: Optional[str]) -> Optional[str]:
    """A valid value for the setting, or None (use HelixSR's default)."""
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    if setting.choices:
        lowered = text.lower()
        return lowered if lowered in setting.choices else None
    try:
        number = min(1.0, max(0.0, float(text)))
    except ValueError:
        return None
    return f"{number:.2f}"


def write(path: Path, values: dict[str, Optional[str]]) -> None:
    """Set the given settings (None = back to HelixSR's default); other lines stay."""
    lines, newline = _lines(path)
    if not lines:
        lines = [HEADER]
    for key, raw in values.items():
        setting = BY_KEY.get(key.lower())
        if setting is None:
            continue
        value = normalize(setting, raw)
        hits = [i for i, section, k, _ in _entries(lines)
                if k.lower() == setting.key.lower() and section.lower() == setting.section.lower()]
        for index in reversed(hits[1:]):   # a duplicate line would be ambiguous
            del lines[index]
        if hits:
            if value is None:
                del lines[hits[0]]
            else:
                lines[hits[0]] = f"{setting.key} = {value}"
            continue
        if value is None:
            continue
        header = next((i for i, line in enumerate(lines)
                       if (m := _SECTION.match(line)) and m.group(1).strip().lower()
                       == setting.section.lower()), None)
        if header is None:
            if lines and lines[-1].strip():
                lines.append("")
            lines += [f"[{setting.section}]", f"{setting.key} = {value}"]
        else:
            lines.insert(header + 1, f"{setting.key} = {value}")
    if lines and lines[0] == HEADER and not any(True for _ in _entries(lines)):
        # A file of ours that sets nothing: no file means HelixSR's defaults.
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        handle.write(newline.join(lines) + newline)


def is_empty(path: Path) -> bool:
    """True for a file this tool made that no longer sets anything."""
    lines, _ = _lines(path)
    if not lines or lines[0] != HEADER:
        return False
    return not any(True for _ in _entries(lines))
