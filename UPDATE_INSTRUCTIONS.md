# AMI Update Instructions

## 🎯 For Users

### Getting Updates

AMI automatically checks for updates:
- **On startup** (5 seconds after launch)
- **Every 24 hours** while running
- **Manually** via tray menu: Right-click → "Check for Updates"

### When an Update is Available

1. **Notification appears** in system tray
2. **Update dialog opens** with:
   - New version number
   - Download size
   - Release notes (what's new)
   - Two options:
     - **Install Now** - Downloads and installs immediately
     - **Remind Me Later** - Postpone update

### Postponement Rules

⚠️ **Important:** You can postpone an update **only 3 times**.

- **1st postponement**: "You can postpone 2 more time(s)"
- **2nd postponement**: "You can postpone 1 more time(s)"
- **3rd postponement**: "This was your last postponement"
- **4th time**: Update is **mandatory** - no "Remind Later" button

### Installation Process

When you click **"Install Now"**:

1. ⏬ **Downloading update...** (progress bar shows status)
2. ✅ **Verifying integrity...** (SHA256 checksum)
3. 📦 **Installing...** (replaces old version)
4. 🔄 **Restarting AMI...** (automatic)

**Total time:** Usually 30-60 seconds depending on connection speed.

### Disabling Auto-Updates

If you prefer manual updates, edit `config.json`:

```json
{
  "updates": {
    "enabled": false
  }
}
```

Then download updates manually from: https://github.com/dgiovannetti/AMI/releases

---

## 🛠️ For Developers

### Creating a New Release

#### 1. Update Version Number

Edit `config.json`:

```json
{
  "app": {
    "version": "1.1.0"  // Increment from 1.0.0
  }
}
```

#### 2. Commit and Tag

```bash
git add config.json
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

#### 3. GitHub Actions Builds Automatically

Once you push the tag, GitHub Actions will:
- ✅ Build Windows executable
- ✅ Build macOS executable
- ✅ Create ZIP packages
- ✅ Upload as artifacts
- ✅ Create GitHub Release (if tag starts with `v`)

Wait ~5-10 minutes for builds to complete.

#### 4. Edit Release Notes

Go to: https://github.com/dgiovannetti/AMI/releases

Edit the auto-generated release and add:

```markdown
## AMI v1.1.0

### 🎉 New Features
- Added feature X
- Improved feature Y

### 🐛 Bug Fixes
- Fixed issue Z

### 📊 Performance
- Reduced memory usage by 20%

---

**Download:**
- Windows: AMI-Windows.zip
- macOS: AMI-macOS.zip

**SHA256 Checksums:**
- Windows: [checksum here]
- macOS: [checksum here]

**Full Changelog:** https://github.com/dgiovannetti/AMI/compare/v1.0.0...v1.1.0
```

#### 5. Verify Update Works

1. Download and run old version (e.g., v1.0.0)
2. Wait 5 seconds after startup
3. Update dialog should appear with new version (v1.1.0)
4. Click "Install Now"
5. Verify update completes and app restarts

### Manual Build & Release

If not using GitHub Actions:

```bash
# On Windows
python build.py  # Creates dist/AMI-Package.zip

# On macOS
python build.py  # Creates dist/AMI-Package.zip

# Generate checksums
shasum -a 256 dist/AMI-Package.zip

# Create release manually
gh release create v1.1.0 \
  dist/AMI-Package.zip \
  --title "AMI v1.1.0" \
  --notes-file RELEASE_NOTES.md
```

### Testing Updates Locally

#### Simulate Old Version

1. Set version to `0.1.0` in `config.json`
2. Run AMI: `python src/tray_app.py`
3. Update dialog should appear (if you have releases > 0.1.0)

#### Test Postponement

```bash
# Run AMI
python src/tray_app.py

# When update dialog appears:
# 1. Click "Remind Me Later" → Check ~/.ami_update_postponed (count=1)
# 2. Restart AMI, click "Remind Me Later" again → (count=2)
# 3. Restart AMI, click "Remind Me Later" again → (count=3)
# 4. Restart AMI → Button should be disabled

# Reset counter
rm ~/.ami_update_postponed
```

#### Force Update Check

From Python console:

```python
import sys
sys.path.insert(0, 'src')

from updater import UpdateManager

updater = UpdateManager("1.0.0", "dgiovannetti/AMI")
update_info = updater.check_for_updates()

if update_info:
    print(f"New version: {update_info['version']}")
    print(f"URL: {update_info['download_url']}")
    print(f"Size: {update_info['size']} bytes")
```

### Versioning Guidelines

Use **Semantic Versioning**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., 1.x.x → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.0.x → 1.1.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 1.0.0 → 1.0.1)

Examples:
- Bug fix: `1.0.0` → `1.0.1`
- New feature: `1.0.1` → `1.1.0`
- Breaking change: `1.1.0` → `2.0.0`

### Release Checklist

- [ ] Version bumped in `config.json`
- [ ] Changelog updated
- [ ] All tests pass locally
- [ ] Committed and tagged
- [ ] GitHub Actions builds successful
- [ ] Release notes added to GitHub Release
- [ ] Checksums added to release notes
- [ ] Tested update from previous version
- [ ] Announced on website/social media

### Rollback Procedure

If an update has critical bugs:

1. **Yank the release** (mark as pre-release on GitHub)
2. **Create hotfix version** (e.g., 1.1.0 → 1.1.1)
3. **Release hotfix immediately**
4. Users on 1.1.0 will auto-update to 1.1.1

### Security Considerations

1. **Always use HTTPS** for downloads (GitHub enforces this)
2. **Include SHA256 checksums** in release notes
3. **Code sign executables** for production (optional but recommended)
4. **Test updates thoroughly** before releasing
5. **Keep old versions available** for emergency rollback

---

## 🔐 Code Signing (Production)

### Windows

Requires **Code Signing Certificate** ($50-300/year):

```bash
signtool sign /f certificate.pfx /p password /fd SHA256 \
  /t http://timestamp.digicert.com AMI.exe
```

### macOS

Requires **Apple Developer Account** ($99/year):

```bash
# Sign
codesign --force --sign "Developer ID Application: Your Name (TEAM_ID)" dist/AMI

# Notarize
xcrun notarytool submit dist/AMI-Package.zip \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password app-specific-password
```

---

## 📊 Update Analytics (Optional)

Track update success rate:

```python
# In updater.py, add telemetry
def report_update_result(from_version, to_version, success):
    requests.post('https://your-analytics.com/api/updates', json={
        'from': from_version,
        'to': to_version,
        'platform': sys.platform,
        'success': success,
        'timestamp': time.time()
    })
```

---

## 🐛 Troubleshooting

### "No updates available" but new release exists

- **Clear GitHub API cache**: Wait 5 minutes, retry
- **Check rate limit**: `curl https://api.github.com/rate_limit`
- **Verify repo URL** in config.json

### Update download fails

- **Check internet connection**
- **GitHub CDN issue**: Wait 10 minutes, retry
- **Manual download**: Get from https://github.com/dgiovannetti/AMI/releases

### Update installs but app doesn't restart

- **Windows**: Check `%TEMP%\ami_update\_update.bat` for errors
- **macOS**: Check `/tmp/ami_update/_update.sh` for errors
- **Manual restart**: Just double-click AMI executable

### Postponement counter stuck

```bash
# Reset counter manually
rm ~/.ami_update_postponed

# Or on Windows
del %USERPROFILE%\.ami_update_postponed
```

---

## 📚 Further Reading

- [OTA_UPDATE_SYSTEM.md](docs/OTA_UPDATE_SYSTEM.md) - Technical deep dive
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
- [Semantic Versioning](https://semver.org/)

---

**Keep AMI up to date** for the latest features, bug fixes, and security patches!

*"Sai se sei davvero online."*

© 2025 CiaoIM™ di Daniel Giovannetti
