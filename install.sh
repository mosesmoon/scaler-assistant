#!/usr/bin/env bash
# Install Scaler 助手 for the current user: ~/.local/share/scaler-assistant,
# a `scaler-assistant` command in ~/.local/bin and an application menu entry.
set -euo pipefail
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${XDG_DATA_HOME:-$HOME/.local/share}/scaler-assistant"
bin="$HOME/.local/bin"
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

python3 -c 'import PyQt6.QtWidgets' 2>/dev/null || {
    echo "需要 PyQt6：sudo pacman -S python-pyqt6" >&2; exit 1; }

command -v 7zz >/dev/null || command -v 7z >/dev/null || command -v 7za >/dev/null \
    || command -v bsdtar >/dev/null || \
    echo "注意：FSR 4.1 / FSR 3 需要 7-Zip 解開 OptiScaler：sudo pacman -S 7zip（或改用 AppImage）" >&2

mkdir -p "$dest" "$bin" "$apps"
rm -rf "$dest/scaler_assistant"
cp -r "$src/scaler_assistant" "$dest/"
find "$dest/scaler_assistant" -name __pycache__ -prune -exec rm -rf {} +
install -m 755 "$src/scaler-assistant" "$dest/scaler-assistant"
ln -sf "$dest/scaler-assistant" "$bin/scaler-assistant"

cat > "$apps/scaler-assistant.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Scaler 助手
Name[en]=Scaler Assistant
Comment=為 Steam 遊戲選擇 DLSS 3.7（HelixSR）、FSR 4.1 或 FSR 3 升頻
Comment[en]=Choose DLSS 3.7 (HelixSR), FSR 4.1 or FSR 3 upscaling for Steam games
Exec=$bin/scaler-assistant
Icon=applications-games
Terminal=false
Categories=Game;
StartupWMClass=scaler-assistant
DESKTOP
update-desktop-database "$apps" >/dev/null 2>&1 || true
echo "已安裝 Scaler 助手：執行 scaler-assistant 或從應用程式選單開啟。"
