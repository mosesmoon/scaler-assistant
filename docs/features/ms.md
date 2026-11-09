# Pembantu Scaler — Panduan Ciri

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · [日本語](ja.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · **Bahasa Melayu** · [हिन्दी](hi.md)

**Pembantu Scaler** ialah alat desktop Linux yang membolehkan anda memilih upscaler bagi setiap permainan Steam — **DLSS 3.7 ([HelixSR](https://github.com/lonewolf0622/HelixSR))**, **FSR 4.1** (Exact atau Lossy daripada [fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides), atau yang asli AMD pada RX 9000) atau **FSR 3** — lalu memasang, menukar, mengemas kini, membaiki dan membuangnya dengan satu klik. Ia juga menunjukkan sama ada upscaler benar-benar berjalan semasa anda bermain.

## Untuk siapa

Memasukkan upscaler yang lebih baik ke dalam permainan di Linux secara manual bermakna:

1. Mencari upscaler yang ada dalam permainan (DLSS, XeSS, FSR 2, FSR 3.0, FSR 3.1), API grafik yang digunakannya dan lokasi `.exe` utamanya.
2. Meletakkan OptiScaler di sebelah `.exe` dengan nama fail yang diterima permainan, bersama DLL FidelityFX yang diperlukan, dan menyunting `OptiScaler.ini` untuk upscaler yang dikehendaki.
3. Menambah `WINEDLLOVERRIDES` pada pilihan pelancaran Steam apabila nama fail itu memerlukannya — tanpa merosakkan apa yang sudah ada.
4. Memuat turun DLL FSR 4.1 yang betul untuk GPU anda, atau menyediakan HelixSR seperti dalam README-nya.
5. Mengulanginya selepas setiap kemas kini, dan sekali lagi apabila kemas kini permainan menulis ganti fail anda.

Pembantu Scaler melakukan semua ini dari satu tetingkap dan menyimpan semua yang digantikan, jadi apabila dibuang, permainan kembali tepat seperti asal.

## Pilihan untuk setiap permainan

API grafik dan upscaler permainan menentukan pilihan yang ditawarkan. Permainan mesti sudah mempunyai sekurang-kurangnya satu upscaler (DLSS, XeSS, FSR 2 atau FSR 3.1): itulah yang diambil alih oleh OptiScaler dan HelixSR.

| Pilihan | Permainan memerlukan | Apa yang diletakkan dalam folder permainan | Pilih dalam permainan |
|---|---|---|---|
| **DLSS 3.7 (HelixSR) · cara FSR** | Direct3D 12, FSR 3.1 | DLL FSR 3.1 permainan diganti dengan HelixSR (fail asal disimpan sebagai `*.original.dll`) | AMD FSR |
| **DLSS 3.7 (HelixSR) · cara OptiScaler** | Direct3D 12, DLSS, XeSS atau FSR 2 | OptiScaler di sebelah `.exe`, dihalakan ke folder `HelixSR` | DLSS |
| **DLSS 3.7 (HelixSR) · cara DLSS** (percubaan) | Direct3D 12, DLSS | Pemuat DLSS HelixSR (`dxgi.dll`) dan HelixSR sebagai `nvngx.dll` | DLSS |
| **FSR 4.1 Exact** | mana-mana empat upscaler | OptiScaler di sebelah `.exe`; DLL FidelityFX dan DLL FSR 4.1 Exact dalam folder `ScalerAssistant` | DLSS, FSR atau XeSS |
| **FSR 4.1 Lossy** | sama | sama, dengan DLL FSR 4.1 Lossy | DLSS, FSR atau XeSS |
| **FSR 4.1.2 Lite / Lite Lossy** | sama | sama, dengan DLL FSR 4.1 4.1.2l-exact / 4.1.2l-lossy | DLSS, FSR atau XeSS |
| **FSR 4.1 (AMD)** — menggantikan Exact / Lossy pada RX 9000 (RDNA 4) | sama | sama, dengan DLL FSR 4.1 asli AMD | DLSS, FSR atau XeSS |
| **FSR 3** | sama | sama; OptiScaler menggunakan FSR 3.1.5 | DLSS, FSR atau XeSS |

- **Exact** memberi gambar FSR 4.1 AMD bait demi bait, dengan shader yang lebih pantas. **Lossy** lebih pantas lagi dan mengubah gambar sedikit; Pembantu Scaler menunjukkan `WARNING.txt`-nya sekali sebelum penggunaan pertama. Jika tidak pasti, pilih Exact.
- **Lossy** sejak DLL dll-2026-10-29 ialah Lossy2 dahulu yang dilatih lagi (Lossy lama digugurkan): jauh kurang bintik gelap pada dedaun, tetapi lebih perlahan mengikut perubahan menjadi cerah. **Lite** dan **Lite Lossy** menggunakan rangkaian FSR 4.1.2 Lite AMD yang lebih kecil (mungkin yang digunakan pemacu AMD untuk grafik terbina dalam): Lite memberi gambar Lite AMD bait demi bait dan sedikit lebih pantas; Lite Lossy menjalankannya setiap dua bingkai dan ialah binaan paling pantas, dengan gambar hampir dengan Lite. Lite sedikit kurang tepat berbanding FSR 4 penuh pada gambar pegun dan sesetengah gerakan, lebih baik pada yang lain. Lossy dan Lite Lossy masing-masing menunjukkan `WARNING.txt` sendiri sekali. Permainan yang disediakan dengan Lossy2 dipaparkan sebagai lapuk dan dikemas kini kepada Lossy.
- HelixSR hanya berfungsi dalam permainan **Direct3D 12**, jadi DLSS 3.7 hanya ditawarkan di situ. FSR 4.1 dan FSR 3 juga berfungsi dalam permainan **Direct3D 11 dan Vulkan**: FSR 3 secara asli, FSR 4.1 melalui laluan Direct3D 12 OptiScaler (kurang diuji berbanding permainan Direct3D 12).
- Klik **"Pilih upscaler"** pada baris permainan (atau **"Upscaler"** apabila sudah dipasang): DLSS 3.7 (HelixSR) membuka submenu dengan cara-caranya; pilihan semasa ditandakan. Menukar akan membuang pilihan semasa dahulu dan memulihkan semuanya.

## Sebelum bermula

- **FSR 4.1 dan FSR 3** tidak memerlukan apa-apa lagi: kali pertama dipilih, Pembantu Scaler bertanya sama ada mahu memuat turun OptiScaler dan DLL FSR 4.1 untuk GPU anda (lihat "Muat turun").
- **DLSS 3.7** memerlukan HelixSR, yang tidak disertakan dalam Pembantu Scaler. Muat turun HelixSR 1.8.0 atau lebih baharu dari [GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases)-nya, ekstrak ke folder yang anda simpan dan jalankan `./helixsr-setup.sh` di situ sekali (ia membina rangkaian HelixSR pada PC anda; apabila ditanya tentang permainan, anda boleh menjawab `n`). Label **HelixSR** di atas menerangkannya; folder HelixSR yang sudah disediakan dalam home, Downloads, Desktop atau Games ditemui sendiri.
  Lebih mudah: tekan **Muat turun dan bina HelixSR** dalam tetingkap itu (HelixSR 2.0 atau lebih baharu); Scaler Assistant melakukan semua ini untuk anda, tanpa terminal.
- Permainan dijalankan melalui **Proton**. HelixSR dibuat untuk GPU AMD (RDNA 1 dan lebih baharu). FSR 4.1 Exact / Lossy dibuat untuk Radeon RX 7000 / RX 6000 dan grafik Radeon terbina dalam (termasuk Steam Deck); GPU lain sepatutnya boleh menjalankannya tetapi belum diuji oleh pembuatnya. FSR 4.1 tidak berfungsi pada GPU Radeon RX 5000 (RDNA 1) (setiap binaan hanya memberikan gambar hitam), jadi Pembantu Scaler mengelabukannya di situ; FSR 3 dan DLSS 3.7 (HelixSR) masih boleh digunakan.

## Ciri

### 1. Mengimbas permainan Steam anda

- Semua pustaka Steam diimbas semasa permulaan pertama (termasuk pada pemacu lain). Klik "⟳ Imbas semula permainan Steam" selepas memasang permainan.
- Bagi setiap permainan: DLL upscaler yang ada, folder `.exe` utama (daripada maklumat pelancaran Steam; pelancar dan `*-Shipping.exe` Unreal dikendalikan), **API grafik** (dibaca daripada jadual import `.exe`: DX12, DX11 atau Vulkan) dan sama ada ia mempunyai **anti-tipu** (Easy Anti-Cheat, BattlEye).
- Nama permainan mengikut bahasa antara muka (nama tempatan Steam). Permainan yang boleh di-upscale disenaraikan dahulu.

### 2. Nama fail OptiScaler yang berfungsi dalam permainan

Permainan memuatkan OptiScaler sebagai DLL sistem di sebelah `.exe`-nya. Nama dipilih mengikut urutan:

1. nama yang anda pilih untuk permainan itu ("Lagi" → "Nama fail OptiScaler…"),
2. nama OptiScaler yang sudah ada,
3. nama yang diberi oleh [senarai keserasian OptiScaler](https://github.com/optiscaler/OptiScaler/wiki) untuk permainan itu (contohnya `d3d12.dll` atau `winmm.dll`),
4. `winmm.dll` untuk permainan Vulkan,
5. nama lain yang kosong (`winmm.dll`, `version.dll`, …) apabila permainan atau mod lain (contohnya ReShade) sudah mempunyai `dxgi.dll`, atau apabila pilihan pelancaran anda menetapkan nama itu kepada versi terbina dalam,
6. selain itu `dxgi.dll`.

Fail yang sudah ada tidak pernah ditulis ganti: ia dipindahkan ke `ScalerAssistant/backup` (`HelixSR/backup` untuk DLSS 3.7) dan dikembalikan semasa dibuang.

### 3. Pilihan pelancaran Steam: hanya yang perlu, milik anda kekal seperti asal

Di bawah Proton, `dxgi.dll` dan `d3d12.dll` dimuatkan tanpa apa-apa lagi. Nama lain memerlukan `WINEDLLOVERRIDES="<nama>=n,b"` dalam pilihan pelancaran, dan Pembantu Scaler menambahnya untuk anda:

- **Hanya satu entri itu dimasukkan.** Jika anda sudah ada `WINEDLLOVERRIDES`, `;winmm=n,b` ditambah di dalamnya; jika tidak, `WINEDLLOVERRIDES="winmm=n,b"` diletakkan di hadapan (bersama `%command%` jika tiada). Selebihnya tidak berubah. Contoh: `-dx12 %command%` menjadi `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`.
- **Hanya satu entri itu dikeluarkan** apabila OptiScaler dibuang atau dinamakan semula. Jika anda tidak mengubah pilihan di antaranya, ia kembali tepat seperti asal; jika diubah, hanya teks yang dimasukkan dikeluarkan dan perubahan anda kekal.
- Entri yang anda sudah ada untuk nama itu tidak disentuh dan tidak dibuang kemudian. Jika pilihan anda menetapkan nama itu kepada versi terbina dalam Wine, Pembantu Scaler menggunakan nama lain dan tidak mengubah tetapan anda.
- Jika entri itu hilang kemudian, permainan menunjukkan "Pilihan pelancaran tiada" dan "Baiki" menambahnya semula.
- Semasa Steam berjalan, pilihan diubah melalui Steam sendiri apabila port nyahpepijatnya tersedia (seperti yang digunakan Decky Loader). Jika tidak, Pembantu Scaler menawarkan untuk menutup Steam, menulis perubahan dan membuka Steam semula — sebelum sebarang fail permainan disentuh.

### 4. Muat turun (FSR 4.1 dan FSR 3)

Klik label **OptiScaler** di atas (atau label GPU):

- **OptiScaler 0.9.4** (dengan DLL FidelityFX AMD: FSR 3 dan FSR 4.1 AMD, serta fakenvapi) dan **FSR 4.1 Exact / Lossy / Lite / Lite Lossy** dalam binaan untuk GPU anda: kad RX 7000, kad RX 6000, grafik RDNA 3 terbina dalam pemproses (juga GeForce, Intel Arc dan GPU lain), atau Steam Deck dan grafik RDNA 2 terbina dalam pemproses. Setiap binaan berfungsi pada semua; binaan untuk GPU anda paling pantas. Jika permainan ranap dengan Exact, pilih binaan untuk grafik terbina dalam.
- Tiada apa dimuat turun sehingga anda bersetuju. Setiap muat turun ialah keluaran tetap yang disemak dengan saiz dan SHA-256 sebelum diekstrak; hanya fail yang diperlukan permainan disimpan, dalam `~/.local/share/scaler-assistant/components/`.
- **Binaan FSR 4.1**: automatik mengikut GPU (RX 9000 / RDNA 4 → FSR 4.1 asli AMD, grafik terbina dalam dan Steam Deck → binaan terbina dalam, GPU lain → binaan kad grafik), atau dipilih sendiri. DLL yang diubah suai tidak pernah digunakan pada RDNA 4. Pada GPU lain, OptiScaler ditetapkan kepada model INT8 FSR 4.
- "Buang muat turun" memadamnya; permainan mengekalkan salinan sendiri.

### 5. Apa yang berubah dalam OptiScaler.ini

Hanya baris yang diperlukan, dalam bahagian masing-masing; semua baris dan komen lain dikekalkan:

| Kunci | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`, `VulkanUpscaler` | `fsr31_12` (melalui Direct3D 12) | `fsr31` (asli) |
| `UpscalerIndex` | `0` (FSR 4) | `1` (FSR 3.1.5) |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | `true` sebelum RDNA 4 | `auto` |
| `FfxDx12Path`, `FfxDx12SRPath`, `FfxDx12FGPath`, `FfxVkPath` | DLL dalam folder `ScalerAssistant` permainan | sama |

`OptiScaler.ini` yang sudah ada disandarkan dahulu dan dikembalikan semasa dibuang.

### 6. Tukar, kemas kini, baiki, buang

- **Tukar** daripada menu upscaler: pilihan semasa dibuang dahulu, kemudian yang baharu dipasang. Antara FSR 4.1 Exact, Lossy dan FSR 3 hanya DLL FSR dan `OptiScaler.ini` berubah.
- **Kemas kini**: permainan menunjukkan "↑ HelixSR … tersedia" apabila folder HelixSR anda ada binaan lebih baharu, atau "↑ Muat turun yang lebih baharu tersedia" apabila muat turun OptiScaler / FSR 4.1 yang lebih baharu (atau binaan FSR 4.1 lain) digunakan. "↑ Kemas kini semua" mengemas kini setiap permainan.
- **Baiki**: kemas kini permainan atau "Sahkan integriti fail permainan" boleh mengembalikan fail asal permainan. Permainan kemudian menunjukkan apa yang berlaku dan "Baiki" meletakkan upscaler semula, menyimpan fail baharu permainan sebagai sandaran.
- **Buang** mengembalikan setiap fail yang diganti atau dipindahkan, dan mengeluarkan entri pilihan pelancaran.

### 7. Tetapan HelixSR tanpa menyunting fail

Untuk DLSS 3.7, "⚙ Tetapan" menyunting `helixsr.ini` permainan dengan borang (penajaman, rangkaian int8, langkah akhir dalam Ultra Performance, saiz wave). "Lalai" meninggalkan baris itu; baris dan komen lain dikekalkan.

### 8. Status langsung dan paparan tindih

- Permainan Steam yang berjalan disemak setiap 3 saat: `/proc/<pid>/maps` menunjukkan sama ada permainan **benar-benar memuatkan** HelixSR atau DLL FSR (dan OptiScaler atau pemuat DLSS). Tiada apa dimuatkan sehingga permainan menggunakan upscaler, jadi "belum dimuatkan" memberitahu apa yang perlu dipilih dalam permainan.
- Untuk HelixSR, `helixsr.log` larian semasa menunjukkan saiz wave dan ralat; pada RDNA 3 dan lebih baharu dengan cara OptiScaler, "Tetapkan WaveSize = 64" ditawarkan apabila log melaporkan wave32.
- Panel butiran permainan (butang ⌄ pada kadnya) ada "Lihat …log" untuk `helixsr.log` atau `OptiScaler.log`, folder permainan, nama fail OptiScaler dan, untuk DLSS 3.7, "⚙ Tetapan".
- Apabila permainan bermula, kad kecil di sudut kanan bawah menunjukkan keputusan kira-kira 10 saat (atau petunjuk selepas 90 saat). Ia tetingkap X11 berasingan yang tidak pernah mengambil fokus; matikan dengan suis pada bar alat.

### 9. Lancar, cari, tapis, bahasa

- "▶ Lancar" memulakan permainan melalui Steam. Cari mengikut nama (sebarang bahasa) atau App ID; penapis: permainan yang boleh di-upscale, upscaler dipasang, belum ada upscaler, perlu dikemas kini atau dibaiki, sedang berjalan, semua permainan.
- 12 bahasa antara muka: 台灣正體中文, 简体中文, English, 日本語, Deutsch, Français, Español, Italiano, ไทย, Tiếng Việt, Bahasa Melayu, हिन्दी.

### 10. Direka untuk selamat

- Tiada apa berubah semasa permainan berjalan; muat turun dan folder HelixSR disemak sebelum sebarang fail disentuh.
- Setiap fail yang diganti disimpan, setiap salinan disemak bait demi bait, dan pilihan pelancaran hanya berubah dengan satu entri yang diterangkan di atas.
- Cara DLSS, FSR 4.1 Lossy dan permainan dengan anti-tipu bertanya dahulu. Jangan sekali-kali gunakan upscaler yang diubah dalam permainan dalam talian: anti-tipu boleh menganggapnya gangguan.

### 11. Rupa

- Mengikut gaya "Liquid Glass" MAKO Assistant: satu kad bagi setiap permainan dengan kulit Steam, cip status, apa yang ditawarkan permainan dan, semasa berjalan, apa yang benar-benar dimuatkan. Butang ⌄ membuka butiran (API grafik, penskala, folder `.exe`, nama OptiScaler, pilihan pelancaran) dan tindakan yang jarang digunakan.
- Butang ialah kristal jernih yang timbul: warna lembut dengan sempadan halus, kilauan melengkung di separuh atas, sinaran di sepanjang tepi bawah dan bayang lembut di bawahnya — semuanya lapisan lut sinar rata, tanpa kecerunan. Tombol suis timbul dengan cara yang sama; tema yang dipilih ialah kristal timbul dalam landasan yang tenggelam. Hijau kebiruan memasang, biru menukar, ambar mengemas kini, merah membuang.
- Tema gelap, cerah atau automatik (ikut desktop). Log aktiviti ialah laci di bahagian bawah tetingkap.

## HelixSR 2.0 dan GPU

- **Muat turun dan bina HelixSR dalam satu langkah**: "Muat turun dan bina HelixSR" (dalam tetingkap HelixSR dan dalam plugin Steam Deck) memuat turun HelixSR terbaharu (2.0 atau lebih baharu) daripada keluaran GitHubnya, disemak dengan SHA-256, ke `~/.local/share/scaler-assistant/helixsr`, dan membinanya pada PC ini dengan program binaan HelixSR sendiri (`setup/helixsr_setup.py`, dijalankan seadanya) — seperti apl HelixSR sendiri, jadi tiada terminal dan tiada langkah permainan. Ia menyediakan apa yang diperlukan binaan: Python dengan numpy (Python 3.14 mudah alih apabila Python sistem tidak dapat membuka pakej zstd NVIDIA, jadi penjanaan bingkai tidak memerlukan `zstd` tambahan) dan DirectX Shader Compiler Microsoft, dijalankan melalui Proton Steam atau Wine. Fail NVIDIA dimuat turun hanya selepas anda bersetuju dalam apl; hasil binaan kekal pada PC anda. Dalam Flatpak binaan berjalan pada hos. Menjalankannya semula hanya membina yang belum ada; keluaran yang lebih baharu menggantikan yang dimuat turun sebelum itu. Anda juga boleh memilih keluaran yang lebih lama (2.0 atau lebih baharu) dan menandakan bahagian pilihan yang boleh dibina oleh setupnya: **Preset K** (HelixSR 3.2.1 atau lebih baharu) dan **kernel Vulkan HLX DLSS** (HelixSR 3.3 atau lebih baharu, `--vulkan` setup: HLX DLSS kemudian berjalan secara asli dalam permainan Vulkan dan bukan melalui jambatan DirectX 12 HelixSR Scaler). Kedua-duanya tidak ditanda secara lalai dan memanjangkan binaan dengan banyak; apa yang dibuat oleh binaan terdahulu kekal (rangkaian tanpa kernel Vulkan dibina semula apabila ia ditanda).
- **HelixSR 2.0 dan lebih baharu** menyimpan DLL yang dibina dalam `HelixSR-fsrfg` dan menawarkan dua cara: **HelixSR Scaler** (binaan OptiScaler HelixSR sendiri di sebelah `.exe`: pilih DLSS dalam permainan; juga permainan DX11 dan Vulkan) dan **cara FSR** (FSR drop-in). Pembantu Scaler memasang kedua-duanya melalui pemasang dalam folder HelixSR anda (`setup/helixsr_bridge.py`, yang digunakan aplikasi HelixSR sendiri), jadi setup HelixSR, aplikasinya dan Pembantu Scaler mengenali, mengemas kini dan membuang pemasangan satu sama lain. Nama fail masih dipilih oleh Pembantu Scaler, dan ia menambah pilihan pelancaran apabila perlu. Permainan yang disediakan dengan cara lama beralih ke HelixSR Scaler semasa dikemas kini. Folder HelixSR 1.8 / 1.9 mengekalkan tiga caranya.
- **Penjanaan bingkai HelixSR** (HelixSR 2.0): dalam permainan DirectX 12 yang ada DLSS Frame Generation (`sl.dlss_g.dll` Streamline), permainan dengan HelixSR Scaler mendapat suis "Penjanaan bingkai HelixSR" pada kadnya (dan dalam plugin Steam Deck). Ia menggunakan pemasang HelixSR sendiri (`scaler-fg`), yang hanya menukar pilihan `[FrameGen]` dalam OptiScaler.ini; kemudian hidupkan DLSS Frame Generation dalam permainan. Ia memerlukan penjanaan bingkai yang dibina oleh `./helixsr-setup.sh` (ia memuat turun fail DLSS Frame Generation NVIDIA); sebelum itu suis dikelabukan bersama sebabnya. Pemasangan baharu membiarkannya mati; kemas kini atau nama fail OptiScaler baharu mengekalkan keadaannya. Permainan DX12 lain masih boleh memilih penjanaan bingkai AMD FSR atau XeSS dalam menu HelixSR Scaler (Insert); permainan DX11 / Vulkan dan cara FSR hanya mendapat peningkatan skala.
- **HelixSR 3.0**: DLL yang dibina ialah `HelixSR/helixsr.dll` (penskala DLSS HelixSR Scaler, "HLX DLSS"), dan cara FSR memasang **HLX FSR 4**, saluran FSR 4 HelixSR sendiri, yang dibina oleh setup HelixSR daripada fail pemacu FSR 4 AMD (ia memuat turun kira-kira 420 MB pakej pemacu AMD daripada AMD; "Muat turun dan bina HelixSR" bertanya dahulu dan turut menyediakan pengkompil shader kedua, DXC 1.9.2609). Pembantu Scaler memasang, mengemas kini, menukar dan membuang kedua-dua cara melalui pemasang dalam keluaran seperti dengan 2.0; permainan yang disediakan dengan 2.0 berpindah dari `HelixSR-fsrfg` ke `HelixSR` semasa kemas kini. HelixSR 3.0 tiada penjanaan bingkai, jadi suis di atas tidak dipaparkan dengannya; penjanaan bingkai AMD FSR dan XeSS kekal dalam menu HelixSR Scaler. Mulai HelixSR 3.2, HLX FSR 4 sudah siap dibina dalam ZIP (daripada FSR 4.1.2 FSR SDK 2.4.0 AMD): setup tidak lagi memuat turun pakej pemacu AMD, dan FSR AMD sendiri di sebelahnya dalam HelixSR Scaler ialah FSR 4.1.2. HelixSR 3.2.1 menambah **Preset K** pilihan untuk HLX DLSS, yang hanya dibina oleh setup HelixSR sendiri (`--preset-k`; "Muat turun dan bina HelixSR" tidak membinanya): apabila sudah dibina, ia dipasang ke dalam permainan bersama HelixSR Scaler (`HelixSR/k`) dan dibuang bersamanya, termasuk lognya. HelixSR 3.3 (HelixSR Scaler 2.3.0) mengekalkan susun atur ini: HelixSR Scaler kini turut menyenaraikan HLX FSR 4 dalam permainan Vulkan. Versi 3.3 membawa HLX FSR 4 yang sudah dibina tanpa pembinanya, jadi "Muat turun dan bina HelixSR" tidak lagi memuat turun DXC 1.9.2609 untuknya.
- **Penskala HelixSR Scaler** (HelixSR 3.0 atau lebih baharu): DLSS 3.7 (HelixSR) ▸ HelixSR Scaler menawarkan **HLX DLSS** — Preset E (Model E, lalai) atau Preset K (selepas Preset K dibina) — dan **HLX FSR 4** — FSR 4 (AMD FSR 4 Lite) atau FSR 4 Full (AMD FSR 4; HelixSR 3.2.1 atau lebih baharu, permainan DirectX 12, AMD BC-250 / RX 5000 / RX 6000 / RX 7000 / Steam Deck sahaja). Pembantu Scaler menulis pilihan ke `OptiScaler.ini` permainan, kunci yang sama dengan menu HelixSR Scaler sendiri (Insert); menukar tidak perlu pasang semula dan kemas kini mengekalkannya. Isu diketahui HelixSR dipaparkan terus di bawah setiap pilihan (Preset K: permainan boleh beku semasa bermula dengan tindanan Steam; FSR 4 Full: bayang dengan DeepReuse 1:2 / 1:4).
- **Permainan dengan FSR 3.0 sahaja** (`ffx_fsr3upscaler_x64.dll`, sebelum DLL FSR 3.1 FidelityFX): tiada DLL yang boleh diganti oleh FSR drop-in HelixSR, tetapi HelixSR Scaler dan OptiScaler mengambil alih FSR 3.0, jadi permainan ini turut mendapat HelixSR Scaler (HLX DLSS / HLX FSR 4) dan FSR 4.1 / FSR 3; pilih FSR dalam permainan. FSR 3.0 yang terbina dalam `.exe` permainan tidak boleh diambil alih.
- **Versi HelixSR terdahulu**: 1.8.x menawarkan ketiga-tiga cara (cara FSR, cara OptiScaler, cara DLSS). HelixSR 1.9.0 – 1.9.3 hanya membawa fail cara FSR, jadi cara OptiScaler dan DLSS dikelabukan ("perlu HelixSR 1.8 atau 2.0"); permainan tanpa FSR 3.1 memerlukan HelixSR 2.0 (HelixSR Scaler). Versi sebelum 1.8.0 tidak disokong.
- **Cara DLSS hanya dengan GeForce**: dengan GPU AMD atau Intel, permainan tidak menawarkan DLSS, jadi cara DLSS (HelixSR 1.x) dikelabukan bersama sebabnya.
- **FSR 4.1.2 Lite Lossy disyorkan** untuk grafik bersepadu (Steam Deck, ROG Ally Z1 / Z2, Ryzen AI MAX) dan GPU Intel: ditanda "★ Disyorkan" hanya dalam pilihan FSR 4.1.

## Berfungsi bersama persediaan HelixSR sendiri

Untuk DLSS 3.7, Pembantu Scaler menulis rekod pemasangan (`helixsr-install.json`), sandaran dan nama fail yang sama seperti persediaan HelixSR, jadi `helixsr-setup.sh` / `helixsr-uninstall.sh` dan Pembantu Scaler mengenali permainan masing-masing. Persediaan HelixSR menganggap DLL FSR dalam folder `ScalerAssistant` permainan sebagai DLL FSR 3.1 permainan dan mungkin menggantinya dengan HelixSR; Pembantu Scaler kemudian melaporkan permainan perlu dibaiki dan "Baiki" mengeluarkan HelixSR. Untuk menggunakan DLSS 3.7 dalam permainan sedemikian, pilihnya dalam Pembantu Scaler.

## Pemalam Steam Deck (Decky Loader)

Program yang sama untuk Mod Permainan, sebagai pemalam [Decky Loader](https://decky.xyz) dalam menu Akses Pantas.

- **Permainan**: permainan yang boleh diskala, yang sedang berjalan dahulu, setiap satu dengan cip status dan, semasa berjalan, apa yang benar-benar dimuatkan. Pilih permainan untuk memilih DLSS 3.7 (HelixSR, setiap cara), FSR 4.1 Exact / Lossy atau FSR 3, atau untuk mengemas kini, membaiki, membuang, menukar nama fail OptiScaler atau membaca lognya. Soalan yang sama seperti aplikasi desktop ditanya dahulu: muat turun, amaran Lossy, cara DLSS dan anti-tipu.
- **Persediaan**: folder HelixSR (pemilih fail), muat turun dan binaan FSR 4.1 (Steam Deck mendapat binaan grafik bersepadu), pemberitahuan apabila permainan bermula (sama ada penskala dimuatkan) dan bahasa (lalai sama seperti Steam).
- Ia berkongsi `state.json`, muat turun dan rekod pilihan pelancaran dengan aplikasi desktop: permainan yang disediakan dalam satu muncul dalam yang lain. Pilihan pelancaran ditulis serta-merta melalui Steam.
- Tiada dalam pemalam: borang tetapan HelixSR (guna aplikasi desktop) dan `helixsr-setup.sh` HelixSR sendiri, yang dijalankan sekali dalam Mod Desktop.
- Dalam plugin, **Muat turun dan bina HelixSR** memuat turun dan membina HelixSR 2.0 atau lebih baharu dalam Mod Permainan juga (mengambil beberapa minit).

Pasang: pasang Decky Loader pada Steam Deck, muat turun `Scaler_Assistant-Decky-<versi>.zip` dari halaman [Releases](https://github.com/mosesmoon/scaler-assistant/releases), kemudian dalam tetapan Decky → Developer (hidupkan mod pembangun dalam General dahulu) → "Install Plugin from ZIP File".

## Memasang Pembantu Scaler

**AppImage (disyorkan)**: Python, Qt dan 7-Zip sudah disertakan.

1. Muat turun `Scaler_Assistant-<versi>-x86_64.AppImage` dari halaman [Releases](https://github.com/mosesmoon/scaler-assistant/releases).
2. Jadikan boleh laku: klik kanan → Properties → Permissions → "Allow executing file as program" (perkataan berbeza mengikut pengurus fail).
3. Klik dua kali.

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

Jika ia tidak bermula, sistem anda mungkin tiada FUSE; jalankan dengan `--appimage-extract-and-run`.

**Pemasang tunggal (.bin)**: `Scaler_Assistant-<versi>-x86_64.bin` memasang aplikasi berpakej yang sama untuk pengguna anda sahaja (tanpa root, tanpa FUSE) ke `~/.local/opt/scaler-assistant`, dengan arahan `scaler-assistant` dan entri menu. **Flatpak**: `Scaler_Assistant-<versi>-x86_64.flatpak` ialah pakej satu fail pada runtime Freedesktop 25.08 (dimuat turun dari Flathub semasa pemasangan). Ia boleh membaca folder home dan pemacu lain (kad SD di bawah `/run/media`) dan melihat proses Steam serta permainan melalui `flatpak-spawn --host`.

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / pasang
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / buang
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**Daripada kod sumber**: Python 3.11+ dan PyQt6 (Arch: `sudo pacman -S python-pyqt6`), serta 7-Zip atau bsdtar untuk mengekstrak OptiScaler (`sudo pacman -S 7zip`).

```bash
./scaler-assistant     # jalankan terus
./install.sh           # pasang ke ~/.local/share/scaler-assistant dan tambah entri menu
```

## Had yang diketahui

- **Permainan Steam sahaja.** Cara FSR 4.1 / FSR 3 telah disemak fail demi fail dengan OptiScaler 0.9.4; setiap permainan berkelakuan berbeza: jika ada masalah, semak senarai keserasian OptiScaler atau pilih nama fail lain untuk OptiScaler.
- FSR 4.1 dalam permainan Direct3D 11 dan Vulkan berjalan melalui laluan Direct3D 12 OptiScaler dan kurang diuji.
- HelixSR berubah dengan pantas. Pembantu Scaler memerlukan HelixSR 1.8.0 atau lebih baharu dan mengikut susun atur 1.8.x / 1.9.x / 2.0.x / 3.0.x / 3.1.x / 3.2.x / 3.3.x.
- Paparan tindih tidak muncul dalam Mod Permainan Steam Deck (gamescope). Pemalam Decky memaparkan pemberitahuan Steam sebagai ganti.
- Dalam bahasa Thai, Vietnam, Melayu dan Hindi, menu klik kanan dalam bahasa Inggeris (Qt tiada terjemahan rasmi). Steam tiada nama permainan dalam bahasa Melayu atau Hindi.

## Lokasi data disimpan

| Lokasi | Kandungan |
|---|---|
| `~/.config/scaler-assistant/state.json` | Keadaan Pembantu Scaler: folder HelixSR, senarai permainan, bahasa, binaan FSR 4.1, nama OptiScaler yang anda pilih, entri yang ditambahnya pada pilihan pelancaran (diambil alih sekali daripada Pembantu HelixSR) |
| `~/.local/share/scaler-assistant/components/` | Fail OptiScaler dan FSR 4.1 yang dimuat turun |
| `~/homebrew/plugins/scaler-assistant/` | Pemalam Decky pada Steam Deck (guna keadaan dan muat turun yang sama seperti di atas) |
| `<permainan>/…/ScalerAssistant/` | FSR 4.1 / FSR 3: DLL FidelityFX, `scaler-install.json`, `backup/` |
| `<permainan>/…/HelixSR/helixsr-install.json`, di sebelah DLL FSR permainan | DLSS 3.7: rekod pemasangan HelixSR (dikongsi dengan persediaan HelixSR) |
| `<permainan>/…/helixsr.ini`, `helixsr.log`, `OptiScaler.ini`, `OptiScaler.log` | Tetapan dan log |

## Lesen

Pembantu Scaler ialah alat bebas dan tidak rasmi, tidak bergabung dengan atau disokong oleh pembuat HelixSR, NVIDIA, AMD, projek OptiScaler atau projek fsr4-shader-performance-overrides, dan tidak mengandungi sebarang fail mereka. Apabila anda minta, ia memuat turun OptiScaler (GPL-3.0; fakenvapi MIT; DLL FidelityFX AMD di bawah lesen AMD) dan DLL FSR 4.1 (GPL-2.0-or-later, DLL AMD yang diubah suai dengan notis AMD) daripada GitHub Releases mereka. AppImage termasuk `7zzs` 7-Zip (GNU LGPL dengan sekatan unRAR, BSD; lesen disertakan). HelixSR percuma di bawah HelixSR Freeware License; selepas persediaannya, DLL HelixSR mengandungi rangkaian NVIDIA, jadi Pembantu Scaler hanya menyalinnya antara folder pada PC anda sendiri. Jangan sekali-kali kongsi atau muat naik. Pemalam Decky mengandungi `7zzs` yang sama.
