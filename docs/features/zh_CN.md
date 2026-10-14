# HelixSR 助手 — 功能介绍

[English](en.md) · [台灣正體中文](zh_TW.md) · **简体中文** · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**HelixSR 助手**是一款 Linux 桌面工具，可以一键为 Steam 游戏安装、切换、更新或移除 **[HelixSR](https://github.com/lonewolf0622/HelixSR)**，并在你玩游戏时显示 HelixSR 是否真的在运行。

HelixSR 通过 Proton，把 NVIDIA DLSS Model E 超分辨率神经网络以普通的 Direct3D 12 计算着色器运行在 AMD 显卡（RDNA 1 及更新）上。

## 这款工具适合谁

HelixSR 没有启动选项，也没有集中的配置文件。它的做法是把 DLL 放进每款游戏的文件夹，每款游戏有三种方式可选。手动安装意味着你要：

1. 查清每款游戏自带哪些超分辨率技术（FSR 3.1、DLSS、XeSS、FSR 2），以及主 `.exe` 在哪里。
2. 为游戏选对安装方式，把游戏原有文件改名保留，再把 HelixSR 的文件复制到正确位置。
3. 如果用 OptiScaler 方式，还要在 `OptiScaler.ini` 中填入正确路径。
4. 每次 HelixSR 更新都要重做一遍；游戏更新覆盖了 HelixSR 时也要再做一遍。
5. 打开 `helixsr.log`，才能确认 HelixSR 到底有没有在运行。

HelixSR 助手把这些都集中在一个窗口里。HelixSR 自带的 setup 在终端里逐个询问每款游戏；HelixSR 助手则把它们列成列表，点一下即可。

## 使用前的准备

> ⚠ **HelixSR 助手不包含 HelixSR，也不会替你下载。** 它只会从你自己设置好的 HelixSR 文件夹复制文件。

1. **下载 HelixSR**（1.8.0 或更新）：从它的 [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) 下载，解压到一个会保留的文件夹，例如主目录。
2. **在该文件夹中运行一次 `./helixsr-setup.sh`**。它会询问是否下载 NVIDIA 的 DLSS DLL，然后用它构建 HelixSR 的神经网络（约一分钟）。当它开始逐个询问游戏时，可以全部回答 `n` 或直接关闭窗口：游戏交给 HelixSR 助手处理。如果助手找到了文件夹但尚未设置，会提供“在终端中运行 setup”按钮。
3. **AMD 显卡，RDNA 1 或更新**（Radeon RX 5000 及更新、Steam Deck、搭载 RDNA 核显的 Ryzen）。Radeon Vega 在 HelixSR 1.9.0 中为实验性支持。
4. **通过 Proton 运行、自带 FSR 3.1、DLSS、XeSS 或 FSR 2 的 Direct3D 12 游戏**。

首次启动时，HelixSR 助手会在主目录、下载、桌面和 Games 文件夹中查找已设置好的 HelixSR 文件夹。你随时可以点击“选择 HelixSR 文件夹…”或顶部的 HelixSR 标签改选其他文件夹。

## HelixSR 进入游戏的三种方式

以下是 HelixSR 本身的三种方式（字母是 HelixSR setup 使用的回答）。HelixSR 助手只列出该游戏可用的方式，并把默认方式放在第一位。

| 方式 | 游戏需要具备 | 游戏文件夹中的变化 | 游戏内选择 |
|---|---|---|---|
| **FSR 方式**（f，FSR 3.1 游戏的默认） | FSR 3.1 | 游戏的 `amd_fidelityfx_upscaler_dx12.dll`（或 `amd_fidelityfx_dx12.dll`）被 HelixSR 替换；游戏原文件保留为 `*.original.dll` | **AMD FSR** |
| **OptiScaler 方式**（o） | DLSS、XeSS 或 FSR 2 | 在游戏 `.exe` 旁放入 OptiScaler（你 HelixSR 文件夹中的官方版本），并把它的 FSR 3.1 后端指向旁边的 `HelixSR` 文件夹；被替换的文件都会移到 `HelixSR/backup` | **DLSS**（FSR 或 XeSS 也可以） |
| **DLSS 方式**（d，实验性） | DLSS | 在游戏 `.exe` 旁放入 HelixSR 的 DLSS 加载器（`dxgi.dll`），并以 `nvngx.dll` 名称放入 HelixSR | **DLSS** |

## 功能

### 1. 扫描 Steam 游戏及其超分辨率技术

- 首次打开时会扫描所有 Steam 游戏库（包括其他硬盘上的游戏库）。安装新游戏后请点击“⟳ 重新扫描 Steam 游戏”。
- 在每款游戏的文件夹中查找 FSR 3.1、DLSS、XeSS 和 FSR 2 的 DLL，并根据 Steam 的启动信息找出主 `.exe` 所在文件夹（能处理启动器和 Unreal 的 `*-Shipping.exe`）。
- 会标出带**反作弊**（Easy Anti-Cheat、BattlEye）的游戏。
- 游戏名称按界面语言显示 Steam 的本地化名称，并按该语言的习惯排序。可使用 HelixSR 的游戏排在前面；默认启用“可使用 HelixSR 的游戏”筛选。

### 2. 一键安装

- 点击“安装 HelixSR”以默认方式安装，或点击旁边的箭头选择其他方式。每种方式都会说明游戏内要选什么。
- 在做任何更改前，会先确认 HelixSR 文件夹已设置好（网络已构建），并且游戏没有在运行。
- DLSS 方式会先说明风险并要求确认。带反作弊的游戏也会要求确认。
- 完成后，日志区会列出替换了哪些文件、游戏原文件保留在哪里，以及游戏内要选什么。

### 3. 切换方式、更新与修复

- **切换**：“更多”→“改用…”会先移除当前方式（把文件全部放回），再安装新方式。你的 HelixSR 设置会随游戏一起迁移。
- **更新**：当你的 HelixSR 文件夹中的版本比游戏中的新（HelixSR 新版本，或重新构建了网络），游戏会显示“↑ 有新版 HelixSR …”和“↑ 更新”按钮；“↑ 全部更新”可一次更新所有游戏。
- **修复**：游戏更新或在 Steam 中“验证游戏文件的完整性”可能会用游戏自己的文件覆盖 HelixSR。这时游戏会说明发生了什么并显示“修复”按钮：它会把 HelixSR 放回原处，并把游戏的新文件保留为备份。
- 当下载文件夹（或其他常见位置）出现较新且已设置好的 HelixSR 文件夹时，助手会询问一次是否改用。

### 4. 移除

- “移除”会去掉 HelixSR，并把它替换或移动过的每个文件都恢复原状。
- 游戏的 HelixSR 设置（`helixsr.ini`）默认保留，除非勾选“同时移除这款游戏的 HelixSR 设置”。
- 你自己放进游戏 `my-fsr` 文件夹的文件绝不会被删除。

### 5. 无需编辑文件即可调整 HelixSR 设置

“⚙ 设置”以表单编辑游戏的 `helixsr.ini`。只提供 HelixSR README 中记载的设置：

| 分组 | 设置 | 可选值 |
|---|---|---|
| 锐化 | 锐化方式 | 默认、关闭、NVIDIA、RCAS |
| | 锐度 | 0.00 – 1.00 |
| | 跟随游戏的锐度滑块 | 默认、是、否 |
| 超分辨率（HelixSR 1.9.0 及更新） | int8 网络 | 默认（自动）、自动、开启、关闭 |
| | 超级性能模式的最终缩放 | 默认（Lanczos）、Lanczos、EASU（FSR 1） |
| 兼容性 | Wave 大小 | 默认、64、32 |

选择“默认”则不写入该行，HelixSR 会使用自己的默认值。文件中的注释和其他设置都会原样保留。文件会写在该游戏安装方式下 HelixSR DLL 的旁边（游戏的 `HelixSR` 文件夹、游戏 FSR DLL 旁，或 `.exe` 旁）。

### 6. HelixSR 实时状态（实际运行的内容）

每 3 秒检查一次正在运行的 Steam 游戏：

- Proton 直接从文件加载 Windows DLL，所以助手能从 `/proc/<pid>/maps` 看出游戏是否**真的加载了 HelixSR**（以及 OptiScaler 或 DLSS 加载器）。
- 游戏开始使用超分辨率技术后才会加载 HelixSR。因此“HelixSR 尚未加载”会告诉你要在游戏的图形设置中选什么。
- 读取本次运行的 `helixsr.log`：显示网络内核的 wave 大小和错误信息。“更多”→“查看 helixsr.log”可以查看完整日志并复制。
- 在 **RDNA 3 或更新**显卡、使用 OptiScaler 方式的游戏中，如果日志显示 wave32，HelixSR 的 README 建议设置 `WaveSize = 64`。助手会检测到这种情况，提供一键“设置 WaveSize = 64”。
- 顶部的显卡标签会显示你的显卡世代（例如“AMD RDNA 3 (gfx1100)”）。

### 7. 游戏启动时的浮层提示

如果装有 HelixSR 的游戏启动时 HelixSR 助手正开着，HelixSR 一加载就会在右下角显示约 10 秒的小卡片，列出版本、安装方式和 wave 大小（每次启动只显示一次；助手打开前就在运行的游戏不会显示）。如果 90 秒后 HelixSR 仍未加载，卡片会提示你在游戏中要选什么。浮层是独立的 X11（XWayland）窗口，不会抢走焦点，鼠标点击会直接穿透。可用工具栏的复选框关闭。在 Steam Deck 游戏模式（gamescope）中不会显示。

### 8. 启动游戏、搜索与筛选

- 每一行都有“▶ 启动”按钮（通过 `steam://rungameid/<AppID>`）；游戏运行时显示“运行中”。
- 可按游戏名称（任何语言）或 App ID 搜索。筛选：可使用 HelixSR 的游戏、已安装、未安装、需要更新或修复、运行中、全部游戏。

### 9. 12 种界面语言

台灣正體中文、简体中文、English、日本語、Deutsch、Français、Español、Italiano、ไทย、Tiếng Việt、Bahasa Melayu、हिन्दी。首次启动时使用系统语言；可在右上角切换（立即生效并记住）。

### 10. 以安全为设计原则

- HelixSR 文件夹尚未设置好或游戏正在运行时，不会做任何更改。
- HelixSR 替换的每个文件都会保留（`*.original.dll` 或 `HelixSR/backup`），每个复制的文件都会逐字节校验。
- 你原有的 `OptiScaler.ini` 会先备份，移除时还原；你在游戏 `HelixSR` 文件夹中手动替换的 FSR DLL 在更新时会保留。
- DLSS 方式和带反作弊的游戏都需要你明确确认。

## 与 HelixSR 自带的 setup 互通

HelixSR 助手写入的安装记录（`helixsr-install.json`）、备份和文件名都与 HelixSR 的 setup 相同。因此：

- 用 `helixsr-setup.sh` 安装的游戏，在 HelixSR 助手中会显示为已安装（含安装方式），也能在这里切换、更新或移除。
- 用 HelixSR 助手安装的游戏，HelixSR 的 setup 和 `helixsr-uninstall.sh` 也能识别，可以更新或移除。

## 安装 HelixSR 助手

**AppImage（推荐）**：已内置 Python 和 Qt，不需要另外安装任何东西。

1. 从 [Releases](https://github.com/mosesmoon/helixsr-assistant/releases) 页面下载 `HelixSR_Assistant-<版本>-x86_64.AppImage`。
2. 设为可执行：右键点击文件 →“属性”→“权限”，勾选“允许作为程序执行文件”（不同文件管理器的用词略有不同）。
3. 双击即可打开 HelixSR 助手。

或在终端中运行：

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

如果无法启动，可能是系统缺少 FUSE；请改用 `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run` 运行。

**从源码运行**：需要 Python 3.11 或更新以及 PyQt6（Arch：`sudo pacman -S python-pyqt6`）。

```bash
./helixsr-assistant    # 直接运行
./install.sh           # 安装到 ~/.local/share/helixsr-assistant，并添加应用程序菜单项
```

## 已知限制

- **仅支持 Steam 游戏。** 其他商店的游戏请使用 HelixSR 自带的 setup（把游戏文件夹拖进去）。
- HelixSR 本身只支持 Direct3D 12 游戏。列表中带 DLSS 或 FSR DLL 的游戏仍可能是 Vulkan 或 Direct3D 11，此时 HelixSR 不起作用。
- HelixSR 更新非常快。HelixSR 助手需要 HelixSR 1.8.0 或更新，并按照 1.8.x、1.9.x 的安装结构制作；如果以后的 HelixSR 改变了安装方式，在 HelixSR 助手更新之前请先使用 HelixSR 自带的 setup。
- 浮层在 Steam Deck 游戏模式（gamescope）中不会显示；原生 Wayland 独占全屏的游戏可能会遮住它。
- 泰语、越南语、马来语和印地语界面中，右键菜单为英文（Qt 没有这些语言的官方翻译）。Steam 没有马来语和印地语的游戏名称，所以这两种语言始终显示原始名称。

## 数据存放位置

| 位置 | 内容 |
|---|---|
| `~/.config/helixsr-assistant/state.json` | HelixSR 助手自身的状态：HelixSR 文件夹、游戏列表缓存、界面语言、浮层设置 |
| `<游戏>/…/HelixSR/helixsr-install.json`、游戏 FSR DLL 旁 | HelixSR 的安装记录（与 HelixSR 自带的 setup 共用） |
| `<游戏>/…/helixsr.ini` | 该游戏的 HelixSR 设置 |
| `<游戏>/…/helixsr.log` | 游戏上次运行时 HelixSR 的报告 |

## 许可

HelixSR 助手是独立的非官方工具，与 HelixSR 作者、NVIDIA、AMD 或 OptiScaler 项目无关，也未获其认可，且不包含它们的任何文件。HelixSR 依据 HelixSR Freeware License 免费使用。HelixSR 的 setup 运行后，HelixSR 的 DLL 中包含 NVIDIA 的神经网络：HelixSR 助手只会在你自己电脑上的文件夹之间复制它们。请勿分享或上传这些文件。
