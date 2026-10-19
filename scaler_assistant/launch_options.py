"""Steam launch options: add or take out one DLL in WINEDLLOVERRIDES, and nothing else.

Under Proton a DLL next to the game's .exe is only loaded instead of Wine's
own when WINEDLLOVERRIDES says ``name=n,b`` (native first). ``dxgi.dll`` and
``d3d12.dll`` are already native in Proton (DXVK, vkd3d-proton); every other
name OptiScaler can use needs the override.

The user's own launch options are never rewritten or removed:

* Adding only inserts text. An existing WINEDLLOVERRIDES gets ``;name=n,b``
  appended inside its value, as it is written; without one, a new assignment
  is put in front. An entry the user already has for the DLL is left alone.
* Each change is recorded (the options before and after it). Taking it out
  restores the options exactly when they are still as Scaler Assistant left
  them; when the user has edited them since, only the inserted text is taken
  out again and every other character stays.
"""

from __future__ import annotations

import re
from typing import Optional

VAR = "WINEDLLOVERRIDES"
COMMAND = "%command%"
# WINEDLLOVERRIDES=… at the start of the options or after whitespace.
_ASSIGN = re.compile(r'(?:(?<=\s)|^)WINEDLLOVERRIDES=("[^"]*"|\'[^\']*\'|[^\s"\']*)')
NO_OVERRIDE_NEEDED = ("dxgi", "d3d12")


class OverrideConflict(ValueError):
    """The user's WINEDLLOVERRIDES already sets this DLL to something else."""


def base(dll_name: str) -> str:
    return dll_name.lower().removesuffix(".dll")


def needs_override(dll_name: str) -> bool:
    return not dll_name.lower().endswith(".asi") and base(dll_name) not in NO_OVERRIDE_NEEDED


def entry(dll_name: str) -> str:
    return f"{base(dll_name)}=n,b"


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def current_overrides(options: str) -> dict[str, str]:
    """dll base name (lower case) -> mode, from the options' WINEDLLOVERRIDES."""
    match = _ASSIGN.search(options or "")
    if not match:
        return {}
    result: dict[str, str] = {}
    for part in _unquote(match.group(1)).split(";"):
        names, _, mode = part.partition("=")
        for name in names.split(","):
            if name.strip():
                result[name.strip().lower()] = mode.strip().replace(" ", "")
    return result


def native_first(mode: str) -> bool:
    return mode.startswith("n")


def has_override(options: str, dll_name: str) -> bool:
    return native_first(current_overrides(options).get(base(dll_name), ""))


def blocked_names(options: str) -> set[str]:
    """DLLs the user's WINEDLLOVERRIDES keeps from loading natively (OptiScaler can't use them)."""
    return {f"{name}.dll" for name, mode in current_overrides(options).items()
            if not native_first(mode)}


def add(options: str, dll_name: str) -> tuple[str, Optional[dict]]:
    """(new options, record of the change) — record is None when nothing had to change."""
    options = options or ""
    dll = base(dll_name)
    existing = current_overrides(options)
    if dll in existing:
        if native_first(existing[dll]):
            return options, None
        raise OverrideConflict(dll)
    token = entry(dll_name)
    match = _ASSIGN.search(options)
    if match:
        value = match.group(1)
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
        inner = value[1:-1] if quoted else value
        inserted = (";" if inner and not inner.endswith(";") else "") + token
        end = match.end() - (1 if quoted else 0)
        after = options[:end] + inserted + options[end:]
        return after, {"dll": dll, "kind": "entry", "text": inserted,
                       "before": options, "after": after}
    assignment = f'{VAR}="{token}"'
    stripped = options.strip()
    if not stripped:
        after = f"{assignment} {COMMAND}"
    elif COMMAND in options:
        after = f"{assignment} {options}"
    else:
        # Plain arguments (e.g. "-dx12") only reach the game through %command%.
        after = f"{assignment} {COMMAND} {options}"
    return after, {"dll": dll, "kind": "assignment", "text": assignment,
                   "before": options, "after": after}


def remove(options: str, record: Optional[dict]) -> str:
    """Take out what ``add`` inserted; every other character the user has stays."""
    options = options or ""
    if not record:
        return options
    if options == record.get("after"):
        return record.get("before", "")
    dll = str(record.get("dll") or "")
    text = str(record.get("text") or "")
    if record.get("kind") == "entry":
        if text and text in options:
            return options.replace(text, "", 1)
        return _drop_entry(options, dll)
    match = _ASSIGN.search(options)
    if not match:
        return options
    if _unquote(match.group(1)) == entry(dll):
        # Our whole assignment, plus the space we put after it.
        end = match.end() + (1 if options[match.end():match.end() + 1] == " " else 0)
        result = options[:match.start()] + options[end:]
        before = record.get("before", "")
        if result.strip() == COMMAND and not before.strip():
            return before
        if result.startswith(f"{COMMAND} ") and result[len(COMMAND) + 1:] == before:
            return before
        return result
    return _drop_entry(options, dll)


def _drop_entry(options: str, dll: str) -> str:
    """Remove ``dll=n,b`` (only that exact entry) from the WINEDLLOVERRIDES value."""
    match = _ASSIGN.search(options)
    if not match:
        return options
    value = match.group(1)
    target = f"{dll}=n,b"
    for pattern in (";" + target, target + ";", target):
        index = value.find(pattern)
        if index >= 0:
            new_value = value[:index] + value[index + len(pattern):]
            return options[:match.start(1)] + new_value + options[match.end(1):]
    return options
