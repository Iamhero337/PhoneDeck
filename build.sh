#!/bin/bash
# PhoneDeck Build Script
# Builds Android APK and Desktop binaries for all platforms

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT_DIR/build-output"
DATE=$(date +"%Y%m%d-%H%M%S")
VERSION="v1.3.0"

echo "╔══════════════════════════════════════════╗"
echo "║       PhoneDeck Build Script v$VERSION       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

mkdir -p "$BUILD_DIR"

# Build Android APK
echo "[1/4] Building Android APK..."
cd "$ROOT_DIR"
./gradlew assembleRelease --no-daemon
cp app/build/outputs/apk/release/app-release.apk "$BUILD_DIR/PhoneDeck-$VERSION-$DATE.apk"
echo "✅ Android APK: $BUILD_DIR/PhoneDeck-$VERSION-$DATE.apk"

# Build Linux binary
echo ""
echo "[2/4] Building Linux binary..."
cd "$ROOT_DIR/companion"
pyinstaller --clean --noconfirm phonedeck-server-linux.spec
cp dist/phonedeck-server-linux "$BUILD_DIR/phonedeck-server-linux-$VERSION-$DATE"
echo "✅ Linux binary: $BUILD_DIR/phonedeck-server-linux-$VERSION-$DATE"

# Build Windows binary (if on Windows or using cross-compile)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo ""
    echo "[3/4] Building Windows binary..."
    pyinstaller --clean --noconfirm phonedeck-server-windows.spec
    cp dist/phonedeck-server-windows.exe "$BUILD_DIR/phonedeck-server-windows-$VERSION-$DATE.exe"
    echo "✅ Windows binary: $BUILD_DIR/phonedeck-server-windows-$VERSION-$DATE.exe"
else
    echo ""
    echo "[3/4] Skipping Windows build (run on Windows or use GitHub Actions)"
fi

# Build macOS binary (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "[4/4] Building macOS binary..."
    pyinstaller --clean --noconfirm --onefile server.py --name phonedeck-server-macos
    cp dist/phonedeck-server-macos "$BUILD_DIR/phonedeck-server-macos-$VERSION-$DATE"
    echo "✅ macOS binary: $BUILD_DIR/phonedeck-server-macos-$VERSION-$DATE"
else
    echo ""
    echo "[4/4] Skipping macOS build (run on macOS or use GitHub Actions)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Build Complete!               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Output directory: $BUILD_DIR"
ls -la "$BUILD_DIR"