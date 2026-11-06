#!/usr/bin/env bash
set -euo pipefail

echo "=== Building AppImage for Telegram Username Hunter ==="

VERSION="1.0.0"
APP_DIR="dist/AppDir"

rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/512x512/apps"

# 1. Build PyInstaller binary on Linux if not present
if [ ! -f "dist/linux_bin/TelegramUsernameHunter/TelegramUsernameHunter" ]; then
    echo "Compiling standalone Linux binary with PyInstaller..."
    python3 -m PyInstaller --noconfirm --onedir --windowed \
        --name=TelegramUsernameHunter \
        --distpath=dist/linux_bin \
        --collect-all=customtkinter \
        --add-data="telegram_username_hunter:telegram_username_hunter" \
        main.py
fi

# 2. Copy binaries and desktop assets
cp -r dist/linux_bin/TelegramUsernameHunter/* "${APP_DIR}/usr/bin/"
cp packaging/linux/telegram-username-hunter.desktop "${APP_DIR}/telegram-username-hunter.desktop"
cp assets/icon.png "${APP_DIR}/telegram-username-hunter.png"
cp assets/icon.png "${APP_DIR}/.DirIcon"

# 3. Create AppRun launcher
cat << 'EOF' > "${APP_DIR}/AppRun"
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH:-}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_USER_DIR="${XDG_DATA_HOME}/telegram-username-hunter"
mkdir -p "${APP_USER_DIR}"
cd "${APP_USER_DIR}"
exec "${HERE}/usr/bin/TelegramUsernameHunter" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# 4. Download appimagetool if missing
if [ ! -f "appimagetool" ]; then
    echo "Downloading appimagetool..."
    curl -fsSL -o appimagetool "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" || \
    curl -fsSL -o appimagetool "https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage"
    chmod +x appimagetool
fi

# 5. Build AppImage
ARCH=x86_64 ./appimagetool --appimage-extract-and-run "${APP_DIR}" "dist/TelegramUsernameHunter_${VERSION}-x86_64.AppImage"
echo "[SUCCESS] AppImage created: dist/TelegramUsernameHunter_${VERSION}-x86_64.AppImage"
