# 🪟 Build AMI per Windows

## Requisiti

- **Windows 10/11** (64-bit)
- **Python 3.8+** installato
- **Git** (per clonare il repository)

---

## 🚀 Procedura Completa

### 1️⃣ Clona il Repository (se necessario)

```bash
# Clona da GitHub
git clone https://github.com/YOUR_USERNAME/AMI.git
cd AMI

# Oppure copia i file direttamente
```

### 2️⃣ Installa Dipendenze

Apri **PowerShell** o **CMD** nella cartella AMI:

```bash
# Installa dipendenze runtime
pip install -r requirements.txt

# Installa dipendenze build
pip install -r requirements-build.txt
```

### 3️⃣ Genera Icone

```bash
python tools\generate_icons.py
```

### 4️⃣ Build .exe

```bash
python build.py
```

Il processo richiede 2-5 minuti. Vedrai:
```
Checking requirements...
  ✓ PyQt6
  ✓ requests
  ✓ matplotlib
  ...
Building executable...
✓ Build successful!
```

---

## 📦 Output

Dopo il build troverai:

```
dist/
├── AMI.exe                    # Eseguibile principale (NON usare direttamente)
└── AMI-Package/               # 📦 Usa questa cartella
    ├── AMI.exe                # ✅ Eseguibile finale
    ├── config.json            # Configurazione
    ├── README.md              # Documentazione
    ├── resources/             # Icone
    └── QUICK_START.txt        # Guida rapida
```

**Importante:** Usa `AMI-Package\AMI.exe`, non quello nella root di `dist\`!

---

## ✅ Test dell'Eseguibile

```bash
# Vai nella cartella del package
cd dist\AMI-Package

# Esegui AMI
AMI.exe
```

Dopo qualche secondo:
- 🟢 L'icona apparirà nella **system tray** (in basso a destra)
- 📊 La **dashboard** si aprirà automaticamente

---

## 📤 Distribuzione

### Distribuisci il Package Completo

```bash
# Crea ZIP per distribuzione (fatto automaticamente)
dist\AMI-Package.zip
```

Oppure condividi l'intera cartella `AMI-Package\`.

### Cosa Include

- ✅ **AMI.exe** - Eseguibile standalone (nessuna dipendenza)
- ✅ **config.json** - Configurazione modificabile
- ✅ **README.md** - Documentazione completa
- ✅ **resources/** - Icone e asset

---

## 🔧 Troubleshooting

### "Windows Defender blocca AMI.exe"

È normale per eseguibili non firmati. Soluzioni:

1. **Click destro** su AMI.exe → **Proprietà**
2. Spunta **"Sblocca"** → **OK**
3. Oppure: Click **"Ulteriori informazioni"** → **"Esegui comunque"**

### "Python non trovato"

Installa Python da: https://www.python.org/downloads/

**Importante:** Spunta "Add Python to PATH" durante l'installazione!

### "PyInstaller fallisce"

```bash
# Reinstalla PyInstaller
pip uninstall pyinstaller
pip install pyinstaller==6.3.0
```

### "Errore di permessi"

Esegui **CMD/PowerShell come Amministratore**

---

## 🎯 Build Avanzato

### Personalizza l'Icona

Modifica `tools\generate_icons.py` e rigenera:

```bash
python tools\generate_icons.py
python build.py
```

### Build Senza Console (già configurato)

L'eseguibile usa `--windowed`, quindi **nessuna finestra console** apparirà.

### Build Multi-File (invece di singolo .exe)

Modifica `build.py`, cambia:
```python
'--onefile',  # Rimuovi questa riga
```

Questo creerà una cartella con più file (più veloce da avviare).

---

## 📊 Specifiche Build

- **Tipo:** Windowed (no console)
- **Modalità:** Onefile (singolo .exe)
- **Icona:** resources/ami.ico
- **Dimensione:** ~100-130 MB
- **Compatibilità:** Windows 10/11 (64-bit)

---

## 🎉 Build Completato!

Hai ora:
- ✅ **AMI.exe** funzionante
- ✅ **Standalone** (nessuna dipendenza)
- ✅ **Pronto per distribuzione**
- ✅ **Configurabile** via config.json

Per usare AMI:
1. Doppio click su `AMI.exe`
2. Cerca l'icona nella system tray
3. La dashboard si apre automaticamente

---

**"Sai se sei davvero online."**
