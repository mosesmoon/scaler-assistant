"""The Steam Deck (Decky) plugin: its bridge to the service and its backend entry point."""

import asyncio
import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from unittest import mock

from scaler_assistant import gpu, i18n
from scaler_assistant.deck import DeckBridge, plain, steam_language

from tests.fakes import make_components, snapshot, write_launch_options
from tests.test_core import DLSS, FSR, PLAIN, Base

REPO = Path(__file__).resolve().parent.parent


class DeckBridgeTest(Base):
    def setUp(self):
        super().setUp()
        self.service._gpus = [gpu.Gpu("AMD", 0x163f, (10, 3, 3), apu=True)]   # Steam Deck
        self.bridge = DeckBridge(self.service)
        self.bridge.set_steam_language("english")
        self.addCleanup(i18n.set_language, "en")

    def game(self, overview, app_id):
        return next(g for g in overview["games"] if g["app_id"] == app_id)

    def test_overview_is_plain_json(self):
        overview = self.bridge.overview()
        json.dumps(overview)
        self.assertEqual({g["app_id"] for g in overview["games"]}, {FSR, DLSS})
        self.assertEqual(overview["unsupported"], 1)
        dlss = self.game(overview, DLSS)
        self.assertEqual(dlss["anti_cheat"], ["Easy Anti-Cheat"])
        self.assertEqual((dlss["fg"], dlss["fg_block"]), (None, ""))
        self.assertIn("fsr4:lossy", [c["id"] for c in dlss["choices"]])
        # DX12 only for HelixSR: offered for FSR's game, not explained away
        self.assertEqual(overview["downloads"]["missing"], ["optiscaler", "fsr4-igpu-rdna2"])
        self.assertNotIn("<", json.dumps(self.bridge.strings()))

    def test_choose_fsr4_lossy_asks_downloads_then_warning_then_installs(self):
        plan = self.bridge.plan(DLSS, "fsr4:lossy")
        kinds = [s["kind"] for s in plan["steps"]]
        self.assertEqual(kinds[:3], ["confirm", "download", "lossy"])   # anti-cheat first
        self.assertEqual(plan["steps"][1]["keys"], ["optiscaler", "fsr4-igpu-rdna2"])
        failed = self.bridge.apply(DLSS, "fsr4:lossy")
        self.assertEqual((failed["ok"], failed["kind"]), (False, "download"))

        make_components(self.root / "components")
        self.bridge.accept_lossy()
        self.assertEqual([s["kind"] for s in self.bridge.plan(DLSS, "fsr4:lossy")["steps"]],
                         ["confirm"])
        before = snapshot(self.common / "DlssGame")
        result = self.bridge.apply(DLSS, "fsr4:lossy")
        self.assertTrue(result["ok"], result)
        game = self.game(self.bridge.overview(), DLSS)
        self.assertEqual((game["choice"], game["tone"]), ("fsr4:lossy", "ok"))
        self.assertTrue(next(c for c in game["choices"] if c["id"] == "fsr4:lossy")["current"])

        removal = self.bridge.removal(DLSS)
        self.assertEqual(removal["settings"], "")      # helixsr.ini only for HelixSR
        self.assertTrue(self.bridge.uninstall(DLSS)["ok"])
        self.assertEqual(snapshot(self.common / "DlssGame"), before)
        self.assertIn(result["message"].splitlines()[0], self.bridge.overview()["log"])

    def test_lossy2_has_its_own_warning(self):
        make_components(self.root / "components")
        self.bridge.accept_lossy()   # Lossy's warning accepted: Lossy2 still asks for its own
        step = next(s for s in self.bridge.plan(DLSS, "fsr4:lossy2")["steps"] if s["kind"] == "lossy")
        self.assertEqual((step["variant"], step["title"]), ("lossy2", i18n.tr("lossy2_title")))
        self.assertEqual(self.bridge.lossy_text("lossy2"), "fsr4-igpu-rdna2 lossy2/WARNING.txt\n")
        self.assertEqual(self.bridge.lossy_text("lossy"), "fsr4-igpu-rdna2 lossy/WARNING.txt\n")
        self.bridge.accept_lossy("lossy2")
        self.assertEqual([s["kind"] for s in self.bridge.plan(DLSS, "fsr4:lossy2")["steps"]],
                         ["confirm"])
        self.assertTrue(self.bridge.apply(DLSS, "fsr4:lossy2")["ok"])
        game = self.game(self.bridge.overview(), DLSS)
        self.assertEqual(game["choice"], "fsr4:lossy2")

    def test_downloads_list_the_build_in_use(self):
        downloads = self.bridge.overview()["downloads"]
        self.assertEqual([i["key"] for i in downloads["items"]], ["optiscaler", "fsr4-igpu-rdna2"])
        self.assertEqual([b[0] for b in downloads["builds"]],
                         ["auto", "rx7000", "rx6000", "igpu_rdna3", "igpu_rdna2", "native"])
        make_components(self.root / "components")   # every build on disk: all are listed
        self.assertEqual(len(self.bridge.overview()["downloads"]["items"]), 5)

    def test_rdna1_shows_fsr4_greyed_out_and_downloads_no_build(self):
        self.service._gpus = [gpu.Gpu("AMD", 0x731f, (10, 1, 0))]   # RX 5700 XT
        overview = self.bridge.overview()
        choices = self.game(overview, FSR)["choices"]
        fsr4 = [c for c in choices if "4.1" in c["label"]]
        self.assertEqual(len(fsr4), 3)
        self.assertTrue(all(c["id"] == "" for c in fsr4))
        self.assertIn("RDNA 1", fsr4[0]["hint"])
        self.assertEqual(choices[-1]["id"], "fsr3")
        self.assertEqual(overview["downloads"]["missing"], ["optiscaler"])
        self.assertIn("RDNA 1", overview["downloads"]["builds"][0][1])

    def test_opti_name_moves_installed_optiscaler_and_launch_options(self):
        make_components(self.root / "components")
        write_launch_options(self.steam, {DLSS: "-dx12 %command%"})
        self.assertTrue(self.bridge.apply(DLSS, "fsr3")["ok"])
        names = self.bridge.opti_names(DLSS)
        self.assertEqual(names["current"], names["auto"])
        self.assertEqual(names["options"][0][0], "")
        result = self.bridge.set_opti_name(DLSS, "winmm.dll")
        self.assertTrue(result["ok"], result)
        game = self.game(self.bridge.overview(), DLSS)
        self.assertEqual(game["opti_name"], "winmm.dll")
        self.assertEqual(game["launch_options"], 'WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%')
        self.assertTrue(self.bridge.uninstall(DLSS)["ok"])
        self.assertEqual(self.game(self.bridge.overview(), DLSS)["launch_options"],
                         "-dx12 %command%")

    def test_helixsr_choice_without_folder_says_so(self):
        self.service.state["helixsr_folder"] = str(self.root / "gone")
        self.service.state["helixsr_searched"] = True
        with mock.patch("scaler_assistant.helixsr.find_candidates", return_value=[]):
            plan = self.bridge.plan(FSR, "helixsr:direct")
        self.assertEqual([s["kind"] for s in plan["steps"]], ["helixsr"])

    def test_languages(self):
        self.assertEqual(steam_language("tchinese"), "zh_TW")
        self.assertEqual(steam_language("schinese"), "zh_CN")
        self.assertEqual(steam_language("brazilian"), "en")
        self.assertEqual(self.bridge.set_steam_language("japanese"), "ja")
        self.assertEqual(self.bridge.set_language("de"), "de")
        self.assertEqual(self.service.language, "de")
        self.assertEqual(self.bridge.set_language(""), "ja")    # back to Steam's language
        self.assertIsNone(self.service.language)
        self.assertEqual(plain("<b>A</b><br>B &amp; C<ul><li>x</li></ul>"), "A\nB & C\n• x")

    def test_runtime_only_for_installed_games(self):
        self.assertIsNone(self.bridge.runtime(DLSS))
        self.assertIsNone(self.bridge.runtime(PLAIN))


class DeckyBackendTest(Base):
    """decky/main.py with a stand-in for Decky Loader's `decky` module."""

    def test_plugin_calls(self):
        runtime = self.root / "runtime"
        runtime.mkdir()
        fake = types.SimpleNamespace(
            DECKY_USER_HOME=str(self.root / "home"), DECKY_PLUGIN_RUNTIME_DIR=str(runtime),
            logger=mock.Mock(), emitted=[])

        async def emit(*args):
            fake.emitted.append(args)
        fake.emit = emit
        env = {"DECKY_PLUGIN_DIR": str(REPO / "decky"), "HOME": os.environ.get("HOME", "")}
        with mock.patch.dict(sys.modules, {"decky": fake}), mock.patch.dict(os.environ, env):
            spec = importlib.util.spec_from_file_location("decky_main", REPO / "decky" / "main.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(os.environ["HOME"], str(self.root / "home"))
            with mock.patch.object(module, "DeckBridge", lambda: DeckBridge(self.service)):
                plugin = module.Plugin()

                async def run():
                    await plugin._main()
                    started = await plugin.start("tchinese")
                    self.assertEqual(started["strings"]["app_name"], "Scaler 助手")
                    overview = await plugin.overview(False)
                    self.assertEqual(len(overview["games"]), 2)
                    with mock.patch("scaler_assistant.components.fetch",
                                    side_effect=lambda c, progress, root: progress(5, 10)):
                        result = await plugin.download(["optiscaler"])
                    await asyncio.sleep(0)
                    return result

                result = asyncio.run(run())
        i18n.set_language("en")
        self.assertTrue(result["ok"], result)
        self.assertEqual(fake.emitted, [("download_progress", "OptiScaler", 5, 10)])
