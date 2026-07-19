#!/bin/bash
# PhoneDeck Local Build Script
# Run this locally to build ALL release artifacts
# NEVER run this on GitHub Actions

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT_DIR/build-output"
VERSION="1.3.0"
DATE=$(date +"%Y%m%d-%H%M%S")

echo "╔══════════════════════════════════════════╗"
echo "║    PhoneDeck Local Build v$VERSION         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

mkdir -p "$BUILD_DIR"

# ========== Android Build ==========
echo "[1/4] Building Android APK..."
cd "$ROOT_DIR"
JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./gradlew assembleRelease --no-daemon

if [ -f "app/build/outputs/apk/release/app-release-unsigned.apk" ]; then
    cp "app/build/outputs/apk/release/app-release-unsigned.apk" "$BUILD_DIR/PhoneDeck-v$VERSION-$DATE.apk"
    echo "✅ Android: $BUILD_DIR/PhoneDeck-v$VERSION-$DATE.apk"
else
    echo "❌ Android build failed - APK not found"
    exit 1
fi

# ========== Linux Build ==========
echo ""
echo "[2/4] Building Linux binary..."
cd "$ROOT_DIR/companion"
pyinstaller --clean --noconfirm phonedeck-server-linux.spec

if [ -f "dist/phonedeck-server-linux" ]; then
    cp "dist/phonedeck-server-linux" "$BUILD_DIR/phonedeck-server-linux-v$VERSION-$DATE"
    chmod +x "$BUILD_DIR/phonedeck-server-linux-v$VERSION-$DATE"
    echo "✅ Linux: $BUILD_DIR/phonedeck-server-linux-v$VERSION-$DATE"
else
    echo "⚠️  Linux binary not found (run on Linux)"
fi

# ========== Windows Build ==========
echo ""
echo "[3/4] Building Windows binary..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    pyinstaller --clean --noconfirm phonedeck-server-windows.spec
    if [ -f "dist/phonedeck-server-windows.exe" ]; then
        cp "dist/phonedeck-server-windows.exe" "$BUILD_DIR/phonedeck-server-windows-v$VERSION-$DATE.exe"
        echo "✅ Windows: $BUILD_DIR/phonedeck-server-windows-v$VERSION-$DATE.exe"
    fi
else
    echo "⏭️  Skipping Windows (run on Windows): pyinstaller --clean phonedeck-server-windows.spec"
fi

# ========== macOS Build ==========
echo ""
echo "[4/4] Building macOS binary..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    pyinstaller --clean --noconfirm --onefile server.py --name phonedeck-server-macos
    if [ -f "dist/phonedeck-server-macos" ]; then
        cp "dist/phonedeck-server-macos" "$BUILD_DIR/phonedeck-server-macos-v$VERSION-$DATE"
        chmod +x "$BUILD_DIR/phonedeck-server-macos-v$VERSION-$DATE"
        echo "✅ macOS: $BUILD_DIR/phonedeck-server-macos-v$VERSION-$DATE"
    fi
else
    echo "⏭️  Skipping macOS (run on macOS): pyinstaller --clean --onefile server.py --name phonedeck-server-macos"
fi

# ========== Summary ==========
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Build Complete!              ║"
echo "╚══════════════════════════════════════════╝"
echo ""
ls -la "$BUILD_DIR"
echo ""
echo "📦 Upload these to GitHub Release manually:"
echo "   https://github.com/iamhero337/PhoneDeck/releases/new"