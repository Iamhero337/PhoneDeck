# Release & Version Management Rules

## Version Bumping (MANDATORY before every release)

### 1. Update ALL version references in a single commit:

**Android (app/build.gradle.kts):**
```kotlin
defaultConfig {
    versionCode = X        // Increment by 1
    versionName = "X.Y.Z"  // Semantic version
}
```

**Python Server (companion/server.py):**
```python
VERSION = "X.Y.Z"
```

**Updater (companion/updater.py):**
```python
CURRENT_VERSION = "vX.Y.Z"
```

**MainActivity (app/src/main/java/.../MainActivity.kt):**
```kotlin
const val CURRENT_VERSION = "vX.Y.Z"
```

### 2. Build Locally FIRST

```bash
# Android
JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./gradlew :app:assembleRelease --no-daemon

# Linux Server
cd companion && pyinstaller --clean --noconfirm phonedeck-server-linux.spec
```

### 3. Verify Builds Work

```bash
# Test APK installs
adb install -r app/build/outputs/apk/release/app-release.apk

# Test Linux binary runs
./companion/dist/phonedeck-server-linux --version
```

### 4. Copy to downloads/ (NOT COMMITTED)

```bash
# Remove OLD versions first
rm -f downloads/PhoneDeck-*.apk
rm -f downloads/phonedeck-server-linux-*

# Copy NEW versions
cp app/build/outputs/apk/release/app-release.apk downloads/PhoneDeck-vX.Y.Z.apk
cp companion/dist/phonedeck-server-linux downloads/phonedeck-server-linux-vX.Y.Z
```

### 5. Create Git Tag & GitHub Release

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

**GitHub Actions will auto-build and attach artifacts to the release.**

### 6. Update CHANGELOG.md

Follow [Keep a Changelog](https://keepachangelog.com/) format.

---

## Auto-Connect Troubleshooting

If "Auto-connect is ON" but not connecting:

1. **Check server is running on desktop:**
   ```bash
   systemctl --user status phonedeck.service
   # or
   journalctl --user -u phonedeck.service -f
   ```

2. **Verify same WiFi network** (phone + desktop)

3. **Check mDNS/zeroconf works:**
   ```bash
   # On desktop, verify service is broadcasting:
   avahi-browse -a | grep phonedeck
   # Or check logs for "Registered service"
   ```

4. **Manual IP fallback:** Open Settings → Connect → enter desktop IP manually

5. **Firewall:** Ensure port 9090 allowed on desktop:
   ```bash
   sudo ufw allow 9090/tcp
   ```

---

## Git Ignore (enforced)

`downloads/` is in `.gitignore` — never commit built artifacts.

---

## Checklist Before Pushing Release

- [ ] All version numbers match across 5 files
- [ ] `./gradlew assembleRelease` succeeds
- [ ] `pyinstaller` builds Linux binary
- [ ] Both artifacts tested locally
- [ ] Old downloads/ files removed
- [ ] New artifacts copied to downloads/
- [ ] CHANGELOG.md updated
- [ ] Git tag created and pushed
- [ ] GitHub Release published (auto or manual)