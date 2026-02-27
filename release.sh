#!/bin/bash
set -e

APP_NAME="gana"
VERSION="1.0.14" # Bumped to push new beautiful post-install
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"
BUILD_DIR="build_termux"
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"
TERMUX_PATH="/data/data/com.termux/files/usr"

echo "🚧 Building $APP_NAME v$VERSION..."

# =========================
# 1. CLEANUP
# =========================
rm -rf "$BUILD_DIR"
rm -rf debs/
mkdir -p debs/

# =========================
# 2. BUILD STRUCTURE
# =========================
mkdir -p "$BUILD_DIR$TERMUX_PATH/bin"
mkdir -p "$BUILD_DIR$TERMUX_PATH/lib/python-gana"
mkdir -p "$BUILD_DIR/DEBIAN"
chmod 755 "$BUILD_DIR/DEBIAN"

cp -r gana "$BUILD_DIR$TERMUX_PATH/lib/python-gana/"

cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python, mpv, ffmpeg
Maintainer: JuniorSir <juniorsir011@gmail.com>
Description: Gana CLI music player for Termux
EOF

# =========================
# 3. BEAUTIFUL POST INSTALL (The Magic Fix)
# =========================
# This script runs on the user's phone right after 'pkg install gana' finishes.
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/data/data/com.termux/files/usr/bin/sh

# Print beautiful Cyan Logo
echo -e "\n\033[38;5;51m\033[1m"
echo "  ██████╗  █████╗ ███╗   ██╗ █████╗ "
echo " ██╔════╝ ██╔══██╗████╗  ██║██╔══██╗"
echo " ██║  ███╗███████║██╔██╗ ██║███████║"
echo " ██║   ██║██╔══██║██║╚██╗██║██╔══██║"
echo " ╚██████╔╝██║  ██║██║ ╚████║██║  ██║"
echo "  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝"
echo -e "\033[0m"

# Print a clean status message
echo -e "\033[38;5;226m>> Initializing Audio Engine & Core Modules...\033[0m"

# Run PIP completely silently! No messy logs!
python -m pip install yt-dlp requests --upgrade --break-system-packages -q > /dev/null 2>&1

# Print final welcome guide
echo -e "\033[38;5;46m[✓] Installation Successful!\033[0m\n"
echo -e "\033[38;5;201m─────────────────────────────────────────\033[0m"
echo -e "\033[1m🚀 QUICK START:\033[0m"
echo -e "   Just type \033[38;5;46mgana\033[0m to open the dashboard."
echo -e "   Or type \033[38;5;46mgana play \"lofi\"\033[0m to quick-play!"
echo -e "\033[38;5;201m─────────────────────────────────────────\033[0m\n"

exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# =========================
# 4. WRAPPER BINARY
# =========================
cat <<EOF > "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"
#!$TERMUX_PATH/bin/sh
export PYTHONPATH="$TERMUX_PATH/lib/python-gana"
exec python -m gana.cli "\$@"
EOF
chmod 755 "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"

# =========================
# 5. BUILD DEB
# =========================
dpkg-deb --build "$BUILD_DIR" "debs/$DEB_NAME"

# =========================
# 6. REGENERATE METADATA
# =========================
rm -f Packages Packages.gz Release Release.gpg InRelease

dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release

gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release

# =========================
# 7. GIT DEPLOY
# =========================
git add -f debs/
git add .
git commit -m "Release $APP_NAME v$VERSION (Beautiful Install UI)"
git push

echo "✅ Uploaded v$VERSION. Wait ~60 seconds."
