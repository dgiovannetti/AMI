# AMI - Cross-Platform Features

## 🌍 Platform Support

AMI is now **fully cross-platform** and works seamlessly on:
- **macOS** (Intel & Apple Silicon)
- **Windows** (x86-64)
- **Linux** (with GTK/Qt support)

---

## 🚦 System Tray Integration

### Semaphore Icon (Traffic Light)

AMI displays a **colored semaphore icon** in your system tray:

| Status | Color | Icon | Description |
|--------|-------|------|-------------|
| **🟢 Online** | Green | Emerald circle with WiFi | Connection is stable and working |
| **🟡 Unstable** | Yellow | Amber circle with WiFi | High latency or packet loss detected |
| **🔴 Offline** | Red | Red circle with WiFi | No internet connection |

### Location

- **Windows**: Bottom-right taskbar (notification area)
- **macOS**: Top-right menu bar
- **Linux**: System tray (varies by desktop environment)

---

## 📊 Dashboard Window

### Minimize to Tray

The dashboard **automatically minimizes to tray** instead of closing when:
- You click the **X** (close button)
- You click the **minimize** button
- You press `Cmd+W` (macOS) or `Alt+F4` (Windows)

### Restore Dashboard

**Three ways** to show/hide the dashboard:

1. **Double-click** the tray icon
2. **Right-click** tray icon → **📊 Dashboard**
3. **Single-click** tray icon (on some systems)

### Hide to Tray Button

A dedicated **⬇️ Hide to Tray** button in the dashboard allows manual hiding without closing.

---

## 🖱️ Tray Icon Interactions

### Left Click / Double Click
- **macOS**: Single click opens menu, double-click toggles dashboard
- **Windows**: Single click opens menu, double-click toggles dashboard
- **Linux**: Varies by desktop environment

### Right Click
Opens context menu with:
- **Status** (current connection state)
- **Latency** (ping time)
- **Uptime** (percentage and duration)
- **🔄 Test Now** (manual connection test)
- **📊 Dashboard** (show/hide dashboard)
- **⚙️ Settings** (configuration)
- **📄 View Logs** (open log file)
- **ℹ️ About** (app information)
- **❌ Exit** (quit application)

---

## 🎨 Icon Design

### High-DPI Support
Icons are rendered at **128x128** resolution for crisp display on:
- Retina displays (macOS)
- 4K/5K monitors
- High-DPI Windows displays

### Visibility Features
- **Outer glow**: Visible on dark backgrounds
- **Dark border**: Visible on light backgrounds
- **3D highlight**: Modern, polished look
- **WiFi symbol**: Clear connection indicator

---

## 🔄 Background Operation

AMI runs **completely in the background**:
- ✅ No taskbar window (unless dashboard is open)
- ✅ No dock icon (macOS, when dashboard is hidden)
- ✅ Minimal CPU usage (~0.1%)
- ✅ Low memory footprint (~50MB)

---

## 🚀 Startup Behavior

### Launch Options

1. **Silent Start** (default):
   - Shows splash screen (3 seconds)
   - Minimizes to tray
   - No dashboard window

2. **Dashboard on Start**:
   ```json
   // In config.json
   "ui": {
     "show_dashboard_on_start": true
   }
   ```

3. **Force Dashboard** (environment variable):
   ```bash
   # macOS/Linux
   AMI_FORCE_DASHBOARD=1 python AMI.py
   
   # Windows
   set AMI_FORCE_DASHBOARD=1
   python AMI.py
   ```

---

## 🛠️ Platform-Specific Notes

### Windows
- **Notification Area**: Icon appears in system tray (bottom-right)
- **Balloons**: Native Windows notifications for status changes
- **Registry**: No registry modifications required
- **Admin Rights**: Not needed (ping uses TCP fallback)

### macOS
- **Menu Bar**: Icon appears in top-right menu bar
- **Notifications**: Native macOS notification center
- **Dock**: No dock icon when dashboard is hidden
- **Permissions**: May request network access permission on first run

### Linux
- **Desktop Environments**: Tested on GNOME, KDE, XFCE
- **Tray Support**: Requires system tray extension (GNOME)
- **Notifications**: Uses libnotify (notify-send)

---

## 🎯 Usage Examples

### Typical Workflow

1. **Launch AMI**
   ```bash
   python AMI.py
   ```

2. **Check status** → Look at tray icon color

3. **View details** → Double-click tray icon

4. **Monitor graphs** → Dashboard shows real-time data

5. **Minimize** → Dashboard hides to tray, monitoring continues

6. **Exit** → Right-click tray → Exit

### Always Running

AMI is designed to **run 24/7** in the background:
- Monitors connection continuously
- Logs all events
- Shows notifications on status changes
- Ready to show dashboard anytime

---

## 📱 Notifications

### Status Change Alerts

AMI shows system notifications when:
- 🟢 **Connection restored** (offline → online)
- 🔴 **Connection lost** (online → offline)
- 🟡 **Connection degraded** (online → unstable)

### Notification Content

Example:
```
AMI - Connection Status
🟢 Connection Restored
Latency: 42ms | Uptime: 98.5%
```

---

## 💾 Data Persistence

All monitoring data is **preserved across restarts**:
- Connection history
- Statistics (total checks, uptime, etc.)
- Event logs
- Graph data

Location: `ami_log.csv` in application directory

---

## 🔧 Troubleshooting

### Tray Icon Not Visible

**Windows**:
- Check taskbar settings → "Select which icons appear on taskbar"
- Look in overflow area (^ icon)

**macOS**:
- Check if menu bar is hidden (System Preferences → Dock & Menu Bar)
- Try `Cmd+Drag` to rearrange icons

**Linux**:
- Install system tray extension (GNOME: TopIcons Plus)
- Check if tray is enabled in desktop settings

### Dashboard Won't Close

The dashboard **minimizes to tray** instead of closing - this is intentional!

To actually quit AMI:
1. Right-click tray icon
2. Click **❌ Exit**

---

## 🎨 Customization

### Icon Style

The traffic light icons are **generated programmatically** and match your system theme.

Future versions may support custom icon themes.

---

## 📄 Credits

**© 2025 CiaoIM™ di Daniel Giovannetti**
- Website: [ciaoim.tech](https://ciaoim.tech)
- Tagline: *"Crafted logic. Measured force. Front-end vision, compiled systems, and hardcoded ethics."*

**Inspiration**: Intuizione colta insieme a Giovanni C. in aliscafo per il 40° Convegno di Capri dei Giovani Imprenditori

---

**Enjoy AMI!** 🎉
