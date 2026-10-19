# Scaler アシスタント — 機能ガイド

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · **日本語** · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**Scaler アシスタント**は、Steam ゲームごとにアップスケーラーを選べる Linux デスクトップツールです。**DLSS 3.7（[HelixSR](https://github.com/lonewolf0622/HelixSR)）**、**FSR 4.1**（[fsr4-shader-performance-overrides](https://github.com/zgauthier2000/fsr4-shader-performance-overrides) の Exact または Lossy、RX 9000 では AMD 純正）、**FSR 3** をワンクリックで導入・切り替え・更新・修復・削除し、プレイ中にアップスケーラーが本当に動いているかも表示します。

## こんな人のために

Linux でゲームのアップスケーラーを手作業で入れ替えるには、次のことが必要です。

1. ゲームに入っているアップスケーラー（DLSS、XeSS、FSR 2、FSR 3.1）、グラフィックス API、メインの `.exe` の場所を調べる。
2. ゲームが受け付けるファイル名で OptiScaler を `.exe` の隣に置き、必要な FidelityFX DLL を添えて、使いたいアップスケーラーに合わせて `OptiScaler.ini` を編集する。
3. ファイル名によっては Steam の起動オプションに `WINEDLLOVERRIDES` を追加する（既存の内容を壊さずに）。
4. GPU に合った FSR 4.1 DLL をダウンロードするか、HelixSR の README のとおりに HelixSR を設定する。
5. 更新のたびに、またゲームの更新でファイルが上書きされるたびに、やり直す。

Scaler アシスタントはこれらをひとつのウィンドウで行い、置き換えたファイルはすべて保存して、削除時にはゲームを元どおりに戻します。

## ゲームごとの選択肢

選べるものはゲームのグラフィックス API とアップスケーラーで決まります。ゲームには少なくとも 1 つのアップスケーラー（DLSS、XeSS、FSR 2、FSR 3.1）が必要です。OptiScaler と HelixSR はそれを引き継ぎます。

| 選択肢 | ゲームに必要なもの | ゲームフォルダーに入るもの | ゲーム内で選ぶもの |
|---|---|---|---|
| **DLSS 3.7（HelixSR）· FSR 方式** | Direct3D 12、FSR 3.1 | ゲームの FSR 3.1 DLL を HelixSR に置き換え（元のファイルは `*.original.dll`） | AMD FSR |
| **DLSS 3.7（HelixSR）· OptiScaler 方式** | Direct3D 12、DLSS／XeSS／FSR 2 | `.exe` の隣に OptiScaler、`HelixSR` フォルダーを参照 | DLSS |
| **DLSS 3.7（HelixSR）· DLSS 方式**（実験的） | Direct3D 12、DLSS | HelixSR の DLSS ローダー（`dxgi.dll`）と `nvngx.dll` としての HelixSR | DLSS |
| **FSR 4.1 Exact** | 4 つのアップスケーラーのいずれか | `.exe` の隣に OptiScaler、`ScalerAssistant` フォルダーに FidelityFX DLL と Exact 版 FSR 4.1 DLL | DLSS・FSR・XeSS |
| **FSR 4.1 Lossy** | 同上 | 同上（Lossy 版 FSR 4.1 DLL） | DLSS・FSR・XeSS |
| **FSR 4.1（AMD）** — RX 9000（RDNA 4）では Exact／Lossy の代わり | 同上 | 同上（AMD 純正 FSR 4.1 DLL） | DLSS・FSR・XeSS |
| **FSR 3** | 同上 | 同上。OptiScaler は FSR 3.1.5 を使用 | DLSS・FSR・XeSS |

- **Exact** は AMD の FSR 4.1 と 1 バイト単位で同じ画を、より速いシェーダーで出します。**Lossy** はさらに速い代わりに画がわずかに変わります。初めて使う前に `WARNING.txt` を一度表示します。迷ったら Exact を選んでください。
- HelixSR は **Direct3D 12** のゲーム専用なので、DLSS 3.7 はそこでのみ表示されます。FSR 4.1 と FSR 3 は **Direct3D 11 と Vulkan** のゲームでも使えます（FSR 3 はネイティブ、FSR 4.1 は OptiScaler の Direct3D 12 経由で、Direct3D 12 のゲームほどは検証されていません）。
- ゲームの行の **「アップスケーラーを選ぶ」**（導入済みなら **「アップスケーラー」**）を押します。DLSS 3.7（HelixSR）はサブメニューで方式を選べ、現在の選択にはチェックが付きます。切り替え時は現在のものを先に削除してすべて元に戻します。

## はじめる前に

- **FSR 4.1 と FSR 3** には他に何もいりません。初めて選ぶと、OptiScaler と GPU に合った FSR 4.1 DLL のダウンロードを確認します（下の「ダウンロード」参照）。
- **DLSS 3.7** には HelixSR が必要ですが、Scaler アシスタントには含まれていません。[HelixSR の GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) から 1.8.0 以降をダウンロードして残しておくフォルダーに展開し、そこで `./helixsr-setup.sh` を一度実行してください（PC 上で HelixSR のネットワークを作ります。ゲームについて聞かれたら `n` で構いません）。上部の **HelixSR** ピルを押すと案内が出ます。ホーム、ダウンロード、デスクトップ、Games フォルダーにあるセットアップ済みの HelixSR は自動で見つけます。
- ゲームは **Proton** で動かします。HelixSR は AMD GPU（RDNA 1 以降）向けです。FSR 4.1 Exact／Lossy は Radeon RX 7000／RX 6000 と Radeon 内蔵グラフィックス（Steam Deck を含む）向けで、他の GPU でも動くはずですが作者は未検証です。

## 機能

### 1. Steam ゲームをスキャン

- 初回起動時にすべての Steam ライブラリ（他のドライブのものも）をスキャンします。ゲームを入れたら「⟳ Steam ゲームを再スキャン」を押してください。
- ゲームごとに、入っているアップスケーラー DLL、メインの `.exe` のフォルダー（Steam の起動情報から。ランチャーや Unreal の `*-Shipping.exe` にも対応）、**グラフィックス API**（`.exe` のインポート表から DX12・DX11・Vulkan を判定）、**アンチチート**（Easy Anti-Cheat、BattlEye）の有無を調べます。
- ゲーム名はインターフェース言語に合わせて表示されます（Steam のローカライズ名）。アップスケールできるゲームが先に並びます。

### 2. ゲームで動く OptiScaler のファイル名

ゲームは `.exe` の隣の OptiScaler をシステム DLL として読み込みます。名前は次の順で決めます。

1. そのゲームにあなたが選んだ名前（「その他」→「OptiScaler のファイル名…」）
2. すでにある OptiScaler の名前
3. [OptiScaler の互換性リスト](https://github.com/optiscaler/OptiScaler/wiki)がそのゲームに指定する名前（`d3d12.dll` や `winmm.dll` など）
4. Vulkan のゲームでは `winmm.dll`
5. ゲームや他の MOD（ReShade など）がすでに `dxgi.dll` を持つとき、または起動オプションでその名前が組み込み版に固定されているときは、空いている別の名前（`winmm.dll`、`version.dll` …）
6. それ以外は `dxgi.dll`

既存のファイルは上書きしません。`ScalerAssistant/backup`（DLSS 3.7 では `HelixSR/backup`）に移し、削除時に戻します。

### 3. Steam の起動オプション：必要なものだけ、あなたの内容はそのまま

Proton では `dxgi.dll` と `d3d12.dll` は追加設定なしで読み込まれます。それ以外の名前はゲームの起動オプションに `WINEDLLOVERRIDES="<名前>=n,b"` が必要で、Scaler アシスタントが追加します。

- **追加するのはその 1 項目だけ。** すでに `WINEDLLOVERRIDES` があればその値に `;winmm=n,b` を足し、なければ先頭に `WINEDLLOVERRIDES="winmm=n,b"` を置きます（`%command%` がなければ補います）。他の内容は変えません。例：`-dx12 %command%` → `WINEDLLOVERRIDES="winmm=n,b" -dx12 %command%`。
- **OptiScaler の削除や改名のときは、その 1 項目だけを取り除きます。** その間に起動オプションを変えていなければ元どおりに戻り、変えていれば追加した文字だけを取り除いてあなたの変更は残します。
- その名前の設定がもともとあれば手を付けず、あとで削除もしません。起動オプションでその名前が Wine の組み込み版に設定されているときは、設定を変えずに別の名前を使います。
- 後でその項目が消えると「起動オプションがありません」と表示され、「修復」で再び追加します。
- Steam の起動中は、デバッグポート（Decky Loader と同じもの）が使えれば Steam を通して変更します。使えなければ、Steam を閉じて書き込み、再び起動するかを確認します。これはゲームのファイルに触れる前に行います。

### 4. ダウンロード（FSR 4.1 と FSR 3）

上部の **OptiScaler** ピル（または GPU ピル）を押します。

- **OptiScaler 0.9.4**（AMD の FidelityFX DLL：FSR 3 と AMD の FSR 4.1、fakenvapi を含む）と、グラフィックスカード用または内蔵グラフィックス用の **FSR 4.1 Exact／Lossy**。
- 同意するまで何もダウンロードしません。各ダウンロードは固定のリリースで、展開前にサイズと SHA-256 を照合し、ゲームに必要なファイルだけを `~/.local/share/scaler-assistant/components/` に保存します。
- **FSR 4.1 のビルド**：GPU から自動選択（RX 9000／RDNA 4 → AMD 純正 FSR 4.1、内蔵グラフィックスと Steam Deck → 内蔵用、その他 → グラフィックスカード用）、または手動で選択。RDNA 4 では改変 DLL を使いません。それ以外の GPU では OptiScaler を FSR 4 の INT8 モデルに設定します。
- 「ダウンロードを削除」で削除できます。ゲーム内のコピーはそのままです。

### 5. OptiScaler.ini で変わるところ

選択に必要な行だけを、それぞれのセクションで変えます。他の行とコメントはそのままです。

| キー | FSR 4.1 | FSR 3 |
|---|---|---|
| `Dx12Upscaler` | `fsr31` | `fsr31` |
| `Dx11Upscaler`、`VulkanUpscaler` | `fsr31_12`（Direct3D 12 経由） | `fsr31`（ネイティブ） |
| `UpscalerIndex` | `0`（FSR 4） | `1`（FSR 3.1.5） |
| `Fsr4Update` | `true` | `false` |
| `Fsr4ForceEnableInt8` | RDNA 4 より前は `true` | `auto` |
| `FfxDx12Path`、`FfxDx12SRPath`、`FfxDx12FGPath`、`FfxVkPath` | ゲームの `ScalerAssistant` フォルダーの DLL | 同左 |

もともとあった `OptiScaler.ini` は先にバックアップし、削除時に戻します。

### 6. 切り替え・更新・修復・削除

- アップスケーラーのメニューから**切り替え**：現在のものを削除してから新しいものを入れます。FSR 4.1 Exact、Lossy、FSR 3 の間では FSR DLL と `OptiScaler.ini` だけが変わります。
- **更新**：HelixSR フォルダーに新しいビルドがあれば「↑ HelixSR … が利用可能」、OptiScaler／FSR 4.1 の新しいダウンロード（または別の FSR 4.1 ビルド）があれば「↑ 新しいダウンロードがあります」と表示します。「↑ すべて更新」で一括更新します。
- **修復**：ゲームの更新や Steam の「ゲームファイルの整合性を確認」で元のファイルが戻ることがあります。その場合は状況を表示し、「修復」でアップスケーラーを戻し、ゲームの新しいファイルはバックアップとして残します。
- **削除**は置き換え・移動したファイルをすべて戻し、起動オプションに追加した項目も取り除きます。

### 7. ファイルを編集せずに HelixSR の設定

DLSS 3.7 では「⚙ 設定」でゲームの `helixsr.ini`（シャープ化、int8 ネットワーク、ウルトラパフォーマンスの最終パス、ウェーブサイズ）をフォームで編集できます。「既定」はその行を書きません。他の行とコメントはそのままです。

### 8. ライブ状態とオーバーレイ

- 実行中の Steam ゲームを 3 秒ごとに確認し、`/proc/<pid>/maps` から HelixSR や FSR DLL（と OptiScaler や DLSS ローダー）が**本当に読み込まれたか**を表示します。ゲームがアップスケーラーを使うまでは読み込まれないため、「まだ読み込まれていません」はゲーム内で何を選ぶべきかを示します。
- HelixSR では今回の `helixsr.log` からウェーブサイズとエラーを表示し、RDNA 3 以降で OptiScaler 方式のときログが wave32 なら「WaveSize = 64 に設定」を提案します。
- ゲームのカードの ⌄ ボタンで開く詳細パネルに、「…log を表示」（`helixsr.log` または `OptiScaler.log`）、ゲームのフォルダー、OptiScaler のファイル名、DLSS 3.7 なら「⚙ 設定」があります。
- ゲーム起動時、右下に約 10 秒間カードで結果を表示します（90 秒たっても読み込まれなければヒント）。フォーカスを奪わない独立した X11 ウィンドウで、ツールバーのスイッチでオフにできます。

### 9. 起動・検索・フィルター・言語

- 「▶ 起動」で Steam からゲームを起動します。名前（どの言語でも）や App ID で検索でき、フィルターは「アップスケールできるゲーム」「アップスケーラー導入済み」「未導入」「更新・修復が必要」「実行中」「すべてのゲーム」です。
- 12 のインターフェース言語：台灣正體中文、简体中文、English、日本語、Deutsch、Français、Español、Italiano、ไทย、Tiếng Việt、Bahasa Melayu、हिन्दी。

### 10. 安全第一の設計

- ゲームの実行中は何も変えません。ファイルに触れる前にダウンロードと HelixSR フォルダーを確認します。
- 置き換えたファイルはすべて保存し、コピーは 1 バイト単位で検証し、起動オプションは上の 1 項目しか変えません。
- DLSS 方式、FSR 4.1 Lossy、アンチチートのあるゲームでは先に確認します。オンラインゲームで改変したアップスケーラーを使わないでください（改ざんとみなされることがあります）。

### 11. 見た目

- MAKO Assistant の「Liquid Glass」スタイル：ゲームごとに Steam のカバー、状態チップ、ゲームが対応する技術、実行中は実際に読み込まれたものを表示するカード。⌄ ボタンで詳細（グラフィックス API、アップスケーラー、`.exe` のフォルダー、OptiScaler の名前、起動オプション）とあまり使わない操作を開きます。
- ボタンはクリスタルのように透明：淡い色、細い枠線、明るい上端で、グラデーションはありません。ティールはインストール、青は切り替え、琥珀は更新、赤は削除です。
- ダーク、ライト、自動（デスクトップに合わせる）のテーマ。アクティビティログはウィンドウ下部の引き出しです。

## HelixSR 2.0 と GPU

- **HelixSR 2.0 以降**はビルド済み DLL を `HelixSR-fsrfg` に置き、2 つの方式があります：**HelixSR Scaler**（`.exe` の横に置く HelixSR 独自の OptiScaler。ゲームで DLSS を選択。DX11 と Vulkan のゲームにも対応）と **FSR 方式**（FSR ドロップイン）。Scaler アシスタントは HelixSR フォルダー内のインストーラー（`setup/helixsr_bridge.py`、HelixSR 公式アプリが使うもの）で両方をインストールするため、HelixSR のセットアップ、そのアプリ、Scaler アシスタントは互いのインストールを認識・更新・削除できます。ファイル名は引き続き Scaler アシスタントが選び、必要なら起動オプションも追加します。以前の方式で設定したゲームは更新時に HelixSR Scaler へ移ります。HelixSR 1.8／1.9 のフォルダーでは従来の 3 方式のままです。
- **HelixSR フレーム生成**（HelixSR 2.0）：DLSS Frame Generation（Streamline の `sl.dlss_g.dll`）を持つ DirectX 12 ゲームでは、HelixSR Scaler を入れるとカード（と Steam Deck プラグイン）に「HelixSR フレーム生成」スイッチが表示されます。HelixSR 自身のインストーラー（`scaler-fg`）で切り替え、OptiScaler.ini の `[FrameGen]` の選択だけを変更します。オンにしたらゲームで DLSS Frame Generation をオンにしてください。`./helixsr-setup.sh` が作成するフレーム生成（NVIDIA の DLSS Frame Generation ファイルをダウンロード）が必要で、それまではスイッチが理由付きでグレー表示になります。新規インストールではオフ、更新や OptiScaler のファイル名変更では状態を保ちます。ほかの DX12 ゲームでは HelixSR Scaler のメニュー（Insert）で AMD FSR や XeSS のフレーム生成を選べます。DX11／Vulkan ゲームと FSR 方式はアップスケールのみです。
- **以前の HelixSR**：1.8.x は 3 方式（FSR 方式、OptiScaler 方式、DLSS 方式）すべて使えます。HelixSR 1.9.0～1.9.3 は FSR 方式のファイルしか含まないため、OptiScaler 方式と DLSS 方式はグレー表示（「HelixSR 1.8 か 2.0 が必要」）。FSR 3.1 のないゲームには HelixSR 2.0（HelixSR Scaler）が必要です。1.8.0 より前は非対応です。
- **DLSS 方式は GeForce のみ**：AMD や Intel の GPU ではゲームで DLSS を選べないため、（HelixSR 1.x の）DLSS 方式は理由つきでグレー表示になります。
- **FSR 4.1 Lossy をおすすめ**：内蔵グラフィックス（Steam Deck、ROG Ally Z1／Z2、Ryzen AI MAX）と Intel GPU では、FSR 4.1 の選択肢の中だけで「★ おすすめ」と表示します。

## HelixSR 本体の setup との連携

DLSS 3.7 では、HelixSR の setup と同じインストール記録（`helixsr-install.json`）、バックアップ、ファイル名を使うので、`helixsr-setup.sh`／`helixsr-uninstall.sh` と Scaler アシスタントは互いのゲームを認識します。HelixSR の setup はゲームの `ScalerAssistant` フォルダーにある FSR DLL をゲーム自身の FSR 3.1 DLL とみなし、HelixSR に置き換えることがあります。その場合 Scaler アシスタントは修復が必要と表示し、「修復」で HelixSR を取り除きます。そのゲームで DLSS 3.7 を使うなら Scaler アシスタントで選んでください。

## Steam Deck プラグイン（Decky Loader）

同じプログラムをゲームモードでも使えます：クイックアクセスメニューの [Decky Loader](https://decky.xyz) プラグインです。

- **ゲーム**：アップスケールできるゲームを実行中のものから順に、状態チップと（実行中なら）実際に読み込まれたものとともに表示します。ゲームを選ぶと DLSS 3.7（HelixSR、各方式）、FSR 4.1 Exact／Lossy、FSR 3 の選択、更新・修復・削除、OptiScaler のファイル名の変更、ログの表示ができます。ダウンロード、Lossy の警告、DLSS 方式、アンチチートはデスクトップ版と同じく先に確認します。
- **設定**：HelixSR のフォルダー（ファイル選択）、ダウンロードと FSR 4.1 のビルド（Steam Deck は内蔵グラフィックス向け）、ゲーム起動時の通知（アップスケーラーが読み込まれたか）、言語（既定は Steam と同じ）。
- `state.json`、ダウンロード、起動オプションの記録をデスクトップ版と共有するので、どちらで設定したゲームも両方に表示されます。起動オプションは Steam 経由でその場で書き込みます。
- プラグインにないもの：HelixSR の設定フォーム（デスクトップ版を使用）と、デスクトップモードで一度実行する HelixSR の `helixsr-setup.sh`。

インストール：Steam Deck に Decky Loader を入れ、[Releases](https://github.com/mosesmoon/scaler-assistant/releases) から `Scaler_Assistant-Decky-<バージョン>.zip` をダウンロードし、Decky の設定 →「開発者」（先に「一般」で開発者モードをオン）→「Install Plugin from ZIP File」を選びます。

## Scaler アシスタントのインストール

**AppImage（推奨）**：Python、Qt、7-Zip を同梱しています。

1. [Releases](https://github.com/mosesmoon/scaler-assistant/releases) から `Scaler_Assistant-<バージョン>-x86_64.AppImage` をダウンロード。
2. 実行可能にする：右クリック →「プロパティ」→「アクセス権」→「プログラムとして実行可能」（表記はファイルマネージャーにより異なります）。
3. ダブルクリックで起動。

```bash
chmod +x Scaler_Assistant-*-x86_64.AppImage
./Scaler_Assistant-*-x86_64.AppImage
```

起動しない場合は FUSE がない可能性があります。`--appimage-extract-and-run` を付けて実行してください。

**単一インストーラー（.bin）**：`Scaler_Assistant-<バージョン>-x86_64.bin` は同じ同梱アプリを現在のユーザーだけに（root も FUSE も不要で）`~/.local/opt/scaler-assistant` へインストールし、`scaler-assistant` コマンドとメニュー項目を追加します。**Flatpak**：`Scaler_Assistant-<バージョン>-x86_64.flatpak` は Freedesktop 25.08 ランタイム（インストール時に Flathub から取得）を使う単一ファイルのバンドルです。ホームフォルダーと他のドライブ（`/run/media` の SD カード）を読み、`flatpak-spawn --host` で Steam とゲームのプロセスを確認します。

```bash
sh Scaler_Assistant-*-x86_64.bin                # install / インストール
sh Scaler_Assistant-*-x86_64.bin --uninstall    # remove / 削除
flatpak install --user Scaler_Assistant-*-x86_64.flatpak
flatpak run io.github.mosesmoon.ScalerAssistant
```

**ソースから**：Python 3.11 以降と PyQt6（Arch：`sudo pacman -S python-pyqt6`）、OptiScaler の展開用に 7-Zip か bsdtar（`sudo pacman -S 7zip`）。

```bash
./scaler-assistant     # そのまま実行
./install.sh           # ~/.local/share/scaler-assistant にインストールしメニューに追加
```

## 既知の制限

- **Steam のゲームのみ。** FSR 4.1／FSR 3 の導入方法は OptiScaler 0.9.4 でファイル単位に確認済みですが、ゲームごとに挙動は異なります。不具合があれば OptiScaler の互換性リストを確認するか、OptiScaler のファイル名を変えてください。
- Direct3D 11 と Vulkan のゲームでの FSR 4.1 は OptiScaler の Direct3D 12 経由で、検証が少なめです。
- HelixSR は変化が速いです。Scaler アシスタントは HelixSR 1.8.0 以降が必要で、1.8.x／1.9.x／2.0.x の構成に合わせています。
- Steam Deck のゲームモード（gamescope）ではオーバーレイは表示されません。Decky プラグインでは代わりに Steam の通知で表示します。
- タイ語、ベトナム語、マレー語、ヒンディー語の右クリックメニューは英語です（Qt の公式翻訳がないため）。Steam にはマレー語とヒンディー語のゲーム名がありません。

## データの保存場所

| 場所 | 内容 |
|---|---|
| `~/.config/scaler-assistant/state.json` | Scaler アシスタントの状態：HelixSR フォルダー、ゲーム一覧、言語、FSR 4.1 のビルド、選んだ OptiScaler の名前、起動オプションに追加した項目（初回に HelixSR アシスタントから引き継ぎ） |
| `~/.local/share/scaler-assistant/components/` | ダウンロードした OptiScaler と FSR 4.1 のファイル |
| `~/homebrew/plugins/scaler-assistant/` | Steam Deck の Decky プラグイン（上と同じ状態とダウンロードを使用） |
| `<ゲーム>/…/ScalerAssistant/` | FSR 4.1／FSR 3：FidelityFX DLL、`scaler-install.json`、`backup/` |
| `<ゲーム>/…/HelixSR/helixsr-install.json`、ゲームの FSR DLL の隣 | DLSS 3.7：HelixSR のインストール記録（HelixSR の setup と共通） |
| `<ゲーム>/…/helixsr.ini`、`helixsr.log`、`OptiScaler.ini`、`OptiScaler.log` | 設定とログ |

## ライセンス

Scaler アシスタントは独立した非公式ツールで、HelixSR の作者、NVIDIA、AMD、OptiScaler プロジェクト、fsr4-shader-performance-overrides プロジェクトとは無関係で承認も受けておらず、それらのファイルを一切含みません。同意したときに限り、OptiScaler（GPL-3.0、fakenvapi は MIT、AMD の FidelityFX DLL は AMD のライセンス）と FSR 4.1 DLL（GPL-2.0-or-later、AMD の告知付きの改変 AMD DLL）を各 GitHub Releases からダウンロードします。AppImage には 7-Zip の `7zzs`（unRAR 制限付き GNU LGPL、BSD、ライセンス同梱）が含まれます。HelixSR は HelixSR Freeware License のもとで無料で使えます。setup 後の HelixSR の DLL には NVIDIA のネットワークが含まれるため、Scaler アシスタントはあなたの PC 内のフォルダー間でのみコピーします。共有やアップロードはしないでください。Decky プラグインにも同じ `7zzs` が含まれます。
