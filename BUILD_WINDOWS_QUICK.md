# 🪟 Build Windows - Guida Rapida (AMI **3.x**)

L’app attuale è in **`3.0/`**. Il vecchio build nella root (`python build.py` senza `cd 3.0`) è la linea 2.x.

## ⚡ Opzione A — Script automatico

Dalla root del repo:

```cmd
build_windows.bat
```

## ⚡ Opzione B — Comandi manuali

```cmd
git pull origin main

REM Icone (scrivono in resources\ alla root) — opzionale se già presenti
python tools\generate_icons.py

REM Build AMI 3.x
cd 3.0
pip install -r requirements.txt
pip install pyinstaller
python build.py
```

**Output:** `3.0\dist\AMI-Package\AMI.exe` (cartella onedir + `config.json`, `resources\`, ecc.)

Per uno **ZIP** da allegare a una release (stesso layout delle CI): comprimi la cartella `3.0\dist\AMI-Package` oppure usa l’artifact **AMI-3.0-Windows-ZIP** / workflow **Release AMI 3.0** su GitHub Actions.

## ✅ Verifica Build

```cmd
cd 3.0\dist\AMI-Package
AMI.exe
```

## 📦 File da Trasferire su Mac

- Cartella `3.0\dist\AMI-Package\` (o ZIP della cartella per release)

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
