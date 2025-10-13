# AMI - Active Monitor of Internet
## Project Summary & Developer Guide

---

## 📊 Project Overview

**AMI** is a Windows desktop application that monitors internet connectivity in real-time, distinguishing between local network availability and actual internet access. Perfect for unstable connections like trains, mobile hotspots, or captive portals.

**Tagline:** "Sai se sei davvero online." (Know if you're really online)

**Version:** 1.0.0  
**License:** MIT  
**Language:** Python 3.8+  
**GUI Framework:** PyQt6  

---

## 🗂️ Complete Project Structure

```
AMI/
│
├── 📄 Core Configuration
│   ├── config.json              # Main configuration file
│   ├── requirements.txt         # Runtime dependencies
│   ├── requirements-build.txt   # Build dependencies
│   └── .gitignore              # Git ignore rules
│
├── 📚 Documentation
│   ├── README.md               # Main documentation
│   ├── QUICKSTART.md           # Quick start guide
│   ├── CHANGELOG.md            # Version history
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   ├── LICENSE                 # MIT License
│   ├── PROJECT_SUMMARY.md      # This file
│   └── .editorconfig          # Editor configuration
│
├── 🐍 Entry Points
│   ├── AMI.py                  # Main launcher (convenience)
│   ├── install.py              # Installation script
│   └── build.py                # Build script for .exe
│
├── 💻 Source Code (src/)
│   ├── __init__.py
│   ├── tray_app.py            # Main application & system tray
│   ├── network_monitor.py      # Network monitoring engine
│   ├── dashboard.py            # Dashboard window with graphs
│   ├── logger.py               # CSV event logging
│   ├── notifier.py             # Windows notifications
│   └── api_server.py           # Optional HTTP API
│
├── 🛠️ Tools (tools/)
│   ├── generate_icons.py       # Icon generator
│   └── startup_manager.py      # Windows auto-start manager
│
└── 🎨 Resources (resources/)
    ├── ami.ico                 # Windows icon
    ├── ami.png                 # Main icon
    ├── ami_logo.png            # Logo (512x512)
    ├── status_green.png        # Online status
    ├── status_yellow.png       # Unstable status
    └── status_red.png          # Offline status
```

---

## 🎯 Core Features Implementation

### 1. Network Monitoring (`network_monitor.py`)
- **Multi-host Ping**: Parallel ping tests to 3 configurable hosts
- **HTTP Verification**: Tests actual web connectivity
- **Local Network Detection**: Distinguishes local vs internet issues
- **Statistics Tracking**: Uptime, latency, success rates
- **Configurable Thresholds**: Define unstable connection criteria

**Key Classes:**
- `NetworkMonitor`: Main monitoring engine
- `PingResult`: Individual ping result data
- `ConnectionStatus`: Overall connection status

### 2. System Tray Application (`tray_app.py`)
- **Color-coded Icon**: Green/Yellow/Red status indicator
- **Context Menu**: Quick access to features
- **Background Monitoring**: Non-blocking checks every N seconds
- **Dashboard Integration**: Opens detailed view on demand

**Key Classes:**
- `SystemTrayApp`: Main application
- `MonitorThread`: Background monitoring thread

### 3. Dashboard (`dashboard.py`)
- **Real-time Statistics**: Current status, latency, uptime
- **Matplotlib Graphs**: Connection history visualization
- **Interactive Controls**: Manual refresh, reset stats
- **Auto-refresh**: Updates every 5 seconds

### 4. Event Logging (`logger.py`)
- **CSV Format**: Timestamp, status, latency, ping results
- **Automatic Rotation**: Prevents unlimited growth
- **Easy Export**: Standard CSV for analysis

### 5. Notifications (`notifier.py`)
- **Windows Toast**: Native Windows 10/11 notifications
- **Smart Triggering**: Only on state changes
- **Configurable**: Choose which events trigger alerts
- **Silent Mode**: Disable notifications but keep logging

### 6. HTTP API (`api_server.py`)
- **RESTful Endpoints**: `/status`, `/health`, `/stats`
- **Localhost Only**: Secure local access
- **JSON Responses**: Easy integration
- **Optional**: Disabled by default

---

## 🔧 Configuration Options

### `config.json` Structure

```json
{
  "app": {
    "name": "AMI",
    "subtitle": "Active Monitor of Internet",
    "version": "1.0.0"
  },
  "monitoring": {
    "ping_hosts": ["8.8.8.8", "1.1.1.1", "github.com"],
    "http_test_url": "https://www.google.com/generate_204",
    "polling_interval": 10,
    "timeout": 5,
    "retry_count": 2,
    "enable_http_test": true
  },
  "thresholds": {
    "unstable_latency_ms": 500,
    "unstable_loss_percent": 30
  },
  "notifications": {
    "enabled": true,
    "silent_mode": false,
    "notify_on_disconnect": true,
    "notify_on_reconnect": true,
    "notify_on_unstable": false
  },
  "logging": {
    "enabled": true,
    "log_file": "ami_log.csv",
    "max_log_size_mb": 10
  },
  "api": {
    "enabled": false,
    "port": 7212
  },
  "startup": {
    "auto_start": false
  },
  "ui": {
    "theme": "auto",
    "show_dashboard_on_start": false
  }
}
```

---

## 🚀 Build & Deployment

### Development Mode
```bash
python install.py    # Install dependencies
python AMI.py        # Run application
```

### Build Executable
```bash
python build.py      # Creates dist/AMI-Package/AMI.exe
```

**Build Process:**
1. Checks all dependencies
2. Generates icons
3. Runs PyInstaller with optimized settings
4. Creates distribution package
5. Generates ZIP archive

**Output:**
- `dist/AMI.exe` - Standalone executable
- `dist/AMI-Package/` - Complete package with config & docs
- `dist/AMI-Package.zip` - Distribution archive

---

## 🧪 Testing Checklist

Before release:
- [ ] System tray icon appears
- [ ] Icons change color based on status
- [ ] Tooltip shows correct information
- [ ] Menu items all functional
- [ ] Dashboard opens and displays data
- [ ] Graphs update in real-time
- [ ] Notifications appear on state change
- [ ] Log file created and populated
- [ ] API endpoints respond (if enabled)
- [ ] Executable builds successfully
- [ ] Config changes take effect after restart

---

## 📈 Performance Characteristics

- **CPU Usage**: < 1% (idle), 2-5% (during checks)
- **Memory**: ~50-80 MB (PyQt6 overhead)
- **Network**: Minimal (3 pings + 1 HTTP per interval)
- **Disk**: Log file grows ~1 KB per check
- **Startup Time**: 2-3 seconds

**Optimization Tips:**
- Increase polling interval for less frequent checks
- Reduce number of ping hosts
- Disable HTTP test if not needed
- Use compiled executable for faster startup

---

## 🔌 API Usage Examples

### Enable API
```json
{
  "api": {
    "enabled": true,
    "port": 7212
  }
}
```

### Query Status
```bash
# Get current status
curl http://localhost:7212/status

# Check health
curl http://localhost:7212/health

# Get statistics
curl http://localhost:7212/stats
```

### Response Example
```json
{
  "status": "online",
  "timestamp": "2025-10-10T12:25:05.123456",
  "avg_latency_ms": 25.5,
  "successful_pings": 3,
  "total_pings": 3,
  "local_network_ok": true,
  "internet_ok": true,
  "http_test_ok": true
}
```

---

## 🎨 Icon Customization

Icons are generated programmatically using PIL:

```bash
python tools/generate_icons.py
```

**Generated Files:**
- `ami.ico` - Multi-size Windows icon (16, 32, 48, 64, 128, 256px)
- `ami.png` - Main 256x256 icon
- `ami_logo.png` - 512x512 logo for about dialog
- `status_*.png` - Status indicators (64x64)

**Customization:**
Edit `tools/generate_icons.py` to change colors, style, or sizes.

---

## 🔐 Security Considerations

1. **Local API**: Only binds to 127.0.0.1 (localhost)
2. **No External Data**: All monitoring is outbound only
3. **No Credentials**: No sensitive data stored
4. **Log Privacy**: Logs contain only timestamps and network stats
5. **Firewall**: May require Windows Firewall exception for ICMP

---

## 🐛 Common Issues & Solutions

### Issue: Icon doesn't appear
**Solution:** 
- Check Task Manager for AMI process
- Run as Administrator
- Check system tray overflow area

### Issue: Always shows offline
**Solution:**
- Check firewall settings
- Try different ping hosts
- Enable HTTP test as fallback
- Some networks block ICMP entirely

### Issue: High CPU usage
**Solution:**
- Increase polling_interval to 30+ seconds
- Reduce ping_hosts to 1-2
- Disable enable_http_test

### Issue: Notifications don't work
**Solution:**
- Check Windows notification settings
- Verify notifications.enabled = true
- Check silent_mode = false
- Install windows-toasts or win10toast

---

## 🛣️ Roadmap

### Version 1.1 (Planned)
- [ ] Settings GUI (replace config.json editing)
- [ ] Dark/Light theme toggle
- [ ] Network speed test integration
- [ ] VPN detection

### Version 1.2 (Future)
- [ ] Telegram bot integration
- [ ] Multi-language support (i18n)
- [ ] macOS native support
- [ ] Linux compatibility

### Version 2.0 (Long-term)
- [ ] Network diagnostics tools
- [ ] Historical data analysis
- [ ] Custom alert rules engine
- [ ] Cloud sync for multi-device monitoring

---

## 📞 Support & Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Contributing**: See CONTRIBUTING.md

---

## 📜 License

MIT License - See LICENSE file for details

---

**AMI - Active Monitor of Internet**  
*"Sai se sei davvero online."*

Version 1.0.0 | © 2025 AMI Project
