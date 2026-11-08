# Trợ lý Scaler — Hướng dẫn tính năng

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · **Tiếng Việt** · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**Trợ lý Scaler** là công cụ desktop trên Linux cho phép bạn chọn bộ upscale cho từng game Steam — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact hoặc Lossy từ [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), hoặc bản gốc của AMD trên RX 9000) hay **FSR 3** — rồi cài, chuyển, cập nhật, sửa và gỡ chỉ với một cú nhấp. Nó còn cho biết bộ upscale có thực sự chạy khi bạn chơi hay không.

## Dành cho ai

Tự tay đưa bộ upscale tốt hơn vào game trên Linux nghĩa là:

1. Tìm xem game có bộ upscale nào (DLSS, XeSS, FSR 2, FSR 3.1), dùng API đồ họa gì và tệp `.exe` chính ở đâu.
2. Đặt OptiScaler cạnh `.exe` với tên tệp mà game chấp nhận, kèm các DLL FidelityFX cần thiết, và sửa `OptiScaler.ini` cho bộ upscale bạn muốn.
3. Thêm `WINEDLLOVERRIDES` vào tùy chọn khởi chạy Steam khi tên tệp đó cần — mà không làm hỏng nội dung đã có.
4. Tải đúng DLL FSR 4.1 cho GPU, hoặc thiết lập HelixSR theo README của nó.
5. Làm lại sau mỗi lần cập nhật, và lần nữa khi bản cập nhật game ghi đè tệp.

Trợ lý Scaler làm tất cả trong một cửa sổ và giữ lại mọi thứ đã thay thế, nên khi gỡ, game trở lại đúng như cũ.

## Các lựa chọn cho mỗi game

API đồ họa và bộ upscale của game quyết định những gì được đề xuất. Game phải có sẵn ít nhất một bộ upscale (DLSS, XeSS, FSR 2 hoặc FSR 3.1): OptiScaler và HelixSR sẽ tiếp quản nó.

| Lựa chọn | Game cần | Những gì được đặt vào thư mục game | Chọn trong game |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · cách FSR** | Direct3D 12, FSR 3.1 | DLL FSR 3.1 của game được thay bằng HelixSR (tệp gốc giữ lại thành `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · cách OptiScaler** | Direct3D 12, DLSS, XeSS hoặc FSR 2 | OptiScaler cạnh `.exe`, trỏ tới thư mục `HelixSR` | DLSS |
| **DLSS 3.7 (HelixSR) · cách DLSS** (thử nghiệm) | Direct3D 12, DLSS | Trình nạp DLSS của HelixSR (`dxgi.dll`) và HelixSR dưới tên `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | một trong bốn bộ upscale | OptiScaler cạnh `.exe`; các DLL FidelityFX và DLL FSR 4.1 Exact trong thư mục `ScalerAssistant` | DLSS, FSR hoặc XeSS |
| **FSR 4.1 Lossy** | như trên | như trên, dùng DLL FSR 4.1 Lossy | DLSS, FSR hoặc XeSS |
| **FSR 4.1.2 Lite / Lite Lossy** | như trên | như trên, dùng DLL FSR 4.1 4.1.2l-exact / 4.1.2l-lossy | DLSS, FSR hoặc XeSS |
| **FSR 4.1 (AMD)** — thay cho Exact / Lossy trên RX 9000 (RDNA 4) | như trên | như trên, dùng DLL FSR 4.1 gốc của AMD | DLSS, FSR hoặc XeSS |
| **FSR 3** | như trên | như trên; OptiScaler dùng FSR 3.1.5 | DLSS, FSR hoặc XeSS |

- **Exact** cho hình ảnh FSR 4.1 của AMD đến từng byte, với shader nhanh hơn. **Lossy** còn nhanh hơn và thay đổi hình ảnh một chút; Trợ lý Scaler hiển thị `WARNING.txt` của nó một lần trước lần dùng đầu tiên. Nếu không chắc, hãy chọn Exact.
- **Lossy** từ các DLL của dll-2026-10-29 là Lossy2 cũ được huấn luyện thêm (Lossy cũ đã bị bỏ): ít đốm tối trong tán lá hơn nhiều, nhưng theo kịp khi hình sáng lên chậm hơn. **Lite** và **Lite Lossy** dùng mạng FSR 4.1.2 Lite nhỏ hơn của AMD (có lẽ là mạng driver AMD dùng cho đồ họa tích hợp): Lite cho hình giống Lite của AMD từng byte và nhanh hơn một chút; Lite Lossy chỉ chạy mạng mỗi hai khung hình, là bản nhanh nhất, hình gần với Lite. Lite kém chính xác hơn FSR 4 đầy đủ một chút ở hình tĩnh và một số chuyển động, tốt hơn ở một số khác. Lossy và Lite Lossy mỗi bản hiển thị `WARNING.txt` riêng một lần. Game đã thiết lập với Lossy2 sẽ hiện là cần cập nhật và chuyển sang Lossy.
- HelixSR chỉ chạy trong game **Direct3D 12**, nên DLSS 3.7 chỉ xuất hiện ở đó. FSR 4.1 và FSR 3 cũng chạy trong game **Direct3D 11 và Vulkan**: FSR 3 chạy gốc, FSR 4.1 qua đường Direct3D 12 của OptiScaler (ít được thử hơn game Direct3D 12).
- Nhấp **"Chọn bộ upscale"** ở dòng của game (hoặc **"Bộ upscale"** khi đã cài): DLSS 3.7 (HelixSR) mở menu con với các cách của nó; lựa chọn hiện tại được đánh dấu. Khi chuyển, lựa chọn hiện tại được gỡ trước và mọi thứ được trả lại.

## Trước khi bắt đầu

- **FSR 4.1 và FSR 3** không cần gì thêm: lần đầu chọn, Trợ lý Scaler hỏi có tải OptiScaler và DLL FSR 4.1 cho GPU của bạn không (xem "Tệp tải về").
- **DLSS 3.7** cần HelixSR, mà Trợ lý Scaler không kèm theo. Tải HelixSR 1.8.0 trở lên từ [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases), giải nén vào thư mục bạn giữ lại và chạy `./helixsr-setup.sh` ở đó một lần (nó tạo mạng của HelixSR trên máy bạn; khi hỏi về game có thể trả lời `n`). Nhãn **HelixSR** ở trên giải thích điều này; thư mục HelixSR đã thiết lập trong home, Downloads, Desktop hoặc Games sẽ được tự tìm.
  Cách dễ hơn: nhấn **Tải và dựng HelixSR** trong cửa sổ đó (HelixSR 2.0 trở lên); Scaler Assistant làm tất cả cho bạn, không cần terminal.
- Game chạy qua **Proton**. HelixSR dành cho GPU AMD (RDNA 1 trở lên). FSR 4.1 Exact / Lossy dành cho Radeon RX 7000 / RX 6000 và đồ họa Radeon tích hợp (kể cả Steam Deck); GPU khác có lẽ chạy được nhưng tác giả chưa thử. FSR 4.1 không hoạt động trên GPU Radeon RX 5000 (RDNA 1) (mọi bản chỉ cho hình đen), nên Trợ lý Scaler làm mờ lựa chọn này trên các card đó; vẫn dùng được FSR 3 và DLSS 3.7 (HelixSR).

## Tính năng

### 1. Quét game Steam

- Lần đầu mở sẽ quét mọi thư viện Steam (kể cả trên ổ khác). Sau khi cài game, nhấp "⟳ Quét lại game Steam".
- Với mỗi game: các DLL upscale có sẵn, thư mục của `.exe` chính (từ thông tin khởi chạy của Steam; hỗ trợ launcher và `*-Shipping.exe` của Unreal), **API đồ họa** (đọc từ bảng import của `.exe`: DX12, DX11 hoặc Vulkan) và có **chống gian lận** hay không (Easy Anti-Cheat, BattlEye).
- Tên game theo ngôn ngữ giao diện (tên bản địa của Steam). Game có thể upscale được xếp trước.

### 2. Tên tệp của OptiScaler phù hợp với game

Game nạp OptiScaler như một DLL hệ thống cạnh `.exe`. Tên được chọn theo thứ tự:

1. tên bạn đã chọn cho game ("Thêm" → "Tên tệp của OptiScaler…"),
2. tên của OptiScaler đã có sẵn,
3. tên mà [danh sách tương thích của OptiScaler](https://github.com/optiscaler/OptiScaler/wiki) nêu cho game (ví dụ `d3d12.dll` hoặc `winmm.dll`),
4. `winmm.dll` cho game Vulkan,
5. tên trống khác (`winmm.dll`, `version.dll`, …) khi game hoặc mod khác (như ReShade) đã có `dxgi.dll`, hoặc khi tùy chọn khởi chạy của bạn đặt tên đó thành bản tích hợp,
6. còn lại là `dxgi.dll`.

Tệp có sẵn không bao giờ bị ghi đè: nó được chuyển vào `ScalerAssistant/backup` (`HelixSR/backup` với DLSS 3.7) và trở lại khi gỡ.

### 3. Tùy chọn khởi chạy Steam: chỉ thêm điều cần thiết, của bạn giữ nguyên

Dưới Proton, `dxgi.dll` và `d3d12.dll` được nạp mà không cần gì thêm. Mọi tên khác cần `WINEDLLOVERRIDES="<tên>=n,b"` trong tùy chọn khởi chạy, và Trợ lý Scaler thêm giúp bạn:

- **Chỉ chèn đúng mục đó.** Nếu bạn đã có `WINEDLLOVERRIDES`, `;winmm=n,b` được thêm vào trong giá trị đó; nếu chưa, `WINEDLLOVERRIDES="winmm=n,b"` được đặt ở đầu (kèm `%command%` nếu thiếu). Mọi thứ khác không đổi. Ví dụ: `-dx12 %command%` thành `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Chỉ bỏ đúng mục đó** khi OptiScaler bị gỡ hoặc đổi tên. Nếu trong thời gian đó bạn không sửa tùy chọn, chúng trở lại y như cũ; nếu có sửa, chỉ phần chữ đã chèn bị bỏ và thay đổi của bạn được giữ.
- Mục bạn đã có sẵn cho tên đó không bị đụng tới và sau này cũng không bị gỡ. Nếu tùy chọn của bạn đặt tên đó thành bản tích hợp của Wine, Trợ lý Scaler dùng tên khác thay vì đổi thiết lập của bạn.
- Nếu mục đó mất đi sau này, game hiển thị "Thiếu tùy chọn khởi chạy" và "Sửa" sẽ thêm lại.
- Khi Steam đang chạy, tùy chọn được đổi qua chính Steam nếu cổng gỡ lỗi của nó khả dụng (như Decky Loader dùng). Nếu không, Trợ lý Scaler đề nghị đóng Steam, ghi thay đổi rồi mở lại Steam — trước khi đụng tới bất kỳ tệp game nào.

### 4. Tệp tải về (FSR 4.1 và FSR 3)

Nhấp nhãn **OptiScaler** ở trên (hoặc nhãn GPU):

- **OptiScaler 0.9.4** (kèm DLL FidelityFX của AMD: FSR 3 và FSR 4.1 của AMD, cùng fakenvapi) và **FSR 4.1 Exact / Lossy / Lite / Lite Lossy** ở bản dựng cho GPU của bạn: card RX 7000, card RX 6000, đồ họa RDNA 3 tích hợp trong bộ xử lý (cả GeForce, Intel Arc và GPU khác), hoặc Steam Deck và đồ họa RDNA 2 tích hợp trong bộ xử lý. Mọi bản dựng đều chạy trên tất cả; bản cho GPU của bạn là nhanh nhất. Nếu game bị crash với Exact, hãy chọn bản cho đồ họa tích hợp.
- Không tải gì cho đến khi bạn đồng ý. Mỗi tệp tải về là một bản cố định, được kiểm tra kích thước và SHA-256 trước khi giải nén; chỉ giữ các tệp game cần, trong `~/.local/share/scaler-assistant/components/`.
- **Bản FSR 4.1**: tự động theo GPU (RX 9000 / RDNA 4 → FSR 4.1 gốc của AMD, đồ họa tích hợp và Steam Deck → bản tích hợp, GPU khác → bản card rời), hoặc tự chọn. Trên RDNA 4 không bao giờ dùng DLL đã sửa. Trên GPU khác, OptiScaler được đặt dùng mô hình INT8 của FSR 4.
- "Xóa tệp tải về" sẽ xóa chúng; game vẫn giữ bản sao riêng.

### 5. Những gì thay đổi trong OptiScaler.ini

Chỉ những dòng cần thiết, trong đúng mục của chúng; mọi dòng và chú thích khác được giữ:

| Khóa | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (qua Direct3D 12) | `fsr31` (gốc) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` trước RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | các DLL trong thư mục `ScalerAssistant` của game | như trên |

`OptiScaler.ini` đã có được sao lưu trước và trả lại khi gỡ.

### 6. Chuyển, cập nhật, sửa, gỡ

- **Chuyển** từ menu bộ upscale: lựa chọn hiện tại được gỡ trước, rồi cài lựa chọn mới. Giữa FSR 4.1 Exact, Lossy và FSR 3 chỉ DLL FSR và `OptiScaler.ini` thay đổi.
- **Cập nhật**: game hiển thị "↑ Có HelixSR …" khi thư mục HelixSR có bản mới hơn, hoặc "↑ Có tệp tải về mới hơn" khi có OptiScaler / FSR 4.1 mới hơn (hoặc bản FSR 4.1 khác). "↑ Cập nhật tất cả" cập nhật mọi game.
- **Sửa**: bản cập nhật game hoặc "Xác minh tính toàn vẹn của tệp game" có thể đưa tệp gốc của game trở lại. Game sẽ cho biết chuyện gì xảy ra, và "Sửa" đưa bộ upscale trở lại, giữ tệp mới của game làm bản sao lưu.
- **Gỡ** trả lại mọi tệp đã bị thay hoặc di chuyển, và bỏ mục trong tùy chọn khởi chạy.

### 7. Cài đặt HelixSR không cần sửa tệp

Với DLSS 3.7, "⚙ Cài đặt" sửa `helixsr.ini` của game bằng biểu mẫu (làm nét, mạng int8, bước cuối ở Ultra Performance, kích thước wave). "Mặc định" bỏ dòng đó; các dòng và chú thích khác được giữ.

### 8. Trạng thái trực tiếp và thông báo nổi

- Game Steam đang chạy được kiểm tra mỗi 3 giây: `/proc/<pid>/maps` cho biết game đã **thực sự nạp** HelixSR hoặc DLL FSR (và OptiScaler hoặc trình nạp DLSS) chưa. Chưa có gì được nạp cho tới khi game dùng bộ upscale, nên "chưa tải" cho biết bạn cần chọn gì trong game.
- Với HelixSR, `helixsr.log` của lần chạy hiện tại cho thấy kích thước wave và lỗi; trên RDNA 3 trở lên với cách OptiScaler, khi nhật ký báo wave32 sẽ đề xuất "Đặt WaveSize = 64".
- Bảng chi tiết của game (nút ⌄ trên thẻ game) có "Xem …log" cho `helixsr.log` hoặc `OptiScaler.log`, thư mục game, tên tệp của OptiScaler và, với DLSS 3.7, "⚙ Cài đặt".
- Khi game khởi động, một thẻ nhỏ ở góc dưới bên phải hiển thị kết quả khoảng 10 giây (hoặc gợi ý sau 90 giây). Đó là cửa sổ X11 riêng, không giành tiêu điểm; tắt bằng công tắc trên thanh công cụ.

### 9. Khởi chạy, tìm kiếm, lọc, ngôn ngữ

- "▶ Khởi chạy" mở game qua Steam. Tìm theo tên (mọi ngôn ngữ) hoặc App ID; bộ lọc: game có thể upscale, đã cài bộ upscale, chưa có bộ upscale, cần cập nhật hoặc sửa, đang chạy, tất cả game.
- 12 ngôn ngữ giao diện: 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Thiết kế an toàn

- Không thay đổi gì khi game đang chạy; tệp tải về và thư mục HelixSR được kiểm tra trước khi đụng tới tệp nào.
- Mọi tệp bị thay đều được giữ, mọi bản sao được kiểm từng byte, và tùy chọn khởi chạy chỉ thay đổi đúng một mục như mô tả ở trên.
- Cách DLSS, FSR 4.1 Lossy và game có chống gian lận đều hỏi trước. Đừng bao giờ dùng bộ upscale đã sửa trong game trực tuyến: chống gian lận có thể coi đó là can thiệp.

### 11. Giao diện

- Theo phong cách "Liquid Glass" của MAKO Assistant: mỗi game một thẻ với ảnh bìa Steam, nhãn trạng thái, những gì game hỗ trợ và, khi đang chạy, những gì thật sự đã được nạp. Nút ⌄ mở chi tiết (API đồ họa, bộ upscale, thư mục `.exe`, tên OptiScaler, tùy chọn khởi chạy) và các thao tác ít dùng.
- Nút là pha lê trong nổi khối: sắc màu nhạt với viền mảnh, vệt sáng cong ở nửa trên, ánh sáng dọc mép dưới bên trong và bóng mềm bên dưới — tất cả là các lớp trong mờ phẳng, không dùng chuyển màu. Núm công tắc cũng nổi lên như vậy; mục giao diện đang chọn là pha lê nổi trong rãnh lõm. Xanh ngọc là cài đặt, xanh dương là chuyển đổi, hổ phách là cập nhật, đỏ là gỡ bỏ.
- Giao diện tối, sáng hoặc tự động (theo desktop). Nhật ký hoạt động nằm trong ngăn kéo ở đáy cửa sổ.

## HelixSR 2.0 và GPU

- **Tải và dựng HelixSR trong một bước**: "Tải và dựng HelixSR" (trong cửa sổ HelixSR và trong plugin Steam Deck) tải HelixSR mới nhất (2.0 trở lên) từ trang phát hành GitHub, kiểm tra bằng SHA-256, vào `~/.local/share/scaler-assistant/helixsr`, rồi dựng trên máy này bằng chương trình dựng riêng của HelixSR (`setup/helixsr_setup.py`, chạy nguyên bản) — giống ứng dụng của HelixSR, nên không cần terminal và không có bước cài vào game. Những gì việc dựng cần cũng được chuẩn bị: Python có numpy (Python 3.14 di động khi Python của hệ thống không giải nén được gói zstd của NVIDIA, nên tạo khung hình không cần cài thêm `zstd`) và DirectX Shader Compiler của Microsoft chạy qua Proton của Steam hoặc Wine. Tệp của NVIDIA chỉ được tải sau khi bạn đồng ý trong ứng dụng; kết quả chỉ ở trên máy bạn. Trong Flatpak, việc dựng chạy trên máy chủ. Chạy lại chỉ dựng phần còn thiếu; bản phát hành mới hơn sẽ thay bản đã tải trước đó.
- **HelixSR 2.0 trở lên** đặt DLL đã dựng trong `HelixSR-fsrfg` và có hai cách: **HelixSR Scaler** (bản OptiScaler riêng của HelixSR đặt cạnh `.exe`: chọn DLSS trong game; cả game DX11 và Vulkan) và **cách FSR** (FSR drop-in). Trợ lý Scaler cài cả hai bằng trình cài đặt trong thư mục HelixSR của bạn (`setup/helixsr_bridge.py`, cái mà ứng dụng của HelixSR dùng), nên setup của HelixSR, ứng dụng của nó và Trợ lý Scaler nhận ra, cập nhật và gỡ bản cài của nhau. Tên tệp vẫn do Trợ lý Scaler chọn, và nó thêm tùy chọn khởi chạy khi cần. Game thiết lập bằng cách cũ sẽ chuyển sang HelixSR Scaler khi cập nhật. Thư mục HelixSR 1.8 / 1.9 vẫn giữ ba cách.
- **Tạo khung hình HelixSR** (HelixSR 2.0): với game DirectX 12 có DLSS Frame Generation (`sl.dlss_g.dll` của Streamline), game đã cài HelixSR Scaler sẽ có công tắc "Tạo khung hình HelixSR" trên thẻ (và trong plugin Steam Deck). Công tắc dùng trình cài đặt riêng của HelixSR (`scaler-fg`), chỉ đổi lựa chọn `[FrameGen]` trong OptiScaler.ini; sau đó bật DLSS Frame Generation trong game. Cần phần tạo khung hình do `./helixsr-setup.sh` tạo (tải các tệp DLSS Frame Generation của NVIDIA); trước đó công tắc bị làm mờ kèm lý do. Cài mới sẽ để tắt; cập nhật hoặc đổi tên tệp OptiScaler giữ nguyên trạng thái. Các game DX12 khác vẫn chọn được tạo khung hình AMD FSR hoặc XeSS trong menu HelixSR Scaler (Insert); game DX11 / Vulkan và cách FSR chỉ có nâng độ phân giải.
- **HelixSR 3.0**: DLL đã dựng là `HelixSR/helixsr.dll` (bộ nâng độ phân giải DLSS của HelixSR Scaler, "HLX DLSS"), và cách FSR cài **HLX FSR 4**, quy trình FSR 4 riêng của HelixSR, do setup của HelixSR dựng từ tệp driver FSR 4 của AMD (tải khoảng 420 MB của gói driver AMD từ AMD; "Tải và dựng HelixSR" hỏi trước và cũng chuẩn bị trình biên dịch shader thứ hai, DXC 1.9.2609). Trợ lý Scaler cài, cập nhật, chuyển và gỡ cả hai cách qua trình cài đặt trong bản phát hành như với 2.0; trò chơi đã thiết lập bằng 2.0 sẽ chuyển từ `HelixSR-fsrfg` sang `HelixSR` khi cập nhật. HelixSR 3.0 không có tạo khung hình nên công tắc ở trên không hiện với nó; tạo khung hình AMD FSR và XeSS vẫn có trong menu của HelixSR Scaler. Từ HelixSR 3.2, HLX FSR 4 đã được dựng sẵn trong ZIP (từ FSR 4.1.2 của FSR SDK 2.4.0 của AMD): setup không còn tải gói driver của AMD, và FSR gốc của AMD bên cạnh nó trong HelixSR Scaler là FSR 4.1.2. HelixSR 3.2.1 thêm **Preset K** tùy chọn cho HLX DLSS, chỉ setup của chính HelixSR dựng được (`--preset-k`; "Tải và dựng HelixSR" không dựng nó): khi đã dựng, nó được cài vào game cùng HelixSR Scaler (`HelixSR/k`) và được gỡ cùng, kể cả tệp log của nó.
- **Phiên bản HelixSR cũ hơn**: 1.8.x có đủ ba cách (cách FSR, cách OptiScaler, cách DLSS). HelixSR 1.9.0 – 1.9.3 chỉ kèm tệp của cách FSR, nên cách OptiScaler và DLSS bị làm mờ ("cần HelixSR 1.8 hoặc 2.0"); game không có FSR 3.1 cần HelixSR 2.0 (HelixSR Scaler). Không hỗ trợ bản trước 1.8.0.
- **Cách DLSS chỉ với GeForce**: với GPU AMD hoặc Intel, game không cho chọn DLSS, nên cách DLSS (HelixSR 1.x) bị làm mờ kèm lý do.
- **Đề xuất FSR 4.1.2 Lite Lossy** cho đồ họa tích hợp (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) và GPU Intel: chỉ đánh dấu "★ Đề xuất" trong các lựa chọn FSR 4.1.

## Dùng chung với setup của HelixSR

Với DLSS 3.7, Trợ lý Scaler ghi cùng bản ghi cài đặt (`helixsr-install.json`), bản sao lưu và tên tệp như setup của HelixSR, nên `helixsr-setup.sh` / `helixsr-uninstall.sh` và Trợ lý Scaler nhận ra game của nhau. Setup của HelixSR coi DLL FSR trong thư mục `ScalerAssistant` của game là DLL FSR 3.1 của game và có thể thay bằng HelixSR; khi đó Trợ lý Scaler báo game cần sửa, và "Sửa" sẽ gỡ HelixSR ra. Muốn dùng DLSS 3.7 trong game đó, hãy chọn trong Trợ lý Scaler.

## Plugin cho Steam Deck (Decky Loader)

Cùng chương trình cho Chế độ chơi game, dưới dạng plugin [Decky Loader](https://decky.xyz) trong menu Truy cập nhanh.

- **Game**: các game có thể upscale, game đang chạy lên trước, mỗi game có nhãn trạng thái và, khi đang chạy, những gì thật sự đã được nạp. Chọn một game để chọn DLSS 3.7 (HelixSR, từng cách), FSR 4.1 Exact / Lossy hoặc FSR 3, hoặc để cập nhật, sửa, gỡ, đổi tên tệp OptiScaler hay đọc nhật ký. Trước đó vẫn hỏi như ứng dụng desktop: tệp tải về, cảnh báo Lossy, cách DLSS và chống gian lận.
- **Thiết lập**: thư mục HelixSR (bộ chọn tệp), tệp tải về và bản FSR 4.1 (Steam Deck dùng bản cho đồ họa tích hợp), thông báo khi game khởi động (cho biết bộ upscale đã nạp chưa) và ngôn ngữ (mặc định giống Steam).
- Dùng chung `state.json`, tệp tải về và bản ghi tùy chọn khởi chạy với ứng dụng desktop: game thiết lập ở bên này sẽ hiện ở bên kia. Tùy chọn khởi chạy được ghi ngay qua Steam.
- Không có trong plugin: biểu mẫu cài đặt HelixSR (dùng ứng dụng desktop) và `helixsr-setup.sh` của HelixSR, chạy một lần trong Chế độ Desktop.
- Trong plugin, **Tải và dựng HelixSR** tải và dựng HelixSR 2.0 trở lên ngay cả ở Chế độ Game (mất vài phút).

Cài đặt: cài Decky Loader trên Steam Deck, tải `Scaler_Assistant-Decky-<phiên bản>.zip` từ trang [Releases](https://github.com/mosesmoon/scaler-assistant/releases), rồi vào cài đặt Decky → Developer (bật chế độ nhà phát triển trong General trước) → "Install Plugin from ZIP File".

## Cài đặt Trợ lý Scaler

**AppImage (khuyên dùng)**: đã kèm Python, Qt và 7-Zip.

1. Tải `Scaler_Assistant-<phiên bản>-x86_64.AppImage` từ trang [Releases](https://github.com/mosesmoon/scaler-assistant/releases).
2. Cho phép chạy: nhấp phải → Properties → Permissions → "Allow executing file as program" (tên gọi tùy trình quản lý tệp).
3. Nhấp đúp.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

Nếu không mở được, có thể hệ thống thiếu FUSE; chạy với `--appimage-extract-and-run`.

**Trình cài một tệp (.bin)**: `Scaler_Assistant-<phiên bản>-x86_64.bin` cài cùng ứng dụng đóng gói cho riêng người dùng của bạn (không cần root, không cần FUSE) vào `~/.local/opt/scaler-assistant`, kèm lệnh `scaler-assistant` và mục trong menu. **Flatpak**: `Scaler_Assistant-<phiên bản>-x86_64.flatpak` là gói một tệp trên runtime Freedesktop 25.08 (tải từ Flathub khi cài). Nó đọc được thư mục home và các ổ khác (thẻ SD trong `/run/media`) và thấy tiến trình của Steam và game qua `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / cài
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / gỡ
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**Từ mã nguồn**: Python 3.11+ và PyQt6 (Arch: `sudo pacman -S python-pyqt6`), cùng 7-Zip hoặc bsdtar để giải nén OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # chạy trực tiếp
./install.sh           # cài vào ~/.local/share/scaler-assistant và thêm vào menu
```

## Giới hạn đã biết

- **Chỉ game Steam.** Các cách FSR 4.1 / FSR 3 đã được kiểm từng tệp với OptiScaler 0.9.4; mỗi game hoạt động khác nhau: khi có lỗi, xem danh sách tương thích của OptiScaler hoặc chọn tên tệp khác cho OptiScaler.
- FSR 4.1 trong game Direct3D 11 và Vulkan chạy qua đường Direct3D 12 của OptiScaler và ít được thử hơn.
- HelixSR thay đổi nhanh. Trợ lý Scaler cần HelixSR 1.8.0 trở lên và theo cấu trúc của 1.8.x / 1.9.x / 2.0.x / 3.0.x / 3.1.x / 3.2.x.
- Thông báo nổi không hiển thị trong Chế độ chơi game của Steam Deck (gamescope). Plugin Decky hiển thị bằng thông báo của Steam thay thế.
- Với tiếng Thái, Việt, Mã Lai và Hindi, menu chuột phải là tiếng Anh (Qt không có bản dịch chính thức). Steam không có tên game tiếng Mã Lai và Hindi.

## Nơi lưu dữ liệu

| Vị trí | Nội dung |
|---|---|
| `~/.config/scaler-assistant/state.json` | Trạng thái của Trợ lý Scaler: thư mục HelixSR, danh sách game, ngôn ngữ, bản FSR 4.1, tên OptiScaler bạn chọn, các mục nó đã thêm vào tùy chọn khởi chạy (nhận một lần từ Trợ lý HelixSR) |
| `~/.local/share/scaler-assistant/components/` | Các tệp OptiScaler và FSR 4.1 đã tải |
| `~/homebrew/plugins/scaler-assistant/` | Plugin Decky trên Steam Deck (dùng cùng trạng thái và tệp tải về như trên) |
| `<game>/…/ScalerAssistant/` | FSR 4.1 / FSR 3: DLL FidelityFX, `scaler-install.json`, `backup/` |
| `<game>/…/HelixSR/helixsr-install.json`, cạnh DLL FSR của game | DLSS 3.7: bản ghi cài đặt của HelixSR (dùng chung với setup của HelixSR) |
| `<game>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Cài đặt và nhật ký |

## Giấy phép

Trợ lý Scaler là công cụ độc lập, không chính thức, không liên kết hay được xác nhận bởi tác giả HelixSR, NVIDIA, AMD, dự án OptiScaler hay dự án fsr4-shader-performance-overrides, và không chứa tệp nào của họ. Khi bạn yêu cầu, nó tải OptiScaler (GPL-3.0; fakenvapi MIT; DLL FidelityFX của AMD theo giấy phép AMD) và DLL FSR 4.1 (GPL-2.0-or-later, DLL AMD đã sửa kèm thông báo của AMD) từ GitHub Releases của họ. AppImage kèm `7zzs` của 7-Zip (GNU LGPL có hạn chế unRAR, BSD; kèm tệp giấy phép). HelixSR miễn phí theo HelixSR Freeware License; sau khi chạy setup, DLL của HelixSR chứa mạng của NVIDIA, nên Trợ lý Scaler chỉ sao chép chúng giữa các thư mục trên máy của bạn. Đừng bao giờ chia sẻ hay tải chúng lên. Plugin Decky có cùng tệp `7zzs`.
