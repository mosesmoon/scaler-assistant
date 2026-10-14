import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helixsr_assistant import gpu, helixsr, hxlog, installer, settings
from helixsr_assistant.games import detect_layout
from helixsr_assistant.installer import InstallError, original, set_ini_value
from helixsr_assistant.runtime import Watch, detect_running
from helixsr_assistant.service import AssistantService, GameRunningError

from tests.fakes import helixsr_dll, make_helixsr, make_steam, snapshot

FSR, DLSS, PLAIN = 100, 200, 300


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.steam = make_steam(self.root)
        self.common = self.steam / "steamapps" / "common"
        self.hx = make_helixsr(self.root / "HelixSR-1.9.0")
        self.win64 = self.common / "FsrGame" / "Game" / "Binaries" / "Win64"
        self.dlss_bin = self.common / "DlssGame" / "bin"
        running = mock.patch("helixsr_assistant.service.running_app_ids", return_value={})
        self.running = running.start()
        self.addCleanup(running.stop)
        self.service = AssistantService(self.steam, self.root / "state.json")
        self.service.set_helixsr_folder(self.hx)
        self.service.scan()

    def tearDown(self):
        self.tmp.cleanup()

    def entry(self, app_id):
        return next(e for e in self.service.entries() if e.app_id == app_id)


class LayoutTest(Base):
    def test_detects_upscalers_ways_and_exe_folder(self):
        fsr = self.entry(FSR)
        self.assertEqual(fsr.layout.inputs, ["DLSS"])
        self.assertEqual(fsr.layout.fsr_targets, [str(self.win64 / "amd_fidelityfx_upscaler_dx12.dll")])
        self.assertEqual(fsr.layout.exe_dir, str(self.win64))
        self.assertEqual(fsr.ways, ["direct", "optiscaler", "dlss"])
        self.assertEqual(fsr.layout.upscalers, ["DLSS", "FSR 3.1"])

        dlss = self.entry(DLSS)
        self.assertEqual(dlss.ways, ["optiscaler", "dlss"])
        self.assertEqual(dlss.layout.exe_dir, str(self.dlss_bin))
        self.assertEqual(dlss.layout.anti_cheat, ["Easy Anti-Cheat"])

        plain = self.entry(PLAIN)
        self.assertEqual(plain.ways, [])
        self.assertFalse(plain.supported)

    def test_combined_dll_only_when_no_upscaler_dll(self):
        (self.win64 / "amd_fidelityfx_upscaler_dx12.dll").unlink()
        layout = detect_layout(self.common / "FsrGame")
        self.assertEqual(layout.fsr_targets, [str(self.win64 / "amd_fidelityfx_dx12.dll")])


class FolderTest(Base):
    def test_inspect(self):
        folder = helixsr.inspect(self.hx)
        self.assertEqual(folder.version, "1.9.0")
        self.assertTrue(folder.ready and folder.has_loader and folder.has_optiscaler)
        old = make_helixsr(self.root / "old", "1.7.0")
        self.assertEqual(helixsr.inspect(old).problem, "hx_too_old")
        raw = make_helixsr(self.root / "raw", built=False)
        self.assertEqual(helixsr.inspect(raw).problem, "hx_not_built")

    def test_set_folder_accepts_parent_of_extracted_release(self):
        outer = self.root / "dl" / "HelixSR-2.0.0"
        make_helixsr(outer / "HelixSR-2.0.0", "2.0.0")
        folder = self.service.set_helixsr_folder(outer)
        self.assertEqual(folder.version, "2.0.0")
        with self.assertRaises(FileNotFoundError):
            self.service.set_helixsr_folder(self.root / "dl")

    def test_finds_folders_in_home(self):
        home = self.root / "home"
        make_helixsr(home / "Downloads" / "HelixSR-1.8.1" / "HelixSR-1.8.1", "1.8.1")
        make_helixsr(home / "HelixSR-1.9.0", "1.9.0", built=False)
        make_helixsr(home / "Games" / "HelixSR-1.9.0", "1.9.0")
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            found = helixsr.find_candidates()
        self.assertEqual([(f.path.parent.name, f.version, f.built) for f in found],
                         [("Games", "1.9.0", True), ("HelixSR-1.8.1", "1.8.1", True),
                          ("home", "1.9.0", False)])


class InstallTest(Base):
    def test_fsr_way_install_and_remove(self):
        before = snapshot(self.common / "FsrGame")
        target = self.win64 / "amd_fidelityfx_upscaler_dx12.dll"
        message = self.service.install(FSR, "direct")
        self.assertIn("AMD FSR", message)
        self.assertEqual(helixsr.dll_version(target), "1.9.0")
        self.assertEqual(original(target).read_bytes(), b"MZ ffxCreateContext game FSR")
        # The combined DLL stays the game's: HelixSR replaces only the upscaler DLL.
        self.assertFalse(helixsr.is_helixsr(self.win64 / "amd_fidelityfx_dx12.dll"))
        record = json.loads((self.win64 / "helixsr-install.json").read_text())
        self.assertEqual((record["route"], record["helixsr"], record["files"]),
                         ("direct", "1.9.0", ["amd_fidelityfx_upscaler_dx12.dll"]))
        entry = self.entry(FSR)
        self.assertEqual((entry.status.route, entry.status.version), ("direct", "1.9.0"))
        self.assertFalse(entry.outdated or entry.status.issues)

        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual(snapshot(self.common / "FsrGame"), before)
        self.assertIsNone(self.entry(FSR).status.route)

    def test_optiscaler_way_backs_up_and_restores(self):
        before = snapshot(self.common / "DlssGame")
        self.service.install(DLSS, "optiscaler")
        hx = self.dlss_bin / "HelixSR"
        self.assertTrue(helixsr.is_optiscaler(self.dlss_bin / "dxgi.dll"))
        self.assertEqual((hx / "backup" / "dxgi.dll").read_bytes(), b"MZ the game's own dxgi")
        for name in ("helixsr.dll", "helixsr_upscaler.dll"):
            self.assertEqual(helixsr.dll_version(hx / name), "1.9.0")
        self.assertTrue((hx / "amd_fidelityfx_upscaler_dx12.amd.dll").is_file())
        self.assertTrue((hx / "amd_fidelityfx_framegeneration_dx12.dll").is_file())
        self.assertTrue((hx / "my-fsr").is_dir())
        ini = (self.dlss_bin / "OptiScaler.ini").read_bytes().decode()
        win = "Z:" + str(hx.resolve()).replace("/", "\\")
        self.assertIn("Dx12Upscaler=fsr31\r\n", ini)
        self.assertIn(f"FfxDx12Path={win}\\helixsr.dll\r\n", ini)
        self.assertIn(f"FfxDx12SRPath={win}\\helixsr_upscaler.dll\r\n", ini)
        self.assertIn(f"FfxDx12FGPath={win}\\amd_fidelityfx_framegeneration_dx12.dll\r\n", ini)
        record = json.loads((hx / "helixsr-install.json").read_text())
        self.assertEqual(record["route"], "optiscaler")
        self.assertEqual(record["moved"], ["dxgi.dll"])
        self.assertEqual(record["ini"], "created")
        self.assertEqual(sorted(record["created"]), ["fakenvapi.dll", "fakenvapi.ini"])
        self.assertNotIn("chosen", record)   # no FSR 3.1 in this game

        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(snapshot(self.common / "DlssGame"), before)
        self.assertFalse(hx.exists())

    def test_switching_ways_carries_settings_and_puts_everything_back(self):
        before = snapshot(self.common / "FsrGame")
        self.service.install(FSR, "direct")
        self.service.write_settings(FSR, {"Sharpener": "rcas", "Sharpness": "0.4"})
        self.assertTrue((self.win64 / "helixsr.ini").is_file())

        self.service.install(FSR, "optiscaler")
        entry = self.entry(FSR)
        self.assertEqual(entry.status.route, "optiscaler")
        self.assertTrue(entry.status.chosen)
        self.assertEqual(original(self.win64 / "amd_fidelityfx_upscaler_dx12.dll").exists(), False)
        self.assertFalse((self.win64 / "helixsr.ini").exists())
        self.assertEqual(settings.read(self.win64 / "HelixSR" / "helixsr.ini"),
                         {"Sharpener": "rcas", "Sharpness": "0.40"})

        self.service.install(FSR, "dlss")
        self.assertEqual(self.entry(FSR).status.route, "dlss")
        self.assertTrue(helixsr.is_loader(self.win64 / "dxgi.dll"))
        self.assertEqual(helixsr.dll_version(self.win64 / "nvngx.dll"), "1.9.0")
        self.assertFalse((self.win64 / "OptiScaler.ini").exists())
        self.assertEqual(self.service.read_settings(FSR), {"Sharpener": "rcas", "Sharpness": "0.40"})

        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual(set(snapshot(self.common / "FsrGame")) - set(before),
                         {"Game/Binaries/Win64/helixsr.ini"})
        self.service.install(FSR, "direct")
        self.service.uninstall(FSR, remove_settings=True)
        self.assertEqual(snapshot(self.common / "FsrGame"), before)

    def test_repair_after_game_update(self):
        self.service.install(FSR, "direct")
        target = self.win64 / "amd_fidelityfx_upscaler_dx12.dll"
        target.write_bytes(b"MZ ffxCreateContext game FSR v2")   # Steam updated the game
        entry = self.entry(FSR)
        self.assertEqual(entry.status.issues, ["is_game_updated"])
        self.assertTrue(entry.needs_attention)
        self.service.install(FSR, "direct")
        self.assertTrue(helixsr.is_helixsr(target))
        self.assertEqual(original(target).read_bytes(), b"MZ ffxCreateContext game FSR v2")
        self.assertEqual(self.entry(FSR).status.issues, [])

    def test_repair_optiscaler_after_game_restores_its_dxgi(self):
        self.service.install(DLSS, "optiscaler")
        (self.dlss_bin / "dxgi.dll").write_bytes(b"MZ the game's own dxgi v2")
        self.assertEqual(self.entry(DLSS).status.issues, ["is_files_replaced"])
        self.service.install(DLSS, "optiscaler")
        self.assertTrue(helixsr.is_optiscaler(self.dlss_bin / "dxgi.dll"))
        self.assertEqual((self.dlss_bin / "HelixSR" / "backup" / "dxgi.dll").read_bytes(),
                         b"MZ the game's own dxgi v2")
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual((self.dlss_bin / "dxgi.dll").read_bytes(), b"MZ the game's own dxgi v2")

    def test_update_all(self):
        self.service.install(FSR, "direct")
        self.service.install(DLSS, "optiscaler")
        newer = make_helixsr(self.root / "HelixSR-1.9.1", "1.9.1")
        self.service.set_helixsr_folder(newer)
        self.assertTrue(self.entry(FSR).outdated and self.entry(DLSS).outdated)
        self.service.update_all()
        for app_id in (FSR, DLSS):
            entry = self.entry(app_id)
            self.assertEqual(entry.status.version, "1.9.1")
            self.assertFalse(entry.outdated)
        self.assertEqual(self.entry(DLSS).status.route, "optiscaler")

    def test_rebuilt_network_counts_as_update(self):
        self.service.install(FSR, "direct")
        (self.hx / "amd_fidelityfx_dx12.dll").write_bytes(helixsr_dll("1.9.0", extra=b"wave64" * 10))
        self.assertTrue(self.entry(FSR).outdated)

    def test_refuses_without_built_network(self):
        before = snapshot(self.common)
        raw = make_helixsr(self.root / "raw", built=False)
        self.service.set_helixsr_folder(raw)
        with self.assertRaises(FileNotFoundError):
            self.service.install(FSR, "direct")
        self.assertEqual(snapshot(self.common), before)

    def test_refuses_while_game_runs(self):
        before = snapshot(self.common)
        self.running.return_value = {FSR: [1234]}
        with self.assertRaises(GameRunningError):
            self.service.install(FSR, "direct")
        self.assertEqual(snapshot(self.common), before)

    def test_unavailable_way(self):
        with self.assertRaises(InstallError):
            self.service.install(DLSS, "direct")
        (self.hx / "dlss-loader" / "dxgi.dll").unlink()
        self.assertEqual(self.entry(DLSS).ways, ["optiscaler"])

    def test_existing_optiscaler_ini_is_edited_and_restored(self):
        own = "[Upscalers]\nDx12Upscaler=xess\n[Libraries]\nFfxDx12Path=auto\n[Menu]\nScale=1.5\n"
        (self.dlss_bin / "OptiScaler.ini").write_text(own)
        self.service.install(DLSS, "optiscaler")
        text = (self.dlss_bin / "OptiScaler.ini").read_text()
        self.assertIn("Dx12Upscaler=fsr31\n", text)
        self.assertIn("Scale=1.5\n", text)
        self.assertIn("FfxDx12SRPath=Z:", text)
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual((self.dlss_bin / "OptiScaler.ini").read_text(), own)

    def test_hand_replaced_amd_fsr_is_kept_on_update(self):
        self.service.install(DLSS, "optiscaler")
        mine = self.dlss_bin / "HelixSR" / "amd_fidelityfx_upscaler_dx12.amd.dll"
        mine.write_bytes(b"MZ ffxCreateContext FSR 4 by hand")
        message = self.service.install(DLSS, "optiscaler")
        self.assertEqual(mine.read_bytes(), b"MZ ffxCreateContext FSR 4 by hand")
        self.assertIn(mine.name, message)

    def test_helixsr_template_ini_removed_user_ini_kept(self):
        self.service.install(FSR, "direct")
        template = self.win64 / "helixsr.ini"
        template.write_text(";Sharpener = nvidia\n")
        record = json.loads((self.win64 / "helixsr-install.json").read_text())
        record["ini_made"] = installer.sha256(template)   # made by HelixSR's setup, untouched
        (self.win64 / "helixsr-install.json").write_text(json.dumps(record))
        self.service.uninstall(FSR, remove_settings=False)
        self.assertFalse(template.exists())


class SettingsTest(unittest.TestCase):
    def test_edit_keeps_other_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "helixsr.ini"
            path.write_bytes(b"; mine\r\n[Sharpening]\r\n;Sharpener = nvidia\r\nSharpness = 0.3\r\n"
                             b"[Forwarding]\r\nDll = x.dll\r\n")
            settings.write(path, {"Sharpness": None, "Sharpener": "NVIDIA", "Int8": "off"})
            text = path.read_bytes().decode()
            self.assertEqual(text, "; mine\r\n[Sharpening]\r\nSharpener = nvidia\r\n;Sharpener = nvidia\r\n"
                                   "[Forwarding]\r\nDll = x.dll\r\n\r\n[Upscaling]\r\nInt8 = off\r\n")
            self.assertEqual(settings.read(path), {"Sharpener": "nvidia", "Int8": "off"})
            settings.write(path, {"Sharpener": "bogus", "Sharpness": "7"})
            self.assertEqual(settings.read(path), {"Int8": "off", "Sharpness": "1.00"})

    def test_own_file_disappears_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "helixsr.ini"
            settings.write(path, {"WaveSize": "64"})
            self.assertTrue(path.read_text().startswith(settings.HEADER))
            self.assertEqual(settings.read(path), {"WaveSize": "64"})
            settings.write(path, {"WaveSize": None})
            self.assertFalse(path.exists())
            settings.write(path, {"WaveSize": None})
            self.assertFalse(path.exists())


class OptiIniTest(unittest.TestCase):
    def test_set_value(self):
        text = "[Upscalers]\r\nDx12Upscaler=auto\r\n[Libraries]\r\n"
        text = set_ini_value(text, "Upscalers", "Dx12Upscaler", "fsr31")
        text = set_ini_value(text, "Libraries", "FfxDx12Path", "Z:\\a")
        text = set_ini_value(text, "Plugins", "X", "1")
        self.assertEqual(text, "[Upscalers]\r\nDx12Upscaler=fsr31\r\n[Libraries]\r\n"
                               "FfxDx12Path=Z:\\a\r\n[Plugins]\r\nX=1\r\n")
        with self.assertRaises(InstallError):
            set_ini_value("A=1\nA=2\n", "S", "A", "3")


class LogTest(unittest.TestCase):
    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "helixsr.log"
            path.write_text("HelixSR 1.9.0 started\nwave size: GPU 1002:744c, network kernels wave32,"
                            " own kernels wave32\nHelixSR ERROR: something failed\n")
            summary = hxlog.summarize(path)
            self.assertEqual((summary.version, summary.wave), ("1.9.0", 32))
            self.assertEqual(summary.problems, ["HelixSR ERROR: something failed"])
            path.write_text("wave size: network kernels wave64\n")
            self.assertEqual(hxlog.summarize(path).wave, 64)
            self.assertTrue(hxlog.summarize(path).ok)


class RuntimeTest(unittest.TestCase):
    def test_detects_loaded_helixsr(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp) / "proc"
            proc.mkdir()
            (proc / "stat").write_text("cpu 1 2 3\nbtime 1000\n")
            game = "/mnt/lib/steamapps/common/Game/bin"
            for pid, env, maps in (
                    (41, b"SteamAppId=100\0HOME=/h\0", "7f00 r--p 0 0 1 /other/steamapps/common/Game/bin/amd_fidelityfx_upscaler_dx12.dll\n"),
                    (42, b"SteamAppId=200\0", "7f00 r--p 0 0 1 /usr/lib/libc.so\n"),
                    (43, b"PATH=/bin\0", "")):
                d = proc / str(pid)
                d.mkdir()
                (d / "environ").write_bytes(env)
                (d / "maps").write_text(maps)
                (d / "stat").write_text(f"{pid} (game.exe) S " + " ".join(["0"] * 18) + " 500 0\n")
            log = Path(tmp) / "helixsr.log"
            log.write_text("wave size: network kernels wave64\n")
            watch = {100: Watch([f"{game}/amd_fidelityfx_upscaler_dx12.dll"], [], [str(log)]),
                     200: Watch([f"{game}/x.dll"], [], [])}
            found = detect_running(watch, proc)
            self.assertEqual(sorted(found), [100, 200])
            self.assertTrue(found[100].helixsr_loaded)
            self.assertEqual(found[100].log.wave, 64)
            self.assertFalse(found[200].helixsr_loaded)


class GpuTest(unittest.TestCase):
    def test_generations(self):
        with tempfile.TemporaryDirectory() as tmp:
            sys = Path(tmp)
            for card, vendor, device in (("card0", "0x1002", "0x744c"), ("card1", "0x1002", "0x163f"),
                                         ("card2", "0x10de", "0x2684")):
                d = sys / "class/drm" / card / "device"
                d.mkdir(parents=True)
                (d / "vendor").write_text(vendor + "\n")
                (d / "device").write_text(device + "\n")
                (d / "uevent").write_text(f"PCI_SLOT_NAME={card}\n")
            (sys / "class/drm/card0-DP-1").mkdir()
            node = sys / "class/kfd/kfd/topology/nodes/1"
            node.mkdir(parents=True)
            (node / "properties").write_text("gfx_target_version 110000\ndevice_id 29772\n")
            ip = sys / "class/drm/card1/device/ip_discovery/die/0/GC/0"
            ip.mkdir(parents=True)
            for name, value in (("major", "10"), ("minor", "3"), ("revision", "3")):
                (ip / name).write_text(value)
            found = gpu.detect(sys)
            self.assertEqual([g.label() for g in found],
                             ["AMD RDNA 3 (gfx1100)", "AMD RDNA 2 (gfx1033)", "NVIDIA (2684)"])
            self.assertTrue(found[0].rdna3_or_newer)
            self.assertFalse(found[1].rdna3_or_newer)
            self.assertIsNone(found[2].supported)


if __name__ == "__main__":
    unittest.main()
