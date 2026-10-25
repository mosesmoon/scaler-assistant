"""Which GPUs this PC has, which AMD generation each one is, and whether it is
built into the processor.

* HelixSR targets AMD RDNA 1 and newer. RDNA 3 and newer run HelixSR's network
  with 64 lanes, which matters for the OptiScaler way (see HelixSR's README,
  "check the wave size").
* FSR 4: RDNA 4 (RX 9000) runs AMD's own FSR 4. Other GPUs run the INT8 model,
  for which the FSR 4.1 Exact / Lossy DLLs exist in four builds: RX 7000 cards,
  RX 6000 cards, RDNA 3 built into the processor (also every other GPU) and
  RDNA 2 built into the processor (also the Steam Deck).

The generation comes from the graphics IP version the amdgpu driver reports
(KFD topology, else IP discovery in sysfs).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

VENDORS = {0x1002: "AMD", 0x10DE: "NVIDIA", 0x8086: "Intel"}
# Graphics IP versions only found in processors (APUs), including the Steam Deck (gfx1033).
_APU_GFX = {
    (9, 0, 2), (9, 0, 9), (9, 0, 12), (10, 3, 3), (10, 3, 5), (10, 3, 6), (10, 3, 7),
    (11, 0, 3), (11, 0, 4), (11, 5, 0), (11, 5, 1), (11, 5, 2), (11, 5, 3),
}


@dataclass
class Gpu:
    vendor: str
    device_id: int
    gfx: Optional[tuple[int, int, int]] = None   # (major, minor, stepping)
    name: str = ""
    apu: bool = False                            # built into the processor

    @property
    def rdna4(self) -> bool:
        return self.vendor == "AMD" and bool(self.gfx) and self.gfx[0] >= 12

    @property
    def family(self) -> str:
        if self.vendor != "AMD" or not self.gfx:
            return ""
        major, minor, _ = self.gfx
        if major == 9:
            return "Vega"
        if major == 10:
            return "RDNA 1" if minor < 3 else "RDNA 2"
        if major == 11:
            return "RDNA 3.5" if minor >= 5 else "RDNA 3"
        if major >= 12:
            return "RDNA 4"
        return "GCN"

    @property
    def gfx_name(self) -> str:
        if not self.gfx:
            return ""
        major, minor, stepping = self.gfx
        return f"gfx{major}{minor:x}{stepping:x}" if major >= 10 else f"gfx{major}0{stepping:x}"

    @property
    def rdna3_or_newer(self) -> bool:
        return self.vendor == "AMD" and bool(self.gfx) and self.gfx[0] >= 11

    @property
    def supported(self) -> Optional[bool]:
        """True for RDNA 1+, False for older AMD GPUs, None when unknown or not AMD."""
        if self.vendor != "AMD" or not self.gfx:
            return None
        return self.gfx[0] >= 10

    def label(self) -> str:
        parts = [self.vendor]
        if self.family:
            parts.append(self.family)
        if self.apu:
            parts.append("APU")
        text = " ".join(parts)
        detail = self.gfx_name or f"{self.device_id:04x}"
        return f"{text} ({detail})"


def main_gpu(gpus: list[Gpu]) -> Optional[Gpu]:
    """The GPU games most likely use: a graphics card over built-in graphics, AMD first."""
    if not gpus:
        return None
    return sorted(gpus, key=lambda g: (g.apu, g.vendor != "AMD", g.gfx is None))[0]


def fsr4_pack(gpu: Optional[Gpu]) -> Optional[str]:
    """Which FSR 4.1 Exact / Lossy build fits, as fsr4-shader-performance-overrides names them:

    * 'rx7000': Radeon RX 7000 cards (RDNA 3 graphics cards);
    * 'rx6000': Radeon RX 6000 cards (RDNA 2 graphics cards);
    * 'igpu_rdna2': RDNA 2 built into the processor (Steam Deck, Radeon 680M / 660M / 610M);
    * 'igpu_rdna3': RDNA 3 / 3.5 built into the processor, and every other GPU
      (GeForce, Intel Arc, older Radeons, unknown);
    * None on RDNA 4, where AMD's own FSR 4 runs and the modified DLLs must not be used."""
    if gpu is None or gpu.vendor != "AMD" or not gpu.gfx:
        return "igpu_rdna3"
    if gpu.rdna4:
        return None
    major, minor, _ = gpu.gfx
    rdna2 = major == 10 and minor >= 3
    if gpu.apu:
        return "igpu_rdna2" if rdna2 else "igpu_rdna3"
    if major == 11:
        return "rx7000"
    if rdna2:
        return "rx6000"
    return "igpu_rdna3"


def legacy_fsr4_pack(setting: str, gpu: Optional[Gpu]) -> str:
    """The build that replaces a choice made when there were two: 'dgpu' or 'igpu'."""
    pack = fsr4_pack(gpu) or ""
    if setting == "dgpu":
        return pack if pack in ("rx7000", "rx6000") else "rx6000"
    return pack if pack in ("igpu_rdna3", "igpu_rdna2") else "igpu_rdna3"


def _read(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def _kfd_gpus(root: Path) -> dict[int, tuple[tuple[int, int, int], bool]]:
    """device id -> (gfx version, built into the processor), from the amdgpu compute topology."""
    found: dict[int, tuple[tuple[int, int, int], bool]] = {}
    nodes = root / "class/kfd/kfd/topology/nodes"
    try:
        entries = sorted(nodes.iterdir())
    except OSError:
        return found
    for node in entries:
        props = {}
        for line in _read(node / "properties").splitlines():
            key, _, value = line.partition(" ")
            props[key] = value.strip()
        try:
            version = int(props.get("gfx_target_version", "0"))
            device = int(props.get("device_id", "0"))
            cpu_cores = int(props.get("cpu_cores_count", "0"))
        except ValueError:
            continue
        if version and device:
            # An APU's GPU node also carries the processor's cores.
            found[device] = ((version // 10000, (version // 100) % 100, version % 100), cpu_cores > 0)
    return found


def _ip_discovery(device: Path) -> Optional[tuple[int, int, int]]:
    for major_file in sorted(device.glob("ip_discovery/die/*/GC/*/major")):
        try:
            major = int(_read(major_file))
            minor = int(_read(major_file.with_name("minor")) or 0)
            stepping = int(_read(major_file.with_name("revision")) or 0)
        except ValueError:
            continue
        return major, minor, stepping
    return None


def detect(root: Path = Path("/sys")) -> list[Gpu]:
    kfd = _kfd_gpus(root)
    gpus: list[Gpu] = []
    seen = set()
    try:
        cards = sorted((root / "class/drm").glob("card[0-9]*"))
    except OSError:
        cards = []
    for card in cards:
        if "-" in card.name:
            continue   # connectors such as card0-DP-1
        device = card / "device"
        try:
            vendor = int(_read(device / "vendor") or "0", 16)
            device_id = int(_read(device / "device") or "0", 16)
        except ValueError:
            continue
        key = (vendor, device_id, _read(device / "uevent"))
        if vendor not in VENDORS or key in seen:
            continue
        seen.add(key)
        gfx, apu = kfd.get(device_id) or (_ip_discovery(device) if vendor == 0x1002 else None, False)
        apu = apu or (gfx in _APU_GFX)
        if vendor == 0x8086:   # Intel's built-in graphics sit on the processor's own bus
            apu = "PCI_SLOT_NAME=0000:00:" in _read(device / "uevent")
        gpus.append(Gpu(VENDORS[vendor], device_id, gfx, _read(device / "product_name"), apu))
    return gpus
