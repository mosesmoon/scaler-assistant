# HelixSR 助手 — 功能介紹

[English](en.md) · **台灣正體中文** · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**HelixSR 助手**是一套 Linux 桌面工具，能一鍵為 Steam 遊戲安裝、切換、更新或移除 **[HelixSR](https://github.com/lonewolf0622/HelixSR)**，並在你玩遊戲時顯示 HelixSR 是否真的在運作。

HelixSR 透過 Proton，把 NVIDIA DLSS Model E 的升頻神經網路，以一般的 Direct3D 12 運算著色器跑在 AMD 顯示卡（RDNA 1 以上）上。

## 這套工具是給誰用的

HelixSR 沒有啟動選項，也沒有集中的設定檔。它的做法是把 DLL 放進每款遊戲的資料夾，每款遊戲有三種方式可選。手動安裝代表你得：

1. 查出每款遊戲內建哪些升頻技術（FSR 3.1、DLSS、XeSS、FSR 2），以及主要 `.exe` 在哪裡。
2. 為遊戲挑對安裝方式，把遊戲原本的檔案改名保留，再把 HelixSR 的檔案複製到正確位置。
3. 若用 OptiScaler 方式，還要在 `OptiScaler.ini` 填入正確路徑。
4. 每次 HelixSR 更新都要重做一次；遊戲更新蓋掉 HelixSR 時也要再做一次。
5. 打開 `helixsr.log`，才能確認 HelixSR 到底有沒有在跑。

HelixSR 助手把這些都整合在一個視窗裡。HelixSR 自己的 setup 是在終端機逐一詢問每款遊戲；HelixSR 助手則把它們列成清單，按一下就好。

## 使用前必須先準備

> ⚠ **HelixSR 助手不包含 HelixSR，也不會替你下載。** 它只會從你自己設定好的 HelixSR 資料夾複製檔案。

1. **下載 HelixSR**（1.8.0 以上）：從它的 [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) 下載，解壓縮到會保留的資料夾，例如家目錄。
2. **在該資料夾執行一次 `./helixsr-setup.sh`**。它會詢問是否下載 NVIDIA 的 DLSS DLL，再用它建立 HelixSR 的神經網路（約一分鐘）。當它開始逐一詢問遊戲時，可以全部回答 `n` 或直接關閉視窗：遊戲交給 HelixSR 助手處理。如果助手找到資料夾但尚未設定，會提供「在終端機執行 setup」按鈕。
3. **AMD 顯示卡，RDNA 1 以上**（Radeon RX 5000 以上、Steam Deck、搭載 RDNA 內顯的 Ryzen）。Radeon Vega 在 HelixSR 1.9.0 屬實驗性支援。
4. **透過 Proton 執行、內建 FSR 3.1、DLSS、XeSS 或 FSR 2 的 Direct3D 12 遊戲**。

第一次啟動時，HelixSR 助手會在家目錄、下載、桌面和 Games 資料夾中尋找已設定好的 HelixSR 資料夾。你隨時可以按「選擇 HelixSR 資料夾…」或上方的 HelixSR 標籤改選別的資料夾。

## HelixSR 進入遊戲的三種方式

以下是 HelixSR 本身的三種方式（英文字母是 HelixSR setup 使用的回答）。HelixSR 助手只會列出該遊戲可用的方式，並把預設方式放在第一個。

| 方式 | 遊戲需要具備 | 遊戲資料夾中的變更 | 遊戲內選擇 |
|---|---|---|---|
| **FSR 方式**（f，FSR 3.1 遊戲的預設） | FSR 3.1 | 遊戲的 `amd_fidelityfx_upscaler_dx12.dll`（或 `amd_fidelityfx_dx12.dll`）被 HelixSR 取代；遊戲原檔保留為 `*.original.dll` | **AMD FSR** |
| **OptiScaler 方式**（o） | DLSS、XeSS 或 FSR 2 | 在遊戲 `.exe` 旁放入 OptiScaler（你 HelixSR 資料夾中的官方版本），把它的 FSR 3.1 後端指向旁邊的 `HelixSR` 資料夾；被取代的檔案都會移到 `HelixSR/backup` | **DLSS**（FSR 或 XeSS 也可以） |
| **DLSS 方式**（d，實驗性） | DLSS | 在遊戲 `.exe` 旁放入 HelixSR 的 DLSS 載入器（`dxgi.dll`），並以 `nvngx.dll` 名稱放入 HelixSR | **DLSS** |

## 功能

### 1. 掃描 Steam 遊戲與其升頻技術

- 第一次開啟時會掃描所有 Steam 遊戲庫（包含其他硬碟上的遊戲庫）。安裝新遊戲後請按「⟳ 重新掃描 Steam 遊戲」。
- 在每款遊戲的資料夾中尋找 FSR 3.1、DLSS、XeSS 和 FSR 2 的 DLL，並從 Steam 的啟動資訊找出主要 `.exe` 所在資料夾（能處理啟動器和 Unreal 的 `*-Shipping.exe`）。
- 會標示含有**反作弊**（Easy Anti-Cheat、BattlEye）的遊戲。
- 遊戲名稱依介面語言顯示 Steam 的在地化名稱，並依該語言的習慣排序。可使用 HelixSR 的遊戲排在前面；預設啟用「可使用 HelixSR 的遊戲」篩選。

### 2. 一鍵安裝

- 按「安裝 HelixSR」以預設方式安裝，或按旁邊的箭頭選擇其他方式。每種方式都會告訴你遊戲內要選什麼。
- 在做任何變更前，會先確認 HelixSR 資料夾已設定好（網路已建立），以及遊戲沒有在執行。
- DLSS 方式會先說明風險並要求確認。含反作弊的遊戲也會要求確認。
- 完成後，記錄區會列出取代了哪些檔案、遊戲原檔保留在哪裡，以及遊戲內要選什麼。

### 3. 切換方式、更新與修復

- **切換**：「更多」→「改用…」會先移除目前的方式（把檔案全部放回），再安裝新方式。你的 HelixSR 設定會跟著遊戲一起帶過去。
- **更新**：當你的 HelixSR 資料夾版本比遊戲中的新（HelixSR 新版本，或重新建立了網路），遊戲會顯示「↑ 有新版 HelixSR …」和「↑ 更新」按鈕；「↑ 全部更新」可一次更新所有遊戲。
- **修復**：遊戲更新或在 Steam「驗證遊戲檔案完整性」可能會用遊戲自己的檔案蓋掉 HelixSR。這時遊戲會說明發生什麼事並顯示「修復」按鈕：它會把 HelixSR 放回原位，並把遊戲的新檔案保留為備份。
- 當下載資料夾（或其他常見位置）出現較新且已設定好的 HelixSR 資料夾時，助手會詢問一次是否改用。

### 4. 移除

- 「移除」會拿掉 HelixSR，並把它取代或搬移過的每個檔案都恢復原狀。
- 遊戲的 HelixSR 設定（`helixsr.ini`）預設保留，除非勾選「一併移除這款遊戲的 HelixSR 設定」。
- 你自己放進遊戲 `my-fsr` 資料夾的檔案絕不會被刪除。

### 5. 不必編輯檔案就能調整 HelixSR 設定

「⚙ 設定」以表單編輯遊戲的 `helixsr.ini`。只提供 HelixSR README 有記載的設定：

| 群組 | 設定 | 可選值 |
|---|---|---|
| 銳利化 | 銳利化方式 | 預設、關閉、NVIDIA、RCAS |
| | 銳利度 | 0.00 – 1.00 |
| | 跟隨遊戲的銳利度滑桿 | 預設、是、否 |
| 升頻（HelixSR 1.9.0 以上） | int8 網路 | 預設（自動）、自動、開啟、關閉 |
| | 超高效能模式的最後縮放 | 預設（Lanczos）、Lanczos、EASU（FSR 1） |
| 相容性 | Wave 大小 | 預設、64、32 |

選「預設」就不寫入該行，HelixSR 會使用自己的預設值。檔案中的註解和其他設定都會原樣保留。檔案會寫在該遊戲安裝方式下 HelixSR DLL 的旁邊（遊戲的 `HelixSR` 資料夾、遊戲 FSR DLL 旁，或 `.exe` 旁）。

### 6. HelixSR 即時狀態（實際在運作的內容）

每 3 秒檢查一次執行中的 Steam 遊戲：

- Proton 是直接從檔案載入 Windows DLL，所以助手能從 `/proc/<pid>/maps` 看出遊戲是否**真的載入了 HelixSR**（以及 OptiScaler 或 DLSS 載入器）。
- 遊戲要開始使用升頻技術才會載入 HelixSR。因此「HelixSR 尚未載入」會告訴你要在遊戲的畫面設定選什麼。
- 讀取本次執行的 `helixsr.log`：顯示網路核心的 wave 大小和錯誤訊息。「更多」→「檢視 helixsr.log」可以看完整記錄並複製。
- 在 **RDNA 3 以上**顯示卡、使用 OptiScaler 方式的遊戲中，若記錄顯示 wave32，HelixSR 的 README 建議設定 `WaveSize = 64`。助手會偵測到這種情況，提供一鍵「設定 WaveSize = 64」。
- 上方的顯示卡標籤會顯示你的顯示卡世代（例如「AMD RDNA 3 (gfx1100)」）。

### 7. 遊戲啟動時的浮動提示

如果裝有 HelixSR 的遊戲啟動時 HelixSR 助手開著，HelixSR 一載入就會在右下角顯示約 10 秒的小卡片，列出版本、安裝方式和 wave 大小（每次啟動只顯示一次；助手開啟前就在執行的遊戲不會顯示）。如果 90 秒後 HelixSR 仍未載入，卡片會提示你在遊戲中要選什麼。浮動提示是獨立的 X11（XWayland）視窗，不會搶走焦點，滑鼠點擊會直接穿透。可用工具列的核取方塊關閉。在 Steam Deck 遊戲模式（gamescope）中不會顯示。

### 8. 啟動遊戲、搜尋與篩選

- 每一列都有「▶ 啟動」按鈕（透過 `steam://rungameid/<AppID>`）；遊戲執行時會顯示「執行中」。
- 可用遊戲名稱（任何語言）或 App ID 搜尋。篩選：可使用 HelixSR 的遊戲、已安裝、未安裝、需要更新或修復、執行中、全部遊戲。

### 9. 12 種介面語言

台灣正體中文、简体中文、English、日本語、Deutsch、Français、Español、Italiano、ไทย、Tiếng Việt、Bahasa Melayu、हिन्दी。第一次啟動時使用系統語言；可在右上角切換（立即生效並記住）。

### 10. 以安全為設計原則

- HelixSR 資料夾尚未設定好、或遊戲正在執行時，不會做任何變更。
- HelixSR 取代的每個檔案都會保留（`*.original.dll` 或 `HelixSR/backup`），每個複製的檔案都會逐位元組比對確認。
- 你原本就有的 `OptiScaler.ini` 會先備份，移除時還原；你在遊戲 `HelixSR` 資料夾中手動替換的 FSR DLL，更新時會保留。
- DLSS 方式和含反作弊的遊戲都需要你明確確認。

## 與 HelixSR 本身的 setup 互通

HelixSR 助手寫入的安裝紀錄（`helixsr-install.json`）、備份和檔名都和 HelixSR 的 setup 相同。因此：

- 用 `helixsr-setup.sh` 安裝的遊戲，在 HelixSR 助手中會顯示為已安裝（含安裝方式），也能在這裡切換、更新或移除。
- 用 HelixSR 助手安裝的遊戲，HelixSR 的 setup 和 `helixsr-uninstall.sh` 也認得，可以更新或移除。

## 安裝 HelixSR 助手

**AppImage（建議）**：已內含 Python 和 Qt，不需要另外安裝任何東西。

1. 從 [Releases](https://github.com/mosesmoon/helixsr-assistant/releases) 頁面下載 `HelixSR_Assistant-<版本>-x86_64.AppImage`。
2. 設定為可執行：對檔案按右鍵 →「內容」→「權限」，勾選「允許以程式執行檔案」（各檔案管理員的用詞略有不同）。
3. 按兩下即可開啟 HelixSR 助手。

或在終端機執行：

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

如果無法啟動，可能是系統缺少 FUSE；請改用 `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run` 執行。

**從原始碼執行**：需要 Python 3.11 以上和 PyQt6（Arch：`sudo pacman -S python-pyqt6`）。

```bash
./helixsr-assistant    # 直接執行
./install.sh           # 安裝到 ~/.local/share/helixsr-assistant，並建立應用程式選單項目
```

## 已知限制

- **只支援 Steam 遊戲。** 其他商店的遊戲請用 HelixSR 本身的 setup（把遊戲資料夾拖進去）。
- HelixSR 本身只支援 Direct3D 12 遊戲。清單中有 DLSS 或 FSR DLL 的遊戲仍可能是 Vulkan 或 Direct3D 11，這時 HelixSR 不會有作用。
- HelixSR 更新非常快。HelixSR 助手需要 HelixSR 1.8.0 以上，並依 1.8.x、1.9.x 的安裝結構製作；如果之後的 HelixSR 改變了安裝方式，在 HelixSR 助手更新前請先用 HelixSR 本身的 setup。
- 浮動提示在 Steam Deck 遊戲模式（gamescope）中不會顯示；原生 Wayland 獨佔全螢幕的遊戲可能會蓋住它。
- 泰文、越南文、馬來文和印地文介面中，右鍵選單為英文（Qt 沒有這些語言的官方翻譯）。Steam 沒有馬來文和印地文的遊戲名稱，所以這兩種語言一律顯示原始名稱。

## 資料儲存位置

| 位置 | 內容 |
|---|---|
| `~/.config/helixsr-assistant/state.json` | HelixSR 助手自己的狀態：HelixSR 資料夾、遊戲清單快取、介面語言、浮動提示設定 |
| `<遊戲>/…/HelixSR/helixsr-install.json`、遊戲 FSR DLL 旁 | HelixSR 的安裝紀錄（與 HelixSR 本身的 setup 共用） |
| `<遊戲>/…/helixsr.ini` | 該遊戲的 HelixSR 設定 |
| `<遊戲>/…/helixsr.log` | 遊戲上次執行時 HelixSR 的回報 |

## 授權

HelixSR 助手是獨立的非官方工具，與 HelixSR 作者、NVIDIA、AMD 或 OptiScaler 專案沒有關聯，也未經其認可，且不含它們的任何檔案。HelixSR 依 HelixSR Freeware License 免費使用。HelixSR 的 setup 執行後，HelixSR 的 DLL 會包含 NVIDIA 的神經網路：HelixSR 助手只會在你自己電腦上的資料夾之間複製它們。請勿分享或上傳這些檔案。
