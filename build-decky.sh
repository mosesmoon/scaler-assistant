#!/usr/bin/env bash
# Build Scaler_Assistant-Decky-<version>.zip, the Steam Deck plugin for Decky Loader.
#
# The zip holds the React panel (decky/src, built with @decky/rollup), the Python
# backend (decky/main.py) with the scaler_assistant package in py_modules (without
# the desktop window), and 7-Zip's static 7zzs for OptiScaler's .7z.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
build="$here/build/decky"
plugin="$build/scaler-assistant"
version="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$here/scaler_assistant/__init__.py")"
output="$here/dist/Scaler_Assistant-Decky-${version}.zip"
seven_zip_url="https://github.com/ip7z/7zip/releases/download/25.01/7z2501-linux-x64.tar.xz"
seven_zip_sha256="4ca3b7c6f2f67866b92622818b58233dc70367be2f36b498eb0bdeaaa44b53f4"

command -v npm >/dev/null || { echo "需要 Node.js / npm" >&2; exit 1; }
package_version="$(sed -n 's/^  "version": "\(.*\)",/\1/p' "$here/decky/package.json")"
[[ "$package_version" == "$version" ]] || {
    echo "錯誤：decky/package.json 的版本 $package_version 與程式版本 $version 不同" >&2; exit 1; }

echo "==> 建置面板（rollup）"
cd "$here/decky"
if [[ -f package-lock.json ]]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
npm run build
cd "$here"

echo "==> 組合外掛資料夾"
rm -rf "$build"
mkdir -p "$plugin/dist" "$plugin/py_modules" "$plugin/bin" "$here/dist"
cp "$here/decky/dist/index.js" "$plugin/dist/"
cp "$here/decky/main.py" "$here/decky/plugin.json" "$here/decky/package.json" "$plugin/"
cp -r "$here/scaler_assistant" "$plugin/py_modules/"
# The desktop window (PyQt6) is not part of the plugin.
rm -rf "$plugin/py_modules/scaler_assistant/"{ui.py,widgets.py,theme.py,overlay.py,assets}
find "$plugin" -name '__pycache__' -prune -exec rm -rf {} +

echo "==> 加入 7-Zip（解開 OptiScaler 的 .7z）"
seven_zip_archive="$here/build/$(basename "$seven_zip_url")"
if ! echo "$seven_zip_sha256  $seven_zip_archive" | sha256sum -c --status 2>/dev/null; then
    curl -fL --progress-bar -o "$seven_zip_archive" "$seven_zip_url"
    echo "$seven_zip_sha256  $seven_zip_archive" | sha256sum -c --status || {
        echo "錯誤：7-Zip 下載檔的 SHA-256 不符" >&2; exit 1; }
fi
tar -xJf "$seven_zip_archive" -C "$plugin/bin" 7zzs License.txt readme.txt
mv "$plugin/bin/License.txt" "$plugin/bin/7zip-License.txt"
mv "$plugin/bin/readme.txt" "$plugin/bin/7zip-readme.txt"
cat > "$plugin/bin/7zip-SOURCE.txt" <<'SOURCE'
7zzs is the static Linux x64 build of 7-Zip 25.01 by Igor Pavlov, unchanged.
Its licence is in 7zip-License.txt (GNU LGPL with the unRAR restriction, BSD 3-clause, BSD 2-clause).
Source code: https://github.com/ip7z/7zip/releases/tag/25.01 (7z2501-src.tar.xz) and https://7-zip.org
Scaler Assistant uses it only to unpack the OptiScaler release it downloads.
SOURCE

cat > "$plugin/README.md" <<'README'
# Scaler Assistant for Decky Loader

Choose DLSS 3.7 (HelixSR), FSR 4.1 Exact / Lossy or FSR 3 for each Steam game from the
Quick Access menu. Same program, settings and downloads as the Scaler Assistant desktop app.
Contains no upscaler files: OptiScaler and the FSR 4.1 DLLs are downloaded only when you
agree; DLSS 3.7 needs your own HelixSR folder (set up in Desktop Mode).

https://github.com/mosesmoon/scaler-assistant
README

echo "==> 自我檢查（不含 Qt 也能載入後端）"
python3 -I -c "
import sys; sys.path.insert(0, '$plugin/py_modules')
import scaler_assistant.deck
assert not any(m.startswith('PyQt') for m in sys.modules), 'Qt imported'
print('backend ok')"
find "$plugin" -name '__pycache__' -prune -exec rm -rf {} +

echo "==> 檢查是否含有建置機器的路徑"
for leak in "$HOME" "$here"; do
    if grep -r -a -l -F "$leak" "$plugin" >/dev/null 2>&1; then
        echo "錯誤：外掛內含建置機器的路徑 $leak：" >&2
        grep -r -a -l -F "$leak" "$plugin" | head -5 >&2
        exit 1
    fi
done

echo "==> 打包 zip"
rm -f "$output"
(cd "$build" && find scaler-assistant -exec touch -h -d '2026-01-01 00:00:00' {} + \
    && zip -qrX "$output" scaler-assistant)

echo
echo "完成：$output ($(du -h "$output" | cut -f1))"
