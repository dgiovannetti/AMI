# AMI v2.0.0 Release Checklist

## ✅ Pre-Release (Completed)

- [x] Complete UI redesign to Stripe/Vercel-inspired theme
- [x] Add accessibility features (WCAG 2.1, colorblind-friendly)
- [x] Change license from MIT to Apache 2.0
- [x] Create NOTICE file with attribution requirements
- [x] Update README with new features and license info
- [x] Update index.html with modern design
- [x] Build macOS version (AMI-macOS.zip - 126MB)
- [x] Create release notes (RELEASE_NOTES_v2.0.0.md)
- [x] Create release script (create_release.sh)
- [x] Commit and push all changes to main branch

## 📦 macOS Build (Ready!)

**File:** `dist/AMI-macOS.zip` (126MB)
**Status:** ✅ Built and ready for release
**Location:** `/Users/dgiovannetti/Documents/GitHub/AMI/dist/AMI-macOS.zip`

### Contents:
- AMI executable (127MB)
- config.json
- README.md
- MACOS_SECURITY.md
- resources/ folder
- QUICK_START.txt

## 🪟 Windows Build (Required)

**Status:** ⚠️ Needs to be built on Windows machine

### Steps to Build on Windows:

1. **Clone repository on Windows:**
   ```cmd
   git clone https://github.com/dgiovannetti/AMI.git
   cd AMI
   ```

2. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   pip install -r requirements-build.txt
   ```

3. **Generate icons:**
   ```cmd
   python tools\generate_icons.py
   ```

4. **Build executable:**
   ```cmd
   python build.py
   ```

5. **Verify output:**
   ```cmd
   dir dist\
   ```
   Should see: `AMI-Windows.zip` (~100-130MB)

6. **Test executable:**
   ```cmd
   cd dist\AMI-Package
   AMI.exe
   ```

7. **Copy ZIP to macOS for release:**
   - Transfer `dist\AMI-Windows.zip` to macOS
   - Place in `/Users/dgiovannetti/Documents/GitHub/AMI/dist/`

## 🚀 Creating the GitHub Release

### Option 1: Automated Script (Recommended)

Once Windows build is ready:

```bash
cd /Users/dgiovannetti/Documents/GitHub/AMI

# Make sure both ZIPs are in dist/
ls -lh dist/AMI-*.zip

# Run release script
./create_release.sh
```

The script will:
- Create git tag `v2.0.0`
- Push tag to GitHub
- Create GitHub release
- Upload both macOS and Windows ZIPs
- Generate release notes

### Option 2: Manual GitHub Release

If you prefer manual creation:

1. **Go to GitHub:**
   https://github.com/dgiovannetti/AMI/releases/new

2. **Create tag:**
   - Tag: `v2.0.0`
   - Target: `main`

3. **Release title:**
   ```
   AMI v2.0.0 - Public Release 🎉
   ```

4. **Release description:**
   Copy from `RELEASE_NOTES_v2.0.0.md` or use this summary:
   ```markdown
   # 🎉 AMI v2.0.0 - Public Release!

   **"Sai se sei davvero online."**

   AMI is now publicly available under Apache License 2.0! Complete redesign with modern UI, accessibility features, and professional polish.

   ## 🎨 Highlights

   - **Modern Design**: Stripe/Vercel-inspired light theme
   - **Accessible**: WCAG 2.1 compliant with colorblind-friendly symbols (✓, !, ✕)
   - **Apache 2.0**: Free for commercial use with attribution
   - **Enhanced Icons**: 512x512px tray icon with high contrast
   - **Professional UI**: Clean cards, subtle shadows, rounded corners
   - **Cross-platform**: macOS and Windows support

   ## 📦 Downloads

   ### macOS (Apple Silicon & Intel)
   - Download `AMI-macOS.zip`
   - Extract and right-click → Open
   - Or: `xattr -cr AMI && chmod +x AMI && ./AMI`

   ### Windows (64-bit)
   - Download `AMI-Windows.zip`
   - Extract and run `AMI.exe`
   - Application appears in system tray

   ## 📜 License

   Apache 2.0 - Free for commercial use with required attribution to **CiaoIM™** and **Daniel Giovannetti**.

   See [NOTICE](https://github.com/dgiovannetti/AMI/blob/main/NOTICE) for attribution requirements.

   ---

   **© 2025 CiaoIM™ by Daniel Giovannetti**
   ```

5. **Upload files:**
   - Drag `dist/AMI-macOS.zip`
   - Drag `dist/AMI-Windows.zip`

6. **Publish release** ✅

## 📋 Post-Release Tasks

### Immediate
- [ ] Verify release is live on GitHub
- [ ] Test download links for both platforms
- [ ] Share release on social media
- [ ] Update website (if separate from GitHub Pages)

### Documentation
- [ ] Update any external documentation
- [ ] Add release to changelog
- [ ] Update version badges if needed

### Community
- [ ] Announce on relevant forums/communities
- [ ] Respond to issues/questions
- [ ] Monitor for bug reports

## 🔗 Important Links

- **Repository**: https://github.com/dgiovannetti/AMI
- **Releases**: https://github.com/dgiovannetti/AMI/releases
- **Issues**: https://github.com/dgiovannetti/AMI/issues
- **Website**: https://dgiovannetti.github.io/AMI/ (if enabled)

## 📊 Release Statistics

### macOS Build
- **Size**: 126MB (127MB executable)
- **Architecture**: Universal (Apple Silicon + Intel)
- **Python**: 3.11.8
- **PyQt6**: Latest
- **Build time**: ~2 minutes

### Windows Build (Expected)
- **Size**: ~100-130MB
- **Architecture**: x64
- **Python**: 3.8+
- **PyQt6**: Latest
- **Build time**: ~3-5 minutes

## ⚠️ Known Issues

None reported yet. Monitor GitHub Issues after release.

## 🎯 Success Criteria

Release is successful when:
- [x] All code changes committed and pushed
- [ ] Windows build completed
- [ ] GitHub release created with both ZIPs
- [ ] Downloads work on both platforms
- [ ] Applications launch without errors
- [ ] Tray icons appear correctly
- [ ] Dashboards display properly

## 📞 Support

If issues arise during release:
1. Check build logs for errors
2. Verify all dependencies are installed
3. Test executables locally before uploading
4. Review GitHub Actions logs (if using CI/CD)

---

**Ready to release AMI v2.0.0 to the world! 🚀**

**"Sai se sei davvero online."**

© 2025 CiaoIM™ by Daniel Giovannetti
