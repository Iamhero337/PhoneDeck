# Release Rules - PhoneDeck (Strict)

## ⛔ NEVER Build on GitHub Actions

**ALL builds MUST be done locally.** Do not use GitHub Actions for building release artifacts.

---

## 📋 Pre-Release Checklist (MANDATORY)

### 1. Version Management - CRITICAL
```bash
# Update ALL of these BEFORE building:
# app/build.gradle.kts          → versionCode = X+1, versionName = "X.Y.Z"
# companion/server.py           → VERSION = "X.Y.Z"
# companion/updater.py          → CURRENT_VERSION = "vX.Y.Z"
# MainActivity.kt               → CURRENT_VERSION = "vX.Y.Z"
```

**versionCode MUST increment by 1 every release** (not optional - Android enforces this)

### 2. Consistent Signing - CRITICAL
```bash
# Use THE SAME keystore forever:
# release.keystore (in repo root)
# Password: phonedeck123
# Alias: phonedeck
# Key Password: phonedeck123
```

**If keystore changes → users CANNOT update** (must uninstall first)

### 3. Build Locally
```bash
# Android
JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./gradlew assembleRelease

# Linux Server
cd companion && pyinstaller --clean --noconfirm phonedeck-server-linux.spec

# Windows (on Windows)
pyinstaller --clean --noconfirm phonedeck-server-windows.spec

# macOS (on macOS)
pyinstaller --clean --noconfirm --onefile server.py --name phonedeck-server-macos
```

### 4. Verify Before Release
```bash
# Check versionCode incremented
grep versionCode app/build.gradle.kts

# Check APK is signed
apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk

# Test install (uninstall old first!)
adb uninstall com.phonedeck.android
adb install app/build/outputs/apk/release/app-release.apk
```

### 5. Release Process
```bash
# 1. Clean downloads
rm -f downloads/PhoneDeck-*.apk downloads/phonedeck-server-*

# 2. Copy artifacts
cp app/build/outputs/apk/release/app-release.apk downloads/PhoneDeck-vX.Y.Z.apk
cp companion/dist/phonedeck-server-linux downloads/phonedeck-server-linux-vX.Y.Z

# 3. Commit & Tag
git add -A
git commit -m "vX.Y.Z: Release notes"
git tag vX.Y.Z
git push origin master
git push origin vX.Y.Z

# 4. Manual GitHub Release
# Go to: https://github.com/iamhero337/PhoneDeck/releases/new
# Upload ALL artifacts from downloads/
```

---

## 🚫 What Causes "Version Conflict" Errors

| Cause | Fix |
|-------|-----|
| versionCode NOT incremented | **ALWAYS increment versionCode** |
| Different keystore/signature | **Use same release.keystore forever** |
| Installing unsigned over signed | **Never mix debug/release builds** |
| Installing old versionCode over new | **Uninstall first if downgrading** |

---

## 🔑 Keystore Management

**Location:** `/home/hero/Documents/Gits/Androiddeck/release.keystore`

**Backup this file SECURELY** - if lost, users cannot update (must uninstall)

```bash
# Verify keystore
keytool -list -keystore release.keystore -alias phonedeck
```

---

## 📱 For New Machines / Clean Builds

1. Copy `release.keystore` to repo root
2. Build locally (not CI)
3. VersionCode = previous + 1
4. Same keystore = seamless updates

**NEVER generate a new keystore for releases.**