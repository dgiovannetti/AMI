# 🎉 AMI v2.0.0 - Public Release!

**"Sai se sei davvero online."**

AMI is now **publicly available** under Apache License 2.0! Complete redesign with modern UI, accessibility features, and professional polish.

---

## 🎨 Highlights

- ✨ **Modern Design**: Stripe/Vercel-inspired light theme with clean cards and subtle shadows
- ♿ **Accessible**: WCAG 2.1 compliant with colorblind-friendly symbols (✓, !, ✕)
- 📜 **Apache 2.0**: Free for commercial use with required attribution
- 🔍 **Enhanced Icons**: 512x512px tray icon with high contrast symbols
- 💎 **Professional UI**: Rounded corners, proper spacing, modern typography
- 🌍 **Cross-platform**: macOS and Windows support

---

## 📦 Installation

### macOS (Apple Silicon & Intel)

1. Download `AMI-macOS.zip` below
2. Extract the ZIP file
3. **Right-click** on `AMI` → **Open** (first time only)
4. Or use Terminal:
   ```bash
   xattr -cr AMI && chmod +x AMI && ./AMI
   ```
5. Application appears in menu bar

**Note**: See [MACOS_SECURITY.md](https://github.com/dgiovannetti/AMI/blob/main/MACOS_SECURITY.md) for Gatekeeper bypass details.

### Windows (64-bit)

⚠️ **Windows build coming soon!** Building on Windows machine now.

When available:
1. Download `AMI-Windows.zip`
2. Extract and run `AMI.exe`
3. Application appears in system tray

---

## ♿ Accessibility Features

All status indicators use **symbols + colors** for universal accessibility:

- **✓ Green** - Online (stable connection)
- **! Yellow** - Unstable (high latency or packet loss)
- **✕ Red** - Offline (no internet)

**Supported conditions:**
- Deuteranopia (red-green colorblindness)
- Protanopia (red-green colorblindness)
- Tritanopia (blue-yellow colorblindness)
- Achromatopsia (total colorblindness)

---

## 📜 License & Attribution

**Apache License 2.0** - Free for personal and commercial use.

### Commercial Use Requirements

If you use AMI in a commercial product, you **MUST** include attribution:

```
Powered by AMI (Active Monitor of Internet) by CiaoIM™
Developed by Daniel Giovannetti
https://github.com/dgiovannetti/AMI
```

Display in: About dialog, Credits section, Help docs, or Application footer.

See [NOTICE](https://github.com/dgiovannetti/AMI/blob/main/NOTICE) file for complete requirements and examples.

---

## 🚀 What's New in v2.0

### Complete UI Redesign
- Light modern theme (Stripe/Vercel-inspired)
- Clean cards with subtle shadows (8px border-radius)
- Tailwind-inspired color palette
- Professional typography and spacing
- Responsive layout that adapts to window size

### Accessibility
- WCAG 2.1 Level AA compliant
- Colorblind-friendly design with symbols
- High contrast icons (512x512px tray icon)
- Universal symbols (✓, !, ✕) alongside colors

### Technical
- ~1% CPU usage (idle)
- ~50MB RAM footprint
- Fast rendering with optimized PyQt6
- Smooth 60fps animations

---

## 📚 Documentation

- **README**: [Main documentation](https://github.com/dgiovannetti/AMI/blob/main/README.md)
- **Release Notes**: [Full v2.0.0 details](https://github.com/dgiovannetti/AMI/blob/main/RELEASE_NOTES_v2.0.0.md)
- **Build Guide**: [Windows build instructions](https://github.com/dgiovannetti/AMI/blob/main/BUILD_WINDOWS.md)
- **Contributing**: [Contribution guide](https://github.com/dgiovannetti/AMI/blob/main/CONTRIBUTING.md)

---

## 🐛 Known Issues

None reported yet. Please [open an issue](https://github.com/dgiovannetti/AMI/issues) if you encounter any problems.

---

## 🤝 Contributing

AMI is now **open for contributions**!

We welcome:
- 🐛 Bug reports and fixes
- ✨ Feature requests and implementations
- 🌍 Translations and localization
- 📚 Documentation improvements
- ♿ Accessibility enhancements

See [CONTRIBUTING.md](https://github.com/dgiovannetti/AMI/blob/main/CONTRIBUTING.md) for guidelines.

---

## 📊 Comparison with v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| **Theme** | Dark neon | Light modern |
| **Accessibility** | Colors only | Colors + symbols |
| **License** | MIT | Apache 2.0 |
| **Tray Icon** | 128x128px | 512x512px |
| **Dashboard** | Brutalist | Stripe-inspired |
| **WCAG** | No | 2.1 Level AA |
| **Status** | Private | Public |

---

## 🙏 Acknowledgments

- **Giovanni Calvario** - Original inspiration at 40° Convegno di Capri
- **Open Source Community** - PyQt6, matplotlib, requests, ping3
- **Accessibility Advocates** - WCAG guidelines and colorblind awareness

---

## 📧 Support

- 💬 **GitHub Issues**: [Report bugs or request features](https://github.com/dgiovannetti/AMI/issues)
- 📖 **Documentation**: Check README and docs folder
- 📊 **Logs**: Review `ami_log.csv` for diagnostics
- 🌟 **Star the repo** if you find AMI useful!

---

<p align="center">
  <strong>© 2025 CiaoIM™ by Daniel Giovannetti</strong><br>
  <a href="https://github.com/dgiovannetti/AMI">GitHub</a> | 
  <a href="https://ciaoim.tech/projects/ami">Website</a>
</p>
