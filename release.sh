#!/bin/bash
set -e

# =========================
# CONFIG
# =========================
APP_NAME="gana"
VERSION="1.0.9" # Bump version to clear cache issues
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"
BUILD_DIR="build_termux"
REPO_DIR="docs"
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"
TERMUX_PATH="/data/data/com.termux/files/usr"

echo "🚧 Building $APP_NAME v$VERSION..."

# =========================
# CLEAN LOCAL BUILD ARTIFACTS
# =========================
rm -rf "$BUILD_DIR"
rm -f "$DEB_NAME"

# =========================
# CLEAN REPO (Crucial Fix)
# =========================
# Remove ALL old .deb files so apt doesn't get confused
rm -f "$REPO_DIR/debs/"*.deb

# =========================
# CREATE TERMUX STRUCTURE
# =========================
mkdir -p "$BUILD_DIR$TERMUX_PATH/bin"
mkdir -p "$BUILD_DIR$TERMUX_PATH/lib/python-gana"
mkdir -p "$BUILD_DIR/DEBIAN"

chmod 755 "$BUILD_DIR/DEBIAN"

# =========================
# COPY SOURCE CODE
# =========================
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
# BUILD DEB
# =========================
dpkg-deb --build "$BUILD_DIR" "$DEB_NAME"

echo "📦 Deb built: $DEB_NAME"

# =========================
# MOVE TO REPO
# =========================
mkdir -p "$REPO_DIR/debs"
mv "$DEB_NAME" "$REPO_DIR/debs/"

cd "$REPO_DIR"

# =========================
# REGENERATE METADATA
# =========================
rm -f Packages Packages.gz Release Release.gpg InRelease

# Scan packages
dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages

# Release file
apt-ftparchive release . > Release

# =========================
# SIGN REPO
# =========================
gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release

# =========================
# EXPORT PUBLIC KEY
# =========================
gpg --export -a "$KEY_ID" > public.key

cd ..

# =========================
# GIT PUSH
# =========================
git add .
git commit -m "Release $APP_NAME v$VERSION (Clean Build)"
git push

echo "✅ Release Complete!"
echo "🌍 Repo URL: https://juniorsir.github.io/gana/"
