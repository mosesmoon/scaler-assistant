"""Read the DLLs a Windows executable imports (normal and delay-loaded imports).

Only the headers and the import tables are read, so even a large game .exe is
handled quickly. Used to tell which graphics API a game renders with.
"""

from __future__ import annotations

import struct
from pathlib import Path

_IMPORT_DIR = 1
_DELAY_IMPORT_DIR = 13
_MAX_DESCRIPTORS = 4096


class PEError(ValueError):
    pass


def _read_cstring(data: bytes, offset: int, limit: int = 260) -> str:
    end = data.find(b"\x00", offset, offset + limit)
    if end < 0:
        raise PEError("unterminated name")
    return data[offset:end].decode("ascii", errors="replace")


def imported_dlls(path: Path | str) -> list[str]:
    """Lower-case names of the DLLs the executable imports, in table order."""
    with open(path, "rb") as handle:
        data = handle.read(64)
        if data[:2] != b"MZ":
            raise PEError("not an MZ executable")
        (pe_offset,) = struct.unpack_from("<I", data, 0x3C)
        handle.seek(pe_offset)
        header = handle.read(24)
        if header[:4] != b"PE\x00\x00":
            raise PEError("no PE signature")
        sections, _, _, _, optional_size, _ = struct.unpack_from("<HIIIHH", header, 6)
        optional = handle.read(optional_size)
        magic = struct.unpack_from("<H", optional, 0)[0]
        if magic == 0x20B:      # PE32+
            dirs_at, count_at = 112, 108
        elif magic == 0x10B:    # PE32
            dirs_at, count_at = 96, 92
        else:
            raise PEError("unknown optional header")
        (dir_count,) = struct.unpack_from("<I", optional, count_at)
        directories = [struct.unpack_from("<II", optional, dirs_at + 8 * i)
                       for i in range(min(dir_count, 16))]
        table = handle.read(40 * sections)
        layout = [struct.unpack_from("<IIII", table, 40 * i + 8) for i in range(sections)]

        def to_offset(rva: int) -> int:
            for virtual_size, virtual_address, raw_size, raw_pointer in layout:
                if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
                    return raw_pointer + rva - virtual_address
            raise PEError(f"RVA {rva:#x} outside the sections")

        def read_at(rva: int, size: int) -> bytes:
            handle.seek(to_offset(rva))
            return handle.read(size)

        names: list[str] = []
        for index, size, name_field in ((_IMPORT_DIR, 20, 12), (_DELAY_IMPORT_DIR, 32, 4)):
            if index >= len(directories):
                continue
            rva, length = directories[index]
            if not rva or not length:
                continue
            try:
                blob = read_at(rva, min(length, size * _MAX_DESCRIPTORS))
            except PEError:
                continue
            for start in range(0, len(blob) - size + 1, size):
                entry = blob[start:start + size]
                if not any(entry):
                    break
                (name_rva,) = struct.unpack_from("<I", entry, name_field)
                try:
                    name = _read_cstring(read_at(name_rva, 260), 0).lower()
                except (PEError, OSError):
                    continue
                if name and name not in names:
                    names.append(name)
        return names


def graphics_api(paths) -> str:
    """'dx12', 'dx11', 'vulkan' or '' (unknown) from the executables' imports.

    A game that can render with D3D12 counts as DX12 even when it also links
    D3D11 or Vulkan: OptiScaler and HelixSR both prefer that path.
    """
    imports: set[str] = set()
    for path in paths:
        try:
            imports.update(imported_dlls(path))
        except (OSError, PEError, struct.error):
            continue
    if "d3d12.dll" in imports:
        return "dx12"
    if "d3d11.dll" in imports:
        return "dx11"
    if "vulkan-1.dll" in imports:
        return "vulkan"
    return ""
