#!/bin/bash
set -e

APP_NAME="gana"
VERSION="1.0.13" # Bumped to clear cache
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"
BUILD_DIR="build_termux"
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"
TERMUX_PATH="/data/data/com.termux/files/usr"

echo "🚧 Building $APP_NAME v$VERSION..."

# =========================
# 1. CLEANUP
# =========================
rm -rf "$BUILD_DIR"
# Delete old debs in the folder to save repo space
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

cat <<EOF > "$BUILD_DIR/DEBIAN/postinst"
#!$TERMUX_PATH/bin/sh
echo "Installing dependencies..."
pip install yt-dlp requests --upgrade --break-system-packages
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

cat <<EOF > "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"
#!$TERMUX_PATH/bin/sh
export PYTHONPATH="$TERMUX_PATH/lib/python-gana"
exec python -m gana.cli "\$@"
EOF
chmod 755 "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"

# =========================
# 3. BUILD DIRECTLY INTO 'debs' FOLDER
# =========================
dpkg-deb --build "$BUILD_DIR" "debs/$DEB_NAME"

# =========================
# 4. REGENERATE METADATA
# =========================
rm -f Packages Packages.gz Release Release.gpg InRelease

# THIS IS THE MAGIC LINE: It scans the 'debs' folder and adds "debs/" to the Packages file paths.
dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release

# Sign
gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release

# =========================
# 5. GIT DEPLOY
# =========================
# Force add the debs folder to bypass any .gitignore rules!
git add -f debs/
git add .
git commit -m "Release $APP_NAME v$VERSION (Moved to debs folder)"
git push

echo "✅ Uploaded v$VERSION into the 'debs/' folder. Wait ~60 seconds."
