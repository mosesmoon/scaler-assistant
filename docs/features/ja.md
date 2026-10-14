# HelixSR アシスタント — 機能ガイド

[English](en.md) · [台灣正體中文](zh_TW.md) · [简体中文](zh_CN.md) · **日本語** · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [ไทย](th.md) · [Tiếng Việt](vi.md) · [Bahasa Melayu](ms.md) · [हिन्दी](hi.md)

**HelixSR アシスタント**は、Steam ゲームへの **[HelixSR](https://github.com/lonewolf0622/HelixSR)** の導入・切り替え・更新・削除をワンクリックで行い、プレイ中に HelixSR が実際に動いているかを表示する Linux デスクトップツールです。

HelixSR は、NVIDIA の DLSS Model E アップスケーリングネットワークを、Proton 経由で AMD GPU（RDNA 1 以降）上の通常の Direct3D 12 コンピュートシェーダーとして動かします。

## 想定する利用者

HelixSR には起動オプションも共通の設定ファイルもありません。ゲームごとに 3 つの方式のいずれかで、DLL をゲームのフォルダーに置く仕組みです。手作業で導入するには次の作業が必要です。

1. 各ゲームがどのアップスケーラー（FSR 3.1、DLSS、XeSS、FSR 2）を持ち、メインの `.exe` がどこにあるかを調べる。
2. ゲームに合った方式を選び、ゲーム本来のファイルを名前を変えて残し、HelixSR のファイルを正しい場所へコピーする。
3. OptiScaler 方式では、`OptiScaler.ini` に正しいパスを書く。
4. HelixSR を更新するたび、またゲームのアップデートで HelixSR が上書きされるたびに、すべてやり直す。
5. HelixSR が本当に動いているかは `helixsr.log` を開いて確かめる。

HelixSR アシスタントはこれらを 1 つのウィンドウで行います。HelixSR 本体の setup はターミナルでゲームを 1 本ずつ質問しますが、HelixSR アシスタントはクリックできる一覧で表示します。

## はじめる前に

> ⚠ **HelixSR アシスタントには HelixSR は含まれておらず、代わりにダウンロードすることもありません。** ご自身で準備した HelixSR フォルダーからファイルをコピーするだけです。

1. **HelixSR をダウンロード**（1.8.0 以降）：[GitHub Releases](https://github.com/lonewolf0622/HelixSR/releases) から入手し、ホームフォルダーなど残しておくフォルダーに展開します。
2. **そのフォルダーで `./helixsr-setup.sh` を一度実行**します。NVIDIA の DLSS DLL のダウンロードを確認し、それから HelixSR のネットワークを構築します（約 1 分）。ゲームごとの質問が始まったら、すべて `n` と答えるかウィンドウを閉じてかまいません。ゲームへの導入は HelixSR アシスタントが行います。フォルダーは見つかったが準備がまだの場合は、「ターミナルで setup を実行」ボタンが表示されます。
3. **AMD GPU（RDNA 1 以降）**（Radeon RX 5000 以降、Steam Deck、RDNA 内蔵の Ryzen）。Radeon Vega は HelixSR 1.9.0 で実験的対応です。
4. **Proton で動作し、FSR 3.1・DLSS・XeSS・FSR 2 のいずれかを持つ Direct3D 12 ゲーム**。

初回起動時、HelixSR アシスタントはホーム、ダウンロード、デスクトップ、Games フォルダーから準備済みの HelixSR フォルダーを探します。「HelixSR フォルダーを選択…」または上部の HelixSR 表示をクリックすれば、いつでも別のフォルダーを選べます。

## HelixSR をゲームに入れる 3 つの方式

HelixSR 本体の 3 つの方式です（英字は HelixSR の setup で使う回答）。HelixSR アシスタントは各ゲームで使える方式だけを、既定の方式を先頭にして表示します。

| 方式 | ゲームに必要なもの | ゲームフォルダーで変わる内容 | ゲーム内で選ぶもの |
|---|---|---|---|
| **FSR 方式**（f、FSR 3.1 のゲームでは既定） | FSR 3.1 | ゲームの `amd_fidelityfx_upscaler_dx12.dll`（または `amd_fidelityfx_dx12.dll`）を HelixSR に置き換え、ゲームのファイルは `*.original.dll` として保存 | **AMD FSR** |
| **OptiScaler 方式**（o） | DLSS、XeSS、FSR 2 | ゲームの `.exe` の隣に OptiScaler（HelixSR フォルダー内の公式版）を置き、その FSR 3.1 バックエンドを隣の `HelixSR` フォルダーに向ける。置き換えたファイルはすべて `HelixSR/backup` へ | **DLSS**（FSR や XeSS でも可） |
| **DLSS 方式**（d、実験的） | DLSS | ゲームの `.exe` の隣に HelixSR の DLSS ローダー（`dxgi.dll`）と、`nvngx.dll` という名前の HelixSR を置く | **DLSS** |

## 機能

### 1. Steam ゲームとそのアップスケーラーをスキャン

- 初回起動時にすべての Steam ライブラリ（別ドライブのライブラリも含む）をスキャンします。ゲームを追加したら「⟳ Steam ゲームを再スキャン」をクリックしてください。
- 各ゲームのフォルダーで FSR 3.1・DLSS・XeSS・FSR 2 の DLL を探し、Steam の起動情報からメインの `.exe` があるフォルダーを特定します（ランチャーや Unreal の `*-Shipping.exe` にも対応）。
- **アンチチート**（Easy Anti-Cheat、BattlEye）のあるゲームには印が付きます。
- ゲーム名はインターフェース言語に合わせた Steam の現地語名で表示し、その言語の順序で並べます。HelixSR を使えるゲームが先頭に来て、「HelixSR を使えるゲーム」フィルターが既定で有効です。

### 2. ワンクリック導入

- 「HelixSR を導入」で既定の方式で導入し、横の矢印で別の方式を選べます。どの方式もゲーム内で何を選べばよいかを表示します。
- 変更を加える前に、HelixSR フォルダーの準備ができているか（ネットワーク構築済みか）と、ゲームが実行中でないかを確認します。
- DLSS 方式は、先にリスクを説明して確認を求めます。アンチチートのあるゲームでも確認を求めます。
- 完了すると、どのファイルを置き換えたか、ゲームのファイルをどこに残したか、ゲーム内で何を選ぶかをログに表示します。

### 3. 方式の切り替え・更新・修復

- **切り替え**：「その他」→「…に切り替え」で、まず今の方式を削除して（すべて元に戻して）から新しい方式を導入します。HelixSR の設定も引き継がれます。
- **更新**：HelixSR フォルダーのビルドがゲーム内より新しい場合（HelixSR の新バージョンやネットワークの再構築）、ゲームに「↑ HelixSR … があります」と「↑ 更新」ボタンが表示されます。「↑ すべて更新」で全ゲームを一度に更新できます。
- **修復**：ゲームのアップデートや Steam の「ゲームファイルの整合性を確認」で、ゲーム本来のファイルが HelixSR の上に戻ることがあります。その場合は何が起きたかと「修復」ボタンが表示され、HelixSR を元の場所に戻し、ゲームの新しいファイルをバックアップとして残します。
- ダウンロードフォルダーなどに新しい準備済みの HelixSR フォルダーが現れると、それに切り替えるかを一度だけ尋ねます。

### 4. 削除

- 「削除」は HelixSR を取り除き、置き換えたり移動したりしたファイルをすべて元どおりに戻します。
- ゲームの HelixSR 設定（`helixsr.ini`）は、「このゲームの HelixSR 設定も削除する」にチェックしない限り残ります。
- ゲームの `my-fsr` フォルダーにご自身で入れたファイルは決して削除しません。

### 5. ファイルを編集せずに HelixSR を設定

「⚙ 設定」で、ゲームの `helixsr.ini` をフォームで編集します。HelixSR の README に記載された設定だけを扱います。

| グループ | 設定 | 値 |
|---|---|---|
| シャープ化 | シャープ化方式 | 既定、オフ、NVIDIA、RCAS |
| | シャープネス | 0.00〜1.00 |
| | ゲームのシャープネススライダーに従う | 既定、はい、いいえ |
| アップスケーリング（HelixSR 1.9.0 以降） | int8 ネットワーク | 既定（自動）、自動、オン、オフ |
| | ウルトラパフォーマンスの最終パス | 既定（Lanczos）、Lanczos、EASU（FSR 1） |
| 互換性 | ウェーブサイズ | 既定、64、32 |

「既定」にするとその行は書かれず、HelixSR 自身の既定値が使われます。ファイル内のコメントやほかの行はそのまま残ります。ファイルは、そのゲームの方式での HelixSR の DLL の隣（ゲームの `HelixSR` フォルダー、ゲームの FSR DLL の隣、または `.exe` の隣）に書かれます。

### 6. HelixSR のリアルタイム状態（実際に動いているもの）

実行中の Steam ゲームを 3 秒ごとに確認します。

- Proton は Windows の DLL をファイルから読み込むため、`/proc/<pid>/maps` でゲームが**本当に HelixSR を読み込んだか**（および OptiScaler や DLSS ローダー）がわかります。
- HelixSR はゲームがアップスケーラーを使い始めてから読み込まれます。そのため「HelixSR はまだ読み込まれていません」は、ゲームのグラフィック設定で何を選ぶべきかを示します。
- 今回の実行の `helixsr.log` を読み、ネットワークカーネルのウェーブサイズとエラー行を表示します。「その他」→「helixsr.log を表示」でログ全体を表示・コピーできます。
- **RDNA 3 以降**の GPU で OptiScaler 方式のゲームでは、ログが wave32 なら HelixSR の README は `WaveSize = 64` を推奨しています。アシスタントはこれを検出し、ワンクリックの「WaveSize = 64 に設定」を表示します。
- 上部の GPU 表示に GPU の世代（例：「AMD RDNA 3 (gfx1100)」）が出ます。

### 7. ゲーム起動時のオーバーレイ

HelixSR を導入したゲームの起動時に HelixSR アシスタントが開いていれば、HelixSR が読み込まれた時点で右下に約 10 秒間、バージョン・方式・ウェーブサイズを示す小さなカードを表示します（起動ごとに 1 回。アシスタントを開く前から動いていたゲームは対象外）。90 秒たっても HelixSR が読み込まれない場合は、ゲーム内で何を選ぶかを表示します。オーバーレイは独立した X11（XWayland）ウィンドウで、フォーカスを奪わず、マウスのクリックも通します。ツールバーのチェックボックスでオフにできます。Steam Deck のゲームモード（gamescope）では表示されません。

### 8. ゲームの起動・検索・フィルター

- 各行に「▶ 起動」ボタンがあります（`steam://rungameid/<AppID>` 経由）。ゲームの実行中は「実行中」と表示します。
- ゲーム名（どの言語でも）や App ID で検索できます。フィルター：HelixSR を使えるゲーム、導入済み、未導入、更新・修復が必要、実行中、すべてのゲーム。

### 9. 12 のインターフェース言語

台灣正體中文、简体中文、English、日本語、Deutsch、Français、Español、Italiano、ไทย、Tiếng Việt、Bahasa Melayu、हिन्दी。初回はシステムの言語を使い、右上で切り替えられます（すぐに反映され、記憶されます）。

### 10. 安全を重視した設計

- HelixSR フォルダーの準備ができていないときや、ゲームが実行中のときは何も変更しません。
- HelixSR が置き換えるファイルはすべて残し（`*.original.dll` または `HelixSR/backup`）、コピーしたファイルは 1 バイトずつ照合します。
- もともとあった `OptiScaler.ini` はバックアップし、削除時に戻します。ゲームの `HelixSR` フォルダーで手動で置き換えた FSR DLL は、更新時にも残します。
- DLSS 方式とアンチチートのあるゲームは、明示的な確認が必要です。

## HelixSR 本体の setup との連携

HelixSR アシスタントは、HelixSR の setup と同じ導入記録（`helixsr-install.json`）、バックアップ、ファイル名を使います。そのため、

- `helixsr-setup.sh` で導入したゲームは HelixSR アシスタントで導入済み（方式付き）と表示され、ここから切り替え・更新・削除できます。
- HelixSR アシスタントで導入したゲームは、HelixSR の setup と `helixsr-uninstall.sh` も認識し、更新や削除ができます。

## HelixSR アシスタントのインストール

**AppImage（推奨）**：Python と Qt を同梱しているので、ほかに何もインストールする必要はありません。

1. [Releases](https://github.com/mosesmoon/helixsr-assistant/releases) ページから `HelixSR_Assistant-<バージョン>-x86_64.AppImage` をダウンロードします。
2. 実行可能にします：ファイルを右クリック →「プロパティ」→「アクセス権」で「プログラムとして実行可能」をオンにします（表記はファイルマネージャーによって異なります）。
3. ダブルクリックで HelixSR アシスタントが開きます。

ターミナルの場合：

```bash
chmod +x HelixSR_Assistant-*-x86_64.AppImage
./HelixSR_Assistant-*-x86_64.AppImage
```

起動しない場合は FUSE がない可能性があります。`./HelixSR_Assistant-*-x86_64.AppImage --appimage-extract-and-run` で実行してください。

**ソースから**：Python 3.11 以降と PyQt6 が必要です（Arch：`sudo pacman -S python-pyqt6`）。

```bash
./helixsr-assistant    # 直接実行
./install.sh           # ~/.local/share/helixsr-assistant にインストールし、アプリメニューに追加
```

## 既知の制限

- **Steam ゲームのみ対応です。** ほかのストアのゲームには HelixSR 本体の setup を使ってください（ゲームのフォルダーをドラッグします）。
- HelixSR 自体は Direct3D 12 のゲームでのみ動作します。DLSS や FSR の DLL があるゲームでも Vulkan や Direct3D 11 の場合があり、そのときは HelixSR は何もしません。
- HelixSR は非常に速いペースで変わります。HelixSR アシスタントは HelixSR 1.8.0 以降が必要で、1.8.x・1.9.x の構成に合わせて作られています。今後の HelixSR で導入方法が変わった場合は、HelixSR アシスタントが更新されるまで HelixSR 本体の setup を使ってください。
- オーバーレイは Steam Deck のゲームモード（gamescope）では表示されず、ネイティブ Wayland の排他フルスクリーンのゲームでは隠れることがあります。
- タイ語・ベトナム語・マレー語・ヒンディー語では右クリックメニューが英語になります（Qt にこれらの言語の公式翻訳がないため）。Steam にはマレー語とヒンディー語のゲーム名がないため、この 2 言語では常に元の名前を表示します。

## データの保存場所

| 場所 | 内容 |
|---|---|
| `~/.config/helixsr-assistant/state.json` | HelixSR アシスタント自身の状態：HelixSR フォルダー、ゲーム一覧のキャッシュ、インターフェース言語、オーバーレイ設定 |
| `<ゲーム>/…/HelixSR/helixsr-install.json`、ゲームの FSR DLL の隣 | HelixSR の導入記録（HelixSR 本体の setup と共通） |
| `<ゲーム>/…/helixsr.ini` | そのゲームの HelixSR 設定 |
| `<ゲーム>/…/helixsr.log` | 前回ゲームを実行したときの HelixSR の報告 |

## ライセンス

HelixSR アシスタントは独立した非公式ツールで、HelixSR の作者、NVIDIA、AMD、OptiScaler プロジェクトとは無関係であり、承認も受けておらず、それらのファイルは一切含みません。HelixSR は HelixSR Freeware License のもとで無料で使えます。HelixSR の setup を実行した後の HelixSR の DLL には NVIDIA のネットワークが含まれます。HelixSR アシスタントはそれをご自身の PC 上のフォルダー間でコピーするだけです。共有やアップロードは絶対にしないでください。
