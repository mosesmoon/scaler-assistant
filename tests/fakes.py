"""Fake Steam libraries, games and HelixSR folders for the tests.

Nothing here contains HelixSR, NVIDIA, OptiScaler or AMD code: every "DLL" is
a few bytes carrying the markers the tool looks for.
"""

from __future__ import annotations

import hashlib
import os
import struct
from pathlib import Path

OPTI_INI = (
    "[Upscalers]\r\n"
    "; Upscaler for DirectX 12\r\n"
    "Dx12Upscaler=auto\r\n"
    "\r\n"
    "[Libraries]\r\n"
    "FfxDx12Path=auto\r\n"
    "FfxDx12SRPath=auto\r\n"
    "FfxDx12FGPath=auto\r\n"
)


def helixsr_dll(version: str, built: bool = True, extra: bytes = b"") -> bytes:
    body = b"MZ" + b"\x00" * 64 + f"\x00HelixSR {version}\x00".encode() + b"\x00" * 64 + extra
    if built:
        weights, pack = b"w" * 60, b"p" * 40
        body += weights + pack + b"HXSRNET1" + struct.pack("<QQQ", len(weights), len(pack), 1)
    return body


def make_helixsr(folder: Path, version: str = "1.9.0", built: bool = True) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "helixsr-setup.sh").write_text("#!/bin/sh\n")
    (folder / "amd_fidelityfx_dx12.dll").write_bytes(helixsr_dll(version, built))
    (folder / "optiscaler").mkdir(exist_ok=True)
    (folder / "optiscaler" / "OptiScaler.dll").write_bytes(b"MZ OptiScaler 0.9.4")
    with open(folder / "optiscaler" / "OptiScaler.ini", "w", newline="") as handle:
        handle.write(OPTI_INI)
    (folder / "optiscaler" / "fakenvapi.dll").write_bytes(b"MZ fakenvapi")
    (folder / "optiscaler" / "fakenvapi.ini").write_text("[fakenvapi]\n")
    (folder / "amd-fsr").mkdir(exist_ok=True)
    (folder / "amd-fsr" / "amd_fidelityfx_upscaler_dx12.dll").write_bytes(b"MZ ffxCreateContext AMD")
    (folder / "amd-fsr" / "amd_fidelityfx_framegeneration_dx12.dll").write_bytes(b"MZ AMD FG")
    (folder / "dlss-loader").mkdir(exist_ok=True)
    (folder / "dlss-loader" / "dxgi.dll").write_bytes(b"MZ HelixSR DLSS loader")
    return folder


def make_steam(root: Path) -> Path:
    """A Steam root with three games:

    100 FsrGame:   Unreal layout, FSR 3.1 (both DLLs), DLSS -> ways f, o, d
    200 DlssGame:  DLSS only, ships its own dxgi.dll, Easy Anti-Cheat -> ways o, d
    300 PlainGame: no upscaler
    """
    steam = root / "Steam"
    common = steam / "steamapps" / "common"
    win64 = common / "FsrGame" / "Game" / "Binaries" / "Win64"
    win64.mkdir(parents=True)
    (win64 / "Game-Win64-Shipping.exe").write_bytes(b"MZ" * 1000)
    (win64 / "amd_fidelityfx_upscaler_dx12.dll").write_bytes(b"MZ ffxCreateContext game FSR")
    (win64 / "amd_fidelityfx_dx12.dll").write_bytes(b"MZ ffxCreateContext game loader")
    (common / "FsrGame" / "FsrGame.exe").write_bytes(b"MZ")
    plugin = common / "FsrGame" / "Engine" / "Plugins" / "DLSS" / "Binaries"
    plugin.mkdir(parents=True)
    (plugin / "nvngx_dlss.dll").write_bytes(b"MZ NVIDIA DLSS")

    dlss = common / "DlssGame"
    (dlss / "bin").mkdir(parents=True)
    (dlss / "bin" / "game.exe").write_bytes(b"MZ" * 1000)
    (dlss / "bin" / "nvngx_dlss.dll").write_bytes(b"MZ NVIDIA DLSS")
    (dlss / "bin" / "dxgi.dll").write_bytes(b"MZ the game's own dxgi")
    (dlss / "EasyAntiCheat").mkdir()

    plain = common / "PlainGame"
    plain.mkdir()
    (plain / "plain.exe").write_bytes(b"MZ")

    apps = steam / "steamapps"
    for app_id, name in ((100, "FsrGame"), (200, "DlssGame"), (300, "PlainGame")):
        (apps / f"appmanifest_{app_id}.acf").write_text(
            f'"AppState"\n{{\n"appid" "{app_id}"\n"name" "{name}"\n"installdir" "{name}"\n}}\n')
    return steam


def snapshot(folder: Path) -> dict[str, str]:
    """relative path -> sha256 of every file (to prove everything was put back)."""
    result = {}
    for directory, _, files in os.walk(folder):
        for name in files:
            path = Path(directory) / name
            result[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result
