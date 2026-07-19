#!/bin/bash
# PhoneDeck Local Build Script
# Run this locally to build ALL release artifacts
# NEVER run this on GitHub Actions

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Extract version from app/build.gradle.kts
VERSION=$(grep 'versionName' "$ROOT_DIR/app/build.gradle.kts" | sed 's/.*"\(.*\)".*/\1/')
VERSION_CODE=$(grep 'versionCode' "$ROOT_DIR/app/build.gradle.kts" | sed 's/.*= \([0-9]*\)/\1/')
echo "╔══════════════════════════════════════════╗"
echo "║    PhoneDeck Local Build v$VERSION (code $VERSION_CODE)   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Clean downloads/
echo "[0/4] Cleaning downloads/..."
rm -f "$ROOT_DIR/downloads/PhoneDeck-*.apk" "$ROOT_DIR/downloads/phonedeck-server-*"

# ========== Android Build ==========
echo "[1/4] Building Android APK..."
cd "$ROOT_DIR"
JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./gradlew assembleRelease --no-daemon

APK_SIGNED="app/build/outputs/apk/release/app-release.apk"
APK_UNSIGNED="app/build/outputs/apk/release/app-release-unsigned.apk"

if [ -f "$APK_SIGNED" ]; then
    cp "$APK_SIGNED" "$ROOT_DIR/downloads/PhoneDeck-v$VERSION.apk"
    echo "✅ Android: $ROOT_DIR/downloads/PhoneDeck-v$VERSION.apk"
elif [ -f "$APK_UNSIGNED" ]; then
    cp "$APK_UNSIGNED" "$ROOT_DIR/downloads/PhoneDeck-v$VERSION.apk"
    echo "⚠️  Android: unsigned APK at $ROOT_DIR/downloads/PhoneDeck-v$VERSION.apk"
else
    echo "❌ Android build failed - APK not found"
    exit 1
fi

# ========== Linux Build ==========
echo ""
echo "[2/4] Building Linux binary..."
cd "$ROOT_DIR/companion"
if command -v pyinstaller &> /dev/null; then
    BUILD_DIR="/tmp/phonedeck-build-$$"
    DIST_DIR="/tmp/phonedeck-dist-$$"
    pyinstaller --clean --noconfirm --workpath "$BUILD_DIR" --distpath "$DIST_DIR" phonedeck-server-linux.spec
    if [ -f "$DIST_DIR/phonedeck-server-linux" ]; then
        cp "$DIST_DIR/phonedeck-server-linux" "$ROOT_DIR/downloads/phonedeck-server-linux-v$VERSION"
        chmod +x "$ROOT_DIR/downloads/phonedeck-server-linux-v$VERSION"
        rm -rf "$BUILD_DIR" "$DIST_DIR"
        echo "✅ Linux: $ROOT_DIR/downloads/phonedeck-server-linux-v$VERSION"
    else
        echo "⚠️  Linux binary not found after build"
        rm -rf "$BUILD_DIR" "$DIST_DIR"
    fi
else
    echo "⚠️  pyinstaller not found - skipping Linux binary build"
fi

# ========== Summary ==========
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Build Complete!              ║"
echo "╚══════════════════════════════════════════╝"
echo ""
ls -la "$ROOT_DIR/downloads/"
echo ""
echo "📦 Artifacts in downloads/ ready for GitHub Release:"
echo "   https://github.com/iamhero337/PhoneDeck/releases/new"
