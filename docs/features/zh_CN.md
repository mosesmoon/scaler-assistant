# Scaler 助手 — 功能介绍

[English](en.md) · [台灣正體中文](zh_TW.md) · **简体中文** · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**Scaler 助手**是一款 Linux 桌面工具，让你为每款 Steam 游戏选择超分辨率技术——**DLSS 3.7（[HelixSR](https://github.com/lonewolf0622/HelixSR)）**、**FSR 4.1**（来自 [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides) 的 Exact 或 Lossy，RX 9000 则用 AMD 原生版）或 **FSR 3**——并一键安装、切换、更新、修复、移除。玩游戏时还会显示超分是否真的在运行。

## 适合谁使用

在 Linux 上手动为游戏换上更好的超分，需要：

1. 查出游戏自带哪些超分技术（DLSS、XeSS、FSR 2、FSR 3.1）、使用哪种图形 API，以及主 `.exe` 在哪里。
2. 把 OptiScaler 以游戏能接受的文件名放到 `.exe` 旁，附上需要的 FidelityFX DLL，并按想用的超分技术修改 `OptiScaler.ini`。
3. 文件名需要时，在游戏的 Steam 启动选项中加入 `WINEDLLOVERRIDES`——而且不能破坏原有内容。
4. 按显卡下载正确的 FSR 4.1 DLL，或按 HelixSR README 的说明设置 HelixSR。
5. 每次更新都再做一遍；游戏更新覆盖文件时也要再做一遍。

Scaler 助手在一个窗口里完成这一切，并保留所有被替换的文件，移除时游戏会完全恢复原样。

## 每款游戏可选的项目

可选项目取决于游戏的图形 API 和超分技术。游戏本身必须至少自带一种超分技术（DLSS、XeSS、FSR 2 或 FSR 3.1）：OptiScaler 和 HelixSR 正是接管这些技术。

| 选项 | 游戏需要 | 放进游戏文件夹的内容 | 游戏内选择 |
|---|---|---|---|
| **DLSS 3.7（HelixSR）· FSR 方式** | Direct3D 12、FSR 3.1 | 游戏的 FSR 3.1 DLL 换成 HelixSR（原文件保留为 `*.original.dll`） | AMD FSR |
| **DLSS 3.7（HelixSR）· OptiScaler 方式** | Direct3D 12、DLSS／XeSS／FSR 2 | `.exe` 旁放入 OptiScaler，指向 `HelixSR` 文件夹 | DLSS |
| **DLSS 3.7（HelixSR）· DLSS 方式**（实验性） | Direct3D 12、DLSS | HelixSR 的 DLSS 加载器（`dxgi.dll`）和以 `nvngx.dll` 命名的 HelixSR | DLSS |
| **FSR 4.1 Exact** | 四种超分技术任一种 | `.exe` 旁放入 OptiScaler；FidelityFX DLL 和 Exact 版 FSR 4.1 DLL 放在 `ScalerAssistant` 文件夹 | DLSS、FSR 或 XeSS |
| **FSR 4.1 Lossy** | 同上 | 同上，改用 Lossy 版 FSR 4.1 DLL | DLSS、FSR 或 XeSS |
| **FSR 4.1（AMD）**——RX 9000（RDNA 4）以此代替 Exact／Lossy | 同上 | 同上，改用 AMD 原生 FSR 4.1 DLL | DLSS、FSR 或 XeSS |
| **FSR 3** | 同上 | 同上；OptiScaler 使用 FSR 3.1.5 | DLSS、FSR 或 XeSS |

- **Exact** 的画面与 AMD 的 FSR 4.1 逐字节相同，只是着色器更快。**Lossy** 更快，但画面略有不同；首次使用前，Scaler 助手会先显示一次它的 `WARNING.txt`。不确定就选 Exact。
- HelixSR 只能用于 **Direct3D 12** 游戏，所以只有这类游戏会出现 DLSS 3.7。FSR 4.1 和 FSR 3 也能用于 **Direct3D 11 与 Vulkan** 游戏：FSR 3 原生支持，FSR 4.1 则通过 OptiScaler 的 Direct3D 12 路径（测试程度不如 Direct3D 12 游戏）。
- 在游戏那一行点击 **“选择超分”**（已安装的游戏点击 **“超分”**）：DLSS 3.7（HelixSR）会展开子菜单列出各方式，当前选择会打勾。切换时会先移除当前项目并全部还原。

## 开始之前

- **FSR 4.1 和 FSR 3** 不需要其他东西：首次选择时，Scaler 助手会询问是否下载 OptiScaler 及适合你显卡的 FSR 4.1 DLL（见下方“下载文件”）。
- **DLSS 3.7** 需要 HelixSR，Scaler 助手不包含它。请从 [HelixSR 的 GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) 下载 1.8.0 或更新版本，解压到会保留的文件夹，并在其中运行一次 `./helixsr-setup.sh`（它会在你的电脑上构建 HelixSR 的神经网络；开始逐个询问游戏时可以回答 `n`）。点击顶部的 **HelixSR** 标签可查看这些说明；Scaler 助手会自动在主目录、下载、桌面或 Games 文件夹中寻找已设置好的 HelixSR 文件夹。
  更简单的方式：在该窗口按 **下载并构建 HelixSR**（HelixSR 2.0 及以上），Scaler 助手会替你完成以上步骤，无需终端。
- 游戏通过 **Proton** 运行。HelixSR 为 AMD 显卡（RDNA 1 及以上）设计。FSR 4.1 Exact／Lossy 为 Radeon RX 7000／RX 6000 及 Radeon 集成显卡（含 Steam Deck）制作；其他 GPU 应该也能运行，但原作者尚未测试。

## 功能

### 1. 扫描 Steam 游戏

- 首次启动时扫描所有 Steam 游戏库（包括其他磁盘上的库）。安装新游戏后点击“⟳ 重新扫描 Steam 游戏”。
- 每款游戏都会找出：自带的超分 DLL、主 `.exe` 所在文件夹（依据 Steam 的启动信息；也能处理启动器和 Unreal 的 `*-Shipping.exe`）、**图形 API**（读取 `.exe` 的导入表：DX12、DX11 或 Vulkan），以及是否含有**反作弊**（Easy Anti-Cheat、BattlEye）。
- 游戏名称跟随界面语言（Steam 的本地化名称）。可以超分的游戏排在前面。

### 2. 为 OptiScaler 选一个游戏能用的文件名

游戏会把放在 `.exe` 旁的 OptiScaler 当作系统 DLL 加载。Scaler 助手按以下顺序决定文件名：

1. 你为这款游戏选的文件名（“更多”→“OptiScaler 文件名…”），
2. 游戏中已存在的 OptiScaler 所用的文件名，
3. [OptiScaler 兼容性列表](https://github.com/optiscaler/OptiScaler/wiki)为这款游戏指定的文件名（例如 `d3d12.dll` 或 `winmm.dll`），
4. Vulkan 游戏用 `winmm.dll`，
5. 游戏或其他模组（例如 ReShade）已有 `dxgi.dll`，或你的启动选项把这个名称设为内置版本时，改用其他空闲的文件名（`winmm.dll`、`version.dll`…），
6. 其他情况用 `dxgi.dll`。

已存在的文件绝不会被覆盖：它会移到 `ScalerAssistant/backup`（DLSS 3.7 则是 `HelixSR/backup`），移除时再放回。

### 3. Steam 启动选项：只加需要的，你原有的内容保持不变

在 Proton 下，`dxgi.dll` 和 `d3d12.dll` 无需其他设置即可加载。其他文件名都需要在游戏的启动选项中加入 `WINEDLLOVERRIDES="<名称>=n,b"`，Scaler 助手会替你加上：

- **只插入这一项。** 如果你已经有 `WINEDLLOVERRIDES`，就在其值中加上 `;winmm=n,b`；否则在最前面加上 `WINEDLLOVERRIDES="winmm=n,b"`（原来没有 `%command%` 时一并补上）。启动选项的其他内容一律不动。例如 `-dx12 %command%` 会变成 `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`。
- **移除 OptiScaler 或改文件名时，只去掉这一项。** 如果期间你没改过启动选项，会完全恢复原来的内容；如果改过，只会去掉当初插入的文字，你的修改都会保留。
- 你原来就有的同名设置不会被改动，之后也不会被移除。如果你的启动选项把这个名称设为 Wine 内置版本，Scaler 助手会改用其他文件名，而不是修改你的设置。
- 如果这一项之后不见了，游戏会显示“缺少启动选项”，点击“修复”即可重新加入。
- Steam 运行时，若 Steam 的调试端口可用（Decky Loader 也用它），会直接通过 Steam 修改。否则 Scaler 助手会询问是否关闭 Steam、写入更改后再重新启动 Steam——这一步发生在修改任何游戏文件之前。

### 4. 下载文件（FSR 4.1 与 FSR 3）

点击顶部的 **OptiScaler** 标签（或 GPU 标签）：

- **OptiScaler 0.9.4**（含 AMD 的 FidelityFX DLL：FSR 3 与 AMD 的 FSR 4.1，以及 fakenvapi），以及给独立显卡或集成显卡用的 **FSR 4.1 Exact／Lossy**。
- 你同意之前不会下载任何东西。每个下载文件都是固定版本，解压前会核对大小和 SHA-256；只保留游戏需要的文件，存放在 `~/.local/share/scaler-assistant/components/`。
- **FSR 4.1 版本**：按显卡自动选择（RX 9000／RDNA 4 → AMD 原生 FSR 4.1；集成显卡与 Steam Deck → 集成显卡版；其他 GPU → 独立显卡版），也可以手动指定。RDNA 4 绝不会使用修改过的 DLL。其他 GPU 会把 OptiScaler 设为使用 FSR 4 的 INT8 模型。
- “删除下载文件”会删除它们；游戏里的副本不受影响。

### 5. OptiScaler.ini 会改哪些地方

只改这个选项需要的几行，且只改在各自的区段；其他每一行和注释都会保留：

| Key | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`、`VulkanUpscaler` | `fsr31_12`（经由 Direct3D 12） | `fsr31`（原生） |
| `UpscalerIndex` | `0`（FSR 4） | `1`（FSR 3.1.5） |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | RDNA 4 之前为 `true` | `auto` |
| `FfxDx12Path`、`FfxDx12SRPath`、`FfxDx12FGPath`、`FfxVkPath` | 游戏 `ScalerAssistant` 文件夹中的 DLL | 同左 |

原本就存在的 `OptiScaler.ini` 会先备份，移除时放回。

### 6. 切换、更新、修复、移除

- 从超分菜单**切换**：先移除当前选项，再安装新的。在 FSR 4.1 Exact、Lossy 与 FSR 3 之间切换时，只会更换 FSR DLL 并修改 `OptiScaler.ini`。
- **更新**：HelixSR 文件夹有较新版本时，游戏会显示“↑ 有 HelixSR … 可用”；使用中的 OptiScaler／FSR 4.1 有较新的下载文件（或更改了 FSR 4.1 版本）时会显示“↑ 有较新的下载文件”。“↑ 全部更新”一次更新所有游戏。
- **修复**：游戏更新或在 Steam 中“验证游戏文件完整性”可能把游戏原文件放回。这时游戏会显示发生了什么，点击“修复”即可把超分放回，并把游戏的新文件保留为备份。
- **移除**会放回所有被替换或移走的文件，并去掉加入启动选项的那一项。

### 7. 无需编辑文件即可调整 HelixSR 设置

使用 DLSS 3.7 时，“⚙ 设置”以表单编辑游戏的 `helixsr.ini`（锐化、int8 网络、超级性能模式的最终缩放、wave 大小）。“默认”会省略该行；文件中的其他行和注释都会保留。

### 8. 实时状态与浮层提示

- 每 3 秒检查运行中的 Steam 游戏：从 `/proc/<pid>/maps` 确认游戏是否**真的加载了** HelixSR 或 FSR DLL（以及 OptiScaler 或 DLSS 加载器）。游戏开始使用超分之前不会加载，所以“尚未加载”会告诉你要在游戏中选什么。
- 使用 HelixSR 时，会从本次运行的 `helixsr.log` 显示 wave 大小和错误；RDNA 3 及以上使用 OptiScaler 方式、日志显示 wave32 时，会提供“设置 WaveSize = 64”。
- 游戏卡片上的 ⌄ 按钮会打开详细信息面板，里面有“查看 …log”（`helixsr.log` 或 `OptiScaler.log`）、打开游戏文件夹、OptiScaler 文件名，以及 DLSS 3.7 的“⚙ 设置”。
- 游戏启动时，右下角会出现小卡片显示结果约 10 秒（90 秒后仍未加载则显示提示）。它是独立的 X11 窗口，不会抢焦点；可用工具栏的开关关闭。

### 9. 启动、搜索、筛选、语言

- “▶ 启动”通过 Steam 打开游戏。可按名称（任何语言）或 App ID 搜索；筛选：可以超分的游戏、已安装超分、尚未安装超分、需要更新或修复、运行中、所有游戏。
- 12 种界面语言：台灣正體中文、简体中文、English、日本語、Deutsch、Français、Español、Italiano、ไทย、Tiếng Việt、Bahasa Melayu、हिन्दी。

### 10. 以安全为设计原则

- 游戏运行时不做任何更改；修改任何文件之前都会先确认下载文件和 HelixSR 文件夹。
- 每个被替换的文件都会保留，每次复制都逐字节比对，启动选项只会按上述说明增减那一项。
- DLSS 方式、FSR 4.1 Lossy 以及含反作弊的游戏都会先询问。请勿在联机游戏中使用修改过的超分：反作弊可能视为篡改。

### 11. 外观

- 参考 MAKO Assistant 的“Liquid Glass”风格：每款游戏一张卡片，含 Steam 封面、状态标签、游戏支持的技术，运行时还会显示真正加载了什么。⌄ 按钮会展开详细信息（图形 API、超分辨率技术、`.exe` 文件夹、OptiScaler 文件名、启动选项）和较少用的操作。
- 按钮为立体浮起的水晶风格：淡淡的色调与细边框，上半部有弧形高光，下缘内侧有一道微光，下方有柔和的阴影，全部由平涂的半透明图层构成，不带渐变。开关的圆钮同样浮起；主题切换的选中项是嵌在凹槽里的浮起水晶。青绿色为安装、蓝色为切换、琥珀色为更新、红色为移除。
- 深色、浅色或自动主题（跟随桌面）。活动记录在窗口底部的抽屉。

## HelixSR 2.0 与显卡

- **一键下载并构建 HelixSR**：“下载并构建 HelixSR”（在 HelixSR 窗口与 Steam Deck 插件中）会从 GitHub 发布页下载最新的 HelixSR（2.0 及以上），校验 SHA-256 后放到 `~/.local/share/scaler-assistant/helixsr`，再用 HelixSR 自己的构建程序（`setup/helixsr_setup.py`，原样运行）在这台电脑上构建。做法与 HelixSR 自己的 App 相同，因此无需终端，也不会进入游戏安装步骤。构建所需的东西也会备齐：带 numpy 的 Python（系统 Python 无法解压 NVIDIA 的 zstd 包时改用便携版 Python 3.14，帧生成无需另装 `zstd`），以及通过 Steam 的 Proton 或 Wine 运行的 Microsoft DirectX 着色器编译器。NVIDIA 的文件只在你于 App 中同意后才下载，构建结果只留在你的电脑上。Flatpak 版在主机上构建。再次运行只会补建缺少的部分；有新版本时会替换之前下载的版本。
- **HelixSR 2.0 及以上**把构建好的 DLL 放在 `HelixSR-fsrfg`，并提供两种方式：**HelixSR Scaler**（HelixSR 自带、放在 `.exe` 旁的 OptiScaler：游戏内选 DLSS；DX11 和 Vulkan 游戏也能用）与 **FSR 方式**（FSR drop-in）。Scaler 助手通过你 HelixSR 文件夹里的安装程序（`setup/helixsr_bridge.py`，即 HelixSR 官方应用使用的那一个）安装这两种方式，所以 HelixSR 的 setup、它的应用和 Scaler 助手都能识别、更新、移除彼此的安装。文件名仍由 Scaler 助手选择，需要时也会加入启动选项。以旧方式设置的游戏在更新时会改用 HelixSR Scaler。HelixSR 1.8／1.9 文件夹仍是原来的三种方式。
- **HelixSR 帧生成**（HelixSR 2.0）：带有 DLSS Frame Generation（Streamline 的 `sl.dlss_g.dll`）的 DirectX 12 游戏，安装 HelixSR Scaler 后卡片上（以及 Steam Deck 插件中）会出现“HelixSR 帧生成”开关。它通过 HelixSR 自己的安装程序（`scaler-fg`）切换，只修改 OptiScaler.ini 的 `[FrameGen]` 选项；打开后在游戏中开启 DLSS Frame Generation。需要 `./helixsr-setup.sh` 生成的帧生成文件（会下载 NVIDIA 的 DLSS Frame Generation 文件），在此之前开关会变灰并说明原因。新安装时默认关闭；更新或更改 OptiScaler 文件名会保留原来的状态。其他 DX12 游戏仍可在 HelixSR Scaler 菜单（Insert）中选择 AMD FSR 或 XeSS 帧生成；DX11／Vulkan 游戏与 FSR 方式只有超分。
- **较旧的 HelixSR 版本**：1.8.x 三种方式（FSR 方式、OptiScaler 方式、DLSS 方式）都能用。HelixSR 1.9.0～1.9.3 只附 FSR 方式的文件，所以 OptiScaler 与 DLSS 方式会变灰（“需要 HelixSR 1.8 或 2.0”）；没有 FSR 3.1 的游戏需要 HelixSR 2.0（HelixSR Scaler）。1.8.0 以前的版本不支持。
- **DLSS 方式仅限 GeForce**：使用 AMD 或 Intel GPU 时，游戏中无法选择 DLSS，所以（HelixSR 1.x 的）DLSS 方式会变灰并说明原因。
- **推荐 FSR 4.1 Lossy**：集成显卡（Steam Deck、ROG Ally Z1／Z2、Ryzen AI MAX）与 Intel GPU 只会在 FSR 4.1 的选项中标示“★ 推荐”。

## 与 HelixSR 自带的 setup 互通

使用 DLSS 3.7 时，Scaler 助手写入与 HelixSR setup 相同的安装记录（`helixsr-install.json`）、备份和文件名，所以 `helixsr-setup.sh`／`helixsr-uninstall.sh` 与 Scaler 助手都能识别对方安装的游戏。HelixSR 的 setup 会把游戏 `ScalerAssistant` 文件夹中的 FSR DLL 当成游戏自己的 FSR 3.1 DLL，可能把它换成 HelixSR；这时 Scaler 助手会把游戏标记为需要修复，点击“修复”即可移除 HelixSR。想在这类游戏中使用 DLSS 3.7，请直接在 Scaler 助手中选择。

## Steam Deck 插件（Decky Loader）

同一套程序也能在游戏模式中使用：[Decky Loader](https://decky.xyz) 的插件，位于快速访问菜单。

- **游戏**：可使用超分辨率的游戏，运行中的排在最前，各自显示状态标签，运行时还会显示真正加载了什么。选择游戏即可选用 DLSS 3.7（HelixSR，各种方式）、FSR 4.1 Exact／Lossy 或 FSR 3，或是更新、修复、移除、修改 OptiScaler 文件名、查看日志。事先询问与桌面版相同：下载文件、Lossy 警告、DLSS 方式与反作弊。
- **设置**：HelixSR 文件夹（文件选择器）、下载文件与 FSR 4.1 版本（Steam Deck 使用集成显卡版）、游戏启动时通知（显示超分辨率是否已加载），以及语言（默认与 Steam 相同）。
- 与桌面版共用 `state.json`、下载文件与启动选项记录，在其中一边设置的游戏另一边也看得到。启动选项通过 Steam 实时写入。
- 插件不包含：HelixSR 设置表单（请用桌面版），以及 HelixSR 本身的 `helixsr-setup.sh`（请在桌面模式运行一次）。
- 插件中的 **下载并构建 HelixSR** 在游戏模式下也能下载并构建 HelixSR 2.0 及以上（需要几分钟）。

安装：先在 Steam Deck 安装 Decky Loader，从 [Releases](https://github.com/mosesmoon/scaler-assistant/releases) 页面下载 `Scaler_Assistant-Decky-<版本>.zip`，再到 Decky 设置 →“开发者”（先在“常规”开启开发者模式）→“Install Plugin from ZIP File”。

## 安装 Scaler 助手

**AppImage（推荐）**：已内含 Python、Qt 和 7-Zip。

1. 从 [Releases](https://github.com/mosesmoon/scaler-assistant/releases) 页面下载 `Scaler_Assistant-<版本>-x86_64.AppImage`。
2. 设为可执行：右键 →“属性”→“权限”→“允许作为程序执行文件”（各文件管理器用词略有不同）。
3. 双击打开。

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

无法启动时，系统可能缺少 FUSE；请加上 `--appimage-extract-and-run` 运行。

**单一安装文件（.bin）**：`Scaler_Assistant-<版本>-x86_64.bin` 只为当前用户安装同一套内含程序（无需 root、无需 FUSE）到 `~/.local/opt/scaler-assistant`，并加入 `scaler-assistant` 命令与菜单项。**Flatpak**：`Scaler_Assistant-<版本>-x86_64.flatpak` 是单文件包，使用 Freedesktop 25.08 runtime（安装时从 Flathub 下载）。它可以读取主目录与其他磁盘（`/run/media` 下的 SD 卡），并通过 `flatpak-spawn --host` 看到 Steam 与游戏的进程。

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / 安装
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / 移除
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**从源码运行**：需要 Python 3.11 及以上和 PyQt6（Arch：`sudo pacman -S python-pyqt6`），以及解压 OptiScaler 用的 7-Zip 或 bsdtar（`sudo pacman -S 7zip`）。

```bash
./scaler-assistant     # 直接运行
./install.sh           # 安装到 ~/.local/share/scaler-assistant，并添加菜单项
```

## 已知限制

- **只支持 Steam 游戏。** FSR 4.1／FSR 3 的安装方式已用 OptiScaler 0.9.4 逐一核对过文件；但每款游戏表现不同，游戏出问题时请查 OptiScaler 的兼容性列表，或为 OptiScaler 换个文件名。
- Direct3D 11 与 Vulkan 游戏的 FSR 4.1 经由 OptiScaler 的 Direct3D 12 路径，测试程度较低。
- HelixSR 变化很快。Scaler 助手需要 HelixSR 1.8.0 或更新版本，并遵循 1.8.x／1.9.x／2.0.x 的文件布局。
- Steam Deck 游戏模式（gamescope）下不会显示浮层提示。Decky 插件会改用 Steam 通知显示。
- 泰语、越南语、马来语和印地语的右键菜单为英文（Qt 没有官方翻译）。Steam 没有马来语和印地语的游戏名称。

## 数据存放位置

| 位置 | 内容 |
|---|---|
| `~/.config/scaler-assistant/state.json` | Scaler 助手的状态：HelixSR 文件夹、游戏列表、语言、FSR 4.1 版本、你选的 OptiScaler 文件名、它加入启动选项的项目（首次会从 HelixSR 助手接手） |
| `~/.local/share/scaler-assistant/components/` | 下载的 OptiScaler 与 FSR 4.1 文件 |
| `~/homebrew/plugins/scaler-assistant/` | Steam Deck 上的 Decky 插件（使用与上面相同的状态和下载文件） |
| `<游戏>/…/ScalerAssistant/` | FSR 4.1／FSR 3：FidelityFX DLL、`scaler-install.json`、`backup/` |
| `<游戏>/…/HelixSR/helixsr-install.json`、游戏 FSR DLL 旁 | DLSS 3.7：HelixSR 的安装记录（与 HelixSR setup 共用） |
| `<游戏>/…/helixsr.ini`、`helixsr.log`、`OptiScaler.ini`、`OptiScaler.log` | 设置与日志 |

## 许可

Scaler 助手是独立的非官方工具，与 HelixSR 作者、NVIDIA、AMD、OptiScaler 项目或 fsr4-shader-performance-overrides 项目没有关联，也未经其认可，且不含它们的任何文件。在你同意时，它会从各自的 GitHub Releases 下载 OptiScaler（GPL-3.0；fakenvapi 为 MIT；AMD 的 FidelityFX DLL 依 AMD 许可）和 FSR 4.1 DLL（GPL-2.0-or-later，附 AMD 声明的修改版 AMD DLL）。AppImage 内附 7-Zip 的 `7zzs`（GNU LGPL 附 unRAR 限制、BSD；附许可文件）。HelixSR 依 HelixSR Freeware License 免费使用；运行 setup 后，HelixSR 的 DLL 会包含 NVIDIA 的神经网络，所以 Scaler 助手只会在你自己电脑上的文件夹之间复制它们。请勿分享或上传这些文件。Decky 插件也内附同一个 `7zzs`。
