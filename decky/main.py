"""Decky Loader backend of Scaler Assistant: the same scaler_assistant package as the
desktop app (in py_modules), run as the Steam Deck's user."""

import asyncio
import os
import shutil
import stat
import sys

import decky

PLUGIN_DIR = os.environ.get("DECKY_PLUGIN_DIR") or os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "py_modules"))

# Same settings and downloads as the desktop app.
os.environ["HOME"] = decky.DECKY_USER_HOME
os.environ.setdefault("XDG_CONFIG_HOME", os.path.join(decky.DECKY_USER_HOME, ".config"))
os.environ.setdefault("XDG_DATA_HOME", os.path.join(decky.DECKY_USER_HOME, ".local", "share"))


def _seven_zip() -> None:
    """Decky unpacks plugins without the executable bit: run 7-Zip from a copy."""
    source = os.path.join(PLUGIN_DIR, "bin", "7zzs")
    if not os.path.isfile(source):
        return
    target = os.path.join(decky.DECKY_PLUGIN_RUNTIME_DIR, "7zzs")
    try:
        if (not os.path.isfile(target)
                or os.path.getsize(target) != os.path.getsize(source)):
            shutil.copyfile(source, target)
        os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        os.environ["SCALER_ASSISTANT_7Z"] = target
    except OSError as error:
        decky.logger.warning("7-Zip: %s", error)


_seven_zip()

from scaler_assistant.deck import DeckBridge  # noqa: E402


class Plugin:
    bridge = None
    lock = None

    async def _main(self):
        self.loop = asyncio.get_running_loop()
        self.lock = asyncio.Lock()
        self.bridge = DeckBridge()
        decky.logger.info("Scaler Assistant ready")

    async def _unload(self):
        pass

    async def _work(self, fn, *args):
        """Blocking work off the event loop, one change at a time."""
        async with self.lock:
            return await self.loop.run_in_executor(None, fn, *args)

    async def _read(self, fn, *args):
        return await self.loop.run_in_executor(None, fn, *args)

    async def start(self, steam_language: str):
        for _ in range(100):          # the frontend can be quicker than _main
            if self.bridge is not None:
                break
            await asyncio.sleep(0.1)
        self.bridge.set_steam_language(steam_language)
        return {"strings": self.bridge.strings(),
                "toast": self.bridge.service.overlay_enabled}

    async def set_language(self, code: str):
        self.bridge.set_language(code or None)
        return {"strings": self.bridge.strings()}

    async def overview(self, rescan: bool = False):
        return await self._work(self.bridge.overview, bool(rescan))

    async def plan(self, app_id: int, choice: str):
        return await self._work(self.bridge.plan, int(app_id), choice)

    async def lossy_text(self):
        return await self._read(self.bridge.lossy_text)

    async def accept_lossy(self):
        self.bridge.accept_lossy()

    async def apply(self, app_id: int, choice: str):
        return await self._work(self.bridge.apply, int(app_id), choice)

    async def removal(self, app_id: int):
        return await self._read(self.bridge.removal, int(app_id))

    async def uninstall(self, app_id: int, remove_settings: bool = False):
        return await self._work(self.bridge.uninstall, int(app_id), bool(remove_settings))

    async def set_frame_generation(self, app_id: int, on: bool):
        return await self._work(self.bridge.set_frame_generation, int(app_id), bool(on))

    async def update_all(self):
        return await self._work(self.bridge.update_all)

    async def download(self, keys):
        loop = self.loop

        def progress(name, done, total):
            asyncio.run_coroutine_threadsafe(
                decky.emit("download_progress", name, int(done), int(total)), loop)

        return await self._work(self.bridge.download, list(keys), progress)

    async def remove_downloads(self):
        return await self._work(self.bridge.remove_downloads)

    async def set_fsr4_build(self, value: str):
        self.bridge.set_fsr4_build(value)

    async def opti_names(self, app_id: int):
        return await self._read(self.bridge.opti_names, int(app_id))

    async def set_opti_name(self, app_id: int, name: str):
        return await self._work(self.bridge.set_opti_name, int(app_id), name or "")

    async def set_helixsr_folder(self, path: str):
        return await self._work(self.bridge.set_helixsr_folder, path)

    async def log_text(self, app_id: int):
        return await self._read(self.bridge.log_text, int(app_id))

    async def set_toast(self, enabled: bool):
        self.bridge.set_toast(bool(enabled))

    async def runtime(self, app_id: int):
        return await self._read(self.bridge.runtime, int(app_id))
