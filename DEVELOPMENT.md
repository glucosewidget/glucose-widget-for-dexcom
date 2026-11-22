# 開発者向けメモ（GlucoseWidget for Dexcom）

利用者向けの説明は [README.md](README.md) を参照してください。

## ソースから動かす
Python 3.10 以上（python.org 版）が必要です。

```bat
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python glucose_widget.py --demo
```

`--demo` を付けると、Dexcom にログインせずに架空のデータで動きます。

## exe のビルド
- **GitHub Actions**：main へのプッシュ・プルリクエスト・手動実行で、[.github/workflows/build.yml](.github/workflows/build.yml) が Windows 上で `GlucoseWidgetForDexcom.exe` を作り、Actions の「Artifacts」に置きます。
  main へのプッシュとプルリクエストでは、アプリのソース（`glucose_widget.py`・`glucosewidget/`・`requirements.txt`・`version_info.txt`・`icon.ico`）かワークフローが変わったときだけビルドします（README などだけの変更ではビルドしません）。
- **手元で作る**：`build_exe.bat` をダブルクリックすると、同じフォルダに `GlucoseWidgetForDexcom.exe` ができます。`build_exe.bat` は cmd で文字化けしないよう Shift-JIS・CRLF で保存しています（`.gitattributes` で改行を変換しない設定）。

どちらも同じ PyInstaller の指定です（`--onefile --noconsole`、`version_info.txt`、`icon.ico` の同梱、`pystray._win32` と `keyring.backends` の取り込み）。

## ベータ版・リリースの作り方

### Actions の画面から手動で作る（ベータ版向け）
1. GitHub の「Actions」→「Build exe」→「Run workflow」を開きます。
2. 「版数」に `0.1.0-beta` のように入れます（形式は `数字.数字.数字` か、その後ろに `-beta` など）。
3. Releases にも載せたいときは「Releases にプレリリースとして公開する」をオンにします。
4. 「Run workflow」を押します。

- 入れた版数が exe のプロパティ（ファイル バージョン・製品バージョン）に書き込まれます（リポジトリの `version_info.txt` は変わりません）。
- 公開しない場合は、その実行の「Artifacts」に `GlucoseWidgetForDexcom-<版数>` として置かれます。
- 公開する場合は、`v<版数>` のタグが付き、Releases に exe と `.sha256` が添付されます。版数に `-` を含むとプレリリースになります。

### タグで作る
1. `version_info.txt` の版数を上げてコミットします（タグで作るときはタグの版数が exe に書き込まれるので、合わせておくと分かりやすくなります）。
2. `v0.1.0` のような `v` で始まるタグを付けてプッシュします。`v0.1.0-beta` のように `-` を含むタグはプレリリースになります。
3. GitHub Actions が exe と `.sha256` を作り、Releases に添付します。

利用者は、`.sha256` と PowerShell の `Get-FileHash .\GlucoseWidgetForDexcom.exe -Algorithm SHA256` の結果を比べて、ファイルが壊れていないか確認できます。

## ファイル構成
| ファイル | 内容 |
|---|---|
| `glucose_widget.py` | 起動（二重起動防止・高DPI）。exe のビルドもこのファイルから |
| `glucosewidget/constants.py` | アプリ名・設定フォルダ・色・サイズ・取得間隔などの定数 |
| `glucosewidget/i18n.py` | 日本語 / 英語の文言、言語の判定 |
| `glucosewidget/config.py` | 設定ファイルの読み書き、パスワード（資格情報マネージャー） |
| `glucosewidget/fetcher.py` | Dexcom Share からの取得（別スレッド）、デモデータ |
| `glucosewidget/sound.py` | アラート音、音量ミキサー連動 |
| `glucosewidget/notify.py` | トースト通知 |
| `glucosewidget/startup.py` | Windows 起動時の自動起動 |
| `glucosewidget/tray.py` | タスクトレイ |
| `glucosewidget/graph.py` | 推移グラフ |
| `glucosewidget/settings_dialog.py` | 設定画面 |
| `glucosewidget/widget.py` | 本体ウィンドウ（表示・メニュー・アラート判定） |
| `version_info.txt` | exe のファイル情報（説明 GlucoseWidget for Dexcom、製品名 GlucoseWidget） |
| `build_exe.bat` | 手元で exe を作るバッチ |
| `.github/workflows/build.yml` | GitHub Actions のビルド設定 |
