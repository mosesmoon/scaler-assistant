"""One-step HelixSR download and build (scaler_assistant.hxsetup) with a stand-in release."""

import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from scaler_assistant import hxsetup
from tests.fakes import helixsr_dll, hlx_dll
from tests.test_core import Base

# A stand-in for HelixSR's build program: --status reads a marker, a build writes the network
# footer (as the real setup appends it to HelixSR's DLL) and prints the setup's progress lines.
FAKE_SETUP = r'''
import struct, sys
from pathlib import Path
out = Path(sys.argv[1]); dll = out / "amd_fidelityfx_dx12.dll"; mark = out / "fg-built"
if "--status" in sys.argv:
    net = dll.read_bytes()[-32:-24] == b"HXSRNET1"
    print(f"network={int(net)} fg={int(mark.exists())}")
    sys.exit(0)
assert "--yes" in sys.argv and "--dxc" in sys.argv
with open(out.parent / "calls.txt", "a") as f:
    f.write(" ".join(sys.argv[2:]) + "\n")
for p in (0, 50, 100):
    print(f"[helixsr-setup] [{'#' * (p // 5)}{'-' * (20 - p // 5)}] {p:4d}%  0:01  network kernels", flush=True)
if "--fg-only" not in sys.argv:
    w = b"W" * 8
    with open(dll, "ab") as f:
        f.write(w + w + b"HXSRNET1" + struct.pack("<QQQ", 8, 8, 1))
if (out.parent / "fg-ok").exists():
    mark.write_text("1")
    sys.exit(0)
print("[helixsr-setup] frame generation: NVIDIA's NGX core could not be unpacked", flush=True)
sys.exit(3)
'''


# HelixSR 3.0's build program: the release folder as its argument, HelixSR/helixsr.dll, HLX FSR 4
# built with the compilers passed as helixsr-setup.sh passes them, no frame generation.
FAKE_SETUP_NGX = r'''
import struct, sys
from pathlib import Path
rel = Path(sys.argv[1]); dll = rel / "HelixSR" / "helixsr.dll"
hlx = rel / "HLX-FSR4" / "amd_fidelityfx_upscaler_dx12.dll"
built = lambda: hlx.read_bytes()[-24:-16] == b"HLXFSR4D"
if "--status" in sys.argv:
    net = dll.read_bytes()[-32:-24] == b"HXSRNET1"
    print(f"network={int(net)} fg=0 hlx={int(built())} k=0")   # 3.2.1 adds k=
    sys.exit(0)
assert "--yes" in sys.argv and "--dxc" in sys.argv
for k in ("--dxc-dir", "--dxc2609-dir", "--wine", "--wineprefix"):
    assert k in sys.argv, k
with open(rel / "calls.txt", "a") as f:
    f.write(" ".join(sys.argv[2:]) + "\n")
if "--fg-only" not in sys.argv:
    w = b"W" * 8
    with open(dll, "ab") as f:
        f.write(w + w + b"HXSRNET1" + struct.pack("<QQQ", 8, 8, 1))
if (rel / "hlx-ok").exists():
    with open(hlx, "ab") as f:
        f.write(b"D" * 8 + b"HLXFSR4D" + struct.pack("<QQ", 8, 1))
    sys.exit(0)
print("[helixsr-setup] HLX FSR 4 was not built: AMD's driver package could not be read", flush=True)
sys.exit(4)
'''


def release_zip_ngx(version="3.0.0", hlx_ok=True) -> bytes:
    data = io.BytesIO()
    top = f"HelixSR-{version}/"
    with zipfile.ZipFile(data, "w") as z:
        z.writestr(top + "helixsr-setup.sh", "#!/bin/sh\n")
        z.writestr(top + "HelixSR/helixsr.dll", helixsr_dll(version, built=False))
        z.writestr(top + "HLX-FSR4/amd_fidelityfx_upscaler_dx12.dll", hlx_dll(built=False))
        z.writestr(top + "helixsr-scaler/OptiScaler.dll", b"MZ OptiScaler HelixSR Scaler v2.0.0")
        z.writestr(top + "setup/helixsr_setup.py", FAKE_SETUP_NGX)
        z.writestr(top + "setup/helixsr_bridge.py", "")
        z.writestr(top + "setup/hlxfsr4/hlx/__init__.py", "")
        if hlx_ok:
            z.writestr(top + "hlx-ok", "")
    return data.getvalue()


def release_zip(version="2.0.0", fg_ok=True) -> bytes:
    data = io.BytesIO()
    top = f"HelixSR-{version}/"
    with zipfile.ZipFile(data, "w") as z:
        z.writestr(top + "helixsr-setup.sh", "#!/bin/sh\n")
        z.writestr(top + "HelixSR-fsrfg/amd_fidelityfx_dx12.dll", helixsr_dll(version, built=False))
        z.writestr(top + "helixsr-scaler/OptiScaler.dll", b"MZ OptiScaler HelixSR Scaler v1.1.0")
        z.writestr(top + "setup/helixsr_setup.py", FAKE_SETUP)
        z.writestr(top + "setup/helixsr_bridge.py", "")
        z.writestr(top + "setup/fg/fg_setup.py", "")
        if fg_ok:
            z.writestr(top + "fg-ok", "")
    return data.getvalue()


def api(*releases) -> list:
    return [{"draft": False, "prerelease": pre, "assets": [{
        "name": f"HelixSR-{v}.zip", "digest": "sha256:" + hashlib.sha256(z).hexdigest(),
        "size": len(z), "browser_download_url": f"https://example.invalid/HelixSR-{v}.zip"}]}
        for v, z, pre in releases]


class HxSetupTest(Base):
    def setUp(self):
        super().setUp()
        env = mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(self.root / "data")})
        env.start()
        self.addCleanup(env.stop)
        self.files = {}
        self.listing = []
        patches = [
            mock.patch.object(hxsetup, "find_python", return_value=sys.executable),
            mock.patch.object(hxsetup, "find_wine", return_value="/bin/true"),
            mock.patch.object(hxsetup, "get_dxc", return_value=Path("/bin/true")),
            mock.patch.object(hxsetup, "get_dxc2609", return_value=self.root / "dxc2609"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def opener(self, request, timeout=0):
        url = request.full_url
        if url == hxsetup.API:
            return io.BytesIO(json.dumps(self.listing).encode())
        return io.BytesIO(self.files[url.rsplit("/", 1)[1]])

    def publish(self, version, fg_ok=True, pre=False, ngx=False):
        self.files[f"HelixSR-{version}.zip"] = (release_zip_ngx(version, fg_ok) if ngx
                                                 else release_zip(version, fg_ok))
        self.listing = api((version, self.files[f"HelixSR-{version}.zip"], pre)) + self.listing

    def test_newest_stable_release_2_or_newer(self):
        self.publish("1.9.3")
        self.publish("2.0.0")
        self.publish("2.1.0", pre=True)
        self.listing.append({"draft": False, "prerelease": False,
                             "assets": [{"name": "HelixSR-2.5.0.zip", "size": 1,
                                         "browser_download_url": "x"}]})   # no digest: skipped
        self.assertEqual(hxsetup.latest_release(self.opener).version, "2.0.0")
        self.listing = api(("1.9.3", self.files["HelixSR-1.9.3.zip"], False))
        with self.assertRaises(hxsetup.SetupError):
            hxsetup.latest_release(self.opener)

    def test_install_builds_and_uses_it(self):
        self.publish("2.0.0")
        seen = []
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            message = self.service.build_helixsr(lambda *a: seen.append(a))
        folder = self.service.helixsr()
        self.assertTrue(folder.ready and folder.modern, message)
        self.assertEqual(folder.path, (self.root / "data/scaler-assistant/helixsr/HelixSR-2.0.0").resolve())
        self.assertIn("HelixSR 2.0.0", message)
        self.assertIn(("build", 50, 100, "network kernels"), seen)
        self.assertEqual([s[0] for s in seen if s[0] == "release"][:1], ["release"])
        calls = (folder.path / "calls.txt").read_text().splitlines()
        self.assertEqual(len(calls), 1)
        self.assertNotIn("--fg-only", calls[0])
        # again: nothing to download or build
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            self.service.build_helixsr()
        self.assertEqual(len((folder.path / "calls.txt").read_text().splitlines()), 1)
        # found again by the search for HelixSR folders
        from scaler_assistant import helixsr
        self.assertIn(folder.path, [f.path for f in helixsr.find_candidates()])

    def test_frame_generation_retried_alone_and_old_version_removed(self):
        self.publish("2.0.0", fg_ok=False)
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            message = self.service.build_helixsr()
        self.assertIn("NGX core could not be unpacked", message)
        first = self.service.helixsr().path
        (first / "fg-ok").write_text("")
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            self.service.build_helixsr()
        self.assertIn("--fg-only", (first / "calls.txt").read_text().splitlines()[-1])
        self.publish("2.0.1")
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            self.service.build_helixsr()
        self.assertEqual(self.service.helixsr().version, "2.0.1")
        self.assertFalse(first.exists())

    def test_checksum_and_unsafe_paths(self):
        self.publish("2.0.0")
        self.files["HelixSR-2.0.0.zip"] += b"x"
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener), \
                self.assertRaises(hxsetup.SetupError):
            self.service.build_helixsr()
        with self.assertRaises(hxsetup.SetupError):
            hxsetup._safe_members(["HelixSR-2.0.0/../../evil"])

    def test_progress_text(self):
        text = self.service.helixsr_auto_progress
        self.assertIn("50", text("build", 50, 100, "x"))
        self.assertIn("12", text("release", 12_000_000, 136_000_000, ""))
        self.assertIn("NVIDIA", self.service.helixsr_auto_consent())


    def test_helixsr_3_builds_hlx_fsr4_without_frame_generation(self):
        from scaler_assistant import helixsr
        from scaler_assistant.i18n import tr
        self.publish("2.0.0")
        self.publish("3.0.0", fg_ok=False, ngx=True)
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            message = self.service.build_helixsr()
        folder = self.service.helixsr()
        self.assertEqual((folder.version, folder.ngx, folder.built), ("3.0.0", True, True))
        self.assertFalse(folder.hlx_ready)
        self.assertIn(tr("hxa_no_hlx"), message)
        self.assertIn("AMD's driver package could not be read", message)
        self.assertNotIn(tr("hxa_no_fg"), message)          # 3.0 has no frame generation
        call = (folder.path / "calls.txt").read_text().splitlines()[0]
        self.assertIn(f"--dxc2609-dir {self.root / 'dxc2609'}", call)
        self.assertIn("--wine /bin/true", call)
        # again: only HLX FSR 4 is retried
        (folder.path / "hlx-ok").write_text("")
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            message = self.service.build_helixsr()
        self.assertIn("--fg-only", (folder.path / "calls.txt").read_text().splitlines()[-1])
        self.assertTrue(helixsr.inspect(folder.path).hlx_ready)
        self.assertNotIn(tr("hxa_no_hlx"), message)
        # built: nothing more to do
        with mock.patch("scaler_assistant.hxsetup.open_url", self.opener):
            self.service.build_helixsr()
        self.assertEqual(len((folder.path / "calls.txt").read_text().splitlines()), 2)

    def test_consent_names_amd_download(self):
        text = self.service.helixsr_auto_consent()
        self.assertIn(hxsetup.AMD_DRIVERS, text)
        self.assertIn("420 MB", text)

class DxcWrapperTest(unittest.TestCase):
    def test_paths_become_drive_z(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"XDG_DATA_HOME": tmp}):
            tools = hxsetup.tools_dir() / "dxc-win" / "bin" / "x64"
            tools.mkdir(parents=True)
            (tools / "dxc.exe").write_bytes(b"MZ")
            fake_wine = Path(tmp) / "wine"
            fake_wine.write_text("#!/bin/sh\nshift\nfor a in \"$@\"; do printf '%s\\n' \"$a\"; done\n")
            fake_wine.chmod(0o755)
            wrapper = hxsetup.get_dxc(str(fake_wine), lambda *a: None)
            import subprocess
            out = subprocess.run([str(wrapper), "-T", "cs_6_6", "-Fo", "/a b/c.dxil", "/x/y.hlsl"],
                                 capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(out, ["-T", "cs_6_6", "-Fo", "Z:\\a b\\c.dxil", "Z:\\x\\y.hlsl"])


    def test_second_compiler_download_is_checked(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            z.writestr("bin\\x64\\dxc.exe", b"MZ dxc 2609")
            z.writestr("bin\\x64\\dxcompiler.dll", b"MZ")
        blob = data.getvalue()
        opener = lambda request, timeout=0: io.BytesIO(blob)
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"XDG_DATA_HOME": tmp}):
            with self.assertRaises(hxsetup.SetupError):   # not the pinned file
                hxsetup.get_dxc2609(lambda *a: None, opener)
            with mock.patch.object(hxsetup, "DXC2609_SHA", hashlib.sha256(blob).hexdigest()):
                folder = hxsetup.get_dxc2609(lambda *a: None, opener)
            self.assertEqual((folder / "dxc.exe").read_bytes(), b"MZ dxc 2609")
            self.assertEqual(folder, hxsetup.tools_dir() / "dxc-win-2609" / "bin" / "x64")
