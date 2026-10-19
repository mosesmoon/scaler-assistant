"""OptiScaler: which file name it gets in a game, and the OptiScaler.ini values for an upscaler.

OptiScaler is loaded by the game as one of a few system DLL names. Which one
works depends on the game:

* ``dxgi.dll`` is the default and, under Proton, needs no launch option.
* A pure Vulkan game may never load dxgi.dll: ``winmm.dll`` is used there.
* When the game (or another mod such as ReShade) already has a dxgi.dll next
  to its .exe, the next free name is used, so the other file stays untouched.
* Some games need a particular name; the list below follows the per-game notes
  in OptiScaler's compatibility list (github.com/optiscaler/OptiScaler/wiki).

Names other than dxgi.dll / d3d12.dll need ``WINEDLLOVERRIDES=<name>=n,b`` in
the game's Steam launch options (see ``launch_options``).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Iterable, Optional

from .helixsr import is_optiscaler

NAMES = ("dxgi.dll", "winmm.dll", "version.dll", "dbghelp.dll", "d3d12.dll",
         "wininet.dll", "winhttp.dll")
FALLBACKS = ("winmm.dll", "version.dll", "dbghelp.dll", "winhttp.dll", "wininet.dll")
INI = "OptiScaler.ini"
LOG = "OptiScaler.log"

# Game name (as Steam shows it) -> the name OptiScaler's compatibility list asks for.
# Only Steam releases, and only notes that name a file; online games are left out.
GAME_NAMES: dict[str, str] = {
    "A Quiet Place: The Road Ahead": "winmm.dll",
    "DEAD OR ALIVE 6": "d3d12.dll",
    "DEAD OR ALIVE 6 Last Round": "d3d12.dll",
    "Dragon Age: The Veilguard": "winmm.dll",
    "Forspoken": "d3d12.dll",
    "Grand Theft Auto: San Andreas – The Definitive Edition": "d3d12.dll",
    "Grand Theft Auto: Vice City – The Definitive Edition": "d3d12.dll",
    "Grand Theft Auto III – The Definitive Edition": "d3d12.dll",
    "Immortals of Aveum": "d3d12.dll",
    "INDIKA": "d3d12.dll",
    "Marvel's Midnight Suns": "d3d12.dll",
    "Need for Speed Unbound": "d3d12.dll",
    "Redfall": "winmm.dll",
    "The Casting of Frank Stone": "winmm.dll",
    "WILD HEARTS": "winmm.dll",
}


def _key(name: str) -> str:
    text = re.sub("[\u2122\u00ae\u00a9]", "", name)   # ™ ® ©
    text = unicodedata.normalize("NFKD", text).casefold()
    text = text.replace("&", "and")
    text = re.sub(r"\b(the|definitive edition|edition)\b", " ", text)
    return re.sub(r"[^0-9a-z]+", "", text)


_GAME_KEYS = {_key(name): dll for name, dll in GAME_NAMES.items()}


def listed_name(game_names: Iterable[str]) -> Optional[str]:
    for name in game_names:
        dll = _GAME_KEYS.get(_key(name))
        if dll:
            return dll
    return None


def installed_name(exe_dir: Path) -> Optional[str]:
    """The name an OptiScaler next to the .exe already uses (any installer's)."""
    for name in NAMES:
        if (exe_dir / name).is_file() and is_optiscaler(exe_dir / name):
            return name
    return None


def choose_name(exe_dir: Path, api: str, game_names: Iterable[str],
                chosen: Optional[str] = None, blocked: Iterable[str] = ()) -> tuple[str, str]:
    """(file name, reason) for OptiScaler in this game.

    ``blocked``: names the user's WINEDLLOVERRIDES keeps from loading natively; those
    are never picked automatically, so the user's own launch options never need changing.

    reason: 'user' (picked by hand), 'installed' (an OptiScaler is already there),
    'listed' (compatibility list), 'vulkan', 'taken' (dxgi.dll belongs to the game or
    another mod, or the launch options block it) or 'default'.
    """
    blocked = {b.lower() for b in blocked}
    if chosen in NAMES:
        return chosen, "user"
    present = installed_name(exe_dir)
    if present and present.lower() not in blocked:
        return present, "installed"
    listed = listed_name(game_names)
    if listed and _free(exe_dir, listed, blocked):
        return listed, "listed"
    if api == "vulkan":
        return _first_free(exe_dir, FALLBACKS, blocked), "vulkan"
    if not _free(exe_dir, "dxgi.dll", blocked):
        return _first_free(exe_dir, FALLBACKS, blocked), "taken"
    return "dxgi.dll", "default"


def _foreign(path: Path) -> bool:
    return (path.exists() or path.is_symlink()) and not is_optiscaler(path)


def _free(exe_dir: Path, name: str, blocked: set[str]) -> bool:
    return name.lower() not in blocked and not _foreign(exe_dir / name)


def _first_free(exe_dir: Path, names: Iterable[str], blocked: set[str] = frozenset()) -> str:
    names = list(names)
    return next((n for n in names if _free(exe_dir, n, blocked)), names[0])


# ---- OptiScaler.ini --------------------------------------------------------------------

class IniError(ValueError):
    pass


_HEADER = re.compile(r"^\s*\[([^\]]*)\]\s*$")


def _section(lines: list[str], section: str) -> Optional[tuple[int, int]]:
    """(header line, end) of the first [section] (OptiScaler repeats some key names per section)."""
    start = None
    for i, line in enumerate(lines):
        match = _HEADER.match(line)
        if not match:
            continue
        if start is not None:
            return start, i
        if match.group(1).strip().lower() == section.lower():
            start = i
    return (start, len(lines)) if start is not None else None


def set_value(text: str, section: str, key: str, value: str) -> str:
    """Set ``key=value`` in [section] of an OptiScaler.ini, keeping every other line as it is."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    found = _section(lines, section)
    if found is None:
        if lines and not lines[-1].endswith(("\n", "\r")):
            lines[-1] += newline
        lines.append(f"[{section}]{newline}{key}={value}{newline}")
        return "".join(lines)
    start, end = found
    pattern = re.compile(r"^\s*%s\s*=" % re.escape(key))
    hits = [i for i in range(start + 1, end) if pattern.match(lines[i])]
    if len(hits) > 1:
        raise IniError(key)
    if hits:
        line = lines[hits[0]]
        ending = line[len(line.rstrip("\r\n")):] or newline
        lines[hits[0]] = f"{key}={value}{ending}"
        return "".join(lines)
    last = start   # after the section's last non-empty line
    for i in range(start + 1, end):
        if lines[i].strip():
            last = i
    if not lines[last].endswith(("\n", "\r")):
        lines[last] += newline
    lines.insert(last + 1, f"{key}={value}{newline}")
    return "".join(lines)


def get_value(text: str, key: str) -> Optional[str]:
    match = re.search(r"(?m)^\s*%s\s*=\s*([^\r\n;]*)" % re.escape(key), text)
    return match.group(1).strip() if match else None


def _options(text: str, key: str) -> str:
    """The comment lines right above ``key=`` (where OptiScaler lists the allowed values)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^\s*%s\s*=" % re.escape(key), line):
            comments = []
            j = i - 1
            while j >= 0 and lines[j].lstrip().startswith(";"):
                comments.append(lines[j])
                j -= 1
            return " ".join(reversed(comments))
    return ""


def _pick(text: str, key: str, wanted: tuple[str, ...]) -> str:
    """The first value of ``wanted`` that this OptiScaler version lists for ``key``."""
    listed = set(re.findall(r"[a-z0-9_]+", _options(text, key).lower()))
    for value in wanted:
        if value in listed:
            return value
    return wanted[0]


def win_path(path: Path) -> str:
    """A path as OptiScaler (running under Proton) reads it: the Linux root is Z:."""
    return "Z:" + str(Path(path).resolve()).replace("/", "\\")


def configure(text: str, upscaler: str, files: dict[str, Path], force_int8: bool) -> str:
    """OptiScaler.ini values for 'fsr4' or 'fsr3' with the given FFX DLLs.

    All three APIs are set, so a wrongly guessed API still gets the right upscaler.
    FSR 4 in DX11 and Vulkan games runs through OptiScaler's DX12 path; FSR 3 there
    uses OptiScaler's native DX11 / Vulkan FSR 3.1.
    """
    fsr4 = upscaler == "fsr4"
    text = set_value(text, "Upscalers", "Dx12Upscaler", _pick(text, "Dx12Upscaler", ("fsr31", "ffx")))
    if fsr4:
        dx11 = _pick(text, "Dx11Upscaler", ("fsr31_12", "ffx_12"))
        vulkan = _pick(text, "VulkanUpscaler", ("fsr31_12", "ffx_12"))
    else:
        dx11 = _pick(text, "Dx11Upscaler", ("fsr31", "ffx"))
        vulkan = _pick(text, "VulkanUpscaler", ("fsr31", "ffx"))
    text = set_value(text, "Upscalers", "Dx11Upscaler", dx11)
    text = set_value(text, "Upscalers", "VulkanUpscaler", vulkan)
    text = set_value(text, "FSR", "UpscalerIndex", "0" if fsr4 else "1")
    text = set_value(text, "FSR", "Fsr4Update", "true" if fsr4 else "false")
    text = set_value(text, "FSR", "Fsr4ForceEnableInt8", "true" if fsr4 and force_int8 else "auto")
    keys = {"loader": "FfxDx12Path", "upscaler": "FfxDx12SRPath",
            "framegeneration": "FfxDx12FGPath", "vulkan": "FfxVkPath"}
    for role, key in keys.items():
        if role in files:
            text = set_value(text, "Libraries", key, win_path(files[role]))
    return text
