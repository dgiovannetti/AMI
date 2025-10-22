#!/bin/bash

# AMI v2.0.0 Release Creation Script
# This script helps create a GitHub release with all necessary files

set -e

VERSION="2.0.0"
TAG="v${VERSION}"
RELEASE_NAME="AMI v${VERSION} - Public Release 🎉"

echo "============================================"
echo "AMI v${VERSION} Release Creation"
echo "============================================"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "Install it with: brew install gh"
    echo "Or visit: https://cli.github.com/"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "❌ Not logged in to GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

# Check if dist files exist
if [ ! -f "dist/AMI-macOS.zip" ]; then
    echo "❌ macOS build not found: dist/AMI-macOS.zip"
    echo "Run: python build.py"
    exit 1
fi

echo "✅ macOS build found: dist/AMI-macOS.zip"
echo ""

# Check if Windows build exists
if [ ! -f "dist/AMI-Windows.zip" ]; then
    echo "⚠️  Windows build not found: dist/AMI-Windows.zip"
    echo "You'll need to build on Windows and add it manually"
    WINDOWS_BUILD=false
else
    echo "✅ Windows build found: dist/AMI-Windows.zip"
    WINDOWS_BUILD=true
fi
echo ""

# Create git tag
echo "Creating git tag: ${TAG}"
git tag -a "${TAG}" -m "AMI v${VERSION} - Public Release

- Complete UI redesign (Stripe/Vercel-inspired)
- Accessibility features (WCAG 2.1, colorblind-friendly)
- License change: MIT → Apache 2.0
- Enhanced tray icon (512x512px with symbols)
- Modern dashboard with clean cards
- Professional dialogs and settings
- Cross-platform support (macOS + Windows)

See RELEASE_NOTES_v${VERSION}.md for full details."

echo "✅ Git tag created"
echo ""

# Push tag
echo "Pushing tag to GitHub..."
git push origin "${TAG}"
echo "✅ Tag pushed"
echo ""

# Create release notes for GitHub
cat > /tmp/ami_release_notes.md << 'EOF'
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

## ♿ Accessibility

All status indicators use **symbols + colors**:
- ✓ **Green** - Online
- ! **Yellow** - Unstable  
- ✕ **Red** - Offline

Supports all types of colorblindness (deuteranopia, protanopia, tritanopia, achromatopsia).

## 📜 License

Apache 2.0 - Free for commercial use with required attribution to **CiaoIM™** and **Daniel Giovannetti**.

See [NOTICE](https://github.com/dgiovannetti/AMI/blob/main/NOTICE) for attribution requirements.

## 📚 Full Release Notes

See [RELEASE_NOTES_v2.0.0.md](https://github.com/dgiovannetti/AMI/blob/main/RELEASE_NOTES_v2.0.0.md) for complete details.

---

**© 2025 CiaoIM™ by Daniel Giovannetti**  
[GitHub](https://github.com/dgiovannetti/AMI) | [Website](https://dgiovannetti.github.io/AMI/)
EOF

# Create GitHub release
echo "Creating GitHub release..."
if [ "$WINDOWS_BUILD" = true ]; then
    gh release create "${TAG}" \
        --title "${RELEASE_NAME}" \
        --notes-file /tmp/ami_release_notes.md \
        dist/AMI-macOS.zip \
        dist/AMI-Windows.zip
else
    gh release create "${TAG}" \
        --title "${RELEASE_NAME}" \
        --notes-file /tmp/ami_release_notes.md \
        dist/AMI-macOS.zip
    
    echo ""
    echo "⚠️  Remember to add Windows build manually:"
    echo "   gh release upload ${TAG} dist/AMI-Windows.zip"
fi

echo ""
echo "============================================"
echo "✅ Release created successfully!"
echo "============================================"
echo ""
echo "View release: https://github.com/dgiovannetti/AMI/releases/tag/${TAG}"
echo ""
echo "Next steps:"
echo "1. Verify release on GitHub"
if [ "$WINDOWS_BUILD" = false ]; then
    echo "2. Build on Windows and upload AMI-Windows.zip"
    echo "3. Update website if needed"
else
    echo "2. Update website if needed"
fi
echo ""
