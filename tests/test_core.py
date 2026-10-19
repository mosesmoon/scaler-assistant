import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hashlib
import io
import zipfile

from scaler_assistant import components, gpu, helixsr, hxlog, installer, optiscaler, settings
from scaler_assistant import launch_options as lo
from scaler_assistant.games import detect_layout
from scaler_assistant.installer import InstallError, original, set_ini_value
from scaler_assistant.pe import graphics_api, imported_dlls
from scaler_assistant.runtime import Watch, detect_running
from scaler_assistant.service import (
    LAYOUT_VERSION,
    AssistantService, GameRunningError, NeedsDownloadError, SteamMustCloseError,
)

from tests.fakes import (
    OPTI_INI_FULL, helixsr_dll, make_components, make_helixsr, make_steam, pe_exe, snapshot,
    write_launch_options,
)

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
        running = mock.patch("scaler_assistant.service.running_app_ids", return_value={})
        self.running = running.start()
        self.addCleanup(running.stop)
        steam_running = mock.patch("scaler_assistant.steam.SteamInstallation.is_running",
                                   return_value=False)
        self.steam_running = steam_running.start()
        self.addCleanup(steam_running.stop)
        self.cef = mock.Mock()
        self.cef.available.return_value = False
        self.gpus = []
        detect = mock.patch("scaler_assistant.gpu.detect", side_effect=lambda *_: self.gpus)
        detect.start()
        self.addCleanup(detect.stop)
        self.service = AssistantService(self.steam, self.root / "state.json", cef=self.cef,
                                        components_root=self.root / "components")
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
        message = self.service.apply(FSR, "helixsr:direct")
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
        before = snapshot(self.common / "FsrGame")
        self.service.apply(FSR, "helixsr:optiscaler")
        hx = self.win64 / "HelixSR"
        self.assertTrue(helixsr.is_optiscaler(self.win64 / "dxgi.dll"))
        for name in ("helixsr.dll", "helixsr_upscaler.dll"):
            self.assertEqual(helixsr.dll_version(hx / name), "1.9.0")
        self.assertTrue((hx / "amd_fidelityfx_upscaler_dx12.amd.dll").is_file())
        self.assertTrue((hx / "amd_fidelityfx_framegeneration_dx12.dll").is_file())
        self.assertTrue((hx / "my-fsr").is_dir())
        ini = (self.win64 / "OptiScaler.ini").read_bytes().decode()
        win = "Z:" + str(hx.resolve()).replace("/", "\\")
        self.assertIn("Dx12Upscaler=fsr31\r\n", ini)
        self.assertIn(f"FfxDx12Path={win}\\helixsr.dll\r\n", ini)
        self.assertIn(f"FfxDx12SRPath={win}\\helixsr_upscaler.dll\r\n", ini)
        self.assertIn(f"FfxDx12FGPath={win}\\amd_fidelityfx_framegeneration_dx12.dll\r\n", ini)
        record = json.loads((hx / "helixsr-install.json").read_text())
        self.assertEqual((record["route"], record["optiscaler"]), ("optiscaler", "dxgi.dll"))
        self.assertEqual(record["moved"], [])
        self.assertEqual(record["ini"], "created")
        self.assertEqual(sorted(record["created"]), ["fakenvapi.dll", "fakenvapi.ini"])
        self.assertEqual(record["chosen"], "optiscaler")   # the game has FSR 3.1 too
        self.assertEqual(self.service.read_launch_options([FSR]).get(FSR, ""), "")

        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual(snapshot(self.common / "FsrGame"), before)
        self.assertFalse(hx.exists())

    def test_optiscaler_way_leaves_the_games_own_dxgi_alone(self):
        before = snapshot(self.common / "DlssGame")
        self.service.apply(DLSS, "helixsr:optiscaler")
        self.assertEqual((self.dlss_bin / "dxgi.dll").read_bytes(), b"MZ the game's own dxgi")
        self.assertTrue(helixsr.is_optiscaler(self.dlss_bin / "winmm.dll"))
        self.assertEqual(self.entry(DLSS).status.opti_name, "winmm.dll")
        self.assertEqual(self.service.read_launch_options([DLSS])[DLSS],
                         'WINEDLLOVERRIDES="winmm=n,b" -dx12 %command% -skipintro')
        self.assertFalse(self.entry(DLSS).launch_missing)
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(snapshot(self.common / "DlssGame"), before)
        self.assertEqual(self.service.read_launch_options([DLSS])[DLSS], "-dx12 %command% -skipintro")

    def test_switching_ways_carries_settings_and_puts_everything_back(self):
        before = snapshot(self.common / "FsrGame")
        self.service.apply(FSR, "helixsr:direct")
        self.service.write_settings(FSR, {"Sharpener": "rcas", "Sharpness": "0.4"})
        self.assertTrue((self.win64 / "helixsr.ini").is_file())

        self.service.apply(FSR, "helixsr:optiscaler")
        entry = self.entry(FSR)
        self.assertEqual(entry.status.route, "optiscaler")
        self.assertTrue(entry.status.chosen)
        self.assertEqual(original(self.win64 / "amd_fidelityfx_upscaler_dx12.dll").exists(), False)
        self.assertFalse((self.win64 / "helixsr.ini").exists())
        self.assertEqual(settings.read(self.win64 / "HelixSR" / "helixsr.ini"),
                         {"Sharpener": "rcas", "Sharpness": "0.40"})

        self.service.apply(FSR, "helixsr:dlss")
        self.assertEqual(self.entry(FSR).status.route, "dlss")
        self.assertTrue(helixsr.is_loader(self.win64 / "dxgi.dll"))
        self.assertEqual(helixsr.dll_version(self.win64 / "nvngx.dll"), "1.9.0")
        self.assertFalse((self.win64 / "OptiScaler.ini").exists())
        self.assertEqual(self.service.read_settings(FSR), {"Sharpener": "rcas", "Sharpness": "0.40"})

        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual(set(snapshot(self.common / "FsrGame")) - set(before),
                         {"Game/Binaries/Win64/helixsr.ini"})
        self.service.apply(FSR, "helixsr:direct")
        self.service.uninstall(FSR, remove_settings=True)
        self.assertEqual(snapshot(self.common / "FsrGame"), before)

    def test_repair_after_game_update(self):
        self.service.apply(FSR, "helixsr:direct")
        target = self.win64 / "amd_fidelityfx_upscaler_dx12.dll"
        target.write_bytes(b"MZ ffxCreateContext game FSR v2")   # Steam updated the game
        entry = self.entry(FSR)
        self.assertEqual(entry.status.issues, ["is_game_updated"])
        self.assertTrue(entry.needs_attention)
        self.service.apply(FSR, "helixsr:direct")
        self.assertTrue(helixsr.is_helixsr(target))
        self.assertEqual(original(target).read_bytes(), b"MZ ffxCreateContext game FSR v2")
        self.assertEqual(self.entry(FSR).status.issues, [])

    def test_repair_optiscaler_after_game_restores_its_dxgi(self):
        self.service.apply(FSR, "helixsr:optiscaler")
        (self.win64 / "dxgi.dll").write_bytes(b"MZ the game's own dxgi v2")   # a game update
        self.assertEqual(self.entry(FSR).issues, ["is_files_replaced"])
        self.service.apply(FSR, "helixsr:optiscaler")
        self.assertTrue(helixsr.is_optiscaler(self.win64 / "dxgi.dll"))
        self.assertEqual((self.win64 / "HelixSR" / "backup" / "dxgi.dll").read_bytes(),
                         b"MZ the game's own dxgi v2")
        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual((self.win64 / "dxgi.dll").read_bytes(), b"MZ the game's own dxgi v2")

    def test_update_all(self):
        self.service.apply(FSR, "helixsr:direct")
        self.service.apply(DLSS, "helixsr:optiscaler")
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
        self.service.apply(FSR, "helixsr:direct")
        (self.hx / "amd_fidelityfx_dx12.dll").write_bytes(helixsr_dll("1.9.0", extra=b"wave64" * 10))
        self.assertTrue(self.entry(FSR).outdated)

    def test_refuses_without_built_network(self):
        before = snapshot(self.common)
        raw = make_helixsr(self.root / "raw", built=False)
        self.service.set_helixsr_folder(raw)
        with self.assertRaises(FileNotFoundError):
            self.service.apply(FSR, "helixsr:direct")
        self.assertEqual(snapshot(self.common), before)

    def test_refuses_while_game_runs(self):
        before = snapshot(self.common)
        self.running.return_value = {FSR: [1234]}
        with self.assertRaises(GameRunningError):
            self.service.apply(FSR, "helixsr:direct")
        self.assertEqual(snapshot(self.common), before)

    def test_unavailable_way(self):
        with self.assertRaises(InstallError):
            self.service.apply(DLSS, "helixsr:direct")
        (self.hx / "dlss-loader" / "dxgi.dll").unlink()
        self.service._gpus = [gpu.Gpu("NVIDIA", 0x2684)]
        entry = self.entry(DLSS)
        self.assertEqual([c for c in entry.choices if c.startswith("helixsr")], ["helixsr:optiscaler"])
        self.assertEqual(entry.blocked, {"helixsr:dlss": "blk_no_files"})

    def test_existing_optiscaler_ini_is_edited_and_restored(self):
        own = "[Upscalers]\nDx12Upscaler=xess\n[Libraries]\nFfxDx12Path=auto\n[Menu]\nScale=1.5\n"
        (self.dlss_bin / "OptiScaler.ini").write_text(own)
        self.service.apply(DLSS, "helixsr:optiscaler")
        text = (self.dlss_bin / "OptiScaler.ini").read_text()
        self.assertIn("Dx12Upscaler=fsr31\n", text)
        self.assertIn("Scale=1.5\n", text)
        self.assertIn("FfxDx12SRPath=Z:", text)
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual((self.dlss_bin / "OptiScaler.ini").read_text(), own)

    def test_hand_replaced_amd_fsr_is_kept_on_update(self):
        self.service.apply(DLSS, "helixsr:optiscaler")
        mine = self.dlss_bin / "HelixSR" / "amd_fidelityfx_upscaler_dx12.amd.dll"
        mine.write_bytes(b"MZ ffxCreateContext FSR 4 by hand")
        message = self.service.apply(DLSS, "helixsr:optiscaler")
        self.assertEqual(mine.read_bytes(), b"MZ ffxCreateContext FSR 4 by hand")
        self.assertIn(mine.name, message)

    def test_helixsr_template_ini_removed_user_ini_kept(self):
        self.service.apply(FSR, "helixsr:direct")
        template = self.win64 / "helixsr.ini"
        template.write_text(";Sharpener = nvidia\n")
        record = json.loads((self.win64 / "helixsr-install.json").read_text())
        record["ini_made"] = installer.sha256(template)   # made by HelixSR's setup, untouched
        (self.win64 / "helixsr-install.json").write_text(json.dumps(record))
        self.service.uninstall(FSR, remove_settings=False)
        self.assertFalse(template.exists())


class FsrTest(Base):
    def setUp(self):
        super().setUp()
        make_components(self.root / "components")
        self.gpus = [gpu.Gpu("AMD", 0x744c, (11, 0, 0))]   # an RX 7900

    def localconfig(self) -> str:
        return (self.steam / "userdata/12345/config/localconfig.vdf").read_text()

    def test_needs_downloads_first(self):
        before = snapshot(self.common)
        components.remove(components.FSR4["dgpu"], self.root / "components")
        self.assertEqual(self.service.plan(DLSS, "fsr4:exact").downloads,
                         [components.FSR4["dgpu"]])
        with self.assertRaises(NeedsDownloadError) as caught:
            self.service.apply(DLSS, "fsr4:exact")
        self.assertEqual(caught.exception.missing, [components.FSR4["dgpu"]])
        self.assertEqual(snapshot(self.common), before)

    def test_choices_follow_the_gpu(self):
        self.assertEqual(self.entry(FSR).choices,
                         ["helixsr:direct", "helixsr:optiscaler", "helixsr:dlss",
                          "fsr4:exact", "fsr4:lossy", "fsr3"])
        self.service._gpus = [gpu.Gpu("AMD", 0x7550, (12, 0, 1))]   # RX 9070: RDNA 4
        self.assertEqual([c for c in self.entry(FSR).choices if c.startswith("fsr")],
                         ["fsr4:native", "fsr3"])
        self.assertFalse(self.service.force_int8())
        self.service._gpus = [gpu.Gpu("AMD", 0x163f, (10, 3, 3), apu=True)]   # Steam Deck
        self.assertEqual(self.service.needed_components("fsr4:lossy")[1], components.FSR4["igpu"])
        self.service.fsr4_build_setting = "dgpu"
        self.assertEqual(self.service.needed_components("fsr4:lossy")[1], components.FSR4["dgpu"])
        self.assertEqual(self.entry(PLAIN).choices, [])

    def test_fsr4_install_switch_and_remove_put_everything_back(self):
        before = snapshot(self.common / "DlssGame")
        options = self.localconfig()
        plan = self.service.plan(DLSS, "fsr4:exact")
        self.assertEqual((plan.opti_name, plan.opti_reason), ("winmm.dll", "taken"))
        self.assertEqual(plan.launch_after, 'WINEDLLOVERRIDES="winmm=n,b" -dx12 %command% -skipintro')

        self.service.apply(DLSS, "fsr4:exact")
        sc = self.dlss_bin / "ScalerAssistant"
        self.assertEqual((self.dlss_bin / "dxgi.dll").read_bytes(), b"MZ the game's own dxgi")
        self.assertTrue(helixsr.is_optiscaler(self.dlss_bin / "winmm.dll"))
        self.assertEqual((sc / "amd_fidelityfx_upscaler_dx12.dll").read_bytes(),
                         b"MZ ffxCreateContext fsr4-dgpu exact/amd_fidelityfx_upscaler_dx12.dll")
        ini = (self.dlss_bin / "OptiScaler.ini").read_bytes().decode()
        win = "Z:" + str(sc.resolve()).replace("/", "\\")
        for line in ("Dx12Upscaler=fsr31", "Dx11Upscaler=fsr31_12", "VulkanUpscaler=fsr31_12",
                     "UpscalerIndex=0", "Fsr4Update=true", "Fsr4ForceEnableInt8=true",
                     f"FfxDx12Path={win}\\amd_fidelityfx_dx12.dll",
                     f"FfxDx12SRPath={win}\\amd_fidelityfx_upscaler_dx12.dll",
                     f"FfxDx12FGPath={win}\\amd_fidelityfx_framegeneration_dx12.dll",
                     f"FfxVkPath={win}\\amd_fidelityfx_vk.dll", "Scale=auto"):
            self.assertIn(line + "\r\n", ini)
        entry = self.entry(DLSS)
        self.assertEqual((entry.status.choice, entry.status.opti_name, entry.outdated, entry.issues),
                         ("fsr4:exact", "winmm.dll", False, []))
        self.assertEqual(entry.launch_options,
                         'WINEDLLOVERRIDES="winmm=n,b" -dx12 %command% -skipintro')

        self.service.apply(DLSS, "fsr4:lossy")
        self.assertEqual((sc / "amd_fidelityfx_upscaler_dx12.dll").read_bytes(),
                         b"MZ ffxCreateContext fsr4-dgpu lossy/amd_fidelityfx_upscaler_dx12.dll")
        self.service.apply(DLSS, "fsr3")
        ini = (self.dlss_bin / "OptiScaler.ini").read_text()
        for line in ("Dx11Upscaler=fsr31\n", "VulkanUpscaler=fsr31\n", "UpscalerIndex=1\n",
                     "Fsr4Update=false\n", "Fsr4ForceEnableInt8=auto\n"):
            self.assertIn(line, ini)
        self.assertEqual((sc / "amd_fidelityfx_upscaler_dx12.dll").read_bytes(),
                         b"MZ ffxCreateContext optiscaler amd_fidelityfx_upscaler_dx12.dll")
        self.assertEqual(self.entry(DLSS).launch_options.count("winmm=n,b"), 1)

        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(snapshot(self.common / "DlssGame"), before)
        self.assertEqual(self.localconfig(), options)
        self.assertIsNone(self.entry(DLSS).status.route)

    def test_users_launch_options_are_never_rewritten(self):
        mine = 'PROTON_LOG=1 WINEDLLOVERRIDES="winmm=b;xinput1_3=n,b" gamemoderun %command% -novid'
        write_launch_options(self.steam, {DLSS: mine})
        self.service.apply(DLSS, "fsr3")
        # winmm is kept builtin by the user: OptiScaler takes the next free name instead.
        self.assertEqual(self.entry(DLSS).status.opti_name, "version.dll")
        self.assertEqual(self.entry(DLSS).launch_options,
                         'PROTON_LOG=1 WINEDLLOVERRIDES="winmm=b;xinput1_3=n,b;version=n,b" '
                         'gamemoderun %command% -novid')
        # The user edits the options while OptiScaler is installed.
        edited = self.entry(DLSS).launch_options.replace("-novid", "-novid -fullscreen")
        write_launch_options(self.steam, {DLSS: edited})
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(self.service.read_launch_options([DLSS])[DLSS],
                         'PROTON_LOG=1 WINEDLLOVERRIDES="winmm=b;xinput1_3=n,b" '
                         'gamemoderun %command% -novid -fullscreen')

    def test_an_override_the_user_already_has_is_left_to_the_user(self):
        mine = 'WINEDLLOVERRIDES="winmm=n,b" %command%'
        write_launch_options(self.steam, {DLSS: mine})
        self.service.apply(DLSS, "fsr3")
        self.assertEqual(self.entry(DLSS).launch_options, mine)
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(self.service.read_launch_options([DLSS])[DLSS], mine)

    def test_repair_puts_a_removed_launch_option_back(self):
        self.service.apply(DLSS, "fsr3")
        write_launch_options(self.steam, {DLSS: "-dx12 %command% -skipintro"})   # removed by hand
        entry = self.entry(DLSS)
        self.assertTrue(entry.launch_missing)
        self.assertEqual(entry.issues, ["is_launch_missing"])
        self.service.apply(DLSS, "fsr3")
        self.assertFalse(self.entry(DLSS).launch_missing)
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(self.service.read_launch_options([DLSS])[DLSS], "-dx12 %command% -skipintro")

    def test_renaming_optiscaler_moves_it_and_its_launch_option(self):
        before = snapshot(self.common / "DlssGame")
        self.service.apply(DLSS, "fsr4:exact")
        self.service.set_opti_name(DLSS, "version.dll")
        self.service.apply(DLSS, "fsr4:exact")
        self.assertFalse((self.dlss_bin / "winmm.dll").exists())
        self.assertTrue(helixsr.is_optiscaler(self.dlss_bin / "version.dll"))
        self.assertEqual(self.entry(DLSS).launch_options,
                         'WINEDLLOVERRIDES="version=n,b" -dx12 %command% -skipintro')
        self.service.uninstall(DLSS, remove_settings=False)
        self.assertEqual(snapshot(self.common / "DlssGame"), before)
        self.assertEqual(self.service.read_launch_options([DLSS])[DLSS], "-dx12 %command% -skipintro")

    def test_steam_must_close_before_anything_changes(self):
        before = snapshot(self.common)
        self.steam_running.return_value = True
        with self.assertRaises(SteamMustCloseError):
            self.service.apply(DLSS, "fsr4:exact")
        self.assertEqual(snapshot(self.common), before)
        # dxgi.dll needs no launch option: Steam may keep running.
        self.service.apply(FSR, "fsr4:exact")
        self.assertEqual(self.entry(FSR).status.opti_name, "dxgi.dll")

    def test_switching_between_helixsr_and_fsr(self):
        before = snapshot(self.common / "FsrGame")
        self.service.apply(FSR, "helixsr:direct")
        self.service.apply(FSR, "fsr4:exact")
        status = self.entry(FSR).status
        self.assertEqual((status.route, status.choice), ("scaler", "fsr4:exact"))
        self.assertEqual((self.win64 / "amd_fidelityfx_upscaler_dx12.dll").read_bytes(),
                         b"MZ ffxCreateContext game FSR")   # the game's own DLL is back
        self.service.apply(FSR, "helixsr:optiscaler")
        self.assertEqual(self.entry(FSR).status.choice, "helixsr:optiscaler")
        self.assertFalse((self.win64 / "ScalerAssistant").exists())
        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual(snapshot(self.common / "FsrGame"), before)

    def test_hand_installed_optiscaler_is_kept_and_put_back(self):
        (self.win64 / "dxgi.dll").write_bytes(b"MZ OptiScaler 0.7 set up by hand")
        own_ini = "[Upscalers]\nDx12Upscaler=xess\n"
        (self.win64 / "OptiScaler.ini").write_text(own_ini)
        before = snapshot(self.common / "FsrGame")
        self.assertEqual(self.service.plan(FSR, "fsr3").opti_reason, "installed")
        self.service.apply(FSR, "fsr3")
        self.assertEqual((self.win64 / "ScalerAssistant/backup/dxgi.dll").read_bytes(),
                         b"MZ OptiScaler 0.7 set up by hand")
        self.service.uninstall(FSR, remove_settings=False)
        self.assertEqual(snapshot(self.common / "FsrGame"), before)

    def test_outdated_when_the_build_changes(self):
        self.service.apply(DLSS, "fsr4:exact")
        self.assertFalse(self.entry(DLSS).outdated)
        self.service.fsr4_build_setting = "igpu"
        self.assertTrue(self.entry(DLSS).outdated)
        self.service.update_all()
        self.assertEqual((self.dlss_bin / "ScalerAssistant/amd_fidelityfx_upscaler_dx12.dll").read_bytes(),
                         b"MZ ffxCreateContext fsr4-igpu exact/amd_fidelityfx_upscaler_dx12.dll")
        self.assertFalse(self.entry(DLSS).outdated)

    def test_leaving_an_install_that_displaced_the_games_dxgi(self):
        self.service.set_opti_name(DLSS, "dxgi.dll")   # by hand: over the game's own dxgi.dll
        self.service.apply(DLSS, "helixsr:optiscaler")
        self.assertTrue(self.entry(DLSS).status.opti_over_foreign)
        self.service.set_opti_name(DLSS, None)
        self.service.apply(DLSS, "fsr3")
        self.assertEqual(self.entry(DLSS).status.opti_name, "winmm.dll")
        self.assertEqual((self.dlss_bin / "dxgi.dll").read_bytes(), b"MZ the game's own dxgi")

    def test_helixsr_setup_dropin_in_our_folder_is_taken_out(self):
        self.service.apply(DLSS, "fsr4:exact")
        with_fsr4 = snapshot(self.common / "DlssGame")
        sc = self.dlss_bin / "ScalerAssistant"
        upscaler = sc / "amd_fidelityfx_upscaler_dx12.dll"
        # What HelixSR's own setup (FSR way) does with a game's FSR 3.1 DLL.
        os.replace(upscaler, original(upscaler))
        upscaler.write_bytes(helixsr_dll("1.8.1"))
        (sc / "helixsr-install.json").write_text(json.dumps(
            {"helixsr": "1.8.1", "files": [upscaler.name], "route": "direct", "ini_made": None}))
        self.assertEqual(self.entry(DLSS).issues, ["is_files_replaced"])
        message = self.service.apply(DLSS, "fsr4:exact")
        self.assertIn("ScalerAssistant", message)
        self.assertEqual(snapshot(self.common / "DlssGame"), with_fsr4)

    def test_rdna4_gets_amds_own_fsr4(self):
        self.service._gpus = [gpu.Gpu("AMD", 0x7550, (12, 0, 1))]
        self.service.apply(FSR, "fsr4:native")
        ini = (self.win64 / "OptiScaler.ini").read_text()
        self.assertIn("Fsr4ForceEnableInt8=auto\n", ini)
        self.assertIn("UpscalerIndex=0\n", ini)
        self.assertEqual((self.win64 / "ScalerAssistant/amd_fidelityfx_upscaler_dx12.dll").read_bytes(),
                         b"MZ ffxCreateContext optiscaler amd_fidelityfx_upscaler_dx12.dll")


class LaunchOptionsTest(unittest.TestCase):
    CASES = [
        ("", 'WINEDLLOVERRIDES="winmm=n,b" %command%'),
        ("%command%", 'WINEDLLOVERRIDES="winmm=n,b" %command%'),
        ("-dx12", 'WINEDLLOVERRIDES="winmm=n,b" %command% -dx12'),
        ("gamemoderun %command% -dx12", 'WINEDLLOVERRIDES="winmm=n,b" gamemoderun %command% -dx12'),
        ('WINEDLLOVERRIDES="xinput1_3=n,b" %command%',
         'WINEDLLOVERRIDES="xinput1_3=n,b;winmm=n,b" %command%'),
        ("WINEDLLOVERRIDES=d3dcompiler_47=n %command%",
         "WINEDLLOVERRIDES=d3dcompiler_47=n;winmm=n,b %command%"),
        ("WINEDLLOVERRIDES='a=n;' %command%", "WINEDLLOVERRIDES='a=n;winmm=n,b' %command%"),
    ]

    def test_add_and_remove_round_trip(self):
        for before, after in self.CASES:
            with self.subTest(before=before):
                added, record = lo.add(before, "winmm.dll")
                self.assertEqual(added, after)
                self.assertEqual(lo.remove(added, record), before)

    def test_remove_after_the_user_edited(self):
        added, record = lo.add('WINEDLLOVERRIDES="a=n" %command%', "winmm.dll")
        edited = added.replace("%command%", "%command% -novid")
        self.assertEqual(lo.remove(edited, record), 'WINEDLLOVERRIDES="a=n" %command% -novid')
        added, record = lo.add("-dx12", "version.dll")
        edited = "PROTON_LOG=1 " + added
        self.assertEqual(lo.remove(edited, record), "PROTON_LOG=1 %command% -dx12")

    def test_existing_entries(self):
        self.assertEqual(lo.add('WINEDLLOVERRIDES="winmm=n,b" %command%', "winmm.dll"),
                         ('WINEDLLOVERRIDES="winmm=n,b" %command%', None))
        with self.assertRaises(lo.OverrideConflict):
            lo.add('WINEDLLOVERRIDES="winmm=b" %command%', "winmm.dll")
        self.assertEqual(lo.blocked_names('WINEDLLOVERRIDES="winmm,version=b;dxgi=n" %command%'),
                         {"winmm.dll", "version.dll"})
        self.assertFalse(lo.needs_override("dxgi.dll") or lo.needs_override("d3d12.dll"))
        self.assertTrue(lo.needs_override("winmm.dll"))


class OptiScalerTest(unittest.TestCase):
    def test_choose_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp)
            self.assertEqual(optiscaler.choose_name(exe, "dx12", ["Game"]), ("dxgi.dll", "default"))
            self.assertEqual(optiscaler.choose_name(exe, "vulkan", ["Game"]), ("winmm.dll", "vulkan"))
            self.assertEqual(optiscaler.choose_name(exe, "dx12", ["Forspoken™"]),
                             ("d3d12.dll", "listed"))
            self.assertEqual(optiscaler.choose_name(
                exe, "dx12", ["Grand Theft Auto: Vice City - The Definitive Edition"]),
                ("d3d12.dll", "listed"))
            self.assertEqual(optiscaler.choose_name(exe, "dx12", ["Game"], blocked={"dxgi.dll"}),
                             ("winmm.dll", "taken"))
            (exe / "dxgi.dll").write_bytes(b"MZ ReShade")
            self.assertEqual(optiscaler.choose_name(exe, "dx12", ["Game"]), ("winmm.dll", "taken"))
            self.assertEqual(optiscaler.choose_name(exe, "dx12", ["Game"], "dbghelp.dll"),
                             ("dbghelp.dll", "user"))
            (exe / "version.dll").write_bytes(b"MZ OptiScaler")
            self.assertEqual(optiscaler.choose_name(exe, "dx12", ["Game"]), ("version.dll", "installed"))

    def test_configure_uses_the_values_this_version_lists(self):
        files = {"upscaler": Path("/g/ScalerAssistant/up.dll")}
        text = optiscaler.configure(OPTI_INI_FULL, "fsr4", files, force_int8=True)
        self.assertIn("Dx11Upscaler=fsr31_12\r\n", text)
        self.assertIn("FfxDx12SRPath=Z:\\g\\ScalerAssistant\\up.dll\r\n", text)
        newer = OPTI_INI_FULL.replace("fsr31_12", "ffx_12").replace("fsr31 (", "ffx (")
        text = optiscaler.configure(newer, "fsr4", files, force_int8=False)
        self.assertIn("Dx11Upscaler=ffx_12\r\n", text)
        self.assertIn("Dx12Upscaler=ffx\r\n", text)
        self.assertIn("Fsr4ForceEnableInt8=auto\r\n", text)


class DetectTest(unittest.TestCase):
    def test_graphics_api_from_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "game.exe"
            exe.write_bytes(pe_exe(["KERNEL32.dll", "d3d11.dll", "d3d12.dll"]))
            self.assertEqual(imported_dlls(exe), ["kernel32.dll", "d3d11.dll", "d3d12.dll"])
            self.assertEqual(graphics_api([exe]), "dx12")
            exe.write_bytes(pe_exe(["KERNEL32.dll", "vulkan-1.dll"]))
            self.assertEqual(graphics_api([exe]), "vulkan")
            exe.write_bytes(b"MZ not really")
            self.assertEqual(graphics_api([exe]), "")

    def test_helixsr_only_for_dx12(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "VkGame"
            game.mkdir()
            (game / "VkGame.exe").write_bytes(pe_exe(["vulkan-1.dll"]))
            (game / "nvngx_dlss.dll").write_bytes(b"MZ NVIDIA DLSS")
            layout = detect_layout(game)
            self.assertEqual(layout.api, "vulkan")
            self.assertEqual(layout.ways(), [])
            self.assertTrue(layout.optiscaler_possible)


class ComponentsTest(unittest.TestCase):
    def test_fetch_checks_size_and_sha256(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zipped:
            zipped.writestr("keep/a.dll", b"MZ a")
            zipped.writestr("other.txt", b"not kept")
        data = buffer.getvalue()
        good = components.Component("test", "1", "https://example.invalid/x.zip",
                                    hashlib.sha256(data).hexdigest(), len(data), "zip",
                                    ("keep/a.dll",), "", "")
        opener = lambda request, timeout: io.BytesIO(data)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = components.fetch(good, root=root, opener=opener)
            self.assertEqual((folder / "keep/a.dll").read_bytes(), b"MZ a")
            self.assertFalse((folder / "other.txt").exists())
            self.assertTrue(components.ready(good, root))
            bad = components.Component("bad", "1", good.url, "0" * 64, len(data), "zip",
                                       ("keep/a.dll",), "", "")
            with self.assertRaises(components.ComponentError):
                components.fetch(bad, root=root, opener=opener)
            self.assertFalse(components.folder(bad, root).exists())


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
            set_ini_value("[S]\nA=1\nA=2\n", "S", "A", "3")
        # The same key name in another section is not touched.
        text = set_ini_value("[XeSS]\nDebugView=auto\n\n[FSR]\nDebugView=auto\n\n[Menu]\n",
                             "FSR", "DebugView", "true")
        self.assertEqual(text, "[XeSS]\nDebugView=auto\n\n[FSR]\nDebugView=true\n\n[Menu]\n")
        text = set_ini_value("[FSR]\nA=1\n\n[Menu]\n", "FSR", "B", "2")
        self.assertEqual(text, "[FSR]\nA=1\nB=2\n\n[Menu]\n")


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
                             ["AMD RDNA 3 (gfx1100)", "AMD RDNA 2 APU (gfx1033)", "NVIDIA (2684)"])
            self.assertTrue(found[0].rdna3_or_newer)
            self.assertFalse(found[1].rdna3_or_newer)
            self.assertIsNone(found[2].supported)
            self.assertTrue(found[1].apu)   # the Steam Deck's graphics
            self.assertEqual(gpu.main_gpu(found), found[0])
            self.assertEqual([gpu.fsr4_pack(g) for g in found], ["dgpu", "igpu", "dgpu"])
            self.assertIsNone(gpu.fsr4_pack(gpu.Gpu("AMD", 0x7550, (12, 0, 1))))


if __name__ == "__main__":
    unittest.main()


class GpuChoicesTest(Base):
    def test_dlss_way_only_with_a_geforce(self):
        self.service._gpus = [gpu.Gpu("AMD", 0x744c, (11, 0, 0))]
        entry = self.entry(DLSS)
        self.assertIn("dlss", entry.ways)
        self.assertNotIn("helixsr:dlss", entry.choices)
        self.assertEqual(entry.blocked, {"helixsr:dlss": "blk_dlss_gpu"})
        with self.assertRaises(InstallError):
            self.service.plan(DLSS, "helixsr:dlss")
        with self.assertRaises(InstallError):
            self.service.apply(DLSS, "helixsr:dlss")
        self.service._gpus = [gpu.Gpu("Intel", 0x56a0, None, apu=False)]
        self.assertIn("helixsr:dlss", self.entry(DLSS).blocked)
        self.service._gpus = [gpu.Gpu("NVIDIA", 0x2684)]
        self.assertIn("helixsr:dlss", self.entry(DLSS).choices)
        self.assertEqual(self.entry(DLSS).blocked, {})

    def test_lossy_recommended_on_built_in_and_intel_graphics(self):
        cases = [(gpu.Gpu("AMD", 0x163f, (10, 3, 3), apu=True), "fsr4:lossy"),     # Steam Deck
                 (gpu.Gpu("AMD", 0x1586, (11, 5, 1), apu=True), "fsr4:lossy"),     # Ryzen AI MAX
                 (gpu.Gpu("Intel", 0x7d55, None, apu=True), "fsr4:lossy"),
                 (gpu.Gpu("AMD", 0x744c, (11, 0, 0)), None),                       # RX 7900
                 (gpu.Gpu("AMD", 0x7550, (12, 0, 1)), None)]                       # RX 9070
        for card, want in cases:
            self.service._gpus = [card]
            self.assertEqual(self.entry(DLSS).recommended, want, card)
        self.service._gpus = []
        self.assertIsNone(self.entry(DLSS).recommended)


class ModernHelixSRTest(Base):
    """HelixSR 2.0: HelixSR-fsrfg, HelixSR Scaler, installed through the release's installer."""

    def setUp(self):
        super().setUp()
        from tests.fakes import make_helixsr_modern
        self.hx2 = make_helixsr_modern(self.root / "HelixSR-2.0.0")
        make_components(self.root / "components")
        self.service._gpus = [gpu.Gpu("AMD", 0x744c, (11, 0, 0))]

    def test_folder_and_ways(self):
        folder = helixsr.inspect(self.hx2)
        self.assertTrue(folder.modern and folder.ready)
        self.assertEqual((folder.version, folder.scaler_version()), ("2.0.0", "1.1.0"))
        self.assertTrue(helixsr.looks_like_helixsr(self.hx2))
        # picking the HelixSR-fsrfg folder itself works too
        chosen = self.service.set_helixsr_folder(self.hx2 / "HelixSR-fsrfg")
        self.assertEqual(chosen.path, self.hx2.resolve())
        self.assertEqual(self.entry(FSR).ways, ["hscaler", "direct"])
        self.assertEqual(self.entry(DLSS).ways, ["hscaler"])
        from tests.fakes import make_helixsr_modern
        unbuilt = make_helixsr_modern(self.root / "raw", built=False)
        self.assertEqual(helixsr.inspect(unbuilt).problem, "hx_not_built")

    def test_hscaler_install_switch_and_remove(self):
        self.service.set_helixsr_folder(self.hx2)
        (self.dlss_bin / "dxgi.dll").write_bytes(b"MZ ReShade")
        before = snapshot(self.common / "DlssGame")
        write_launch_options(self.steam, {DLSS: "-dx12 %command%"})
        message = self.service.apply(DLSS, "helixsr:hscaler")
        status = self.entry(DLSS).status
        self.assertEqual((status.choice, status.version), ("helixsr:hscaler", "2.0.0"), message)
        self.assertNotEqual(status.opti_name, "dxgi.dll")   # ReShade's file stays
        self.assertTrue((self.dlss_bin / "HelixSR-fsrfg" / "amd_fidelityfx_dx12.dll").is_file())
        calls = (self.hx2 / "bridge-calls.txt").read_text()
        self.assertIn(f"--scaler-name {status.opti_name}", calls)
        self.assertIn("--anticheat-ok yes", calls)          # DlssGame has Easy Anti-Cheat
        stem = status.opti_name.rsplit(".", 1)[0]
        self.assertIn(f'{stem}=n,b', self.entry(DLSS).launch_options)
        self.assertEqual(self.entry(DLSS).issues, [])
        # an earlier HelixSR way is updated to HelixSR Scaler
        self.assertEqual(self.service.plan(DLSS, "helixsr:optiscaler").choice, "helixsr:hscaler")
        # switching to FSR 3 takes HelixSR Scaler out first (its record, the game's files back)
        self.service.apply(DLSS, "fsr3")
        self.assertEqual(self.entry(DLSS).status.choice, "fsr3")
        self.assertFalse((self.dlss_bin / "HelixSR-Scaler.files").exists())
        self.assertFalse((self.dlss_bin / "HelixSR-fsrfg").exists())
        self.service.uninstall(DLSS, False)
        self.assertEqual(snapshot(self.common / "DlssGame"), before)
        self.assertEqual(self.entry(DLSS).launch_options, "-dx12 %command%")

    def test_scan_ignores_helixsr_scaler_files(self):
        self.service.set_helixsr_folder(self.hx2)
        self.service.apply(DLSS, "helixsr:hscaler")
        self.service.scan()
        self.assertEqual(self.entry(DLSS).layout.fsr_targets, [])
        self.assertEqual(self.entry(DLSS).status.route, "hscaler")


class AntiCheatTest(unittest.TestCase):
    def test_vendors_helixsr_knows(self):
        import tempfile
        from scaler_assistant.games import detect_layout
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "Sora"
            (game / "bin" / "equ8_conf").mkdir(parents=True)
            (game / "bin" / "game.exe").write_bytes(b"MZ")
            (game / "bin" / "nvngx_dlss.dll").write_bytes(b"MZ")
            (game / "bin" / "Game_BE.exe").write_bytes(b"MZ")
            self.assertEqual(detect_layout(game).anti_cheat, ["BattlEye", "EQU8"])


class FrameGenerationTest(Base):
    """HelixSR 2.0's frame generation switch: HelixSR Scaler in a game with DLSS Frame Generation."""

    def setUp(self):
        super().setUp()
        from tests.fakes import make_helixsr_modern
        self.hx2 = make_helixsr_modern(self.root / "HelixSR-2.0.0", fg=True)
        make_components(self.root / "components")
        self.service._gpus = [gpu.Gpu("AMD", 0x744c, (11, 0, 0))]
        self.service.set_helixsr_folder(self.hx2)
        (self.dlss_bin / "sl.dlss_g.dll").write_bytes(b"MZ Streamline DLSS-G")
        self.service.scan()

    def calls(self):
        return (self.hx2 / "bridge-calls.txt").read_text()

    def test_offered_only_with_helixsr_scaler_and_dlss_fg(self):
        self.assertTrue(self.entry(DLSS).layout.dlss_fg)
        self.assertFalse(self.entry(FSR).layout.dlss_fg)
        self.assertIsNone(self.entry(DLSS).fg)              # nothing installed yet
        self.service.apply(DLSS, "fsr3")
        self.assertIsNone(self.entry(DLSS).fg)              # not HelixSR
        self.service.apply(DLSS, "helixsr:hscaler")
        entry = self.entry(DLSS)
        self.assertEqual((entry.fg, entry.fg_block), (False, None))
        self.assertNotIn("--fg", self.calls())               # a new install leaves it off
        self.service.apply(FSR, "helixsr:hscaler")
        self.assertIsNone(self.entry(FSR).fg)                # no DLSS Frame Generation there
        with self.assertRaises(installer.InstallError):
            self.service.set_frame_generation(FSR, True)

    def test_switch_on_and_off(self):
        self.service.apply(DLSS, "helixsr:hscaler")
        before_fg = self.calls()
        message = self.service.set_frame_generation(DLSS, True)
        self.assertIn("scaler-fg --game", self.calls()[len(before_fg):])
        self.assertIn("--on true", self.calls())
        self.assertIn("HelixSR: fake bridge", message)
        status = self.entry(DLSS).status
        self.assertEqual((status.fg, status.fg_files, self.entry(DLSS).fg), (True, True, True))
        # a new OptiScaler file name means a fresh install: frame generation stays on
        self.service.set_opti_name(DLSS, "winmm.dll")
        self.service.apply(DLSS, "helixsr:hscaler")
        self.assertIn("--scaler-name winmm.dll", self.calls())
        self.assertIn("--fg on", self.calls())
        self.assertTrue(self.entry(DLSS).fg)
        self.service.set_frame_generation(DLSS, False)
        self.assertIn("--on false", self.calls())
        self.assertFalse(self.entry(DLSS).fg)
        self.service.uninstall(DLSS, False)
        self.assertFalse((self.dlss_bin / "HelixSR-fsrfg").exists())

    def test_not_built_greys_it_out(self):
        for name in ("_nvngx.dll", "nvngx_dlssg.dll", "hxfg_data.bin"):
            (self.hx2 / "HelixSR-fsrfg" / "helixsr-fg" / name).unlink()
        self.assertFalse(helixsr.inspect(self.hx2).fg_ready)
        self.service.apply(DLSS, "helixsr:hscaler")
        entry = self.entry(DLSS)
        self.assertEqual((entry.fg, entry.fg_block), (False, "fg_not_built_short"))
        with self.assertRaises(installer.InstallError):
            self.service.set_frame_generation(DLSS, True)
        self.assertNotIn("scaler-fg", self.calls())


class TlsContextTest(unittest.TestCase):
    """Downloads trust the system's CAs even in a Python that can't find them (Decky Loader)."""

    def test_system_bundle_when_python_has_none(self):
        import ssl
        bundle = next((f for f in components.CA_FILES if os.path.isfile(f)), None)
        if bundle is None:
            self.skipTest("no system CA bundle here")
        empty = lambda *a, **k: ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        paths = ssl.DefaultVerifyPaths(None, None, "SSL_CERT_FILE", "/nowhere/cert.pem",
                                       "SSL_CERT_DIR", "/nowhere/certs")
        with mock.patch.object(components, "_context", None), \
                mock.patch("ssl.create_default_context", empty), \
                mock.patch("ssl.get_default_verify_paths", return_value=paths), \
                mock.patch.dict(os.environ, {}, clear=False) as env:
            env.pop("SSL_CERT_FILE", None)
            context = components.tls_context()
        self.assertGreater(context.cert_store_stats()["x509_ca"], 0)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)


class BridgeRunnerTest(unittest.TestCase):
    """HelixSR's installer runs with unreadable folders counting as not there."""

    def test_permission_error_is_not_there(self):
        import subprocess, sys, tempfile
        from scaler_assistant import hxbridge
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "bridge.py"
            script.write_text(
                "import pathlib, sys\n"
                "def denied(self, *a, **k):\n"
                "    raise PermissionError(13, 'Permission denied', str(self))\n"
                "pathlib.Path.stat = denied\n"
                "pathlib.Path.lstat = denied\n"
                "p = pathlib.Path(sys.argv[1])\n"
                "print(p.exists(), p.is_file(), p.is_dir(), sys.argv[1:], __name__)\n"
                "sys.exit(3)\n")
            done = subprocess.run([sys.executable, "-I", "-c", hxbridge._RUNNER, str(script),
                                   "/x/HelixSR/helixsr-install.json", "games"],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 3, done.stderr)
            self.assertEqual(done.stdout.strip(),
                             "False False False ['/x/HelixSR/helixsr-install.json', 'games'] __main__")


class HelixSR19Test(Base):
    def test_ways_without_their_files_are_greyed_out(self):
        """HelixSR 1.9 releases carry neither optiscaler/ nor dlss-loader/: only the FSR way."""
        import shutil
        self.service._gpus = [gpu.Gpu("NVIDIA", 0x2684)]
        shutil.rmtree(self.hx / "optiscaler")
        shutil.rmtree(self.hx / "dlss-loader")
        fsr = self.entry(FSR)
        self.assertEqual([c for c in fsr.choices if c.startswith("helixsr")], ["helixsr:direct"])
        self.assertEqual(fsr.blocked, {"helixsr:optiscaler": "blk_no_files",
                                       "helixsr:dlss": "blk_no_files"})
        with self.assertRaises(InstallError):
            self.service.apply(DLSS, "helixsr:optiscaler")
        self.service.apply(FSR, "helixsr:direct")
        self.assertEqual(self.entry(FSR).status.choice, "helixsr:direct")


class SandboxTest(unittest.TestCase):
    def test_proc_snapshot_finds_steam_games(self):
        """The host-side snapshot Flatpak uses (run here directly) keeps what runtime reads."""
        import subprocess, sys, time
        from scaler_assistant import sandbox
        from scaler_assistant.runtime import running_app_ids
        game = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                env=dict(os.environ, SteamAppId="424242"))
        self.addCleanup(game.kill)
        time.sleep(0.3)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "proc"
            subprocess.run(["sh", "-c", sandbox._SNAPSHOT, "snapshot", str(dest)], check=True)
            self.assertTrue((dest / "stat").is_file())
            self.assertIn(game.pid, running_app_ids(dest).get(424242, []))
            self.assertTrue((dest / str(game.pid) / "maps").is_file())
        self.assertFalse(sandbox.in_flatpak())
        self.assertEqual(sandbox.host(["steam"]), ["steam"])
        self.assertEqual(sandbox.proc_root(), Path("/proc"))


class ApiDetectionTest(unittest.TestCase):
    def make(self, imports, files, mention=b""):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        game = Path(tmp.name) / "Game"
        (game / "bin").mkdir(parents=True)
        (game / "bin" / "game.exe").write_bytes(pe_exe(["KERNEL32.dll", *imports]) + mention + b"\0" * 64)
        for name in files:
            (game / "bin" / name).write_bytes(b"MZ " + name.encode())
        return detect_layout(game).api

    def test_dx12_renderer_wins_over_static_d3d11_or_vulkan_imports(self):
        # D3D11 linked statically, D3D12 loaded at run time; FSR 3.1 has only a D3D12 back end
        self.assertEqual(self.make(["d3d11.dll"], ["nvngx_dlss.dll", "amd_fidelityfx_upscaler_dx12.dll"]), "dx12")
        self.assertEqual(self.make(["d3d11.dll"], ["nvngx_dlss.dll"], b"LoadLibrary d3d12.dll"), "dx12")
        self.assertEqual(self.make(["d3d11.dll"], ["nvngx_dlss.dll"]), "dx11")
        self.assertEqual(self.make(["vulkan-1.dll"], ["nvngx_dlss.dll", "libxess.dll"]), "vulkan")
        self.assertEqual(self.make(["vulkan-1.dll"], ["amd_fidelityfx_dx12.dll"]), "dx12")


class LayoutCacheTest(Base):
    def test_old_scan_results_are_redone_once(self):
        self.service.state["games"][0]["layout"]["api"] = "dx11"
        self.service.state.pop("layout_version")
        self.service.scan(rescan_library=False)
        self.assertNotIn("dx11", {g["layout"]["api"] for g in self.service.state["games"]})
        self.assertEqual(self.service.state["layout_version"], LAYOUT_VERSION)
