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
# Run the unified build script:
./build.sh

# This will:
# - Build signed APK at downloads/PhoneDeck-vX.Y.Z.apk
# - Build Linux server binary at downloads/phonedeck-server-linux-vX.Y.Z
```

### 4. Verify Before Release
```bash
# Check versionCode incremented
grep versionCode app/build.gradle.kts

# Check APK is signed
apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk

# Check downloads/ has artifacts
ls -la downloads/

# Test install (uninstall old first!)
adb uninstall com.phonedeck.android
adb install downloads/PhoneDeck-vX.Y.Z.apk
```

### 5. Release Process
```bash
# 1. Build via build.sh (already populates downloads/)

# 2. Commit & Tag
git add -A
git commit -m "vX.Y.Z: Release notes"
git tag vX.Y.Z
git push origin master
git push origin vX.Y.Z

# 3. Manual GitHub Release
# Go to: https://github.com/iamhero337/PhoneDeck/releases/new
# Tag: vX.Y.Z
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
2. Run `./build.sh`
3. VersionCode = previous + 1
4. Same keystore = seamless updates

**NEVER generate a new keystore for releases.**
