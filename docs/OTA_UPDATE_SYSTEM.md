# AMI OTA Update System

## 📋 Overview

AMI includes a robust Over-The-Air (OTA) update system that automatically checks for new versions from GitHub Releases and installs them seamlessly.

## 🔑 Key Features

### 1. **Automatic Update Checks**
- Checks for updates on startup (configurable)
- Periodic checks every 24 hours (configurable)
- Manual check via tray menu: "Check for Updates"

### 2. **Forced Updates After 3 Postponements**
- Users can postpone an update up to **3 times**
- After 3 postponements, the update becomes **mandatory**
- Postponement counter is tracked locally in `~/.ami_update_postponed`

### 3. **Secure Downloads**
- Downloads updates directly from GitHub Releases
- Verifies SHA256 checksums (if provided in release notes)
- Platform-specific packages (Windows/macOS/Linux)

### 4. **Seamless Installation**
- Downloads update in background
- Replaces executable automatically
- Restarts application after installation
- No manual intervention required

### 5. **User-Friendly UI**
- Beautiful PyQt6 dialog with release notes
- Progress bar during download
- Clear postponement warnings
- Tray notifications

## 🔧 Configuration

Edit `config.json`:

```json
{
  "updates": {
    "enabled": true,
    "check_on_startup": true,
    "check_interval_hours": 24,
    "github_repo": "dgiovannetti/AMI",
    "max_postponements": 3,
    "notify_on_update": true
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable OTA updates |
| `check_on_startup` | boolean | `true` | Check for updates when app starts |
| `check_interval_hours` | integer | `24` | Hours between automatic checks |
| `github_repo` | string | `"dgiovannetti/AMI"` | GitHub repository to check |
| `max_postponements` | integer | `3` | Maximum times update can be postponed |
| `notify_on_update` | boolean | `true` | Show tray notification when update available |

## 📦 How It Works

### Update Flow

```
1. App starts → Check for updates (5s delay)
                    ↓
2. GitHub API call → Get latest release info
                    ↓
3. Version comparison → Is new version available?
                    ↓
4. If yes → Show update dialog with release notes
                    ↓
5. User chooses:
   - Install Now → Download & install → Restart
   - Remind Later → Increment postpone count
   - Close dialog → Same as "Remind Later"
                    ↓
6. If postponed 3 times → Next dialog has no "Remind Later" button
                    ↓
7. Update is mandatory → Must install
```

### Postponement Logic

```python
postpone_count = get_current_count()

if postpone_count < max_postponements (3):
    # Allow postponement
    show_button("Remind Me Later")
    remaining = 3 - postpone_count
    show_warning(f"You can postpone {remaining} more time(s)")
else:
    # Mandatory update
    hide_button("Remind Me Later")
    show_warning("This update is mandatory")
```

### Platform Detection

The updater automatically selects the correct package:

```python
if sys.platform == 'win32':
    # Download AMI-Windows.zip
    download_asset('AMI-Windows.zip')
    
elif sys.platform == 'darwin':
    # Download AMI-macOS.zip
    download_asset('AMI-macOS.zip')
    
elif sys.platform.startswith('linux'):
    # Download AMI-Linux.zip
    download_asset('AMI-Linux.zip')
```

## 🚀 For Developers

### Creating a Release

1. **Update version in `config.json`**:
   ```json
   {
     "app": {
       "version": "1.1.0"
     }
   }
   ```

2. **Commit and tag**:
   ```bash
   git add config.json
   git commit -m "Bump version to 1.1.0"
   git tag v1.1.0
   git push origin main --tags
   ```

3. **GitHub Actions automatically**:
   - Builds Windows and macOS packages
   - Creates ZIP archives
   - Uploads artifacts
   - Creates GitHub Release (if tagged)

4. **(Optional) Add checksums to release notes**:
   ```bash
   # Generate SHA256
   shasum -a 256 dist/AMI-Package.zip
   
   # Add to release notes
   SHA256: abc123def456...
   ```

### Release Notes Format

The updater shows release notes in the dialog. Use Markdown:

```markdown
## AMI 1.1.0

### 🎉 New Features
- Added automatic OTA updates
- Improved connection detection

### 🐛 Bug Fixes
- Fixed memory leak in dashboard
- Corrected macOS Gatekeeper instructions

### 📊 Performance
- Reduced polling interval to 1 second
- Optimized network checks

---

**SHA256 Checksums:**
- Windows: abc123...
- macOS: def456...
```

### Manual Release Creation

If not using GitHub Actions:

```bash
# Build for current platform
python build.py

# The package is in dist/AMI-Package.zip

# Create release on GitHub
gh release create v1.1.0 \
  dist/AMI-Package.zip \
  --title "AMI v1.1.0" \
  --notes "Release notes here..."
```

## 🔐 Security

### Checksum Verification

If SHA256 checksum is in release notes:

```python
# Updater automatically verifies
download_file(url)
if not verify_sha256(file, expected_checksum):
    raise SecurityError("Checksum mismatch!")
```

### HTTPS Only

All downloads use HTTPS from GitHub CDN:
```
https://github.com/dgiovannetti/AMI/releases/download/v1.1.0/AMI-Package.zip
```

### Code Signing (Optional)

For production, sign executables:

**Windows:**
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com AMI.exe
```

**macOS:**
```bash
codesign --force --sign "Developer ID Application" dist/AMI
xcrun notarytool submit dist/AMI-Package.zip --apple-id ... --password ...
```

## 🧪 Testing Updates

### Test with Different Versions

1. **Set current version low**:
   ```json
   {"app": {"version": "0.1.0"}}
   ```

2. **Create a test release on GitHub**:
   ```bash
   git tag v0.2.0-test
   git push origin v0.2.0-test
   ```

3. **Run AMI**:
   - Update dialog should appear
   - Test "Install Now" and "Remind Later"

4. **Test postponement limit**:
   - Click "Remind Later" 3 times
   - 4th time: button should be disabled

### Simulate Update Check

```python
# In Python console or test script
from updater import UpdateManager

updater = UpdateManager("1.0.0", "dgiovannetti/AMI")
update_info = updater.check_for_updates()

if update_info:
    print(f"New version: {update_info['version']}")
    print(f"Download URL: {update_info['download_url']}")
    print(f"Size: {update_info['size']} bytes")
```

### Reset Postponement Counter

```bash
# Remove postpone file
rm ~/.ami_update_postponed
```

## 📊 Update Analytics (Future)

Optional telemetry for update success rate:

```python
# Send anonymous update event
send_telemetry({
    'event': 'update_installed',
    'from_version': '1.0.0',
    'to_version': '1.1.0',
    'platform': 'darwin',
    'success': True
})
```

## 🐛 Troubleshooting

### Update Not Detected

1. **Check internet connection**
2. **Verify GitHub repo URL** in config.json
3. **Check GitHub API rate limits** (60 requests/hour for unauthenticated)
4. **View console output**:
   ```
   [UPDATE] Checking for updates...
   [UPDATE] New version available: 1.1.0
   ```

### Download Fails

- **Network issue**: Retry manually via tray menu
- **GitHub CDN down**: Wait and retry
- **Checksum mismatch**: File corrupted, retry download

### Installation Fails

**Windows:**
- Antivirus blocking: Add AMI to exclusions
- Permissions: Run as administrator

**macOS:**
- Gatekeeper blocking: `xattr -cr AMI`
- Permissions: `chmod +x AMI`

### App Doesn't Restart

- Update script issue
- Check temp folder: `/tmp/ami_update/` (macOS) or `%TEMP%\ami_update\` (Windows)
- Manually restart AMI

## 📝 Implementation Files

- **`src/updater.py`** - Core update logic and download manager
- **`src/update_dialog.py`** - PyQt6 UI for update notifications
- **`src/tray_app.py`** - Integration with main app
- **`config.json`** - Update configuration
- **`.github/workflows/build.yml`** - Automated release builds

## 🔄 Update Lifecycle

```
┌─────────────────┐
│   AMI Starts    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Check Updates  │◄─────── Every 24h
│   (5s delay)    │
└────────┬────────┘
         │
         ▼
   ┌────────────┐
   │  New Ver?  │───No───► Continue normally
   └─────┬──────┘
         │Yes
         ▼
┌─────────────────┐
│  Show Dialog    │
│  with Notes     │
└────────┬────────┘
         │
     ┌───┴────┐
     │ User   │
     │ Choice │
     └───┬────┘
         │
    ┌────┴────┐
    │         │
Postpone  Install
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ Count │ │ Download │
│  +1   │ │   ZIP    │
└───┬───┘ └────┬─────┘
    │          │
    │          ▼
    │    ┌──────────┐
    │    │  Verify  │
    │    │ Checksum │
    │    └────┬─────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │ Extract  │
    │    │ & Replace│
    │    └────┬─────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │ Restart  │
    │    │   AMI    │
    │    └──────────┘
    │
    ▼
┌─────────┐
│ Count   │
│ >= 3?   │
└───┬─────┘
    │
  Yes │
    │
    ▼
┌─────────┐
│Mandatory│
│ Update  │
└─────────┘
```

## 🎯 Best Practices

1. **Always test updates** on a separate machine first
2. **Include detailed release notes** for transparency
3. **Test rollback** if update fails
4. **Monitor update success rate** via telemetry
5. **Keep old versions available** on GitHub for manual downgrade
6. **Sign executables** for production releases
7. **Use semantic versioning**: `MAJOR.MINOR.PATCH`

---

**AMI OTA Update System** - Keeping your internet monitor up to date, automatically.

*"Sai se sei davvero online."*

© 2025 CiaoIM™ di Daniel Giovannetti
