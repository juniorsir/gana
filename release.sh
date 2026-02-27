#!/bin/bash
set -e

# =========================
# CONFIG
# =========================
APP_NAME="gana"
VERSION="1.0.11" # Bumped to 1.0.11
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"
BUILD_DIR="build_termux"
REPO_DIR="."     # <--- FIXED: Now builds in the ROOT directory
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"
TERMUX_PATH="/data/data/com.termux/files/usr"

echo "🚧 Building $APP_NAME v$VERSION..."

# =========================
# CLEANUP
# =========================
rm -rf "$BUILD_DIR"
rm -f "$DEB_NAME"
rm -f debs/*.deb

# =========================
# BUILD STRUCTURE
# =========================
mkdir -p "$BUILD_DIR$TERMUX_PATH/bin"
mkdir -p "$BUILD_DIR$TERMUX_PATH/lib/python-gana"
mkdir -p "$BUILD_DIR/DEBIAN"
chmod 755 "$BUILD_DIR/DEBIAN"

cp -r gana "$BUILD_DIR$TERMUX_PATH/lib/python-gana/"

# =========================
# CONTROL FILE
# =========================
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
# POST INSTALL
# =========================
cat <<EOF > "$BUILD_DIR/DEBIAN/postinst"
#!$TERMUX_PATH/bin/sh
echo "Installing dependencies..."
pip install yt-dlp requests --upgrade --break-system-packages
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# =========================
# WRAPPER BINARY
# =========================
cat <<EOF > "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"
#!$TERMUX_PATH/bin/sh
export PYTHONPATH="$TERMUX_PATH/lib/python-gana"
exec python -m gana.cli "\$@"
EOF
chmod 755 "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"

# =========================
# BUILD DEB & MOVE
# =========================
dpkg-deb --build "$BUILD_DIR" "$DEB_NAME"
mkdir -p debs
mv "$DEB_NAME" debs/

# =========================
# REGENERATE METADATA
# =========================
rm -f Packages Packages.gz Release Release.gpg InRelease

dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release

# Sign
gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release

# =========================
# GIT DEPLOY
# =========================
git add .
git commit -m "Release $APP_NAME v$VERSION (Root Path Fix)"
git push

echo "✅ Uploaded v$VERSION. Wait ~30 seconds for GitHub Pages to deploy!"
