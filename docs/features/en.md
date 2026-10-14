# HelixSR Assistant — Feature Guide

**English** · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**HelixSR Assistant** is a Linux desktop tool that installs, switches, updates and removes **[HelixSR](https://github.com/lonewolf0622/HelixSR)** in your Steam games with one click, and shows whether HelixSR is actually running when you play.

HelixSR runs NVIDIA's DLSS Model E upscaling network on AMD GPUs (RDNA 1 and newer) as ordinary Direct3D 12 compute shaders, through Proton.

## Who it is for

HelixSR has no launch options or central settings file. It works by putting DLL files into each game's folder, one of three ways per game. Doing that by hand means:

1. Finding out which upscalers each game ships (FSR 3.1, DLSS, XeSS, FSR 2) and where its main `.exe` is.
2. Picking the right way for the game, renaming the game's own files to keep them safe, and copying HelixSR's files to the right places.
3. Editing `OptiScaler.ini` with the right paths for the OptiScaler way.
4. Doing it all again after every HelixSR update, and again when a game update overwrites HelixSR.
5. Opening `helixsr.log` to find out whether HelixSR is really running.

HelixSR Assistant does all of this from one window. HelixSR's own setup asks about every game in a terminal; HelixSR Assistant shows them as a list you can click.

## Before you start

> ⚠ **HelixSR Assistant does not include HelixSR and never downloads it for you.** It only copies files from the HelixSR folder you set up yourself.

1. **Download HelixSR** (1.8.0 or newer) from its [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) and extract it into a folder you keep, for example your home folder.
2. **Run `./helixsr-setup.sh` in that folder once.** It asks to download NVIDIA's DLSS DLL and builds HelixSR's network from it (about a minute). When it starts asking about games, you can answer `n` or close the window: HelixSR Assistant handles the games. If the folder is found but not set up yet, HelixSR Assistant offers a "Run setup in a terminal" button.
3. **An AMD GPU, RDNA 1 or newer** (Radeon RX 5000 and newer, Steam Deck, Ryzen APUs with RDNA graphics). Radeon Vega support is experimental in HelixSR 1.9.0.
4. **Direct3D 12 games running through Proton** that ship FSR 3.1, DLSS, XeSS or FSR 2.

On first start, HelixSR Assistant looks for a set-up HelixSR folder in your home folder, Downloads, Desktop and Games folders. You can always pick another one with "Choose HelixSR folder…" or by clicking the HelixSR pill at the top.

## The three ways HelixSR gets into a game

These are HelixSR's own three ways (the letters are the answers HelixSR's setup uses). HelixSR Assistant only offers the ways that work for each game, with the default first.

| Way | The game needs | What changes in the game folder | Select in the game |
|---|---|---|---|
| **FSR way** (f, the default for FSR 3.1 games) | FSR 3.1 | The game's `amd_fidelityfx_upscaler_dx12.dll` (or `amd_fidelityfx_dx12.dll`) is replaced by HelixSR; the game's file is kept as `*.original.dll` | **AMD FSR** |
| **OptiScaler way** (o) | DLSS, XeSS or FSR 2 | OptiScaler (the official release in your HelixSR folder) next to the game's `.exe`, its FSR 3.1 backend pointed at a `HelixSR` folder next to it; everything it replaces goes to `HelixSR/backup` | **DLSS** (FSR or XeSS also work) |
| **DLSS way** (d, experimental) | DLSS | HelixSR's DLSS loader as `dxgi.dll` and HelixSR as `nvngx.dll` next to the game's `.exe` | **DLSS** |

## Features

### 1. Scans your Steam games and their upscalers

- On first start, every Steam library is scanned (also libraries on other drives). Click "⟳ Rescan Steam games" after installing games.
- Each game's folder is searched for FSR 3.1, DLSS, XeSS and FSR 2 DLLs, and the folder of its main `.exe` is found from Steam's launch information (launchers and Unreal `*-Shipping.exe` are handled).
- Games with **anti-cheat** (Easy Anti-Cheat, BattlEye) are marked.
- Game names follow the interface language (Steam's localized names) and are sorted the way that language sorts. Games HelixSR can use come first; the "Games that can use HelixSR" filter is on by default.

### 2. One-click install

- Click "Install HelixSR" to install the default way, or the arrow next to it to pick another way. Each way says what to select in the game.
- Before anything is changed, the tool checks that the HelixSR folder is set up (the network is built) and that the game is not running.
- The DLSS way asks for confirmation and explains its risks first. Games with anti-cheat also ask for confirmation.
- When it is done, the log says exactly which files were replaced, where the game's own files were kept, and what to select in the game.

### 3. Switch ways, update and repair

- **Switch**: "More" → "Switch to …" removes the current way first (putting everything back) and then installs the new one. Your HelixSR settings move with the game.
- **Update**: when your HelixSR folder has a newer build than a game (a new HelixSR version, or the network built again), the game shows "↑ HelixSR … available" and an "↑ Update" button; "↑ Update all" updates every game at once.
- **Repair**: a game update or "Verify integrity of game files" in Steam can put the game's own files back over HelixSR. The game then shows what happened and a "Repair" button, which puts HelixSR back in place and keeps the game's new files as the backup.
- When a newer set-up HelixSR folder appears in your Downloads (or other usual places), the tool offers to switch to it once.

### 4. Remove

- "Remove" takes HelixSR out and puts back every file it replaced or moved, exactly as it was.
- The game's HelixSR settings (`helixsr.ini`) are kept unless you tick "Also remove this game's HelixSR settings".
- Files you put into the game's `my-fsr` folder yourself are never deleted.

### 5. HelixSR settings without editing files

"⚙ Settings" edits the game's `helixsr.ini` with a form. Only the settings HelixSR's README documents are offered:

| Group | Setting | Values |
|---|---|---|
| Sharpening | Sharpener | Default, Off, NVIDIA, RCAS |
| | Sharpness | 0.00 – 1.00 |
| | Follow the game's sharpness slider | Default, Yes, No |
| Upscaling (HelixSR 1.9.0+) | int8 network | Default (auto), Auto, On, Off |
| | Ultra Performance final pass | Default (Lanczos), Lanczos, EASU (FSR 1) |
| Compatibility | Wave size | Default, 64, 32 |

"Default" leaves the line out, so HelixSR uses its own default. Comments and any other lines in the file are kept as they are. The file is written next to HelixSR's DLL for the game's way (the game's `HelixSR` folder, next to the game's FSR DLL, or next to the `.exe`).

### 6. Live HelixSR status (what is actually running)

Running Steam games are checked every 3 seconds:

- Proton loads Windows DLLs from their files, so the tool can see in `/proc/<pid>/maps` whether the game has **really loaded HelixSR** (and OptiScaler or the DLSS loader).
- HelixSR is only loaded once the game uses the upscaler. "HelixSR not loaded yet" therefore tells you what to select in the game's graphics settings.
- `helixsr.log` from the current run is read: the network kernels' wave size and any error lines are shown. "More" → "View helixsr.log" shows the whole log with a copy button.
- On **RDNA 3 and newer** GPUs in games using the OptiScaler way, HelixSR's README recommends `WaveSize = 64` when the log says wave32. The tool notices this and offers a one-click "Set WaveSize = 64".
- The GPU pill at the top shows your GPU's generation (for example "AMD RDNA 3 (gfx1100)").

### 7. Overlay when a game starts

If HelixSR Assistant is open when a game with HelixSR starts, a small card appears in the bottom-right corner for about 10 seconds as soon as HelixSR loads, showing the version, the way and the wave size (once per launch; games already running before the tool opened are skipped). If HelixSR is still not loaded after 90 seconds, the card says what to select in the game. The overlay is a separate X11 (XWayland) window that never takes focus and lets mouse clicks through. Turn it off with the toolbar checkbox. It does not appear in Steam Deck Gaming Mode (gamescope).

### 8. Launch games, search and filters

- Every row has a "▶ Launch" button (through `steam://rungameid/<AppID>`); it shows "Running" while the game runs.
- Search by game name (any language) or App ID. Filters: games that can use HelixSR, installed, not installed, needs update or repair, running, all games.

### 9. Twelve interface languages

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. The system language is used on first start; switch at the top right (applies immediately and is remembered).

### 10. Built to be safe

- Nothing is changed unless the HelixSR folder is set up and the game is closed.
- Every file HelixSR replaces is kept (`*.original.dll` or `HelixSR/backup`), and every copied file is checked byte for byte.
- An `OptiScaler.ini` you already had is backed up and restored on removal; an FSR DLL you replaced by hand in the game's `HelixSR` folder is kept on updates.
- The DLSS way and games with anti-cheat need an explicit confirmation.

## Works together with HelixSR's own setup

HelixSR Assistant writes the same install record (`helixsr-install.json`), backups and file names as HelixSR's setup. So:

- Games you set up with `helixsr-setup.sh` show up as installed in HelixSR Assistant, with their way, and can be switched, updated or removed there.
- Games set up with HelixSR Assistant are recognised by HelixSR's setup and `helixsr-uninstall.sh`, which can update or remove them.

## Installing HelixSR Assistant

**AppImage (recommended)**: Python and Qt are included, so nothing else needs to be installed.

1. Download `HelixSR_Assistant-<version>-x86_64.AppImage` from the [Releases](https://github.com/mosesmoon/helixsr-assistant/releases) page.
2. Make it executable: right-click the file → Properties → Permissions, and turn on "Allow executing file as program" (the wording varies by file manager).
3. Double-click it to open HelixSR Assistant.

Or in a terminal:

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

If it does not start, your system may be missing FUSE; run it with `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run` instead.

**From source**: requires Python 3.11 or later and PyQt6 (Arch: `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # run directly
./install.sh           # install to ~/.local/share/helixsr-assistant and add an application menu entry
```

## Known limitations

- **Steam games only.** For games from other stores, use HelixSR's own setup (drag the game's folder into it).
- HelixSR itself only works in Direct3D 12 games. A game listed with a DLSS or FSR DLL may still be Vulkan or Direct3D 11; HelixSR then does nothing there.
- HelixSR changes very quickly. HelixSR Assistant needs HelixSR 1.8.0 or newer and was made against the 1.8.x and 1.9.x layout; if a future HelixSR changes how games are set up, use HelixSR's own setup until HelixSR Assistant is updated.
- The overlay does not appear in Steam Deck Gaming Mode (gamescope), and games in native Wayland exclusive fullscreen may cover it.
- In Thai, Vietnamese, Malay and Hindi, right-click menus are in English (Qt has no official translations for these languages). Steam has no Malay or Hindi game names, so these two languages always show the original names.

## Where data is stored

| Location | Contents |
|---|---|
| `~/.config/helixsr-assistant/state.json` | HelixSR Assistant's own state: HelixSR folder, game list cache, interface language, overlay setting |
| `<game>/…/HelixSR/helixsr-install.json`, next to the game's FSR DLL | HelixSR's install record (shared with HelixSR's own setup) |
| `<game>/…/helixsr.ini` | HelixSR's settings for that game |
| `<game>/…/helixsr.log` | What HelixSR reported the last time the game ran |

## Licences

HelixSR Assistant is an independent, unofficial tool. It is not affiliated with or endorsed by HelixSR's author, NVIDIA, AMD or the OptiScaler project, and it contains none of their files. HelixSR is free to use under the HelixSR Freeware License. After HelixSR's setup has run, HelixSR's DLLs contain NVIDIA's network: HelixSR Assistant only copies them between folders on your own PC. Never share or upload them.
