"""Which GPUs this PC has, and which AMD generation each one is.

HelixSR targets AMD RDNA 1 and newer. RDNA 3 and newer run HelixSR's network
with 64 lanes, which matters for the OptiScaler way (see HelixSR's README,
"check the wave size"). The generation comes from the graphics IP version that
the amdgpu driver reports (KFD topology, else IP discovery in sysfs).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

VENDORS = {0x1002: "AMD", 0x10DE: "NVIDIA", 0x8086: "Intel"}


@dataclass
class Gpu:
    vendor: str
    device_id: int
    gfx: Optional[tuple[int, int, int]] = None   # (major, minor, stepping)
    name: str = ""

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
        text = " ".join(parts)
        detail = self.gfx_name or f"{self.device_id:04x}"
        return f"{text} ({detail})"


def _read(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def _kfd_gpus(root: Path) -> dict[int, tuple[int, int, int]]:
    """device id -> gfx version, from the amdgpu compute topology."""
    found: dict[int, tuple[int, int, int]] = {}
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
        except ValueError:
            continue
        if version and device:
            found[device] = (version // 10000, (version // 100) % 100, version % 100)
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
        gfx = kfd.get(device_id) or (_ip_discovery(device) if vendor == 0x1002 else None)
        gpus.append(Gpu(VENDORS[vendor], device_id, gfx, _read(device / "product_name")))
    return gpus
