# Trợ lý HelixSR — Hướng dẫn tính năng

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · **Tiếng Việt** · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**Trợ lý HelixSR** là công cụ máy tính để bàn cho Linux, giúp cài, chuyển cách, cập nhật và gỡ **[HelixSR](https://github.com/lonewolf0622/HelixSR)** trong các game Steam chỉ với một cú nhấp, đồng thời cho biết khi chơi HelixSR có thực sự đang chạy hay không.

HelixSR chạy mạng upscale DLSS Model E của NVIDIA trên GPU AMD (RDNA 1 trở lên) dưới dạng compute shader Direct3D 12 thông thường, thông qua Proton.

## Công cụ này dành cho ai

HelixSR không có tùy chọn khởi chạy hay tệp cài đặt chung. Nó hoạt động bằng cách đặt các tệp DLL vào thư mục của từng game, theo một trong ba cách cho mỗi game. Làm thủ công nghĩa là:

1. Tìm xem mỗi game có những bộ upscale nào (FSR 3.1, DLSS, XeSS, FSR 2) và tệp `.exe` chính nằm ở đâu.
2. Chọn đúng cách cho game, đổi tên tệp gốc của game để giữ lại, rồi sao chép tệp của HelixSR vào đúng chỗ.
3. Với cách OptiScaler, phải điền đúng đường dẫn vào `OptiScaler.ini`.
4. Làm lại tất cả sau mỗi lần cập nhật HelixSR, và thêm lần nữa khi bản cập nhật game ghi đè HelixSR.
5. Mở `helixsr.log` để biết HelixSR có thực sự đang chạy không.

Trợ lý HelixSR làm tất cả trong một cửa sổ. Setup của HelixSR hỏi từng game trong terminal; Trợ lý HelixSR hiển thị chúng thành danh sách để nhấp.

## Trước khi bắt đầu

> ⚠ **Trợ lý HelixSR không kèm HelixSR và không bao giờ tải hộ bạn.** Nó chỉ sao chép tệp từ thư mục HelixSR do bạn tự chuẩn bị.

1. **Tải HelixSR** (1.8.0 trở lên) từ [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) và giải nén vào một thư mục bạn sẽ giữ lại, ví dụ thư mục home.
2. **Chạy `./helixsr-setup.sh` trong thư mục đó một lần.** Nó sẽ hỏi trước khi tải DLL DLSS của NVIDIA và dùng nó để tạo mạng của HelixSR (khoảng một phút). Khi nó bắt đầu hỏi từng game, bạn có thể trả lời `n` hoặc đóng cửa sổ: phần game để Trợ lý HelixSR lo. Nếu tìm thấy thư mục nhưng chưa thiết lập, Trợ lý sẽ có nút “Chạy setup trong terminal”.
3. **GPU AMD RDNA 1 trở lên** (Radeon RX 5000 trở lên, Steam Deck, Ryzen APU có đồ họa RDNA). Hỗ trợ Radeon Vega vẫn đang thử nghiệm trong HelixSR 1.9.0.
4. **Game Direct3D 12 chạy qua Proton** có FSR 3.1, DLSS, XeSS hoặc FSR 2.

Ở lần khởi động đầu, Trợ lý HelixSR sẽ tìm thư mục HelixSR đã thiết lập trong các thư mục home, Downloads, Desktop và Games. Bạn luôn có thể chọn thư mục khác bằng “Chọn thư mục HelixSR…” hoặc nhấp vào nhãn HelixSR ở trên cùng.

## Ba cách đưa HelixSR vào game

Đây là ba cách của chính HelixSR (chữ cái là câu trả lời mà setup của HelixSR dùng). Trợ lý HelixSR chỉ đưa ra những cách dùng được cho từng game, cách mặc định đứng đầu.

| Cách | Game cần có | Thay đổi trong thư mục game | Chọn trong game |
|---|---|---|---|
| **Cách FSR** (f, mặc định cho game có FSR 3.1) | FSR 3.1 | `amd_fidelityfx_upscaler_dx12.dll` (hoặc `amd_fidelityfx_dx12.dll`) của game được thay bằng HelixSR; tệp của game được giữ dưới tên `*.original.dll` | **AMD FSR** |
| **Cách OptiScaler** (o) | DLSS, XeSS hoặc FSR 2 | Đặt OptiScaler (bản chính thức trong thư mục HelixSR của bạn) cạnh `.exe` của game, trỏ backend FSR 3.1 của nó tới thư mục `HelixSR` bên cạnh; mọi tệp bị thay đều được chuyển vào `HelixSR/backup` | **DLSS** (FSR hoặc XeSS cũng được) |
| **Cách DLSS** (d, thử nghiệm) | DLSS | Đặt trình nạp DLSS của HelixSR là `dxgi.dll` và HelixSR là `nvngx.dll` cạnh `.exe` của game | **DLSS** |

## Tính năng

### 1. Quét game Steam và bộ upscale của chúng

- Lần đầu mở sẽ quét toàn bộ thư viện Steam (cả trên ổ đĩa khác). Sau khi cài game mới, hãy nhấp “⟳ Quét lại game Steam”.
- Tìm DLL FSR 3.1, DLSS, XeSS và FSR 2 trong thư mục từng game, và xác định thư mục chứa `.exe` chính từ thông tin khởi chạy của Steam (có xử lý trình khởi chạy và `*-Shipping.exe` của Unreal).
- Game có **chống gian lận** (Easy Anti-Cheat, BattlEye) sẽ được đánh dấu.
- Tên game theo ngôn ngữ giao diện (tên bản địa hóa của Steam) và sắp xếp theo ngôn ngữ đó. Game dùng được HelixSR đứng trước; bộ lọc “Game dùng được HelixSR” bật sẵn.

### 2. Cài bằng một cú nhấp

- Nhấp “Cài HelixSR” để cài theo cách mặc định, hoặc mũi tên bên cạnh để chọn cách khác. Mỗi cách đều cho biết cần chọn gì trong game.
- Trước khi thay đổi bất cứ điều gì, công cụ kiểm tra thư mục HelixSR đã thiết lập (đã tạo mạng) và game không đang chạy.
- Cách DLSS sẽ giải thích rủi ro trước và yêu cầu xác nhận. Game có chống gian lận cũng yêu cầu xác nhận.
- Khi xong, nhật ký ghi rõ tệp nào đã bị thay, tệp của game được giữ ở đâu và cần chọn gì trong game.

### 3. Chuyển cách, cập nhật và sửa

- **Chuyển cách**: “Thêm” → “Chuyển sang…” sẽ gỡ cách hiện tại trước (trả lại mọi thứ) rồi cài cách mới. Cài đặt HelixSR của bạn được chuyển theo.
- **Cập nhật**: khi thư mục HelixSR của bạn có bản mới hơn bản trong game (phiên bản HelixSR mới, hoặc mạng được tạo lại), game sẽ hiện “↑ Đã có HelixSR …” và nút “↑ Cập nhật”; “↑ Cập nhật tất cả” cập nhật mọi game cùng lúc.
- **Sửa**: bản cập nhật game hoặc “Kiểm tra tính toàn vẹn của tệp game” trong Steam có thể đặt lại tệp của game đè lên HelixSR. Khi đó game sẽ cho biết chuyện gì đã xảy ra kèm nút “Sửa”: nó đặt HelixSR về chỗ cũ và giữ tệp mới của game làm bản sao lưu.
- Khi trong Downloads (hoặc chỗ thường dùng khác) xuất hiện thư mục HelixSR mới hơn và đã thiết lập, công cụ sẽ hỏi một lần có muốn chuyển sang không.

### 4. Gỡ

- “Gỡ” bỏ HelixSR và trả mọi tệp nó đã thay hoặc di chuyển về đúng như cũ.
- Cài đặt HelixSR của game (`helixsr.ini`) được giữ lại, trừ khi bạn đánh dấu “Gỡ luôn cài đặt HelixSR của game này”.
- Tệp bạn tự đặt vào thư mục `my-fsr` của game không bao giờ bị xóa.

### 5. Cài đặt HelixSR mà không cần sửa tệp

“⚙ Cài đặt” chỉnh `helixsr.ini` của game bằng biểu mẫu. Chỉ có các cài đặt được ghi trong README của HelixSR:

| Nhóm | Cài đặt | Giá trị |
|---|---|---|
| Làm nét | Bộ làm nét | Mặc định, Tắt, NVIDIA, RCAS |
| | Độ nét | 0.00 – 1.00 |
| | Theo thanh trượt độ nét của game | Mặc định, Có, Không |
| Upscale (HelixSR 1.9.0+) | Mạng int8 | Mặc định (tự động), Tự động, Bật, Tắt |
| | Bước cuối ở chế độ Ultra Performance | Mặc định (Lanczos), Lanczos, EASU (FSR 1) |
| Tương thích | Kích thước wave | Mặc định, 64, 32 |

“Mặc định” sẽ không ghi dòng đó, để HelixSR dùng giá trị mặc định của nó. Chú thích và mọi dòng khác trong tệp được giữ nguyên. Tệp được ghi cạnh DLL của HelixSR theo cách của game (thư mục `HelixSR` của game, cạnh DLL FSR của game, hoặc cạnh `.exe`).

### 6. Trạng thái HelixSR trực tiếp (thứ thực sự đang chạy)

Các game Steam đang chạy được kiểm tra mỗi 3 giây:

- Proton nạp DLL Windows trực tiếp từ tệp, nên công cụ thấy được trong `/proc/<pid>/maps` game **đã thực sự nạp HelixSR chưa** (cùng OptiScaler hoặc trình nạp DLSS).
- HelixSR chỉ được nạp khi game bắt đầu dùng bộ upscale. Vì vậy “HelixSR chưa được nạp” cho bạn biết cần chọn gì trong cài đặt đồ họa của game.
- Đọc `helixsr.log` của lần chạy hiện tại: hiển thị kích thước wave của kernel mạng và các dòng lỗi. “Thêm” → “Xem helixsr.log” hiển thị toàn bộ nhật ký kèm nút sao chép.
- Trên GPU **RDNA 3 trở lên**, ở game dùng cách OptiScaler, README của HelixSR khuyên đặt `WaveSize = 64` khi nhật ký báo wave32. Công cụ phát hiện điều này và có nút “Đặt WaveSize = 64” chỉ một cú nhấp.
- Nhãn GPU ở trên cùng hiển thị thế hệ GPU của bạn (ví dụ “AMD RDNA 3 (gfx1100)”).

### 7. Thông báo khi mở game

Nếu Trợ lý HelixSR đang mở khi một game có HelixSR khởi động, ngay khi HelixSR được nạp sẽ có một thẻ nhỏ hiện ở góc phải dưới khoảng 10 giây, cho biết phiên bản, cách cài và kích thước wave (mỗi lần mở game một lần; game đã chạy trước khi mở công cụ sẽ bị bỏ qua). Nếu sau 90 giây HelixSR vẫn chưa được nạp, thẻ sẽ cho biết cần chọn gì trong game. Thông báo là cửa sổ X11 (XWayland) riêng, không bao giờ lấy tiêu điểm và để cú nhấp chuột đi xuyên qua. Có thể tắt bằng ô đánh dấu trên thanh công cụ. Không hiện trong chế độ Game của Steam Deck (gamescope).

### 8. Mở game, tìm kiếm và lọc

- Mỗi dòng có nút “▶ Chơi” (qua `steam://rungameid/<AppID>`); khi game đang chạy sẽ hiện “Đang chạy”.
- Tìm theo tên game (bất kỳ ngôn ngữ nào) hoặc App ID. Bộ lọc: game dùng được HelixSR, đã cài, chưa cài, cần cập nhật hoặc sửa, đang chạy, tất cả game.

### 9. 12 ngôn ngữ giao diện

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. Lần đầu dùng ngôn ngữ hệ thống; đổi ở góc trên bên phải (áp dụng ngay và được ghi nhớ).

### 10. Thiết kế an toàn

- Không thay đổi gì nếu thư mục HelixSR chưa thiết lập hoặc game đang chạy.
- Mọi tệp HelixSR thay thế đều được giữ (`*.original.dll` hoặc `HelixSR/backup`), và mọi tệp sao chép đều được kiểm tra từng byte.
- `OptiScaler.ini` bạn đã có sẽ được sao lưu và khôi phục khi gỡ; DLL FSR bạn tự thay trong thư mục `HelixSR` của game được giữ khi cập nhật.
- Cách DLSS và game có chống gian lận đều cần xác nhận rõ ràng.

## Dùng chung với setup của chính HelixSR

Trợ lý HelixSR ghi cùng bản ghi cài đặt (`helixsr-install.json`), cùng bản sao lưu và tên tệp như setup của HelixSR. Do đó:

- Game thiết lập bằng `helixsr-setup.sh` hiện là đã cài trong Trợ lý HelixSR, kèm cách cài, và có thể chuyển, cập nhật hoặc gỡ tại đây.
- Game thiết lập bằng Trợ lý HelixSR được setup của HelixSR và `helixsr-uninstall.sh` nhận ra, và chúng có thể cập nhật hoặc gỡ.

## Cài Trợ lý HelixSR

**AppImage (khuyên dùng)**: đã kèm Python và Qt, không cần cài thêm gì.

1. Tải `HelixSR_Assistant-<phiên bản>-x86_64.AppImage` từ trang [Releases](https://github.com/mosesmoon/helixsr-assistant/releases).
2. Cho phép chạy: nhấp chuột phải vào tệp → Properties → Permissions, bật “Allow executing file as program” (chữ khác nhau tùy trình quản lý tệp).
3. Nhấp đúp để mở Trợ lý HelixSR.

Hoặc trong terminal:

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

Nếu không mở được, hệ thống có thể thiếu FUSE; hãy chạy bằng `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run`.

**Từ mã nguồn**: cần Python 3.11 trở lên và PyQt6 (Arch: `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # chạy trực tiếp
./install.sh           # cài vào ~/.local/share/helixsr-assistant và thêm mục vào menu ứng dụng
```

## Hạn chế đã biết

- **Chỉ hỗ trợ game Steam.** Với game từ cửa hàng khác, hãy dùng setup của chính HelixSR (kéo thư mục game vào).
- Bản thân HelixSR chỉ chạy trong game Direct3D 12. Game có DLL DLSS hay FSR vẫn có thể là Vulkan hoặc Direct3D 11; khi đó HelixSR không có tác dụng.
- HelixSR thay đổi rất nhanh. Trợ lý HelixSR cần HelixSR 1.8.0 trở lên và được làm theo cấu trúc của 1.8.x và 1.9.x; nếu phiên bản HelixSR sau này đổi cách thiết lập game, hãy dùng setup của chính HelixSR cho đến khi Trợ lý HelixSR được cập nhật.
- Thông báo không hiện trong chế độ Game của Steam Deck (gamescope), và game toàn màn hình độc quyền trên Wayland gốc có thể che nó.
- Ở tiếng Thái, tiếng Việt, tiếng Mã Lai và tiếng Hindi, menu chuột phải là tiếng Anh (Qt không có bản dịch chính thức cho các ngôn ngữ này). Steam không có tên game tiếng Mã Lai và Hindi, nên hai ngôn ngữ này luôn hiện tên gốc.

## Nơi lưu dữ liệu

| Vị trí | Nội dung |
|---|---|
| `~/.config/helixsr-assistant/state.json` | Trạng thái riêng của Trợ lý HelixSR: thư mục HelixSR, bộ nhớ đệm danh sách game, ngôn ngữ giao diện, cài đặt thông báo |
| `<game>/…/HelixSR/helixsr-install.json`, cạnh DLL FSR của game | Bản ghi cài đặt của HelixSR (dùng chung với setup của HelixSR) |
| `<game>/…/helixsr.ini` | Cài đặt HelixSR của game đó |
| `<game>/…/helixsr.log` | Những gì HelixSR báo lại ở lần chạy game gần nhất |

## Giấy phép

Trợ lý HelixSR là công cụ độc lập, không chính thức. Nó không liên kết hay được tác giả HelixSR, NVIDIA, AMD hoặc dự án OptiScaler chứng thực, và không chứa bất kỳ tệp nào của họ. HelixSR được dùng miễn phí theo HelixSR Freeware License. Sau khi chạy setup của HelixSR, các DLL của HelixSR chứa mạng của NVIDIA: Trợ lý HelixSR chỉ sao chép chúng giữa các thư mục trên máy của bạn. Tuyệt đối không chia sẻ hay tải chúng lên.
