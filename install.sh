#!/usr/bin/env bash
# Install HelixSR 助手 for the current user: ~/.local/share/helixsr-assistant,
# a `helixsr-assistant` command in ~/.local/bin and an application menu entry.
set -euo pipefail
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dest="${XDG_DATA_HOME:-$HOME/.local/share}/helixsr-assistant"
bin="$HOME/.local/bin"
apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

python3 -c 'import PyQt6.QtWidgets' 2>/dev/null || {
    echo "需要 PyQt6：sudo pacman -S python-pyqt6" >&2; exit 1; }

mkdir -p "$dest" "$bin" "$apps"
rm -rf "$dest/helixsr_assistant"
cp -r "$src/helixsr_assistant" "$dest/"
find "$dest/helixsr_assistant" -name __pycache__ -prune -exec rm -rf {} +
install -m 755 "$src/helixsr-assistant" "$dest/helixsr-assistant"
ln -sf "$dest/helixsr-assistant" "$bin/helixsr-assistant"

cat > "$apps/helixsr-assistant.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=HelixSR 助手
Name[en]=HelixSR Assistant
Comment=為 Steam 遊戲一鍵安裝、切換或移除 HelixSR
Comment[en]=Install, switch or remove HelixSR in Steam games
Exec=$bin/helixsr-assistant
Icon=applications-games
Terminal=false
Categories=Game;
StartupWMClass=helixsr-assistant
DESKTOP
update-desktop-database "$apps" >/dev/null 2>&1 || true
echo "已安裝 HelixSR 助手：執行 helixsr-assistant 或從應用程式選單開啟。"
