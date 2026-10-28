"""Fake Steam libraries, games and HelixSR folders for the tests.

Nothing here contains HelixSR, NVIDIA, OptiScaler or AMD code: every "DLL" is
a few bytes carrying the markers the tool looks for.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path

from scaler_assistant import components

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


# The comment lines OptiScaler 0.9.4 writes above the keys Scaler Assistant sets.
OPTI_INI_FULL = (
    "[Upscalers]\r\n"
    "; fsr22 (native DX11), fsr31 (native DX11), xess_12 (dx11on12), fsr31_12 (dx11on12, FSR4), dlss\r\n"
    "Dx11Upscaler=auto\r\n"
    "; xess, fsr21, fsr22, fsr31 (also for FSR4), dlss - Default (auto) is xess\r\n"
    "Dx12Upscaler=auto\r\n"
    "; fsr21 (native VK), fsr31 (native VK), fsr31_12 (VKon12, FSR4), dlss\r\n"
    "VulkanUpscaler=auto\r\n"
    "\r\n[FSR]\r\nUpscalerIndex=auto\r\nFsr4Update=auto\r\nFsr4ForceEnableInt8=auto\r\n"
    "\r\n[Libraries]\r\nFfxDx12Path=auto\r\nFfxDx12SRPath=auto\r\nFfxDx12FGPath=auto\r\n"
    "FfxVkPath=auto\r\n\r\n[Menu]\r\nScale=auto\r\n"
)


def make_components(root: Path) -> Path:
    """Downloaded OptiScaler and FSR 4.1 packs as Scaler Assistant keeps them (fake bytes)."""
    for component in components.ALL:
        base = components.folder(component, root)
        files = {}
        for member in component.members:
            path = base / member
            path.parent.mkdir(parents=True, exist_ok=True)
            if member == "OptiScaler.ini":
                with open(path, "w", newline="") as handle:
                    handle.write(OPTI_INI_FULL)
            elif member == "OptiScaler.dll":
                path.write_bytes(b"MZ OptiScaler 0.9.4")
            elif member.endswith(".txt") or member.endswith(".md") or member.endswith(".ini"):
                path.write_text(f"{component.key} {member}\n")
            else:
                path.write_bytes(f"MZ ffxCreateContext {component.key} {member}".encode())
            files[member] = components.sha256_file(path)
        (base / components.MANIFEST).write_text(json.dumps({"files": files}))
    return root


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
    write_launch_options(steam, {200: "-dx12 %command% -skipintro"})
    return steam


def write_launch_options(steam: Path, options: dict[int, str]) -> Path:
    """localconfig.vdf of one Steam user with these launch options."""
    config = steam / "userdata" / "12345" / "config"
    config.mkdir(parents=True, exist_ok=True)

    def quoted(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    apps = "".join(f'\t\t\t\t\t"{app_id}"\n\t\t\t\t\t{{\n'
                   f'\t\t\t\t\t\t"LaunchOptions"\t\t{quoted(value)}\n\t\t\t\t\t}}\n'
                   for app_id, value in options.items())
    path = config / "localconfig.vdf"
    path.write_text('"UserLocalConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n'
                    '\t\t\t"Steam"\n\t\t\t{\n\t\t\t\t"apps"\n\t\t\t\t{\n' + apps +
                    '\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n')
    return path


def pe_exe(imports: list[str]) -> bytes:
    """A minimal PE32+ executable whose import table names these DLLs."""
    section_va, section_raw = 0x1000, 0x200
    names = b""
    offsets = []
    descriptors_size = 20 * (len(imports) + 1)
    for name in imports:
        offsets.append(section_va + descriptors_size + len(names))
        names += name.encode() + b"\x00"
    descriptors = b"".join(struct.pack("<IIIII", 0, 0, 0, rva, 0) for rva in offsets) + b"\x00" * 20
    section = (descriptors + names).ljust(0x200, b"\x00")
    optional = bytearray(240)
    struct.pack_into("<H", optional, 0, 0x20B)
    struct.pack_into("<I", optional, 108, 16)
    struct.pack_into("<II", optional, 112 + 8, section_va, descriptors_size)
    coff = struct.pack("<HHIIIHH", 0x8664, 1, 0, 0, 0, len(optional), 0x22)
    header = struct.pack("<8sIIIIIIHHI", b".idata", len(section), section_va, len(section),
                         section_raw, 0, 0, 0, 0, 0x40000040)
    pe = b"PE\x00\x00" + coff + bytes(optional) + header
    mz = bytearray(0x40)
    mz[:2] = b"MZ"
    struct.pack_into("<I", mz, 0x3C, 0x40)
    return (bytes(mz) + pe).ljust(section_raw, b"\x00") + section


def snapshot(folder: Path) -> dict[str, str]:
    """relative path -> sha256 of every file (to prove everything was put back)."""
    result = {}
    for directory, _, files in os.walk(folder):
        for name in files:
            path = Path(directory) / name
            result[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


# A stand-in for the installer HelixSR 2.0 releases carry (setup/helixsr_bridge.py): it only
# speaks the same command line and JSON and lays files out the way HelixSR Scaler does.
FAKE_BRIDGE = r'''
import json, os, re, shutil, sys
from pathlib import Path
release, command = Path(sys.argv[1]), sys.argv[2]
ngx = (release / "HelixSR" / "helixsr.dll").is_file()   # HelixSR 3.0's layout
helix = "HelixSR" if ngx else "HelixSR-fsrfg"
helix_dll = "helixsr.dll" if ngx else "amd_fidelityfx_dx12.dll"
args = dict(zip(sys.argv[3::2], sys.argv[4::2]))
log = release / "bridge-calls.txt"
with open(log, "a") as f:
    f.write(" ".join(sys.argv[2:]) + "\n")
def answer(**kw):
    print(json.dumps(dict(protocol=1, ok=True, messages=["fake bridge"], **kw)))
def exe_dir(game):
    for d, _, files in os.walk(game):
        if any(n.endswith(".exe") for n in files):
            return Path(d)
    raise SystemExit("no exe")
if command == "install":
    t = exe_dir(args["--game"])
    if args["--way"] == "scaler":
        name = args.get("--scaler-name", "dxgi.dll")
        files = []
        if (t / "HelixSR-Scaler.files").exists():   # an update: the earlier install out first
            for rel in (t / "HelixSR-Scaler.files").read_text().splitlines():
                if rel and not rel.startswith(("#", "name=")) and (t / rel).is_file():
                    (t / rel).unlink()
            for d in ("HelixSR", "HelixSR-fsrfg"):
                shutil.rmtree(t / d, ignore_errors=True)
            backup = t / "HelixSR-Scaler-backup"
            if backup.is_dir():
                for f in backup.rglob("*"):
                    if f.is_file():
                        os.replace(f, t / f.relative_to(backup))
                shutil.rmtree(backup)
        if (t / name).exists():
            (t / "HelixSR-Scaler-backup").mkdir(exist_ok=True)
            os.replace(t / name, t / "HelixSR-Scaler-backup" / name)
        shutil.copyfile(Path(args["--scaler"]) / "OptiScaler.dll", t / name)
        files.append(name)
        (t / helix).mkdir(exist_ok=True)
        shutil.copyfile(release / helix / helix_dll, t / helix / helix_dll)
        files.append(helix + "/" + helix_dll)
        (t / "OptiScaler.ini").write_text("[HelixSR]\n")
        files.append("OptiScaler.ini")
        if ngx:   # made when the game starts; removed with HelixSR Scaler
            (t / helix / "helixsr.ini").write_text("[HelixSR]\n")
        if args.get("--fg") == "on" and not ngx:
            (t / "HelixSR-fsrfg" / "helixsr-fg").mkdir(exist_ok=True)
            (t / "HelixSR-fsrfg" / "helixsr-fg" / "nvexec64.dll").write_bytes(b"MZ fg")
            files.append("HelixSR-fsrfg/helixsr-fg/nvexec64.dll")
            (t / "OptiScaler.ini").write_text(
                "[HelixSR]\n[FrameGen]\nFGInput=nvngxfg\nFGNvngxReplacement=HelixSR\n")
        (t / "HelixSR-Scaler.files").write_text(
            "# HelixSR Scaler, installed by HelixSR Desktop\n# version=" +
            args.get("--scaler-version", "") + "\n" + ("# layout=ngx\n" if ngx else "") +
            "name=" + name + "\n" + "\n".join(files) + "\n")
    elif args["--way"] == "fsr" and ngx:   # HLX FSR 4 in place of the game's FSR 3.1 DLLs
        hlx = release / "HLX-FSR4" / "amd_fidelityfx_upscaler_dx12.dll"
        version = re.search(rb"\x00HelixSR (\d+\.\d+\.\d+)\x00",
                            (release / helix / helix_dll).read_bytes()).group(1).decode()
        found = {n: [Path(d) / n for d, _, names in os.walk(args["--game"]) if n in names]
                 for n in ("amd_fidelityfx_upscaler_dx12.dll", "amd_fidelityfx_dx12.dll")}
        for t in found["amd_fidelityfx_upscaler_dx12.dll"] or found["amd_fidelityfx_dx12.dll"]:
            if b"HLX FSR 4 (" not in t.read_bytes():
                shutil.copyfile(t, t.with_name(t.stem + ".original.dll"))
            shutil.copyfile(hlx, t)
            (t.parent / "helixsr-install.json").write_text(json.dumps(
                {"helixsr": version, "upscaler": "HLX FSR 4", "files": [t.name],
                 "route": "direct", "ini_made": None}))
    answer(game={})
elif command == "scaler-fg":
    t = exe_dir(args["--game"])
    on = args["--on"] == "true"
    fg = t / "HelixSR-fsrfg" / "helixsr-fg"
    if on and not fg.is_dir():
        fg.mkdir(parents=True)
        (fg / "nvexec64.dll").write_bytes(b"MZ fg")
        with open(t / "HelixSR-Scaler.files", "a") as f:
            f.write("HelixSR-fsrfg/helixsr-fg/nvexec64.dll\n")
    (t / "OptiScaler.ini").write_text(
        "[HelixSR]\n[FrameGen]\nFGInput=" + ("nvngxfg" if on else "auto") +
        "\nFGNvngxReplacement=" + ("HelixSR" if on else "auto") + "\n")
    answer(game={})
elif command == "remove":
    answer(game={})
else:
    print(json.dumps({"protocol": 1, "ok": False, "error": "unknown", "messages": []}))
'''


def make_helixsr_modern(folder: Path, version: str = "2.0.0", built: bool = True,
                        fg: bool = False) -> Path:
    """A HelixSR 2.0 style release: HelixSR-fsrfg, helixsr-scaler and the installer."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "helixsr-setup.sh").write_text("#!/bin/sh\n")
    (folder / "HelixSR-fsrfg").mkdir(exist_ok=True)
    (folder / "HelixSR-fsrfg" / "amd_fidelityfx_dx12.dll").write_bytes(helixsr_dll(version, built))
    (folder / "helixsr-scaler").mkdir(exist_ok=True)
    (folder / "helixsr-scaler" / "OptiScaler.dll").write_bytes(
        b"MZ OptiScaler HelixSR Scaler v1.1.0 (marker)")
    (folder / "setup" / "fg").mkdir(parents=True, exist_ok=True)
    (folder / "setup" / "fg" / "fg_setup.py").write_text("# stand-in\n")
    (folder / "setup" / "helixsr_bridge.py").write_text(FAKE_BRIDGE)
    fg_dir = folder / "HelixSR-fsrfg" / "helixsr-fg"
    fg_dir.mkdir(exist_ok=True)
    (fg_dir / "nvexec64.dll").write_bytes(b"MZ fg executor (marker)")
    if fg:   # what HelixSR's setup adds when it builds frame generation (stand-ins)
        for name in ("_nvngx.dll", "nvngx_dlssg.dll", "hxfg_data.bin"):
            (fg_dir / name).write_bytes(b"marker")
    return folder


def hlx_dll(built: bool = True) -> bytes:
    """A stand-in for HLX FSR 4's DLL; built: with the shader data HelixSR's setup appends."""
    body = b"MZ" + b"\x00" * 64 + b"ffxCreateContext HLX FSR 4 (4.1.2)" + b"\x00" * 64
    if built:
        data = b"s" * 50
        body += data + b"HLXFSR4D" + struct.pack("<QQ", len(data), 1)
    return body


def make_helixsr_ngx(folder: Path, version: str = "3.0.0", built: bool = True,
                     hlx: bool = True) -> Path:
    """A HelixSR 3.0 style release: HelixSR/helixsr.dll, HLX-FSR4, helixsr-scaler, the installer
    and no frame generation."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "helixsr-setup.sh").write_text("#!/bin/sh\n")
    (folder / "HelixSR").mkdir(exist_ok=True)
    (folder / "HelixSR" / "helixsr.dll").write_bytes(helixsr_dll(version, built))
    (folder / "HelixSR" / "helixsr.ini").write_text("[HelixSR]\n")
    (folder / "HLX-FSR4").mkdir(exist_ok=True)
    (folder / "HLX-FSR4" / "amd_fidelityfx_upscaler_dx12.dll").write_bytes(hlx_dll(hlx))
    (folder / "helixsr-scaler").mkdir(exist_ok=True)
    (folder / "helixsr-scaler" / "OptiScaler.dll").write_bytes(
        b"MZ OptiScaler HelixSR Scaler v2.0.0 (marker)")
    (folder / "setup" / "hlxfsr4").mkdir(parents=True, exist_ok=True)
    (folder / "setup" / "helixsr_bridge.py").write_text(FAKE_BRIDGE)
    return folder
