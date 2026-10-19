#!/usr/bin/env bash
# Build Scaler_Assistant-<version>-x86_64.flatpak, a single-file Flatpak bundle.
#
# The bundle carries the same bundled app as the AppImage (portable CPython,
# trimmed PyQt6, 7-Zip's 7zzs) on the org.freedesktop.Platform runtime, which
# `flatpak install` fetches from Flathub. Only the flatpak command is needed to
# build (no flatpak-builder, no SDK): the AppDir is the app's /app.
#
# Sandbox: games and Steam live in the home folder and on other drives (SD card
# under /run/media), Steam's processes are read through flatpak-spawn --host
# (scaler_assistant.sandbox), and Steam's CEF port needs the network.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
app_id="io.github.mosesmoon.ScalerAssistant"
runtime_version="${FLATPAK_RUNTIME:-25.08}"
appdir="$here/build/AppDir"
build="$here/build/flatpak"
version="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$here/scaler_assistant/__init__.py")"
output="$here/dist/Scaler_Assistant-${version}-x86_64.flatpak"

command -v flatpak >/dev/null || { echo "需要 flatpak 指令" >&2; exit 1; }
if [[ ! -x "$appdir/AppRun" || "${REBUILD_APPDIR:-0}" = 1 ]]; then
    echo "==> 先建置 AppDir（build-appimage.sh）"
    "$here/build-appimage.sh"
fi

echo "==> 準備 /app"
rm -rf "$build"
files="$build/app/files"
mkdir -p "$files/bin" "$files/share/applications" "$files/share/metainfo" \
         "$files/share/icons/hicolor/256x256/apps"
cp -a "$appdir/." "$files/"
rm -f "$files/.DirIcon"
cat > "$files/bin/scaler-assistant" <<'LAUNCHER'
#!/bin/sh
exec /app/AppRun "$@"
LAUNCHER
chmod +x "$files/bin/scaler-assistant"
sed -e "s/^Icon=.*/Icon=$app_id/" -e "s/^Exec=.*/Exec=scaler-assistant/" \
    -e "s/^StartupWMClass=.*/StartupWMClass=scaler-assistant/" \
    "$appdir/scaler-assistant.desktop" > "$files/share/applications/$app_id.desktop"
cp "$here/packaging/scaler-assistant.png" "$files/share/icons/hicolor/256x256/apps/$app_id.png"
cat > "$files/share/metainfo/$app_id.metainfo.xml" <<METAINFO
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>$app_id</id>
  <name>Scaler Assistant</name>
  <name xml:lang="zh-TW">Scaler 助手</name>
  <summary>Choose DLSS 3.7 (HelixSR), FSR 4.1 or FSR 3 for your Steam games</summary>
  <summary xml:lang="zh-TW">為 Steam 遊戲選擇 DLSS 3.7（HelixSR）、FSR 4.1 或 FSR 3</summary>
  <metadata_license>CC0-1.0</metadata_license>
  <developer id="io.github.mosesmoon"><name>mosesmoon</name></developer>
  <url type="homepage">https://github.com/mosesmoon/scaler-assistant</url>
  <launchable type="desktop-id">$app_id.desktop</launchable>
  <releases><release version="$version"/></releases>
</component>
METAINFO
cat > "$build/app/metadata" <<METADATA
[Application]
name=$app_id
runtime=org.freedesktop.Platform/x86_64/$runtime_version
sdk=org.freedesktop.Sdk/x86_64/$runtime_version
METADATA

echo "==> 權限與匯出"
flatpak build-finish "$build/app" --command=scaler-assistant \
    --share=network --share=ipc --socket=x11 --socket=wayland --device=dri \
    --filesystem=home --filesystem=/run/media --filesystem=/media --filesystem=/mnt \
    --talk-name=org.freedesktop.Flatpak >/dev/null
flatpak build-export "$build/repo" "$build/app" stable >/dev/null
mkdir -p "$here/dist"
rm -f "$output"
flatpak build-bundle "$build/repo" "$output" "$app_id" stable \
    --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo

echo "==> 檢查是否含有建置機器的路徑"
for leak in "$HOME" "$here"; do
    if grep -r -a -l -F "$leak" "$build/app" >/dev/null 2>&1; then
        echo "錯誤：Flatpak 內含建置機器的路徑 $leak" >&2
        exit 1
    fi
done

echo
echo "完成：$output ($(du -h "$output" | cut -f1))"
echo "安裝：flatpak install --user $(basename "$output")"
