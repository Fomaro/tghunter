#!/usr/bin/env bash
set -euo pipefail

echo "=== Building Debian Package (.deb) for Telegram Username Hunter ==="

VERSION="1.0.0"
ARCH="amd64"
PKG_DIR="dist/deb_pkg"
BUILD_DIR="${PKG_DIR}/telegram-username-hunter_${VERSION}_${ARCH}"

rm -rf "${PKG_DIR}"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/telegram-username-hunter"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/512x512/apps"

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

# 2. Copy binaries and assets
cp -r dist/linux_bin/TelegramUsernameHunter/* "${BUILD_DIR}/usr/lib/telegram-username-hunter/"
cp packaging/linux/telegram-username-hunter.desktop "${BUILD_DIR}/usr/share/applications/"
cp assets/icon.png "${BUILD_DIR}/usr/share/icons/hicolor/512x512/apps/telegram-username-hunter.png"

# 3. Wrapper script in /usr/bin
cat << 'EOF' > "${BUILD_DIR}/usr/bin/telegram-username-hunter"
#!/usr/bin/env bash
# Wrapper ensuring proper working directory and user data storage
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_USER_DIR="${XDG_DATA_HOME}/telegram-username-hunter"
mkdir -p "${APP_USER_DIR}"
cd "${APP_USER_DIR}"
exec /usr/lib/telegram-username-hunter/TelegramUsernameHunter "$@"
EOF
chmod +x "${BUILD_DIR}/usr/bin/telegram-username-hunter"

# 4. Control file
cat << EOF > "${BUILD_DIR}/DEBIAN/control"
Package: telegram-username-hunter
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Fomaro <vinogradov-semen@list.ru>
Depends: libc6 (>= 2.31), python3-tk
Description: High-performance Telegram Username Hunter and Fragment Valuation Suite
 Automated tool for hunting free Telegram usernames, bot names,
 premium aliases, evaluating market potential, and tracking Fragment TON auctions.
EOF

# 5. Build .deb package
dpkg-deb --build "${BUILD_DIR}" "dist/TelegramUsernameHunter_${VERSION}_${ARCH}.deb"
echo "[SUCCESS] Debian package created: dist/TelegramUsernameHunter_${VERSION}_${ARCH}.deb"
