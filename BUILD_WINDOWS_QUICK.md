# 🪟 Build Windows - Guida Rapida

## ⚡ Comandi Veloci

### Su Windows (PowerShell o CMD):

```cmd
# 1. Clona/Aggiorna repository
git pull origin main

# 2. Installa dipendenze (se necessario)
pip install -r requirements.txt
pip install -r requirements-build.txt

# 3. Genera icone (se necessario)
python tools\generate_icons.py

# 4. BUILD!
python build.py

# Output: dist\AMI-Windows.zip (100-130MB)
```

## ✅ Verifica Build

```cmd
# Test eseguibile
cd dist\AMI-Package
AMI.exe

# Dovrebbe:
# - Apparire icona in system tray
# - Aprire dashboard
# - Mostrare versione 2.0.0
```

## 📦 File da Trasferire su Mac

Dopo il build, trasferisci su Mac:
- `dist\AMI-Windows.zip` (per release)

## 🔍 Checksum

Dopo il trasferimento su Mac, calcola SHA256:
```bash
shasum -a 256 dist/AMI-Windows.zip
```

## 📊 Specifiche Build

- **Python**: 3.8+
- **Dimensione attesa**: 100-130 MB
- **Versione**: 2.0.0
- **Architettura**: x64
- **Tipo**: Windowed (no console)

## ⚠️ Troubleshooting

### "Windows Defender blocca"
Normale per exe non firmati. Click "Ulteriori informazioni" → "Esegui comunque"

### "PyInstaller non trovato"
```cmd
pip install pyinstaller==6.3.0
```

### "Errore import PyQt6"
```cmd
pip install PyQt6
```

## 🎯 Dopo il Build

1. ✅ Testa `AMI.exe` su Windows
2. ✅ Verifica versione 2.0.0 (non deve chiedere aggiornamenti)
3. ✅ Trasferisci `AMI-Windows.zip` su Mac
4. ✅ Calcola checksum
5. ✅ Pronto per release!

---

**Tempo stimato**: 3-5 minuti

**© 2025 CiaoIM™ by Daniel Giovannetti**
