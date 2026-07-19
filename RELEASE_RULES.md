# Release Rules - PhoneDeck

## ⛔ NEVER Build on GitHub Actions

**ALL builds MUST be done locally.** Do not use GitHub Actions for building release artifacts.

### Required Local Build Process

```bash
# 1. Build Android APK (requires Android Studio/JDK 21)
cd Androiddeck
JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./gradlew assembleRelease

# 2. Build Linux binary
cd companion
pyinstaller --clean --noconfirm phonedeck-server-linux.spec

# 3. Build Windows binary (on Windows machine or via Wine)
pyinstaller --clean --noconfirm phonedeck-server-windows.spec

# 4. Build macOS binary (on macOS)
pyinstaller --clean --noconfirm --onefile server.py --name phonedeck-server-macos
```

### Release Checklist

1. **Version bump** in:
   - `app/build.gradle.kts` (versionCode, versionName)
   - `companion/server.py` (VERSION)
   - `companion/updater.py` (CURRENT_VERSION)
   - `MainActivity.kt` (CURRENT_VERSION)

2. **Build locally** all artifacts:
   - `app/build/outputs/apk/release/app-release-unsigned.apk`
   - `companion/dist/phonedeck-server-linux`
   - `companion/dist/phonedeck-server-windows.exe`
   - `companion/dist/phonedeck-server-macos`

3. **Commit & tag**:
   ```bash
   git add -A
   git commit -m "vX.Y.Z: Release notes"
   git tag vX.Y.Z
   git push origin master
   git push origin vX.Y.Z
   ```

4. **Manual GitHub Release**:
   - Go to https://github.com/iamhero337/PhoneDeck/releases/new
   - Tag: `vX.Y.Z`
   - Title: `PhoneDeck vX.Y.Z`
   - Upload ALL artifacts manually
   - Publish

### Why Local Builds?

- ✅ Reproducible environment
- ✅ No CI/CD flakiness
- ✅ Faster iteration
- ✅ Full control over signing/keys
- ✅ No secrets in CI
- ✅ Works offline

### Workflow Files

**DELETED** - `.github/workflows/android.yml` and `.github/workflows/desktop.yml` removed per this rule.

If workflows are re-added, they MUST be for testing/linting ONLY - never for producing release artifacts.