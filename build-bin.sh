#!/usr/bin/env bash
# Build Scaler_Assistant-<version>-x86_64.bin: one self-extracting installer.
#
# It carries the same bundled app as the AppImage (portable CPython, trimmed
# PyQt6, 7-Zip's 7zzs) as a plain folder, so it needs no FUSE. Running it installs
# for the current user (no root): ~/.local/opt/scaler-assistant, the command
# ~/.local/bin/scaler-assistant and a menu entry. `--uninstall` takes those out
# again (settings and downloads stay).
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
appdir="$here/build/AppDir"
version="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$here/scaler_assistant/__init__.py")"
output="$here/dist/Scaler_Assistant-${version}-x86_64.bin"

if [[ ! -x "$appdir/AppRun" || "${REBUILD_APPDIR:-0}" = 1 ]]; then
    echo "==> 先建置 AppDir（build-appimage.sh）"
    "$here/build-appimage.sh"
fi

echo "==> 打包內容"
payload="$here/build/bin-payload.tar.gz"
rm -f "$payload"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='2026-01-01 00:00:00' \
    -C "$here/build" -czf "$payload" AppDir

echo "==> 寫入安裝程式"
mkdir -p "$here/dist"
{
    sed "s/@VERSION@/$version/g" <<'HEADER'
#!/bin/sh
# Scaler Assistant @VERSION@ installer for Linux x86_64 (Steam Deck Desktop Mode too).
#   sh Scaler_Assistant-@VERSION@-x86_64.bin               install for this user
#   sh Scaler_Assistant-@VERSION@-x86_64.bin --uninstall   remove it again
#   sh Scaler_Assistant-@VERSION@-x86_64.bin --extract DIR only unpack the app
set -e
data="${XDG_DATA_HOME:-$HOME/.local/share}"
dest="$HOME/.local/opt/scaler-assistant"
bin="$HOME/.local/bin/scaler-assistant"
desktop="$data/applications/scaler-assistant.desktop"
icon="$data/icons/hicolor/256x256/apps/scaler-assistant.png"
say() { printf '%s\n' "$*"; }

payload() {   # the archive after the marker line
    skip=$(awk '/^__SCALER_ASSISTANT_PAYLOAD__$/ { print NR + 1; exit }' "$0")
    tail -n +"$skip" "$0"
}

case "${1:-}" in
    --uninstall)
        rm -rf "$dest"
        rm -f "$bin" "$desktop" "$icon"
        command -v update-desktop-database >/dev/null 2>&1 && \
            update-desktop-database -q "$data/applications" 2>/dev/null || true
        say "Scaler Assistant removed (settings in ~/.config/scaler-assistant and downloads stay)."
        say "已移除 Scaler 助手（~/.config/scaler-assistant 的設定與下載檔保留）。"
        exit 0 ;;
    --extract)
        [ -n "${2:-}" ] || { say "usage: $0 --extract DIR"; exit 2; }
        mkdir -p "$2"
        payload | tar -xz -C "$2"
        say "Unpacked to $2/AppDir (run $2/AppDir/AppRun)."
        exit 0 ;;
    -h|--help)
        sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
        exit 0 ;;
    "") ;;
    *) say "unknown option: $1 (see --help)"; exit 2 ;;
esac

[ "$(uname -m)" = x86_64 ] || { say "x86_64 Linux only / 只支援 x86_64 Linux"; exit 1; }
say "Installing Scaler Assistant @VERSION@ … / 正在安裝 Scaler 助手 @VERSION@ …"
tmp=$(mktemp -d "${TMPDIR:-/tmp}/scaler-assistant.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
payload | tar -xz -C "$tmp"
mkdir -p "$(dirname "$dest")" "$(dirname "$bin")" "$(dirname "$desktop")" "$(dirname "$icon")"
rm -rf "$dest"
mv "$tmp/AppDir" "$dest"
cat > "$bin" <<LAUNCHER
#!/bin/sh
exec "$dest/AppRun" "\$@"
LAUNCHER
chmod +x "$bin"
cp "$dest/scaler-assistant.png" "$icon"
sed "s|^Exec=.*|Exec=$bin|" "$dest/scaler-assistant.desktop" > "$desktop"
command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database -q "$data/applications" 2>/dev/null || true
say "Done: Scaler Assistant is in your application menu (command: $bin)."
say "完成：可在應用程式選單開啟 Scaler 助手（指令：$bin）。"
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) say "Note: ~/.local/bin is not in PATH / 提示：~/.local/bin 不在 PATH 中" ;; esac
exit 0
__SCALER_ASSISTANT_PAYLOAD__
HEADER
    cat "$payload"
} > "$output"
chmod +x "$output"
rm -f "$payload"

echo "==> 自我檢查（在暫存家目錄安裝、執行、移除）"
check="$(mktemp -d)"
HOME="$check" XDG_DATA_HOME="$check/.local/share" sh "$output" >/dev/null
(cd / && HOME="$check" QT_QPA_PLATFORM=offscreen "$check/.local/bin/scaler-assistant" --self-test)
grep -q "^Exec=$check/.local/bin/scaler-assistant$" "$check/.local/share/applications/scaler-assistant.desktop"
HOME="$check" XDG_DATA_HOME="$check/.local/share" sh "$output" --uninstall >/dev/null
[[ ! -e "$check/.local/opt/scaler-assistant" && ! -e "$check/.local/bin/scaler-assistant" ]]
rm -rf "$check"

echo
echo "完成：$output ($(du -h "$output" | cut -f1))"
