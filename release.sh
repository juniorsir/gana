#!/data/data/com.termux/files/usr/bin/bash
set -e

VERSION="1.0.6"
KEY="87256EF09168BFBB9787D47F0D5C7BC2E3F98249"

echo "[1] Cleaning..."
rm -rf build dist debian/usr
mkdir -p debian/usr/share/gana

echo "[2] Building wheel..."
python -m build

echo "[3] Copying wheel..."
cp dist/gana_player-$VERSION-py3-none-any.whl debian/usr/share/gana/

echo "[4] Fixing permissions..."
chmod 755 debian
chmod 755 debian/DEBIAN
chmod 755 debian/DEBIAN/postinst

echo "[5] Building .deb..."
dpkg-deb --build debian
mv debian.deb gana_${VERSION}_termux.deb

echo "[6] Updating APT repo..."
cp gana_${VERSION}_termux.deb repo/debs/

cd repo

rm -f Packages Packages.gz Release Release.gpg InRelease

dpkg-scanpackages . /dev/null > Packages
gzip -k -f Packages
apt-ftparchive release . > Release

gpg --default-key $KEY -abs -o Release.gpg Release
gpg --default-key $KEY --clearsign -o InRelease Release

git add .
git commit -m "Release gana $VERSION" || true
git push --set-upstream origin main

echo "✅ Release complete."
