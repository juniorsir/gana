#!/bin/bash
set -e

APP_NAME="gana"
VERSION="1.0.19" # Bumped to ensure clean deploy
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"
BUILD_DIR="build_termux"
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"
TERMUX_PATH="/data/data/com.termux/files/usr"

# 1. REMEMBER CURRENT BRANCH
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch is '$ORIGINAL_BRANCH'. Will return here after deploy."

# =========================
# 2. BUILD THE .DEB FILE
# =========================
echo "🚧 Building $APP_NAME v$VERSION..."
rm -rf "$BUILD_DIR"
rm -f "$DEB_NAME" # Clean any old deb in root
mkdir -p "$BUILD_DIR$TERMUX_PATH/bin"
mkdir -p "$BUILD_DIR$TERMUX_PATH/lib/python-gana"
mkdir -p "$BUILD_DIR/DEBIAN"
chmod 755 "$BUILD_DIR/DEBIAN"
cp -r gana "$BUILD_DIR$TERMUX_PATH/lib/python-gana/"

# Control File
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Architecture: all
Depends: python, mpv, ffmpeg
Maintainer: JuniorSir <juniorsir011@gmail.com>
Description: Gana CLI music player for Termux
EOF

# Post-Install
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/data/data/com.termux/files/usr/bin/sh
spin() { pid=$!; i=0; printf "\033[?25l"; while kill -0 \$pid 2>/dev/null; do i=\$(( (i+1) % 4 )); case \$i in 0) c="|";; 1) c="/";; 2) c="-";; 3) c="\\";; esac; printf "\r\033[38;5;51m[%s]\033[0m %s..." "\$c" "\$1"; sleep 0.1; done; wait \$pid; printf "\r\033[?25h\033[38;5;46m[✓]\033[0m %s... Done!       \n" "\$1"; };
python -m pip install yt-dlp requests --upgrade --break-system-packages -q > /dev/null 2>&1 &
spin "Initializing Audio Engine"
printf "\n\033[38;5;46m[✓] GANA is installed!\033[0m Type 'gana' to start.\n"
exit 0
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Wrapper
cat <<EOF > "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"
#!$TERMUX_PATH/bin/sh
export PYTHONPATH="$TERMUX_PATH/lib/python-gana"
exec python -m gana.cli "\$@"
EOF
chmod 755 "$BUILD_DIR$TERMUX_PATH/bin/$APP_NAME"

# Build It!
dpkg-deb --build "$BUILD_DIR" "$DEB_NAME"

# =========================
# 3. DEPLOY TO GH-PAGES
# =========================
echo "🚀 Deploying to APT repository..."
git checkout gh-pages
# Clean old repo files
rm -rf debs/ Packages* Release* InRelease* public.key
mkdir -p debs
mv "$DEB_NAME" debs/

# Regenerate Metadata
dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release
gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release
gpg --export -a "$KEY_ID" > public.key
touch .nojekyll

# Commit and Push
git add .
git commit -m "Deploy $APP_NAME v$VERSION"
git push origin gh-pages

# =========================
# 4. RETURN TO ORIGINAL BRANCH
# =========================
git checkout "$ORIGINAL_BRANCH"
rm -rf "$BUILD_DIR" # Clean up temp build folder
echo "✅ Deployment complete! Returned to '$ORIGINAL_BRANCH'."
