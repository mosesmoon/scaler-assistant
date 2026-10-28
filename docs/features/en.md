# Scaler Assistant — Feature Guide

**English** · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**Scaler Assistant** is a Linux desktop tool that lets you pick the upscaler for each of your Steam games — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact or Lossy from [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), or AMD's own on RX 9000) or **FSR 3** — and installs, switches, updates, repairs and removes it with one click. It shows whether the upscaler is actually running when you play.

## Who it is for

Getting a better upscaler into a game on Linux by hand means:

1. Finding out which upscalers the game ships (DLSS, XeSS, FSR 2, FSR 3.1), which graphics API it renders with and where its main `.exe` is.
2. Putting OptiScaler next to the `.exe` under a file name that game accepts, with the FidelityFX DLLs it needs, and editing `OptiScaler.ini` for the upscaler you want.
3. Adding `WINEDLLOVERRIDES` to the game's Steam launch options when that file name needs it — without breaking what is already there.
4. Downloading the right FSR 4.1 DLL for your GPU, or setting HelixSR up the way its README describes.
5. Doing it again after every update, and again when a game update overwrites your files.

Scaler Assistant does all of this from one window and keeps everything it replaces, so removing puts the game back exactly as it was.

## The choices for each game

The game's graphics API and upscalers decide which choices are offered. The game must already ship at least one upscaler (DLSS, XeSS, FSR 2 or FSR 3.1): that is what OptiScaler and HelixSR take over.

| Choice | The game needs | What is put into the game folder | Select in the game |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · FSR way** | Direct3D 12, FSR 3.1 | The game's FSR 3.1 DLL is replaced by HelixSR (the game's file is kept as `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · OptiScaler way** | Direct3D 12, DLSS, XeSS or FSR 2 | OptiScaler next to the `.exe`, pointed at a `HelixSR` folder | DLSS |
| **DLSS 3.7 (HelixSR) · DLSS way** (experimental) | Direct3D 12, DLSS | HelixSR's DLSS loader (`dxgi.dll`) and HelixSR as `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | any of the four upscalers | OptiScaler next to the `.exe`; the FidelityFX DLLs and the Exact FSR 4.1 DLL in a `ScalerAssistant` folder | DLSS, FSR or XeSS |
| **FSR 4.1 Lossy** | the same | the same, with the Lossy FSR 4.1 DLL | DLSS, FSR or XeSS |
| **FSR 4.1 Lossy2** | the same | the same, with the Lossy2 FSR 4.1 DLL | DLSS, FSR or XeSS |
| **FSR 4.1 (AMD)** — instead of Exact / Lossy on RX 9000 (RDNA 4) | the same | the same, with AMD's own FSR 4.1 DLL | DLSS, FSR or XeSS |
| **FSR 3** | the same | the same; OptiScaler uses FSR 3.1.5 | DLSS, FSR or XeSS |

- **Exact** gives AMD's FSR 4.1 picture byte for byte, with faster shaders. **Lossy** is faster again and changes the picture slightly; Scaler Assistant shows its `WARNING.txt` once before you use it for the first time. If you are not sure, take Exact.
- **Lossy2** is Lossy with six of the network's twelve layers retrained: swaying foliage comes closer to AMD's picture and there are fewer fireflies, but it follows brightening more slowly and is the same as Lossy in Ultra Performance. It is offered next to Lossy so you can compare them, and shows its own `WARNING.txt` once.
- HelixSR only works in **Direct3D 12** games, so DLSS 3.7 is only offered there. FSR 4.1 and FSR 3 also work in **Direct3D 11 and Vulkan** games: FSR 3 natively, FSR 4.1 through OptiScaler's Direct3D 12 path (less tested than Direct3D 12 games).
- Click **"Choose upscaler"** in a game's row (or **"Upscaler"** once one is installed): DLSS 3.7 (HelixSR) opens a submenu with its ways; the current choice is ticked. Switching removes the current one first and puts everything back.

## Before you start

- **FSR 4.1 and FSR 3** need nothing else: the first time you pick one, Scaler Assistant asks to download OptiScaler and the FSR 4.1 DLLs for your GPU (see "Downloads" below).
- **DLSS 3.7** needs HelixSR, which Scaler Assistant does not include. Download HelixSR 1.8.0 or newer from its [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases), extract it into a folder you keep and run `./helixsr-setup.sh` there once (it builds HelixSR's network on your PC; when it starts asking about games you can answer `n`). Click the **HelixSR** pill at the top for this; Scaler Assistant finds a set-up HelixSR folder in your home, Downloads, Desktop or Games folder by itself.
  Easier: press **Download and build HelixSR** in that window (HelixSR 2.0 or newer); Scaler Assistant does all of this for you, without a terminal.
- Games run through **Proton**. HelixSR is made for AMD GPUs (RDNA 1 and newer). FSR 4.1 Exact / Lossy are made for Radeon RX 7000 / RX 6000 and integrated Radeon graphics (Steam Deck included); other GPUs should run them but are untested by their author. FSR 4.1 does not work on Radeon RX 5000 (RDNA 1) GPUs (every build gives only a black picture), so Scaler Assistant greys it out there; FSR 3 and DLSS 3.7 (HelixSR) remain.

## Features

### 1. Scans your Steam games

- Every Steam library is scanned on first start (also libraries on other drives). Click "⟳ Rescan Steam games" after installing games.
- For each game: the upscaler DLLs it ships, the folder of its main `.exe` (from Steam's launch information; launchers and Unreal `*-Shipping.exe` are handled), its **graphics API** (read from the `.exe`'s import table: DX12, DX11 or Vulkan) and whether it has **anti-cheat** (Easy Anti-Cheat, BattlEye).
- Game names follow the interface language (Steam's localized names). Games that can be upscaled come first.

### 2. OptiScaler gets a file name that works in the game

The game loads OptiScaler as a system DLL next to its `.exe`. Scaler Assistant picks the name:

1. one you chose for the game ("More" → "OptiScaler's file name…"),
2. the name of an OptiScaler that is already there,
3. the name [OptiScaler's compatibility list](https://github.com/optiscaler/OptiScaler/wiki) gives for the game (for example `d3d12.dll` or `winmm.dll`),
4. `winmm.dll` for Vulkan games,
5. another free name (`winmm.dll`, `version.dll`, …) when the game or another mod (ReShade, for example) already has a `dxgi.dll`, or when your launch options keep that name builtin,
6. otherwise `dxgi.dll`.

A file that is already there is never overwritten: it goes into `ScalerAssistant/backup` (`HelixSR/backup` for DLSS 3.7) and comes back on removal.

### 3. Steam launch options: only what is needed, and yours stay as they are

`dxgi.dll` and `d3d12.dll` load under Proton without anything else. Every other name needs `WINEDLLOVERRIDES="<name>=n,b"` in the game's launch options, and Scaler Assistant adds it for you:

- **Only that one entry is inserted.** If you already have `WINEDLLOVERRIDES`, `;winmm=n,b` is appended inside it; otherwise `WINEDLLOVERRIDES="winmm=n,b"` is put in front (with `%command%` if your options had none). Nothing else in your options changes. Example: `-dx12 %command%` becomes `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Only that one entry is taken out** when OptiScaler is removed or renamed. If you did not change the options in between, they return exactly to what they were; if you did, only the inserted text is removed and your changes stay.
- An entry you already had for that name is left alone and is not removed later. If your options set that name to Wine's builtin version, Scaler Assistant uses another name instead of changing your setting.
- If the entry goes missing later, the game shows "Launch option missing" and "Repair" adds it again.
- While Steam runs, the options are changed through Steam itself when its debugging port is available (as Decky Loader uses). Otherwise Scaler Assistant offers to close Steam, write the change and start Steam again — before any game file is touched.

### 4. Downloads (FSR 4.1 and FSR 3)

Click the **OptiScaler** pill at the top (or the GPU pill):

- **OptiScaler 0.9.4** (with AMD's FidelityFX DLLs: FSR 3 and AMD's FSR 4.1, plus fakenvapi) and **FSR 4.1 Exact / Lossy / Lossy2** in the build for your GPU: RX 7000 cards, RX 6000 cards, RDNA 3 graphics built into the processor (also GeForce, Intel Arc and other GPUs), or the Steam Deck and RDNA 2 graphics built into the processor. Every build works on all of them; the one for your GPU is the fastest. If a game crashes with Exact, choose a build for built-in graphics.
- Nothing is downloaded until you agree. Each download is a fixed release checked against its size and SHA-256 before it is unpacked; only the files games need are kept, in `~/.local/share/scaler-assistant/components/`.
- **FSR 4.1 build**: automatic from your GPU (RX 9000 / RDNA 4 → AMD's own FSR 4.1, integrated graphics and Steam Deck → the integrated build, other GPUs → the graphics-card build), or chosen by hand. The modified DLLs are never used on RDNA 4. On other GPUs, OptiScaler is set to FSR 4's INT8 model.
- "Remove downloads" deletes them; games keep their own copies.

### 5. What changes in OptiScaler.ini

Only the lines the choice needs, in their own sections; every other line and comment is kept:

| Key | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (through Direct3D 12) | `fsr31` (native) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` before RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | the DLLs in the game's `ScalerAssistant` folder | the same |

An `OptiScaler.ini` that was already there is backed up first and put back on removal.

### 6. Switch, update, repair, remove

- **Switch** from the upscaler menu: the current choice is removed first, then the new one is installed. Between FSR 4.1 Exact, Lossy and FSR 3 only the FSR DLL and `OptiScaler.ini` change.
- **Update**: a game shows "↑ HelixSR … available" when your HelixSR folder has a newer build, or "↑ Newer download available" when a newer OptiScaler / FSR 4.1 download (or another FSR 4.1 build) is in use. "↑ Update all" updates every game.
- **Repair**: a game update or "Verify integrity of game files" can put the game's own files back. The game then shows what happened and "Repair" puts the upscaler back, keeping the game's new files as the backup.
- **Remove** puts back every file that was replaced or moved, and takes the launch-option entry out again.

### 7. HelixSR settings without editing files

For DLSS 3.7, "⚙ Settings" edits the game's `helixsr.ini` with a form (sharpening, int8 network, Ultra Performance final pass, wave size). "Default" leaves the line out; other lines and comments are kept.

### 8. Live status and the overlay

- Running Steam games are checked every 3 seconds: `/proc/<pid>/maps` shows whether the game has **really loaded** HelixSR or the FSR DLL (and OptiScaler or the DLSS loader). Nothing is loaded until the game uses the upscaler, so "not loaded yet" tells you what to select in the game.
- For HelixSR, `helixsr.log` from the current run shows the wave size and errors; on RDNA 3 and newer with the OptiScaler way, "Set WaveSize = 64" is offered when the log says wave32.
- A game's details panel (the ⌄ button on its card) has "View …log" for `helixsr.log` or `OptiScaler.log`, the game's folder, OptiScaler's file name and, for DLSS 3.7, "⚙ Settings".
- When a game starts, a small card in the bottom-right corner shows the result for about 10 seconds (or a hint after 90 seconds). It is a separate X11 window that never takes focus; turn it off with the switch in the toolbar.

### 9. Launch, search, filters, languages

- "▶ Launch" starts the game through Steam. Search by name (any language) or App ID; filters: games that can be upscaled, upscaler installed, no upscaler yet, needs update or repair, running, all games.
- 12 interface languages: 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Built to be safe

- Nothing changes while the game runs; downloads and the HelixSR folder are checked before any file is touched.
- Every replaced file is kept, every copy is verified byte for byte, and launch options are only ever changed by the one entry described above.
- The DLSS way, FSR 4.1 Lossy and games with anti-cheat ask first. Never use a changed upscaler in online games: anti-cheat can treat it as tampering.

### 11. Look and feel

- In the style of MAKO Assistant ("Liquid Glass"): one card per game with its Steam cover, a status chip, what the game offers and, while it runs, what is really loaded. The ⌄ button opens the game's details (graphics API, upscalers, `.exe` folder, OptiScaler's name, launch options) and its less frequent actions.
- Buttons are raised clear crystal: a light tint with a hairline border, a curved highlight on the upper half, a glint along the lower rim and a soft shadow underneath — all flat translucent layers, no gradients. Switch knobs stand up the same way; the selected theme segment is a raised crystal in a sunken track. Teal installs, blue changes, amber updates, red removes.
- Dark, light or automatic theme (follows the desktop). The activity log is the drawer at the bottom of the window.

## HelixSR 2.0 and the GPU

- **Download and build HelixSR in one step**: "Download and build HelixSR" (in the HelixSR window and in the Steam Deck plugin) downloads the newest HelixSR (2.0 or newer) from its GitHub releases, checked by SHA-256, into `~/.local/share/scaler-assistant/helixsr`, and builds it on this PC with HelixSR's own build program (`setup/helixsr_setup.py`, run as is) — the way HelixSR's own app does it, so no terminal and no games step. It brings what the build needs: a Python with numpy (a portable Python 3.14 when the system's can't unpack NVIDIA's zstd package, so frame generation needs no extra `zstd` program) and Microsoft's DirectX Shader Compiler, run through Steam's Proton or Wine. NVIDIA's files are downloaded only after you agree in the app; what is built stays on your PC. Inside Flatpak the build runs on the host. Running it again only builds what is missing; a newer release replaces the one downloaded before.
- **HelixSR 2.0 and newer** keep the built DLL in `HelixSR-fsrfg` and offer two ways: **HelixSR Scaler** (HelixSR's own OptiScaler build next to the `.exe`: select DLSS in the game; also DX11 and Vulkan games) and the **FSR way** (FSR drop-in). Scaler Assistant installs both through the installer inside your HelixSR folder (`setup/helixsr_bridge.py`, the one HelixSR's own app uses), so HelixSR's setup, its app and Scaler Assistant recognise, update and remove each other's installs. It still picks the file name and adds the launch option when one is needed. Games set up with an earlier way move to HelixSR Scaler on update. HelixSR 1.8.x keeps its three ways; with 1.9.0 – 1.9.3 only the FSR way (the others are greyed out).
- **HelixSR frame generation** (HelixSR 2.0): in DirectX 12 games that have DLSS Frame Generation (Streamline's `sl.dlss_g.dll`), a game with HelixSR Scaler gets a "HelixSR frame generation" switch on its card (and in the Steam Deck plugin). It runs HelixSR's own installer (`scaler-fg`), which only changes OptiScaler.ini's `[FrameGen]` choice; then turn on DLSS Frame Generation in the game. It needs the frame generation that `./helixsr-setup.sh` builds (it downloads NVIDIA's DLSS Frame Generation files); until then the switch is greyed out with the reason. New installs leave it off; an update or a new OptiScaler file name keeps it as it was. Other DX12 games can still pick AMD FSR or XeSS frame generation in HelixSR Scaler's menu (Insert); DX11 / Vulkan games and the FSR way get upscaling only.
- **HelixSR 3.0**: the built DLL is `HelixSR/helixsr.dll` (HelixSR Scaler's DLSS upscaler, "HLX DLSS"), and the FSR way puts in **HLX FSR 4**, HelixSR's own FSR 4 pipeline, which HelixSR's setup builds from AMD's FSR 4 driver file (it downloads about 420 MB of AMD's driver package from AMD; "Download and build HelixSR" asks before it and also brings the second shader compiler, DXC 1.9.2609). Scaler Assistant installs, updates, switches and removes both ways through the release's installer as with 2.0; games set up with 2.0 move from `HelixSR-fsrfg` to `HelixSR` on update. HelixSR 3.0 has no frame generation, so the switch above is not shown with it; AMD FSR and XeSS frame generation stay in HelixSR Scaler's menu.
- **Earlier HelixSR versions**: 1.8.x offers all three ways (FSR way, OptiScaler way, DLSS way). HelixSR 1.9.0 – 1.9.3 releases only carry the FSR way's files, so the OptiScaler and DLSS ways are greyed out there ("needs HelixSR 1.8 or 2.0"); games without FSR 3.1 need HelixSR 2.0 (HelixSR Scaler). Versions before 1.8.0 are not supported.
- **DLSS way only with a GeForce**: with an AMD or Intel GPU, games don't offer DLSS to select, so the (HelixSR 1.x) DLSS way is greyed out with the reason.
- **FSR 4.1 Lossy recommended** on built-in graphics (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) and Intel GPUs: marked "★ Recommended" among the FSR 4.1 choices only.

## Works together with HelixSR's own setup

For DLSS 3.7, Scaler Assistant writes the same install record (`helixsr-install.json`), backups and file names as HelixSR's setup, so `helixsr-setup.sh` / `helixsr-uninstall.sh` and Scaler Assistant recognise each other's games. HelixSR's setup sees the FSR DLL in a game's `ScalerAssistant` folder as the game's own FSR 3.1 DLL and may replace it with HelixSR; Scaler Assistant then reports the game as needing repair and "Repair" takes HelixSR out again. To use DLSS 3.7 in such a game, choose it in Scaler Assistant.

## Steam Deck plugin (Decky Loader)

The same program for Game Mode, as a plugin for [Decky Loader](https://decky.xyz) in the Quick Access menu.

- **Games**: the games that can be upscaled, running games first, each with its status chip and, while it runs, what is really loaded. Select a game to choose DLSS 3.7 (HelixSR, each way), FSR 4.1 Exact / Lossy or FSR 3, or to update, repair or remove it, change OptiScaler's file name or read its log. The same questions come first as in the desktop app: downloads, the Lossy warning, the DLSS way and anti-cheat.
- **Setup**: the HelixSR folder (file picker), the downloads and the FSR 4.1 build (the Steam Deck gets the integrated-graphics build), a notification when a game starts (it says whether the upscaler loaded) and the language (by default the same as Steam).
- It shares `state.json`, the downloads and the launch-option records with the desktop app, so games set up in one show up in the other. Launch options are written live through Steam.
- Not in the plugin: HelixSR's settings form (use the desktop app) and HelixSR's own `helixsr-setup.sh`, which you run once in Desktop Mode.
- In the plugin, **Download and build HelixSR** downloads and builds HelixSR 2.0 or newer in Game Mode too (it takes several minutes).

Install: put Decky Loader on the Steam Deck, download `Scaler_Assistant-Decky-<version>.zip` from the [Releases](https://github.com/mosesmoon/scaler-assistant/releases) page, then in Decky's settings → Developer (turn on Developer mode in General first) → "Install Plugin from ZIP File".

## Installing Scaler Assistant

**AppImage (recommended)**: Python, Qt and 7-Zip are included.

1. Download `Scaler_Assistant-<version>-x86_64.AppImage` from the [Releases](https://github.com/mosesmoon/scaler-assistant/releases) page.
2. Make it executable: right-click → Properties → Permissions → "Allow executing file as program" (the wording varies by file manager).
3. Double-click it.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

If it does not start, your system may be missing FUSE; run it with `--appimage-extract-and-run`.

**Single installer (.bin)**: `Scaler_Assistant-<version>-x86_64.bin` installs the same bundled app for your user only (no root, no FUSE) into `~/.local/opt/scaler-assistant`, with the `scaler-assistant` command and a menu entry. **Flatpak**: `Scaler_Assistant-<version>-x86_64.flatpak` is a single-file bundle on the Freedesktop 25.08 runtime (fetched from Flathub on install). It may read your home folder and other drives (SD cards under `/run/media`) and sees Steam's and the games' processes through `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / install
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / remove
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**From source**: Python 3.11+ and PyQt6 (Arch: `sudo pacman -S python-pyqt6`), plus 7-Zip or bsdtar to unpack OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # run directly
./install.sh           # install to ~/.local/share/scaler-assistant and add a menu entry
```

## Known limitations

- **Steam games only.** The FSR 4.1 / FSR 3 routes have been checked file by file with OptiScaler 0.9.4; every game behaves differently, so check OptiScaler's compatibility list when a game misbehaves, or pick another OptiScaler file name.
- FSR 4.1 in Direct3D 11 and Vulkan games runs through OptiScaler's Direct3D 12 path and is less tested.
- HelixSR changes quickly. Scaler Assistant needs HelixSR 1.8.0 or newer and follows the 1.8.x / 1.9.x / 2.0.x / 3.0.x layout.
- The overlay does not appear in Steam Deck Gaming Mode (gamescope). The Decky plugin shows a Steam notification there instead.
- In Thai, Vietnamese, Malay and Hindi, right-click menus are in English (Qt has no official translations). Steam has no Malay or Hindi game names.

## Where data is stored

| Location | Contents |
|---|---|
| `~/.config/scaler-assistant/state.json` | Scaler Assistant's state: HelixSR folder, game list, language, FSR 4.1 build, OptiScaler names you chose, the launch-option entries it added (taken over from HelixSR Assistant once) |
| `~/.local/share/scaler-assistant/components/` | The downloaded OptiScaler and FSR 4.1 files |
| `~/homebrew/plugins/scaler-assistant/` | The Decky plugin on the Steam Deck (it uses the same state and downloads as above) |
| `<game>/…/ScalerAssistant/` | FSR 4.1 / FSR 3: the FidelityFX DLLs, `scaler-install.json`, `backup/` |
| `<game>/…/HelixSR/helixsr-install.json`, next to the game's FSR DLL | DLSS 3.7: HelixSR's install record (shared with HelixSR's setup) |
| `<game>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Settings and logs |

## Licences

Scaler Assistant is an independent, unofficial tool, not affiliated with or endorsed by HelixSR's author, NVIDIA, AMD, the OptiScaler project or the fsr4-shader-performance-overrides project, and it contains none of their files. When you ask, it downloads OptiScaler (GPL-3.0; fakenvapi MIT; AMD's FidelityFX DLLs under AMD's licence) and the FSR 4.1 DLLs (GPL-2.0-or-later, modified AMD DLLs with AMD's notice) from their GitHub releases. The AppImage includes 7-Zip's `7zzs` (GNU LGPL with the unRAR restriction, BSD; licence included). HelixSR is free to use under the HelixSR Freeware License; after its setup, HelixSR's DLLs contain NVIDIA's network, so Scaler Assistant only copies them between folders on your own PC. Never share or upload them. The Decky plugin includes the same `7zzs`.
