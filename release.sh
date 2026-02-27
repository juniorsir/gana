#!/bin/bash
set -e

APP_NAME="gana"
VERSION="1.1.17" # Bumped to fix Bad Substitution
KEY_ID="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"
BUILD_DIR="build_termux"
DEB_NAME="${APP_NAME}_${VERSION}_all.deb"
TERMUX_PATH="/data/data/com.termux/files/usr"

echo "🚧 Building $APP_NAME v$VERSION..."

rm -rf "$BUILD_DIR"
rm -rf debs/
mkdir -p debs/

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
# 3. POSIX-SAFE ANIMATION
# =========================
cat <<'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/data/data/com.termux/files/usr/bin/sh

# Print Logo
printf "\n\033[38;5;51m\033[1m"
printf "  ██████╗  █████╗ ███╗   ██╗ █████╗ \n"
printf " ██╔════╝ ██╔══██╗████╗  ██║██╔══██╗\n"
printf " ██║  ███╗███████║██╔██╗ ██║███████║\n"
printf " ██║   ██║██╔══██║██║╚██╗██║██╔══██║\n"
printf " ╚██████╔╝██║  ██║██║ ╚████║██║  ██║\n"
printf "  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝\n"
printf "\033[0m\n"

# POSIX-Safe Spinner Function
spin() {
    pid=$!
    i=0
    # Hide cursor
    printf "\033[?25l"
    
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) % 4 ))
        case $i in
            0) char="|" ;;
            1) char="/" ;;
            2) char="-" ;;
            3) char="\\" ;;
        esac
        
        printf "\r\033[38;5;51m[%s]\033[0m %s..." "$char" "$1"
        sleep 0.1
    done
    wait $pid
    
    # Show cursor, print success
    printf "\r\033[?25h\033[38;5;46m[✓]\033[0m %s... Done!       \n" "$1"
}

# Run PIP silently
python -m pip install yt-dlp requests --upgrade --break-system-packages -q > /dev/null 2>&1 &

# Animate
spin "Initializing Audio Engine"

printf "\n\033[38;5;201m─────────────────────────────────────────\033[0m\n"
printf "\033[1m🚀 QUICK START:\033[0m\n"
printf "   Just type \033[38;5;46mgana\033[0m to open the dashboard.\n"
printf "   Or type \033[38;5;46mgana play \"lofi\"\033[0m to quick-play!\n"
printf "\033[38;5;201m─────────────────────────────────────────\033[0m\n\n"

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
# 5. BUILD & DEPLOY
# =========================
dpkg-deb --build "$BUILD_DIR" "debs/$DEB_NAME"

rm -f Packages Packages.gz Release Release.gpg InRelease
dpkg-scanpackages debs /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release

gpg --default-key "$KEY_ID" -abs -o Release.gpg Release
gpg --default-key "$KEY_ID" --clearsign -o InRelease Release

git add -f debs/
git add .
git commit -m "Release $APP_NAME v$VERSION (Posix Fix)"
git push

echo "✅ Uploaded v$VERSION. Wait ~60 seconds."
