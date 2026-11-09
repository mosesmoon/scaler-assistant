"""Which upscaler HelixSR Scaler runs in a game (HelixSR 3.0 and newer).

HelixSR Scaler, HelixSR's own OptiScaler build, reads it from the game's OptiScaler.ini, the
same keys its in-game menu (Insert) writes:

* HLX DLSS (``HelixSR/helixsr.dll``), HelixSR Scaler's DLSS upscaler and its default:
  ``[Upscalers]`` left on auto; ``[HelixSR] DlssModel`` = auto (Model E, "Preset E") or ``k``
  (NVIDIA's DLSS 4 Preset K, ``HelixSR/k`` in the game, built only on request).
* HLX FSR 4 (``OptiScaler/amd_fidelityfx_upscaler_dx12.dll``, first in its FidelityFX list):
  ``Dx12Upscaler = ffx``, DirectX 11 and Vulkan through DirectX 12 (``ffx_12``), or in Vulkan
  games its own Vulkan build (``OptiScaler/custom/HLX FSR 4/ffx_vk``, HelixSR 3.3).
* HLX FSR 4 Full (``OptiScaler/custom/HLX FSR 4 Full``, HelixSR 3.2.1): ``Dx12Upscaler`` = the
  folder's name. DirectX 12 only, and HelixSR Scaler only lists it on the AMD GPUs it is made
  for (BC-250, RDNA 1, RDNA 2, RDNA 3, Steam Deck).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from . import optiscaler

OPTI_INI = "OptiScaler.ini"
UPSCALERS = ("dlss_e", "dlss_k", "fsr4", "fsr4_full")
DLSS = ("dlss_e", "dlss_k")
FSR4 = ("fsr4", "fsr4_full")
K_DLL = "HelixSR/k/helixsr.dll"
FULL = "HLX FSR 4 Full"
FULL_DLL = f"OptiScaler/custom/{FULL}/ffx/amd_fidelityfx_upscaler_dx12.dll"
VK = "HLX FSR 4"
VK_DLL = f"OptiScaler/custom/{VK}/ffx_vk/amd_fidelityfx_upscaler_vk.dll"
KEYS = {"dx11": "Dx11Upscaler", "vulkan": "VulkanUpscaler"}   # anything else: Dx12Upscaler
_AUTO = ("", "auto", "dlss", "dlss_12")
_FFX = ("ffx", "ffx_12", "fsr31", "fsr31_12")


def _fp16(device: int) -> bool:   # BC-250, RDNA 1 (HelixSR Scaler's CustomProviders.h)
    return (device in (0x13FE, 0x143F) or 0x7310 <= device <= 0x731F
            or 0x7340 <= device <= 0x734F or 0x7360 <= device <= 0x736F)


def _int8(device: int) -> bool:   # RDNA 2, RDNA 3 and their APUs, the Steam Deck
    return (0x73A0 <= device <= 0x73FF or 0x7420 <= device <= 0x743F or 0x7440 <= device <= 0x74FF
            or device in (0x1681, 0x164E, 0x15BF, 0x15C8, 0x1900, 0x1901, 0x150E, 0x1586, 0x1114,
                          0x163F, 0x1435, 0x1490))


def full_gpu(gpus: Iterable) -> bool:
    """HLX FSR 4 Full runs on this PC's main GPU (HelixSR Scaler hides it on every other GPU)."""
    gpus = list(gpus)
    if not gpus:
        return True   # unknown: the benefit of the doubt
    main = gpus[0]
    return main.vendor == "AMD" and (_fp16(main.device_id) or _int8(main.device_id))


def _read(path: Path) -> str:
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as handle:
        return handle.read()


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        handle.write(text)


def current(exe: Path, api: str) -> Optional[str]:
    """What the game's OptiScaler.ini picks for its graphics API; None when it picks something
    else (AMD's FSR, XeSS... chosen in HelixSR Scaler's menu) or there is no OptiScaler.ini."""
    try:
        text = _read(exe / OPTI_INI)
    except OSError:
        return None
    upscalers = optiscaler.section_text(text, "Upscalers")
    value = (optiscaler.get_value(upscalers, KEYS.get(api, "Dx12Upscaler")) or "").strip().lower()
    if value == FULL.lower():
        return "fsr4_full"
    if value == VK.lower() or value in _FFX:
        index = (optiscaler.get_value(optiscaler.section_text(text, "FSR"), "UpscalerIndex")
                 or "auto").strip().lower()
        return "fsr4" if index in ("auto", "0", "") else None
    if value in _AUTO:
        model = (optiscaler.get_value(optiscaler.section_text(text, "HelixSR"), "DlssModel")
                 or "").strip().lower()
        return "dlss_k" if model == "k" else "dlss_e"
    return None


def write(exe: Path, value: str) -> None:
    """Make HelixSR Scaler in the game run ``value`` (one of UPSCALERS). All three APIs are set,
    so a wrongly guessed API still gets it where it can run."""
    if value not in UPSCALERS:
        raise ValueError(value)
    path = exe / OPTI_INI
    text = _read(path)
    if value in DLSS:
        text = optiscaler.set_value(text, "Upscalers", "Dx12Upscaler", "auto")
        text = optiscaler.set_value(text, "Upscalers", "Dx11Upscaler", "auto")
        text = optiscaler.set_value(text, "Upscalers", "VulkanUpscaler", "auto")
        text = optiscaler.set_value(text, "HelixSR", "DlssModel", "k" if value == "dlss_k" else "auto")
    else:
        dx12 = FULL if value == "fsr4_full" else "ffx"
        vulkan = VK if (exe / VK_DLL).is_file() else "ffx_12"
        text = optiscaler.set_value(text, "Upscalers", "Dx12Upscaler", dx12)
        text = optiscaler.set_value(text, "Upscalers", "Dx11Upscaler", "ffx_12")
        text = optiscaler.set_value(text, "Upscalers", "VulkanUpscaler", vulkan)
        text = optiscaler.set_value(text, "FSR", "UpscalerIndex", "auto")
    _write(path, text)
