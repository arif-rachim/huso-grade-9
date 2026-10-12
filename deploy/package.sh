#!/usr/bin/env bash
# Builds one release archive: deploy/package.sh VERSION PLATFORM BINARY DATABASE OUTDIR
#   deploy/package.sh 0.1.0 linux-x86_64 target/release/huso storage/app.db out
# Writes OUTDIR/huso-VERSION-PLATFORM.tar.gz (the program, the database and the deploy helpers).
set -euo pipefail
version=$1; platform=$2; binary=$3; database=$4; out=$5
here="$(cd "$(dirname "$0")" && pwd)"
name="huso-$version-$platform"
exe=huso
case "$platform" in windows*) exe=huso.exe ;; esac
rm -rf "$out/$name"
mkdir -p "$out/$name/storage"
cp "$binary" "$out/$name/$exe"
cp "$database" "$out/$name/storage/app.db"
cp "$here/env.example" "$here/DEPLOY.md" "$here/start.sh" "$here/start.ps1" "$here/huso.service" "$out/$name/"
chmod +x "$out/$name/start.sh" "$out/$name/$exe"
tar -C "$out" -czf "$out/$name.tar.gz" "$name"
echo "$out/$name.tar.gz"
