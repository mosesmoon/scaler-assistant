# Scaler 助手 — 功能介紹

[English](en.md) · **台灣正體中文** · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**Scaler 助手**是一套 Linux 桌面工具，讓你替每款 Steam 遊戲選擇升頻技術——**DLSS 3.7（[HelixSR](https://github.com/lonewolf0622/HelixSR)）**、**FSR 4.1**（來自 [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides) 的 Exact 或 Lossy，RX 9000 則用 AMD 原生版）或 **FSR 3**——並一鍵安裝、切換、更新、修復、移除。玩遊戲時還會顯示升頻是否真的在運作。

## 適合誰使用

在 Linux 上手動替遊戲換上更好的升頻，需要：

1. 查出遊戲內建哪些升頻技術（DLSS、XeSS、FSR 2、FSR 3.1）、用哪種繪圖 API，以及主要 `.exe` 在哪裡。
2. 把 OptiScaler 以遊戲能接受的檔名放到 `.exe` 旁，附上需要的 FidelityFX DLL，並依想用的升頻技術修改 `OptiScaler.ini`。
3. 檔名需要時，在遊戲的 Steam 啟動選項加入 `WINEDLLOVERRIDES`——而且不能弄壞原本的內容。
4. 依顯示卡下載正確的 FSR 4.1 DLL，或照 HelixSR README 的說明設定 HelixSR。
5. 每次更新都再做一次；遊戲更新蓋掉檔案時也要再做一次。

Scaler 助手在一個視窗裡完成這一切，並保留所有被取代的檔案，移除時遊戲會完全恢復原狀。

## 每款遊戲可選的項目

可選項目取決於遊戲的繪圖 API 和升頻技術。遊戲本身必須至少內建一種升頻技術（DLSS、XeSS、FSR 2 或 FSR 3.1）：OptiScaler 和 HelixSR 就是接手這些技術。

| 選項 | 遊戲需要 | 放進遊戲資料夾的內容 | 遊戲內選擇 |
|---|---|---|---|
| **DLSS 3.7（HelixSR）· FSR 方式** | Direct3D 12、FSR 3.1 | 遊戲的 FSR 3.1 DLL 換成 HelixSR（遊戲原檔保留為 `*.original.dll`） | AMD FSR |
| **DLSS 3.7（HelixSR）· OptiScaler 方式** | Direct3D 12、DLSS／XeSS／FSR 2 | `.exe` 旁放入 OptiScaler，指向 `HelixSR` 資料夾 | DLSS |
| **DLSS 3.7（HelixSR）· DLSS 方式**（實驗性） | Direct3D 12、DLSS | HelixSR 的 DLSS 載入器（`dxgi.dll`）和以 `nvngx.dll` 為名的 HelixSR | DLSS |
| **FSR 4.1 Exact** | 四種升頻技術任一種 | `.exe` 旁放入 OptiScaler；FidelityFX DLL 和 Exact 版 FSR 4.1 DLL 放在 `ScalerAssistant` 資料夾 | DLSS、FSR 或 XeSS |
| **FSR 4.1 Lossy** | 同上 | 同上，改用 Lossy 版 FSR 4.1 DLL | DLSS、FSR 或 XeSS |
| **FSR 4.1.2 Lite / Lite Lossy** | 同上 | 同上，改用 4.1.2l-exact / 4.1.2l-lossy 版 FSR 4.1 DLL | DLSS、FSR 或 XeSS |
| **FSR 4.1（AMD）**——RX 9000（RDNA 4）以此取代 Exact／Lossy | 同上 | 同上，改用 AMD 原生 FSR 4.1 DLL | DLSS、FSR 或 XeSS |
| **FSR 3** | 同上 | 同上；OptiScaler 使用 FSR 3.1.5 | DLSS、FSR 或 XeSS |

- **Exact** 的畫面與 AMD 的 FSR 4.1 逐位元組相同，只是著色器更快。**Lossy** 更快，但畫面會略有不同；第一次使用前，Scaler 助手會先顯示一次它的 `WARNING.txt`。不確定的話就選 Exact。
- **Lossy** 自 dll-2026-10-29 的 DLL 起，就是原本的 Lossy2 再經訓練（舊的 Lossy 已移除）：樹葉中的黑點少了很多，但畫面變亮時跟得較慢。**Lite** 與 **Lite Lossy** 執行 AMD 較小的 FSR 4.1.2 Lite 網路（很可能就是 AMD 驅動程式給內建顯示晶片用的）：Lite 的畫面與 AMD 的 Lite 逐位元組相同，且略快；Lite Lossy 每兩格才跑一次網路，是最快的版本，畫面接近 Lite。Lite 在靜態畫面與部分動態上比完整 FSR 4 略不精確，另一些動態則較好。Lossy 與 Lite Lossy 會各自先顯示一次它們的 `WARNING.txt`。用 Lossy2 設定的遊戲會顯示為可更新，更新後改用 Lossy。
- HelixSR 只能用於 **Direct3D 12** 遊戲，所以只有這類遊戲會出現 DLSS 3.7。FSR 4.1 和 FSR 3 也能用於 **Direct3D 11 與 Vulkan** 遊戲：FSR 3 原生支援，FSR 4.1 則透過 OptiScaler 的 Direct3D 12 路徑（測試程度不如 Direct3D 12 遊戲）。
- 在遊戲那一列按 **「選擇升頻」**（已安裝的遊戲按 **「升頻」**）：DLSS 3.7（HelixSR）會展開子選單列出它的方式，目前的選擇會打勾。切換時會先移除目前的項目並全部還原。

## 開始之前

- **FSR 4.1 和 FSR 3** 不需要其他東西：第一次選擇時，Scaler 助手會詢問是否下載 OptiScaler 及適合你顯示卡的 FSR 4.1 DLL（見下方「下載檔」）。
- **DLSS 3.7** 需要 HelixSR，Scaler 助手並不包含它。請從 [HelixSR 的 GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) 下載 1.8.0 以上版本，解壓縮到會保留的資料夾，並在那裡執行一次 `./helixsr-setup.sh`（它會在你的電腦上建立 HelixSR 的神經網路；開始逐一詢問遊戲時可以回答 `n`）。按上方的 **HelixSR** 標籤可看到這些說明；Scaler 助手會自動在家目錄、下載、桌面或 Games 資料夾中尋找已設定好的 HelixSR 資料夾。
  更簡單的方式：在該視窗按 **下載並建置 HelixSR**（HelixSR 2.0 以上），Scaler 助手會替你完成以上步驟，不需要終端機。
- 遊戲透過 **Proton** 執行。HelixSR 是為 AMD 顯示卡（RDNA 1 以上）設計的。FSR 4.1 Exact／Lossy 是為 Radeon RX 7000／RX 6000 及 Radeon 內建顯示晶片（含 Steam Deck）製作；其他 GPU 應該也能執行，但原作者尚未測試。FSR 4.1 無法在 Radeon RX 5000（RDNA 1）顯示卡上使用（每個版本都只有黑畫面），因此 Scaler 助手在這類顯示卡上會將它反灰；仍可使用 FSR 3 與 DLSS 3.7（HelixSR）。

## 功能

### 1. 掃描 Steam 遊戲

- 第一次啟動時掃描所有 Steam 遊戲庫（包含其他磁碟上的遊戲庫）。安裝新遊戲後按「⟳ 重新掃描 Steam 遊戲」。
- 每款遊戲都會找出：內建的升頻 DLL、主要 `.exe` 的資料夾（依 Steam 的啟動資訊；也能處理啟動器和 Unreal 的 `*-Shipping.exe`）、**繪圖 API**（讀 `.exe` 的匯入表：DX12、DX11 或 Vulkan），以及是否含有**反作弊**（Easy Anti-Cheat、BattlEye）。
- 遊戲名稱跟隨介面語言（Steam 的在地化名稱）。可以升頻的遊戲排在前面。

### 2. 替 OptiScaler 選一個遊戲能用的檔名

遊戲會把放在 `.exe` 旁的 OptiScaler 當成系統 DLL 載入。Scaler 助手依下列順序決定檔名：

1. 你替這款遊戲選的檔名（「更多」→「OptiScaler 檔名…」），
2. 遊戲中已經存在的 OptiScaler 所用的檔名，
3. [OptiScaler 相容性清單](https://github.com/optiscaler/OptiScaler/wiki)對這款遊戲指定的檔名（例如 `d3d12.dll` 或 `winmm.dll`），
4. Vulkan 遊戲用 `winmm.dll`，
5. 遊戲或其他模組（例如 ReShade）已有 `dxgi.dll`，或你的啟動選項把這個名稱設為內建版本時，改用其他空著的檔名（`winmm.dll`、`version.dll`…），
6. 其他情況用 `dxgi.dll`。

已存在的檔案絕不會被覆蓋：它會移到 `ScalerAssistant/backup`（DLSS 3.7 則是 `HelixSR/backup`），移除時再放回。

### 3. Steam 啟動選項：只加需要的，你原本的內容保持不變

在 Proton 下，`dxgi.dll` 和 `d3d12.dll` 不需要其他設定就會載入。其他檔名都需要在遊戲的啟動選項加入 `WINEDLLOVERRIDES="<名稱>=n,b"`，Scaler 助手會替你加上：

- **只插入這一項。** 如果你已經有 `WINEDLLOVERRIDES`，就在它的值裡加上 `;winmm=n,b`；沒有的話就在最前面加上 `WINEDLLOVERRIDES="winmm=n,b"`（原本沒有 `%command%` 時一併補上）。啟動選項的其他內容一律不動。例如 `-dx12 %command%` 會變成 `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`。
- **移除 OptiScaler 或改檔名時，只拿掉這一項。** 如果期間你沒改過啟動選項，會完全回到原本的內容；如果你改過，只會移除當初插入的文字，你的修改都會保留。
- 你原本就有的同名設定不會被改動，之後也不會被移除。如果你的啟動選項把這個名稱設為 Wine 內建版本，Scaler 助手會改用其他檔名，而不是修改你的設定。
- 如果這一項之後不見了，遊戲會顯示「缺少啟動選項」，按「修復」就會重新加入。
- Steam 執行中時，若 Steam 的除錯連接埠可用（Decky Loader 也是用這個），會直接透過 Steam 修改。否則 Scaler 助手會詢問是否關閉 Steam、寫入變更後再重新開啟 Steam——這一步發生在修改任何遊戲檔案之前。

### 4. 下載檔（FSR 4.1 與 FSR 3）

按上方的 **OptiScaler** 標籤（或 GPU 標籤）：

- **OptiScaler 0.9.4**（含 AMD 的 FidelityFX DLL：FSR 3 與 AMD 的 FSR 4.1，以及 fakenvapi），以及適合你 GPU 版本的 **FSR 4.1 Exact／Lossy／Lite／Lite Lossy**：RX 7000 顯示卡、RX 6000 顯示卡、處理器內建的 RDNA 3 顯示晶片（也適用 GeForce、Intel Arc 與其他 GPU），或 Steam Deck 與處理器內建的 RDNA 2 顯示晶片。每個版本在這些 GPU 上都能用，對應你 GPU 的版本最快。若遊戲用 Exact 會當掉，可改選內建顯示晶片的版本。
- 你同意之前不會下載任何東西。每個下載檔都是固定的版本，解開前會核對大小和 SHA-256；只保留遊戲需要的檔案，存在 `~/.local/share/scaler-assistant/components/`。
- **FSR 4.1 版本**：依顯示卡自動選擇（RX 9000／RDNA 4 → AMD 原生 FSR 4.1；內建顯示晶片與 Steam Deck → 內建顯示晶片版；其他 GPU → 獨立顯示卡版），也可以手動指定。RDNA 4 絕不會使用修改過的 DLL。其他 GPU 會把 OptiScaler 設為使用 FSR 4 的 INT8 模型。
- 「移除下載檔」會刪除它們；遊戲裡的複本不受影響。

### 5. OptiScaler.ini 會改哪些地方

只改這個選項需要的那幾行，而且只改在各自的區段；其他每一行和註解都會保留：

| Key | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`、`VulkanUpscaler` | `fsr31_12`（經由 Direct3D 12） | `fsr31`（原生） |
| `UpscalerIndex` | `0`（FSR 4） | `1`（FSR 3.1.5） |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | RDNA 4 之前為 `true` | `auto` |
| `FfxDx12Path`、`FfxDx12SRPath`、`FfxDx12FGPath`、`FfxVkPath` | 遊戲 `ScalerAssistant` 資料夾中的 DLL | 同左 |

原本就存在的 `OptiScaler.ini` 會先備份，移除時放回。

### 6. 切換、更新、修復、移除

- 從升頻選單**切換**：先移除目前的選項，再安裝新的。FSR 4.1 Exact、Lossy 與 FSR 3 之間切換時，只會換 FSR DLL 和修改 `OptiScaler.ini`。
- **更新**：HelixSR 資料夾有較新的版本時，遊戲會顯示「↑ 有 HelixSR … 可用」；使用中的 OptiScaler／FSR 4.1 有較新的下載檔（或改了 FSR 4.1 版本）時會顯示「↑ 有較新的下載檔」。「↑ 全部更新」一次更新所有遊戲。
- **修復**：遊戲更新或在 Steam「驗證遊戲檔案的完整性」可能把遊戲原本的檔案放回去。這時遊戲會顯示發生了什麼，按「修復」就會把升頻放回去，並把遊戲的新檔案保留為備份。
- **移除**會放回所有被取代或移走的檔案，並把加入啟動選項的那一項拿掉。

### 7. 不必編輯檔案就能調整 HelixSR 設定

使用 DLSS 3.7 時，「⚙ 設定」以表單編輯遊戲的 `helixsr.ini`（銳利化、int8 網路、超高效能模式的最後縮放、wave 大小）。「預設」會省略該行；檔案中的其他行和註解都會保留。

### 8. 即時狀態與浮動提示

- 每 3 秒檢查執行中的 Steam 遊戲：從 `/proc/<pid>/maps` 確認遊戲是否**真的載入了** HelixSR 或 FSR DLL（以及 OptiScaler 或 DLSS 載入器）。遊戲開始使用升頻之前不會載入，所以「尚未載入」會告訴你要在遊戲中選什麼。
- 使用 HelixSR 時，會從本次執行的 `helixsr.log` 顯示 wave 大小和錯誤；RDNA 3 以上使用 OptiScaler 方式、記錄顯示 wave32 時，會提供「設定 WaveSize = 64」。
- 遊戲卡片上的 ⌄ 按鈕會打開詳細資訊面板，裡面有「檢視 …log」（`helixsr.log` 或 `OptiScaler.log`）、開啟遊戲資料夾、OptiScaler 檔名，以及 DLSS 3.7 的「⚙ 設定」。
- 遊戲啟動時，右下角會出現小卡片顯示結果約 10 秒（90 秒後仍未載入則顯示提示）。它是獨立的 X11 視窗，不會搶焦點；可用工具列的開關關閉。

### 9. 啟動、搜尋、篩選、語言

- 「▶ 啟動」透過 Steam 開啟遊戲。可用名稱（任何語言）或 App ID 搜尋；篩選：可以升頻的遊戲、已安裝升頻、尚未安裝升頻、需要更新或修復、執行中、所有遊戲。
- 12 種介面語言：台灣正體中文、简体中文、English、日本語、Deutsch、Français、Español、Italiano、ไทย、Tiếng Việt、Bahasa Melayu、हिन्दी。

### 10. 以安全為設計原則

- 遊戲執行中時不做任何變更；修改任何檔案之前都會先確認下載檔和 HelixSR 資料夾。
- 每個被取代的檔案都會保留，每次複製都逐位元組比對，啟動選項只會依上面說明增減那一項。
- DLSS 方式、FSR 4.1 Lossy 以及含反作弊的遊戲都會先詢問。請勿在線上遊戲使用修改過的升頻：反作弊可能視為竄改。

### 11. 外觀

- 參考 MAKO Assistant 的「Liquid Glass」風格：每款遊戲一張卡片，含 Steam 封面、狀態標籤、遊戲支援的技術，執行時還會顯示真正載入了什麼。⌄ 按鈕會展開詳細資訊（繪圖 API、升頻技術、`.exe` 資料夾、OptiScaler 檔名、啟動選項）和較少用的操作。
- 按鈕為立體浮起的水晶風格：淡淡的色調與細邊框，上半部有弧形的反光，下緣內側有一道微光，底下有柔和的陰影，全部由平塗的半透明圖層構成，不帶漸層。開關的圓鈕同樣浮起；主題切換的選取項是嵌在凹槽中的浮起水晶。青綠色為安裝、藍色為切換、琥珀色為更新、紅色為移除。
- 深色、淺色或自動主題（跟隨桌面）。活動紀錄在視窗底部的抽屜。

## HelixSR 2.0 與顯示卡

- **一鍵下載並建置 HelixSR**：「下載並建置 HelixSR」（在 HelixSR 視窗與 Steam Deck 外掛中）會從 GitHub 發布頁下載最新的 HelixSR（2.0 以上），核對 SHA-256 後放到 `~/.local/share/scaler-assistant/helixsr`，再用 HelixSR 自己的建置程式（`setup/helixsr_setup.py`，原封不動執行）在這台電腦上建置。做法與 HelixSR 自己的 App 相同，所以不需要終端機，也不會進入遊戲安裝步驟。建置需要的東西也會備齊：有 numpy 的 Python（系統的 Python 無法解壓 NVIDIA 的 zstd 套件時，改用可攜式 Python 3.14，影格生成不必另外安裝 `zstd`），以及透過 Steam 的 Proton 或 Wine 執行的 Microsoft DirectX 著色器編譯器。NVIDIA 的檔案只會在你於 App 中同意後才下載，建置結果只留在你的電腦。Flatpak 版會在主機上建置。再執行一次只會補建缺少的部分；有新版時會取代先前下載的版本。
- **HelixSR 2.0 以上**把建好的 DLL 放在 `HelixSR-fsrfg`，並提供兩種方式：**HelixSR Scaler**（HelixSR 自帶、放在 `.exe` 旁的 OptiScaler：遊戲內選 DLSS；DX11 和 Vulkan 遊戲也能用）與 **FSR 方式**（FSR drop-in）。Scaler 助手透過你 HelixSR 資料夾裡的安裝程式（`setup/helixsr_bridge.py`，也就是 HelixSR 官方 App 使用的那一個）安裝這兩種方式，所以 HelixSR 的 setup、它的 App 和 Scaler 助手都能辨識、更新、移除彼此的安裝。檔名仍由 Scaler 助手選擇，需要時也會加入啟動選項。以舊方式設定的遊戲在更新時會改用 HelixSR Scaler。HelixSR 1.8.x 仍有三種方式；1.9.0～1.9.3 只有 FSR 方式（其他方式反灰）。
- **HelixSR 影格生成**（HelixSR 2.0）：有 DLSS Frame Generation（Streamline 的 `sl.dlss_g.dll`）的 DirectX 12 遊戲，裝了 HelixSR Scaler 後卡片上（以及 Steam Deck 外掛中）會出現「HelixSR 影格生成」開關。它透過 HelixSR 自己的安裝程式（`scaler-fg`）切換，只改 OptiScaler.ini 的 `[FrameGen]` 選項；打開後在遊戲中開啟 DLSS Frame Generation。需要 `./helixsr-setup.sh` 建好的影格生成（會下載 NVIDIA 的 DLSS Frame Generation 檔案），在那之前開關會反灰並說明原因。新安裝時預設關閉；更新或改 OptiScaler 檔名會保留原本的狀態。其他 DX12 遊戲仍可在 HelixSR Scaler 選單（Insert）選 AMD FSR 或 XeSS 影格生成；DX11／Vulkan 遊戲與 FSR 方式只有升頻。
- **HelixSR 3.0**：建置好的 DLL 改為 `HelixSR/helixsr.dll`（HelixSR Scaler 的 DLSS 升頻器「HLX DLSS」），FSR 方式改裝 **HLX FSR 4**——HelixSR 自己的 FSR 4 流程，由 HelixSR 的 setup 從 AMD 的 FSR 4 驅動程式檔案建置（會從 AMD 下載驅動程式套件中約 420 MB；「下載並建置 HelixSR」會先詢問，並一併備好第二個著色器編譯器 DXC 1.9.2609）。Scaler 助手與 2.0 相同，透過發布版內的安裝程式安裝、更新、切換與移除兩種方式；用 2.0 設定的遊戲在更新時會從 `HelixSR-fsrfg` 移到 `HelixSR`。HelixSR 3.0 沒有影格生成，所以搭配 3.0 時不顯示上面的開關；HelixSR Scaler 選單中仍可選 AMD FSR 與 XeSS 影格生成。 HelixSR 3.2 起，HLX FSR 4 已在 ZIP 中建置好（由 AMD FSR SDK 2.4.0 的 FSR 4.1.2 建置）：setup 不再下載 AMD 驅動程式套件，HelixSR Scaler 中與它並列的 AMD 原版 FSR 也換成 FSR 4.1.2。
- **較舊的 HelixSR 版本**：1.8.x 三種方式（FSR 方式、OptiScaler 方式、DLSS 方式）都能用。HelixSR 1.9.0～1.9.3 只附 FSR 方式的檔案，所以 OptiScaler 與 DLSS 方式會反灰（「需要 HelixSR 1.8 或 2.0」）；沒有 FSR 3.1 的遊戲需要 HelixSR 2.0（HelixSR Scaler）。1.8.0 以前的版本不支援。
- **DLSS 方式僅限 GeForce**：使用 AMD 或 Intel GPU 時，遊戲中無法選擇 DLSS，所以（HelixSR 1.x 的）DLSS 方式會反灰並說明原因。
- **推薦 FSR 4.1.2 Lite Lossy**：內建顯示晶片（Steam Deck、ROG Ally Z1／Z2、Ryzen AI MAX）與 Intel GPU 只會在 FSR 4.1 的選項中標示「★ 推薦」。

## 與 HelixSR 本身的 setup 互通

使用 DLSS 3.7 時，Scaler 助手寫入與 HelixSR setup 相同的安裝紀錄（`helixsr-install.json`）、備份和檔名，所以 `helixsr-setup.sh`／`helixsr-uninstall.sh` 與 Scaler 助手都認得對方安裝的遊戲。HelixSR 的 setup 會把遊戲 `ScalerAssistant` 資料夾中的 FSR DLL 當成遊戲自己的 FSR 3.1 DLL，可能把它換成 HelixSR；這時 Scaler 助手會把遊戲標示為需要修復，按「修復」即可把 HelixSR 移除。想在這類遊戲使用 DLSS 3.7，請直接在 Scaler 助手中選擇。

## Steam Deck 外掛（Decky Loader）

同一套程式也能在遊戲模式中使用：[Decky Loader](https://decky.xyz) 的外掛，位於快速存取選單。

- **遊戲**：可升頻的遊戲，執行中的排在最前，各自顯示狀態標籤，執行時還會顯示真正載入了什麼。選擇遊戲即可選用 DLSS 3.7（HelixSR，各種方式）、FSR 4.1 Exact／Lossy 或 FSR 3，或是更新、修復、移除、修改 OptiScaler 檔名、查看記錄檔。事前詢問與桌面版相同：下載檔、Lossy 警告、DLSS 方式與反作弊。
- **設定**：HelixSR 資料夾（檔案選擇器）、下載檔與 FSR 4.1 版本（Steam Deck 使用內建顯示晶片版）、遊戲啟動時通知（顯示升頻是否已載入），以及語言（預設與 Steam 相同）。
- 與桌面版共用 `state.json`、下載檔與啟動選項紀錄，在其中一邊設定的遊戲另一邊也看得到。啟動選項透過 Steam 即時寫入。
- 外掛不包含：HelixSR 設定表單（請用桌面版），以及 HelixSR 本身的 `helixsr-setup.sh`（請在桌面模式執行一次）。
- 外掛中的 **下載並建置 HelixSR** 在遊戲模式也能下載並建置 HelixSR 2.0 以上（需要幾分鐘）。

安裝：先在 Steam Deck 安裝 Decky Loader，從 [Releases](https://github.com/mosesmoon/scaler-assistant/releases) 頁面下載 `Scaler_Assistant-Decky-<版本>.zip`，再到 Decky 設定 →「開發者」（先在「一般」開啟開發者模式）→「Install Plugin from ZIP File」。

## 安裝 Scaler 助手

**AppImage（建議）**：已內含 Python、Qt 和 7-Zip。

1. 從 [Releases](https://github.com/mosesmoon/scaler-assistant/releases) 頁面下載 `Scaler_Assistant-<版本>-x86_64.AppImage`。
2. 設定為可執行：按右鍵 →「內容」→「權限」→「允許以程式執行檔案」（各檔案管理員的用詞略有不同）。
3. 按兩下開啟。

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

無法啟動時，系統可能缺少 FUSE；請加上 `--appimage-extract-and-run` 執行。

**單一安裝檔（.bin）**：`Scaler_Assistant-<版本>-x86_64.bin` 只替目前的使用者安裝同一套內含程式（不需 root、不需 FUSE）到 `~/.local/opt/scaler-assistant`，並加入 `scaler-assistant` 指令與選單項目。**Flatpak**：`Scaler_Assistant-<版本>-x86_64.flatpak` 是單一檔案的套件，使用 Freedesktop 25.08 runtime（安裝時從 Flathub 下載）。它可以讀取家目錄與其他磁碟（`/run/media` 下的 SD 卡），並透過 `flatpak-spawn --host` 看到 Steam 與遊戲的程序。

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / 安裝
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / 移除
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**從原始碼執行**：需要 Python 3.11 以上和 PyQt6（Arch：`sudo pacman -S python-pyqt6`），以及解開 OptiScaler 用的 7-Zip 或 bsdtar（`sudo pacman -S 7zip`）。

```bash
./scaler-assistant     # 直接執行
./install.sh           # 安裝到 ~/.local/share/scaler-assistant，並建立選單項目
```

## 已知限制

- **只支援 Steam 遊戲。** FSR 4.1／FSR 3 的安裝方式已用 OptiScaler 0.9.4 逐一核對過檔案；但每款遊戲的表現不同，遊戲出問題時請查 OptiScaler 的相容性清單，或替 OptiScaler 換個檔名。
- Direct3D 11 與 Vulkan 遊戲的 FSR 4.1 經由 OptiScaler 的 Direct3D 12 路徑，測試程度較低。
- HelixSR 變化很快。Scaler 助手需要 HelixSR 1.8.0 以上，並依照 1.8.x／1.9.x／2.0.x / 3.0.x / 3.1.x／3.2.x 的檔案配置。
- Steam Deck 遊戲模式（gamescope）下不會顯示浮動提示。Decky 外掛會改以 Steam 通知顯示。
- 泰文、越南文、馬來文和印地文的右鍵選單是英文（Qt 沒有官方翻譯）。Steam 沒有馬來文和印地文的遊戲名稱。

## 資料存放位置

| 位置 | 內容 |
|---|---|
| `~/.config/scaler-assistant/state.json` | Scaler 助手的狀態：HelixSR 資料夾、遊戲清單、語言、FSR 4.1 版本、你選的 OptiScaler 檔名、它加入啟動選項的項目（第一次會從 HelixSR 助手接手） |
| `~/.local/share/scaler-assistant/components/` | 下載的 OptiScaler 與 FSR 4.1 檔案 |
| `~/homebrew/plugins/scaler-assistant/` | Steam Deck 上的 Decky 外掛（使用與上面相同的狀態和下載檔） |
| `<遊戲>/…/ScalerAssistant/` | FSR 4.1／FSR 3：FidelityFX DLL、`scaler-install.json`、`backup/` |
| `<遊戲>/…/HelixSR/helixsr-install.json`、遊戲 FSR DLL 旁 | DLSS 3.7：HelixSR 的安裝紀錄（與 HelixSR setup 共用） |
| `<遊戲>/…/helixsr.ini`、`helixsr.log`、`OptiScaler.ini`、`OptiScaler.log` | 設定與記錄 |

## 授權

Scaler 助手是獨立的非官方工具，與 HelixSR 作者、NVIDIA、AMD、OptiScaler 專案或 fsr4-shader-performance-overrides 專案沒有關聯，也未經其認可，且不含它們的任何檔案。在你同意時，它會從各自的 GitHub Releases 下載 OptiScaler（GPL-3.0；fakenvapi 為 MIT；AMD 的 FidelityFX DLL 依 AMD 授權）和 FSR 4.1 DLL（GPL-2.0-or-later，附 AMD 聲明的修改版 AMD DLL）。AppImage 內附 7-Zip 的 `7zzs`（GNU LGPL 附 unRAR 限制、BSD；附授權檔）。HelixSR 依 HelixSR Freeware License 免費使用；執行 setup 後，HelixSR 的 DLL 會包含 NVIDIA 的神經網路，所以 Scaler 助手只會在你自己電腦上的資料夾之間複製它們。請勿分享或上傳這些檔案。Decky 外掛也內附同一個 `7zzs`。
