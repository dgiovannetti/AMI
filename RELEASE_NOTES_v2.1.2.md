# AMI v2.1.2 - Startup Performance Update

Release date: 2025-02-08

## Summary

Performance and stability update focused on faster startup and fixing the unexpected closure issue.

---

## What's New in v2.1.2

### Startup Performance

- **Splash close on first status**: Splash screen now closes when the first connection check completes (after minimum 1.5s display), instead of a fixed 3s wait
- **Onedir build**: PyInstaller now uses onedir mode instead of onefile — no extraction at runtime, faster subsequent launches
- **Deferred ISP/VPN**: First connection check skips ISP and VPN detection for quicker initial status display
- **Dashboard off by default**: `show_dashboard_on_start` now defaults to `false` — avoids heavy matplotlib import at startup

### Stability

- **Fixed "chiusura inattesa"**: Splash fade-out animation now defers close to next event loop tick to prevent crash when animation and widget destruction overlap
- **Upx disabled**: Disabled UPX compression for faster binary loading at runtime

---

## Technical Details

- Build: onedir (COLLECT) instead of onefile
- PyInstaller: upx=False
- Splash: QTimer.singleShot(0, self.close) in fade_out finished handler
- NetworkMonitor: ISP/VPN skipped when total_checks == 1

---

## Upgrade Notes

- No config migration needed
- To show dashboard on start: Settings → UI → enable "Show dashboard on start"
- Existing users: update will be offered via in-app updater

---

**© 2025 CiaoIM™ by Daniel Giovannetti**
