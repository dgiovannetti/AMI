# AMI v2.0.0 - Public Release 🎉

**Release Date:** October 22, 2025

**"Sai se sei davvero online."**

---

## 🎊 Major Milestone: Public Release!

AMI is now **publicly available** under the Apache License 2.0! This is a complete redesign from the ground up with modern UI, accessibility features, and professional polish.

---

## 🎨 Complete UI Redesign

### Modern, Clean Interface
- **Stripe/Vercel-inspired design** - Professional, clean aesthetic
- **Light theme** with Tailwind-inspired color palette
- **Subtle shadows** and rounded corners (8-12px border-radius)
- **Proper spacing** and typography hierarchy
- **Responsive layout** that adapts to window size

### Design System
- **Background**: `#F9FAFB` (Gray-50)
- **Surface**: `#FFFFFF` (White)
- **Primary**: `#3B82F6` (Blue-500)
- **Success**: `#10B981` (Green-500)
- **Warning**: `#F59E0B` (Amber-500)
- **Error**: `#EF4444` (Red-500)

### Components Rebuilt
- ✅ **Dashboard** - Clean cards with real-time graphs
- ✅ **Update Dialog** - Modern with emoji icons
- ✅ **Settings Dialog** - Professional tabs and inputs
- ✅ **Tray Icon** - Large, accessible with symbols
- ✅ **Compact Mode** - Minimal, centered layout
- ✅ **Charts** - Light backgrounds with clear labels

---

## ♿ Accessibility Features (WCAG 2.1 Compliant)

### Colorblind-Friendly Design
All status indicators now use **symbols + colors**:
- **✓ Green** - Online (checkmark)
- **! Yellow** - Unstable (exclamation)
- **✕ Red** - Offline (X mark)

### Supported Conditions
- Deuteranopia (red-green colorblindness)
- Protanopia (red-green colorblindness)
- Tritanopia (blue-yellow colorblindness)
- Achromatopsia (total colorblindness)

### Implementation
- **Tray icon**: 512x512px with large white symbols
- **Dashboard cards**: Symbols in status text
- **Compact mode**: Large symbols (72pt)
- **High contrast**: Strong text/background ratios

---

## 📜 License: Apache 2.0

### Why Apache 2.0?
- ✅ **Requires attribution** for commercial use
- ✅ **Grants patent rights** (protects users)
- ✅ **Allows commercial use** (business-friendly)
- ✅ **Permits modification** (fork-friendly)
- ✅ **Industry standard** (Android, Kubernetes, Apache)

### Commercial Use Requirements
If you use AMI commercially, you **MUST** include:
```
Powered by AMI (Active Monitor of Internet) by CiaoIM™
Developed by Daniel Giovannetti
https://github.com/dgiovannetti/AMI
```

See [NOTICE](NOTICE) file for complete requirements.

---

## 🚀 New Features

### Enhanced Tray Icon
- **Huge size**: 512x512px for maximum visibility
- **Accessible symbols**: ✓, !, ✕ in white on colored circle
- **High contrast**: Visible on any background

### Modern Dashboard
- **Stat cards** with proper layout and spacing
- **Real-time graphs** with light theme
- **Responsive grid** (1-4 columns based on width)
- **Compact mode** for small windows (<720px width)

### Professional Dialogs
- **Update dialog**: Clean with emoji icons and info boxes
- **Settings dialog**: Tabbed interface with live apply
- **Rounded corners**: 8px border-radius throughout
- **Subtle borders**: 1px solid `#E5E7EB`

---

## 🔧 Technical Improvements

### Performance
- **~1% CPU** usage (idle)
- **~50MB RAM** footprint
- **Fast rendering** with optimized PyQt6
- **Smooth animations** at 60fps

### Code Quality
- **Clean separation** of concerns
- **Modern Python** 3.8+ features
- **Type hints** where applicable
- **Comprehensive error handling**

### Build System
- **PyInstaller** for cross-platform builds
- **Automatic icon generation**
- **ZIP packaging** for easy distribution
- **Code signing** support (macOS)

---

## 📦 Installation

### macOS
1. Download `AMI-macOS.zip`
2. Extract and right-click `AMI` → Open
3. Or use Terminal: `xattr -cr AMI && chmod +x AMI && ./AMI`

### Windows
1. Download `AMI-Windows.zip`
2. Extract and run `AMI.exe`
3. Application appears in system tray

---

## 🐛 Bug Fixes

- ✅ Fixed dashboard layout issues
- ✅ Fixed card value display
- ✅ Fixed graph rendering on light backgrounds
- ✅ Fixed spacing inconsistencies
- ✅ Fixed tray icon size on high-DPI displays
- ✅ Fixed compact mode layout

---

## 📚 Documentation

### New Files
- **NOTICE** - Attribution requirements for commercial use
- **LICENSE** - Apache 2.0 full text
- **RELEASE_NOTES_v2.0.0.md** - This file

### Updated Files
- **README.md** - Complete rewrite with new features
- **index.html** - Modern light theme website
- **MACOS_SECURITY.md** - Gatekeeper bypass instructions

---

## 🙏 Acknowledgments

Special thanks to:
- **Giovanni Calvario** - For the original inspiration during the 40° Convegno di Capri
- **Open source community** - For PyQt6, matplotlib, requests, ping3
- **Accessibility advocates** - For WCAG guidelines and colorblind awareness

---

## 🔮 Future Plans

- 🌍 **Localization** - Multi-language support
- 📱 **Mobile companion** - iOS/Android app
- 🔔 **Advanced notifications** - Slack, Discord, email
- 📈 **Analytics** - Historical data visualization
- ⚙️ **Plugins** - Extensible architecture
- 🎨 **Themes** - Dark mode option

---

## 📧 Support & Contributing

- **GitHub Issues**: [Report bugs](https://github.com/dgiovannetti/AMI/issues)
- **Pull Requests**: Contributions welcome!
- **Documentation**: Check README and docs folder
- **Star the repo**: If you find AMI useful! ⭐

---

## 📝 License

```
Copyright 2025 CiaoIM™ by Daniel Giovannetti

Licensed under the Apache License, Version 2.0
See LICENSE file for details
See NOTICE file for attribution requirements
```

---

<p align="center">
  <strong>AMI v2.0.0 - Active Monitor of Internet</strong><br>
  "Sai se sei davvero online."<br>
  <br>
  © 2025 CiaoIM™ by Daniel Giovannetti<br>
  <a href="https://github.com/dgiovannetti/AMI">https://github.com/dgiovannetti/AMI</a>
</p>
