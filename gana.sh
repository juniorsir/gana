#!/bin/bash
set -e

APP_NAME="gana"
VERSION="1.1.18"
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"

PRIVATE_REPO="$HOME/gana_cli"
PUBLIC_REPO="$HOME/gana"

BUILD_DIR="build_termux"
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"

PREFIX="$PREFIX"

echo "🚧 Building $APP_NAME v$VERSION..."

rm -rf "$BUILD_DIR"
rm -f "$DEB_NAME"

mkdir -p "$BUILD_DIR/$PREFIX/bin"
mkdir -p "$BUILD_DIR/$PREFIX/lib/python-gana"
mkdir -p "$BUILD_DIR/DEBIAN"

cp -r gana "$BUILD_DIR/$PREFIX/lib/python-gana/"

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
#!$PREFIX/bin/sh
python -m pip install yt-dlp requests --upgrade
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod -R 755 "$BUILD_DIR"
chmod 644 "$BUILD_DIR/DEBIAN/control"
cat <<EOF > "$BUILD_DIR/$PREFIX/bin/$APP_NAME"
#!$PREFIX/bin/sh
export PYTHONPATH="$PREFIX/lib/python-gana"
exec python -m gana.cli "\$@"
EOF
chmod 755 "$BUILD_DIR/$PREFIX/bin/$APP_NAME"

dpkg-deb --build "$BUILD_DIR" "$DEB_NAME"

echo "📦 Deb built."

# =========================
# COPY TO PUBLIC REPO
# =========================

mv "$DEB_NAME" "$PUBLIC_REPO/debs/"

cd "$PUBLIC_REPO"

rm -f Packages Packages.gz Release Release.gpg InRelease

dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release

gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release

gpg --export -a "$KEY_ID" > public.key

git add .
git commit -m "Release $APP_NAME v$VERSION"
git push

echo "✅ Public APT repo updated."
