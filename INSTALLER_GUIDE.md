# 📦 Guida Completa: Creare Installer per macOS e Windows

## 🎯 Obiettivo

Creare applicazioni standalone installabili/avviabili da un singolo file per:
- **macOS**: `.app` bundle (doppio click) + opzionale `.dmg` installer
- **Windows**: `.exe` standalone + opzionale installer NSIS

---

## 🍎 macOS - Applicazione .app

### Metodo 1: Build Attuale (Eseguibile Singolo)

**Cosa hai ora:**
```bash
python build.py
# Output: dist/AMI (127MB, eseguibile UNIX)
```

**Pro:** File singolo, no dipendenze
**Contro:** Non è un `.app`, richiede `xattr -cr`

### Metodo 2: Bundle .app (Raccomandato)

**Build:**
```bash
python build_macos_app.py
```

**Output:**
- `dist/AMI.app` - Vera applicazione macOS
- `dist/AMI-macOS-App.zip` - ZIP per distribuzione
- `dist/AMI-macOS-Installer.dmg` - Installer drag-and-drop (opzionale)

**Vantaggi:**
- ✅ Doppio click per avviare
- ✅ Appare come app in Finder
- ✅ Icona personalizzata
- ✅ Info.plist con metadati
- ✅ Può essere trascinata in /Applications

**Struttura .app:**
```
AMI.app/
├── Contents/
│   ├── Info.plist          # Metadati app
│   ├── MacOS/
│   │   └── AMI             # Eseguibile
│   └── Resources/
│       ├── ami.icns        # Icona
│       ├── config.json
│       └── resources/
```

### Creazione DMG Installer

Il DMG è un'immagine disco che permette drag-and-drop installation:

```bash
# Automatico con lo script
python build_macos_app.py
# Rispondi 'y' quando chiede di creare DMG

# Manuale
hdiutil create -volname "AMI" -srcfolder dist/AMI.app -ov -format UDZO dist/AMI-Installer.dmg
```

**Risultato:**
- Utente apre `AMI-Installer.dmg`
- Vede finestra con AMI.app e cartella Applications
- Trascina AMI.app in Applications
- Fatto! ✅

---

## 🪟 Windows - Applicazione .exe

### Metodo 1: Build Attuale (Eseguibile Singolo)

**Cosa hai ora:**
```cmd
python build.py
REM Output: dist\AMI.exe (100-130MB)
```

**Pro:** File singolo, no installazione
**Contro:** Windows Defender può bloccare, no auto-start

### Metodo 2: Installer NSIS (Professionale)

**Build:**
```cmd
python build_windows_installer.py
```

**Output:**
- `dist\AMI.exe` - Eseguibile standalone
- `dist\AMI-Windows.zip` - ZIP per distribuzione
- `AMI-Setup.exe` - Installer professionale (opzionale)

**Vantaggi Installer:**
- ✅ Installazione in Program Files
- ✅ Shortcut Desktop + Start Menu
- ✅ Auto-start con Windows (opzionale)
- ✅ Uninstaller nel Pannello di Controllo
- ✅ Firma digitale (se hai certificato)

**Cosa fa l'installer:**
1. Copia AMI.exe in `C:\Program Files\AMI\`
2. Crea shortcut Desktop
3. Crea voce Start Menu
4. Registra in "Programmi e Funzionalità"
5. Opzionalmente aggiunge a startup

---

## 📊 Confronto Metodi

### macOS

| Metodo | File | Dimensione | Installazione | Gatekeeper |
|--------|------|------------|---------------|------------|
| **Eseguibile** | AMI | 127MB | Nessuna | Richiede bypass |
| **.app Bundle** | AMI.app | 130MB | Drag to /Applications | Richiede bypass |
| **DMG Installer** | .dmg | 80MB (compresso) | Drag-and-drop | Richiede bypass |

### Windows

| Metodo | File | Dimensione | Installazione | Defender |
|--------|------|------------|---------------|----------|
| **Eseguibile** | AMI.exe | 100-130MB | Nessuna | Può bloccare |
| **ZIP Package** | .zip | 100MB | Estrai ed esegui | Può bloccare |
| **NSIS Installer** | Setup.exe | 50MB | Wizard guidato | Meno problemi |

---

## 🚀 Istruzioni Passo-Passo

### macOS: Creare .app + DMG

```bash
# 1. Installa dipendenze
pip install -r requirements.txt
pip install -r requirements-build.txt

# 2. Genera icone (se necessario)
python tools/generate_icons.py

# 3. Build .app
python build_macos_app.py

# 4. Test
open dist/AMI.app

# 5. Distribuisci
# - dist/AMI-macOS-App.zip (per download)
# - dist/AMI-macOS-Installer.dmg (per installazione)
```

### Windows: Creare .exe + Installer

```cmd
REM 1. Installa dipendenze
pip install -r requirements.txt
pip install -r requirements-build.txt

REM 2. Genera icone (se necessario)
python tools\generate_icons.py

REM 3. Build .exe
python build_windows_installer.py

REM 4. (Opzionale) Installa NSIS
REM Download da: https://nsis.sourceforge.io/

REM 5. Crea installer
makensis installer.nsi

REM 6. Test
dist\AMI.exe

REM 7. Distribuisci
REM - dist\AMI-Windows.zip (per download)
REM - AMI-Setup.exe (per installazione)
```

---

## 🔐 Firma Digitale (Raccomandato per Release)

### macOS: Code Signing

```bash
# Richiede Apple Developer Account ($99/anno)

# 1. Ottieni certificato da Apple Developer
# 2. Firma l'app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/AMI.app

# 3. Notarizza (per Gatekeeper)
xcrun notarytool submit dist/AMI-macOS-App.zip --apple-id your@email.com --password app-specific-password --team-id TEAMID

# 4. Staple ticket
xcrun stapler staple dist/AMI.app
```

**Vantaggi:**
- ✅ Nessun warning Gatekeeper
- ✅ Installazione senza `xattr -cr`
- ✅ Professionale e sicuro

### Windows: Code Signing

```cmd
REM Richiede certificato code signing (~$200-400/anno)

REM 1. Ottieni certificato da CA (DigiCert, Sectigo, etc.)
REM 2. Firma l'exe
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\AMI.exe

REM 3. Verifica
signtool verify /pa dist\AMI.exe
```

**Vantaggi:**
- ✅ Nessun warning Windows Defender
- ✅ SmartScreen non blocca
- ✅ Professionale e sicuro

---

## 📦 Distribuzione Finale

### Opzione 1: GitHub Releases (Attuale)

```
AMI v2.0.0
├── AMI-macOS.zip (127MB) - Eseguibile singolo
└── AMI-Windows.zip (100MB) - Eseguibile singolo
```

### Opzione 2: App Bundle + Installer (Professionale)

```
AMI v2.0.0
├── AMI-macOS-App.zip (130MB) - .app bundle
├── AMI-macOS-Installer.dmg (80MB) - DMG installer
├── AMI-Windows.zip (100MB) - .exe standalone
└── AMI-Setup.exe (50MB) - NSIS installer
```

### Opzione 3: Solo Installer (Più Semplice per Utenti)

```
AMI v2.0.0
├── AMI-macOS-Installer.dmg (80MB) - Drag-and-drop
└── AMI-Setup.exe (50MB) - Wizard installazione
```

---

## 🎯 Raccomandazione

### Per Release Pubblica v2.0.0:

**macOS:**
1. Usa `.app` bundle (più professionale)
2. Crea DMG per installazione facile
3. Considera code signing se hai budget

**Windows:**
1. Mantieni `.exe` standalone (funziona bene)
2. Aggiungi installer NSIS per utenti avanzati
3. Considera code signing per evitare Defender

### File da Distribuire:

```
Release v2.0.0:
├── AMI-macOS.zip          # .app bundle in ZIP
├── AMI-macOS.dmg          # Installer drag-and-drop
├── AMI-Windows.zip        # .exe standalone in ZIP
└── AMI-Setup.exe          # Installer Windows (opzionale)
```

---

## 🛠️ Script Pronti

Ho creato:
- `build_macos_app.py` - Build .app + DMG per macOS
- `build_windows_installer.py` - Build .exe + NSIS per Windows

Entrambi gestiscono automaticamente:
- Creazione bundle/package
- Icone e metadati
- ZIP per distribuzione
- Installer opzionali

---

## ❓ FAQ

**Q: Devo firmare le app?**
A: Non obbligatorio ma raccomandato per release pubblica. Senza firma, utenti devono bypassare security warnings.

**Q: Quanto costa la firma?**
A: macOS: $99/anno (Apple Developer), Windows: $200-400/anno (certificato code signing)

**Q: Posso creare DMG su Windows?**
A: No, DMG richiede macOS. Ma puoi creare .app su macOS e distribuire come ZIP.

**Q: NSIS è gratuito?**
A: Sì, NSIS è open source e gratuito.

**Q: Gli utenti preferiscono installer o standalone?**
A: Dipende:
- **Tecnici**: Preferiscono standalone (più controllo)
- **Utenti normali**: Preferiscono installer (più facile)
- **Soluzione**: Offri entrambi!

---

**Pronto per creare installer professionali!** 🚀

© 2025 CiaoIM™ by Daniel Giovannetti
