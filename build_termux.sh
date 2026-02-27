#!/bin/bash

# --- CONFIGURATION ---
APP_NAME="gana"
VERSION="1.0.6"
TERMUX_PREFIX="/data/data/com.termux/files/usr"
BUILD_DIR="build_termux"

echo "🚧 Building GANA v$VERSION for Termux..."

# 1. Clean previous builds
rm -rf "$BUILD_DIR"
rm -f "${APP_NAME}_${VERSION}_termux.deb"

# 2. Create Termux Directory Structure
mkdir -p "$BUILD_DIR/$TERMUX_PREFIX/bin"
mkdir -p "$BUILD_DIR/$TERMUX_PREFIX/lib/python-gana"
mkdir -p "$BUILD_DIR/DEBIAN"

# Fix permissions for dpkg
chmod 755 "$BUILD_DIR/DEBIAN"

# 3. Copy Python Source Code
cp -r gana "$BUILD_DIR/$TERMUX_PREFIX/lib/python-gana/"

# 4. Create Control File
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python, mpv, ffmpeg
Maintainer: Your Name <you@example.com>
Description: A Cyberpunk CLI Music Player (Termux Edition)
EOF

# 5. Create Post-Install Script
cat <<EOF > "$BUILD_DIR/DEBIAN/postinst"
#!/data/data/com.termux/files/usr/bin/sh
echo "Installing Python dependencies..."
pip install yt-dlp requests --upgrade
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# 6. Create Binary Wrapper
cat <<EOF > "$BUILD_DIR/$TERMUX_PREFIX/bin/gana"
#!/data/data/com.termux/files/usr/bin/sh
export PYTHONPATH="$TERMUX_PREFIX/lib/python-gana"
exec python -m gana.cli "\$@"
EOF
chmod 755 "$BUILD_DIR/$TERMUX_PREFIX/bin/gana"

# 7. Build DEB
dpkg-deb --build "$BUILD_DIR" "${APP_NAME}_${VERSION}_termux.deb"

echo "✅ Build Complete: ${APP_NAME}_${VERSION}_termux.deb"
