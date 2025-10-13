# 🪟 Come Creare AMI.exe per Windows

Ci sono **3 modi** per ottenere l'eseguibile Windows di AMI:

---

## 🎯 Metodo 1: Build Manuale su Windows (Raccomandato)

### Requisiti
- Windows 10/11
- Python 3.8+ ([Download](https://www.python.org/downloads/))
- Git (opzionale)

### Procedura

#### 1. Ottieni il codice

**Opzione A - Con Git:**
```bash
git clone https://github.com/YOUR_USERNAME/AMI.git
cd AMI
```

**Opzione B - Senza Git:**
1. Scarica lo ZIP del repository
2. Estrai in una cartella
3. Apri PowerShell/CMD in quella cartella

#### 2. Build Automatico (Facile)

Doppio click su:
```
build_windows.bat
```

Oppure da PowerShell:
```bash
.\build_windows.bat
```

#### 3. Build Manuale (se preferisci)

```bash
# Installa dipendenze
pip install -r requirements.txt
pip install -r requirements-build.txt

# Genera icone
python tools\generate_icons.py

# Build exe
python build.py
```

### ✅ Risultato

Troverai l'eseguibile in:
```
dist\AMI-Package\AMI.exe
```

**Dimensione:** ~100-130 MB  
**Tipo:** Standalone (nessuna dipendenza richiesta)

---

## 🚀 Metodo 2: GitHub Actions (Build Automatico Cloud)

Se fai il push su GitHub, il build avviene automaticamente!

### Setup (Una Volta Sola)

1. **Fai Push del Codice su GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Il Build Parte Automaticamente:**
   - Vai su **GitHub** → **Actions**
   - Vedrai il workflow "Build AMI" in esecuzione
   - Aspetta 5-10 minuti

3. **Scarica l'Eseguibile:**
   - Nella pagina Actions
   - Click sul build completato
   - **Download artifact** → `AMI-Windows.zip`

### Build con Release Tag

Per creare una release:

```bash
# Crea un tag versione
git tag v1.0.0
git push origin v1.0.0
```

GitHub creerà automaticamente una **Release** con l'exe allegato!

---

## 💻 Metodo 3: Macchina Virtuale Windows

Se sei su Mac/Linux ma vuoi buildare localmente:

### Con VirtualBox/VMware/Parallels

1. Installa Windows 10/11 in VM
2. Installa Python in Windows
3. Copia i file AMI nella VM
4. Esegui `build_windows.bat`
5. Copia l'exe fuori dalla VM

### Con Wine (Non Raccomandato)

PyInstaller con Wine non funziona bene, sconsigliato.

---

## 📦 Distribuzione dell'Exe

### Cosa Distribuire

```
AMI-Package/          # Tutta questa cartella
├── AMI.exe           # Eseguibile
├── config.json       # Configurazione
├── README.md         # Documentazione
├── resources/        # Icone (opzionale se embedded)
└── QUICK_START.txt   # Guida rapida
```

### Crea ZIP Distribuzione

```bash
# Su Windows
Compress-Archive -Path dist\AMI-Package\* -DestinationPath AMI-v1.0.0.zip
```

Oppure usa il file già creato:
```
dist\AMI-Package.zip
```

---

## 🔒 Windows Defender / SmartScreen

### Problema Comune

Windows potrebbe bloccare l'exe perché **non è firmato digitalmente**.

### Soluzioni

**Per Utenti Finali:**

1. Click **"Ulteriori informazioni"**
2. Click **"Esegui comunque"**

**Per Sviluppatori (Firmare l'Exe):**

Acquista un certificato code-signing da:
- DigiCert
- Sectigo
- GlobalSign

Poi firma con:
```bash
signtool sign /f certificate.pfx /p password AMI.exe
```

**Alternativa Gratuita:**

Distribuisci tramite **Microsoft Store** (firma automatica)

---

## 🎨 Personalizzazione

### Cambia Icona

Modifica `tools/generate_icons.py`:

```python
# Cambia i colori
colors = {
    'green': (0, 255, 0),    # Più brillante
    'yellow': (255, 255, 0),  # Giallo puro
    'red': (255, 50, 50)      # Rosso chiaro
}
```

Rigenera:
```bash
python tools\generate_icons.py
python build.py
```

### Cambia Configurazione Default

Modifica `config.json` prima del build:

```json
{
  "monitoring": {
    "polling_interval": 5,  // Check più frequenti
    "ping_hosts": ["8.8.8.8", "1.1.1.1", "mio-server.com"]
  }
}
```

---

## 🐛 Troubleshooting

### "PyInstaller non trovato"

```bash
pip install pyinstaller==6.3.0
```

### "Build fallisce con errori"

```bash
# Reinstalla tutto
pip uninstall -y PyQt6 matplotlib numpy requests
pip install -r requirements.txt
pip install -r requirements-build.txt
python build.py
```

### "Exe si blocca all'avvio"

Esegui da CMD per vedere gli errori:
```bash
cd dist\AMI-Package
AMI.exe
```

Se vedi errori, controlla:
- `config.json` è presente?
- Permessi di esecuzione?
- Antivirus interferisce?

### "Dimensione exe troppo grande"

Normale, PyQt6 + matplotlib sono pesanti (~100 MB).

Per ridurre:
- Usa build multi-file (più veloce)
- Rimuovi dipendenze non usate
- Usa UPX compression (risky)

---

## 📊 Confronto Metodi

| Metodo | Pro | Contro | Tempo |
|--------|-----|--------|-------|
| **Build Manuale** | Pieno controllo, locale | Serve Windows | 5-10 min |
| **GitHub Actions** | Automatico, cloud | Serve repo GitHub | 10-15 min |
| **VM** | Flessibile | Più complesso | 15-30 min |

---

## ✅ Checklist Pre-Build

- [ ] Python 3.8+ installato
- [ ] `pip install -r requirements.txt` completato
- [ ] `pip install -r requirements-build.txt` completato
- [ ] Icone generate (`python tools\generate_icons.py`)
- [ ] `config.json` personalizzato (opzionale)

## ✅ Checklist Post-Build

- [ ] File `dist\AMI-Package\AMI.exe` esiste
- [ ] Test: doppio click su `AMI.exe`
- [ ] Icona appare nella system tray
- [ ] Dashboard si apre automaticamente
- [ ] Notifiche funzionano
- [ ] Log file creato (`ami_log.csv`)

---

## 🎉 Build Completato!

Hai ora un **eseguibile Windows standalone** di AMI!

### Cosa Puoi Fare

- ✅ Distribuire agli utenti finali
- ✅ Installare su più PC senza Python
- ✅ Pubblicare su GitHub Releases
- ✅ Condividere lo ZIP

### Next Steps

1. Testa l'exe su diverse versioni Windows
2. Raccolta feedback utenti
3. Pubblica su GitHub Releases
4. (Opzionale) Firma digitalmente

---

**"Sai se sei davvero online."**

Per supporto: https://github.com/YOUR_USERNAME/AMI/issues
