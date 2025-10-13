# AMI Quick Start Guide

## 🚀 Getting Started in 3 Minutes

### Step 1: Install Dependencies

```bash
# Navigate to the AMI directory
cd /path/to/AMI

# Run the installation script
python install.py
```

Or manually:
```bash
pip install -r requirements.txt
pip install Pillow  # For icon generation
```

### Step 2: Generate Icons

```bash
python tools/generate_icons.py
```

### Step 3: Run AMI

```bash
python AMI.py
```

The application will appear in your system tray!

---

## 🎯 For Windows Users (Executable)

### Build the Executable

```bash
# Install build dependencies
pip install -r requirements-build.txt

# Build the executable
python build.py
```

The executable will be created in `dist/AMI-Package/AMI.exe`

### Run the Executable

1. Navigate to `dist/AMI-Package/`
2. Double-click `AMI.exe`
3. Look for the AMI icon in your system tray (bottom-right)

---

## 📋 First Time Setup

### 1. Check the System Tray

After starting AMI, look for a colored circle icon in your system tray:
- 🟢 **Green** = Online
- 🟡 **Yellow** = Unstable
- 🔴 **Red** = Offline

### 2. Right-Click the Icon

Try these options:
- **Test Now** - Run an immediate connection test
- **Dashboard** - See detailed statistics and graphs
- **View Logs** - Check connection history

### 3. Customize Settings (Optional)

Edit `config.json` to customize:

```json
{
  "monitoring": {
    "polling_interval": 1,  // Check every 1 second (terminal-like speed)
    "ping_hosts": ["8.8.8.8", "1.1.1.1", "github.com"]
  },
  "notifications": {
    "enabled": true,
    "notify_on_disconnect": true,
    "notify_on_reconnect": true
  }
}
```

After editing, restart AMI.

---

## 🔧 Common Tasks

### Enable Auto-Start with Windows

**Option 1: Using config.json**
```json
{
  "startup": {
    "auto_start": true
  }
}
```

**Option 2: Manual shortcut**
1. Create a shortcut to `AMI.exe`
2. Press `Win + R`, type `shell:startup`, press Enter
3. Copy the shortcut to the Startup folder

### View Connection Logs

1. Right-click AMI tray icon
2. Select "View Logs"
3. Opens `ami_log.csv` with your default CSV viewer

### Change Polling Interval

Edit `config.json`:
```json
{
  "monitoring": {
    "polling_interval": 30  // Check every 30 seconds instead of 10
  }
}
```

### Enable API Server

Edit `config.json`:
```json
{
  "api": {
    "enabled": true,
    "port": 7212
  }
}
```

Then query status from any application:
```bash
curl http://localhost:7212/status
```

---

## ❓ Troubleshooting

### Icon doesn't appear
- Check Task Manager - is AMI.exe running?
- Try running as Administrator
- Check system tray overflow (click arrow in taskbar)

### Always shows offline
- Check firewall settings (allow AMI.exe)
- Try different ping hosts in config.json
- Some networks block ICMP - enable HTTP test

### High CPU usage
- Increase `polling_interval` in config.json
- Reduce number of `ping_hosts`
- Disable `enable_http_test`

### No notifications
- Check Windows notification settings
- Verify `notifications.enabled = true` in config.json
- Disable `silent_mode` if enabled

---

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [CHANGELOG.md](CHANGELOG.md) for version history
- Customize `config.json` for your network environment
- Build your own executable with `python build.py`

---

**"Sai se sei davvero online."**
