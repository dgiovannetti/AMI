# 📦 Publish Release v2.1.0 on GitHub / Pubblicare Release v2.1.0 su GitHub

## 1. Build (già fatto)

```bash
python build.py
```

Output: `dist/AMI-Package/AMI.app`, `dist/AMI-macOS.zip`, eventuale DMG

## 2. Commit e tag

```bash
git add .
git commit -m "Release v2.1.0 - Finestra compatta, nome AMI su macOS, bundle .app"
git tag v2.1.0
git push origin main
git push origin v2.1.0
```

## 3. Crea GitHub Release

1. Vai su: https://github.com/dgiovannetti/AMI/releases/new?tag=v2.1.0

2. **Title**: `AMI v2.1.0 - Update Release`

3. **Description**: copia da `GITHUB_RELEASE_NOTES_v2.1.0.md`

4. **Attach files**:
   - `dist/AMI-macOS.zip`
   - `dist/AMI-macOS-Installer.dmg` (se presente)

5. ✅ Spunta "Set as the latest release"

6. Clicca **Publish release**

---

**Release page**: https://github.com/dgiovannetti/AMI/releases/tag/v2.1.0
