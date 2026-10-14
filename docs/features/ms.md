# Pembantu HelixSR — Panduan Ciri

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · **Bahasa Melayu** · [हिन्दी](hi.md)

**Pembantu HelixSR** ialah alat desktop Linux yang memasang, menukar cara, mengemas kini dan membuang **[HelixSR](https://github.com/lonewolf0622/HelixSR)** dalam permainan Steam anda dengan satu klik, serta menunjukkan semasa bermain sama ada HelixSR benar-benar berjalan.

HelixSR menjalankan rangkaian penskalaan DLSS Model E milik NVIDIA pada GPU AMD (RDNA 1 dan lebih baharu) sebagai compute shader Direct3D 12 biasa, melalui Proton.

## Untuk siapa alat ini

HelixSR tiada pilihan pelancaran dan tiada fail tetapan pusat. Ia berfungsi dengan meletakkan fail DLL ke dalam folder setiap permainan, menggunakan salah satu daripada tiga cara bagi setiap permainan. Melakukannya secara manual bermakna:

1. Mencari upscaler yang ada dalam setiap permainan (FSR 3.1, DLSS, XeSS, FSR 2) dan lokasi `.exe` utamanya.
2. Memilih cara yang betul, menamakan semula fail asal permainan supaya selamat, dan menyalin fail HelixSR ke tempat yang betul.
3. Bagi cara OptiScaler, menulis laluan yang betul dalam `OptiScaler.ini`.
4. Mengulang semuanya selepas setiap kemas kini HelixSR, dan sekali lagi apabila kemas kini permainan menulis ganti HelixSR.
5. Membuka `helixsr.log` untuk mengetahui sama ada HelixSR benar-benar berjalan.

Pembantu HelixSR melakukan semua ini dalam satu tetingkap. Setup HelixSR sendiri bertanya satu demi satu permainan dalam terminal; Pembantu HelixSR menunjukkannya sebagai senarai untuk diklik.

## Sebelum bermula

> ⚠ **Pembantu HelixSR tidak termasuk HelixSR dan tidak sekali-kali memuat turunnya untuk anda.** Ia hanya menyalin fail daripada folder HelixSR yang anda sediakan sendiri.

1. **Muat turun HelixSR** (1.8.0 atau lebih baharu) daripada [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) dan ekstrak ke folder yang anda simpan, contohnya folder home.
2. **Jalankan `./helixsr-setup.sh` dalam folder itu sekali.** Ia bertanya dahulu sebelum memuat turun DLL DLSS NVIDIA, lalu membina rangkaian HelixSR daripadanya (kira-kira seminit). Apabila ia mula bertanya tentang permainan, anda boleh menjawab `n` atau menutup tetingkap: permainan diuruskan oleh Pembantu HelixSR. Jika folder ditemui tetapi belum disediakan, Pembantu menawarkan butang “Jalankan setup dalam terminal”.
3. **GPU AMD RDNA 1 atau lebih baharu** (Radeon RX 5000 dan lebih baharu, Steam Deck, APU Ryzen dengan grafik RDNA). Sokongan Radeon Vega masih percubaan dalam HelixSR 1.9.0.
4. **Permainan Direct3D 12 yang berjalan melalui Proton** dan mempunyai FSR 3.1, DLSS, XeSS atau FSR 2.

Pada permulaan pertama, Pembantu HelixSR mencari folder HelixSR yang telah disediakan dalam folder home, Downloads, Desktop dan Games anda. Anda sentiasa boleh memilih folder lain dengan “Pilih folder HelixSR…” atau mengklik label HelixSR di atas.

## Tiga cara HelixSR masuk ke dalam permainan

Inilah tiga cara HelixSR sendiri (huruf ialah jawapan yang digunakan oleh setup HelixSR). Pembantu HelixSR hanya menawarkan cara yang berfungsi untuk setiap permainan, dengan cara lalai di hadapan.

| Cara | Permainan perlu ada | Perubahan dalam folder permainan | Pilih dalam permainan |
|---|---|---|---|
| **Cara FSR** (f, lalai bagi permainan FSR 3.1) | FSR 3.1 | `amd_fidelityfx_upscaler_dx12.dll` (atau `amd_fidelityfx_dx12.dll`) permainan diganti dengan HelixSR; fail permainan disimpan sebagai `*.original.dll` | **AMD FSR** |
| **Cara OptiScaler** (o) | DLSS, XeSS atau FSR 2 | OptiScaler (keluaran rasmi dalam folder HelixSR anda) di sebelah `.exe` permainan, dengan backend FSR 3.1 dihalakan ke folder `HelixSR` di sebelahnya; semua yang diganti dipindahkan ke `HelixSR/backup` | **DLSS** (FSR atau XeSS juga boleh) |
| **Cara DLSS** (d, percubaan) | DLSS | Pemuat DLSS HelixSR sebagai `dxgi.dll` dan HelixSR sebagai `nvngx.dll` di sebelah `.exe` permainan | **DLSS** |

## Ciri

### 1. Mengimbas permainan Steam dan upscaler masing-masing

- Pada permulaan pertama, semua pustaka Steam diimbas (termasuk pada pemacu lain). Selepas memasang permainan, klik “⟳ Imbas semula permainan Steam”.
- Folder setiap permainan dicari untuk DLL FSR 3.1, DLSS, XeSS dan FSR 2, dan folder `.exe` utamanya dikenal pasti daripada maklumat pelancaran Steam (pelancar dan `*-Shipping.exe` Unreal diambil kira).
- Permainan dengan **anti-tipu** (Easy Anti-Cheat, BattlEye) ditanda.
- Nama permainan mengikut bahasa antara muka (nama setempat Steam) dan disusun mengikut bahasa itu. Permainan yang boleh guna HelixSR berada di atas; penapis “Permainan yang boleh guna HelixSR” aktif secara lalai.

### 2. Pemasangan satu klik

- Klik “Pasang HelixSR” untuk memasang dengan cara lalai, atau anak panah di sebelahnya untuk memilih cara lain. Setiap cara memberitahu apa yang perlu dipilih dalam permainan.
- Sebelum apa-apa diubah, alat ini memastikan folder HelixSR sudah disediakan (rangkaian sudah dibina) dan permainan tidak sedang berjalan.
- Cara DLSS menerangkan risikonya dahulu dan meminta pengesahan. Permainan dengan anti-tipu juga meminta pengesahan.
- Selepas siap, log menyatakan dengan tepat fail yang diganti, di mana fail permainan disimpan, dan apa yang perlu dipilih dalam permainan.

### 3. Tukar cara, kemas kini dan baiki

- **Tukar**: “Lagi” → “Tukar ke …” membuang cara semasa dahulu (mengembalikan semuanya) dan kemudian memasang cara baharu. Tetapan HelixSR anda dibawa bersama.
- **Kemas kini**: apabila folder HelixSR anda mempunyai binaan lebih baharu daripada permainan (versi HelixSR baharu, atau rangkaian dibina semula), permainan menunjukkan “↑ HelixSR … tersedia” dan butang “↑ Kemas kini”; “↑ Kemas kini semua” mengemas kini setiap permainan sekali gus.
- **Baiki**: kemas kini permainan atau “Sahkan integriti fail permainan” dalam Steam boleh meletakkan semula fail permainan di atas HelixSR. Permainan kemudian menunjukkan apa yang berlaku dan butang “Baiki”, yang meletakkan HelixSR kembali dan menyimpan fail baharu permainan sebagai sandaran.
- Apabila folder HelixSR yang lebih baharu dan sudah disediakan muncul dalam Downloads (atau tempat biasa lain), alat ini bertanya sekali sama ada mahu menggunakannya.

### 4. Buang

- “Buang” mengeluarkan HelixSR dan mengembalikan setiap fail yang diganti atau dipindahkannya tepat seperti asal.
- Tetapan HelixSR permainan (`helixsr.ini`) dikekalkan melainkan anda menanda “Buang juga tetapan HelixSR permainan ini”.
- Fail yang anda letakkan sendiri dalam folder `my-fsr` permainan tidak akan dipadam.

### 5. Tetapan HelixSR tanpa menyunting fail

“⚙ Tetapan” menyunting `helixsr.ini` permainan melalui borang. Hanya tetapan yang didokumenkan dalam README HelixSR ditawarkan:

| Kumpulan | Tetapan | Nilai |
|---|---|---|
| Penajaman | Penajam | Lalai, Mati, NVIDIA, RCAS |
| | Ketajaman | 0.00 – 1.00 |
| | Ikut gelangsar ketajaman permainan | Lalai, Ya, Tidak |
| Penskalaan (HelixSR 1.9.0+) | Rangkaian int8 | Lalai (auto), Auto, Hidup, Mati |
| | Langkah akhir dalam Ultra Performance | Lalai (Lanczos), Lanczos, EASU (FSR 1) |
| Keserasian | Saiz wave | Lalai, 64, 32 |

“Lalai” meninggalkan baris itu, jadi HelixSR menggunakan nilai lalainya sendiri. Komen dan baris lain dalam fail dikekalkan seperti sedia ada. Fail ditulis di sebelah DLL HelixSR mengikut cara permainan (folder `HelixSR` permainan, di sebelah DLL FSR permainan, atau di sebelah `.exe`).

### 6. Status HelixSR secara langsung (apa yang benar-benar berjalan)

Permainan Steam yang sedang berjalan diperiksa setiap 3 saat:

- Proton memuatkan DLL Windows terus daripada failnya, jadi alat ini dapat melihat dalam `/proc/<pid>/maps` sama ada permainan **benar-benar memuatkan HelixSR** (serta OptiScaler atau pemuat DLSS).
- HelixSR hanya dimuatkan apabila permainan menggunakan upscaler. Oleh itu “HelixSR belum dimuatkan” memberitahu apa yang perlu dipilih dalam tetapan grafik permainan.
- `helixsr.log` larian semasa dibaca: saiz wave kernel rangkaian dan baris ralat ditunjukkan. “Lagi” → “Lihat helixsr.log” menunjukkan log penuh dengan butang salin.
- Pada GPU **RDNA 3 dan lebih baharu**, dalam permainan dengan cara OptiScaler, README HelixSR mengesyorkan `WaveSize = 64` apabila log melaporkan wave32. Alat ini mengesannya dan menawarkan “Tetapkan WaveSize = 64” dengan satu klik.
- Label GPU di atas menunjukkan generasi GPU anda (contohnya “AMD RDNA 3 (gfx1100)”).

### 7. Paparan tindih semasa permainan bermula

Jika Pembantu HelixSR dibuka semasa permainan dengan HelixSR bermula, sebaik sahaja HelixSR dimuatkan, satu kad kecil muncul di sudut kanan bawah selama kira-kira 10 saat menunjukkan versi, cara dan saiz wave (sekali bagi setiap pelancaran; permainan yang sudah berjalan sebelum alat dibuka dilangkau). Jika HelixSR masih belum dimuatkan selepas 90 saat, kad itu memberitahu apa yang perlu dipilih dalam permainan. Paparan tindih ialah tetingkap X11 (XWayland) berasingan yang tidak mengambil fokus dan membiarkan klik tetikus menembusinya. Boleh dimatikan dengan kotak semak pada bar alat. Ia tidak muncul dalam Mod Permainan Steam Deck (gamescope).

### 8. Lancar permainan, cari dan tapis

- Setiap baris ada butang “▶ Lancar” (melalui `steam://rungameid/<AppID>`); ia menunjukkan “Sedang berjalan” semasa permainan berjalan.
- Cari mengikut nama permainan (dalam apa-apa bahasa) atau App ID. Penapis: permainan yang boleh guna HelixSR, dipasang, tidak dipasang, perlu dikemas kini atau dibaiki, sedang berjalan, semua permainan.

### 9. Dua belas bahasa antara muka

台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी. Bahasa sistem digunakan pada permulaan pertama; tukar di kanan atas (berkuat kuasa serta-merta dan diingati).

### 10. Direka untuk selamat

- Tiada apa-apa diubah jika folder HelixSR belum disediakan atau permainan sedang berjalan.
- Setiap fail yang diganti oleh HelixSR disimpan (`*.original.dll` atau `HelixSR/backup`), dan setiap fail yang disalin diperiksa bait demi bait.
- `OptiScaler.ini` yang sedia ada disandarkan dan dipulihkan semasa dibuang; DLL FSR yang anda ganti sendiri dalam folder `HelixSR` permainan dikekalkan semasa kemas kini.
- Cara DLSS dan permainan dengan anti-tipu memerlukan pengesahan yang jelas.

## Berfungsi bersama setup HelixSR sendiri

Pembantu HelixSR menulis rekod pemasangan (`helixsr-install.json`), sandaran dan nama fail yang sama seperti setup HelixSR. Oleh itu:

- Permainan yang disediakan dengan `helixsr-setup.sh` ditunjukkan sebagai dipasang dalam Pembantu HelixSR, bersama caranya, dan boleh ditukar, dikemas kini atau dibuang di situ.
- Permainan yang disediakan dengan Pembantu HelixSR dikenali oleh setup HelixSR dan `helixsr-uninstall.sh`, yang boleh mengemas kini atau membuangnya.

## Memasang Pembantu HelixSR

**AppImage (disyorkan)**: Python dan Qt sudah disertakan, tiada apa-apa lagi perlu dipasang.

1. Muat turun `HelixSR_Assistant-<versi>-x86_64.AppImage` daripada halaman [Releases](https://github.com/mosesmoon/helixsr-assistant/releases).
2. Jadikannya boleh laku: klik kanan pada fail → Properties → Permissions, dan hidupkan “Allow executing file as program” (perkataannya berbeza mengikut pengurus fail).
3. Klik dua kali untuk membuka Pembantu HelixSR.

Atau dalam terminal:

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

Jika ia tidak bermula, sistem anda mungkin tiada FUSE; jalankannya dengan `./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run`.

**Daripada kod sumber**: memerlukan Python 3.11 atau lebih baharu dan PyQt6 (Arch: `sudo pacman -S python-pyqt6`).

```bash
./helixsr-assistant    # jalankan terus
./install.sh           # pasang ke ~/.local/share/helixsr-assistant dan tambah entri menu aplikasi
```

## Had yang diketahui

- **Permainan Steam sahaja.** Bagi permainan dari kedai lain, gunakan setup HelixSR sendiri (seret folder permainan ke dalamnya).
- HelixSR sendiri hanya berfungsi dalam permainan Direct3D 12. Permainan yang disenaraikan dengan DLL DLSS atau FSR mungkin masih menggunakan Vulkan atau Direct3D 11; HelixSR tidak memberi kesan di situ.
- HelixSR berubah dengan sangat pantas. Pembantu HelixSR memerlukan HelixSR 1.8.0 atau lebih baharu dan dibuat berdasarkan susunan 1.8.x dan 1.9.x; jika HelixSR akan datang mengubah cara permainan disediakan, gunakan setup HelixSR sendiri sehingga Pembantu HelixSR dikemas kini.
- Paparan tindih tidak muncul dalam Mod Permainan Steam Deck (gamescope), dan permainan dalam skrin penuh eksklusif Wayland asli mungkin menutupnya.
- Dalam bahasa Thai, Vietnam, Melayu dan Hindi, menu klik kanan dalam bahasa Inggeris (Qt tiada terjemahan rasmi untuk bahasa ini). Steam tiada nama permainan dalam bahasa Melayu atau Hindi, jadi kedua-dua bahasa ini sentiasa menunjukkan nama asal.

## Di mana data disimpan

| Lokasi | Kandungan |
|---|---|
| `~/.config/helixsr-assistant/state.json` | Keadaan Pembantu HelixSR sendiri: folder HelixSR, cache senarai permainan, bahasa antara muka, tetapan paparan tindih |
| `<permainan>/…/HelixSR/helixsr-install.json`, di sebelah DLL FSR permainan | Rekod pemasangan HelixSR (dikongsi dengan setup HelixSR) |
| `<permainan>/…/helixsr.ini` | Tetapan HelixSR untuk permainan itu |
| `<permainan>/…/helixsr.log` | Laporan HelixSR kali terakhir permainan dijalankan |

## Lesen

Pembantu HelixSR ialah alat bebas dan tidak rasmi. Ia tidak bergabung dengan atau disokong oleh pengarang HelixSR, NVIDIA, AMD atau projek OptiScaler, dan tidak mengandungi sebarang fail mereka. HelixSR boleh digunakan secara percuma di bawah HelixSR Freeware License. Selepas setup HelixSR dijalankan, DLL HelixSR mengandungi rangkaian NVIDIA: Pembantu HelixSR hanya menyalinnya antara folder dalam PC anda sendiri. Jangan sekali-kali kongsi atau muat naiknya.
