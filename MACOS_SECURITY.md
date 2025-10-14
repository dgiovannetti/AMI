# macOS Security & Gatekeeper Guide

## 🔒 "Apple non può verificare che AMI non contenga malware"

Questo messaggio è **normale** e **sicuro**. AMI non è firmato con un certificato Apple Developer ($99/anno), quindi macOS Gatekeeper lo blocca per precauzione.

**Nota:** AMI su macOS è un eseguibile UNIX (non un `.app` bundle), quindi appare come file generico in Finder.

## ✅ Soluzioni per aprire AMI

### Metodo 1: Click destro + Apri (Consigliato)

1. **NON fare doppio click** su `AMI` (l'eseguibile UNIX)
2. **Click destro** (o Ctrl+click) sul file
3. Seleziona **"Apri"** dal menu contestuale
4. Nel dialog che appare, clicca **"Apri"**
5. ✅ L'app si avvierà e macOS la ricorderà come "sicura"

**Questo bypass funziona solo la prima volta.** Dopo, puoi aprire AMI normalmente con doppio click.

---

### Metodo 2: Impostazioni di Sistema

1. Prova ad aprire `AMI` normalmente (verrà bloccato)
2. Apri **Impostazioni di Sistema**
3. Vai su **Privacy e Sicurezza**
4. Scorri in basso fino a vedere:
   > "AMI" è stato bloccato perché non proviene da uno sviluppatore identificato
5. Clicca **"Apri comunque"**
6. Conferma con **"Apri"**

---

### Metodo 3: Terminale (Avanzato)

Rimuovi l'attributo di quarantena da AMI:

```bash
# Vai nella directory dove hai estratto AMI
cd /path/to/AMI-Package

# Rimuovi quarantena dall'eseguibile
xattr -cr AMI

# Rendi eseguibile (se necessario)
chmod +x AMI

# Avvia l'app
./AMI
```

**Cosa fa questo comando:**
- `xattr -cr`: Rimuove gli attributi estesi (extended attributes) di quarantena
- `chmod +x`: Assicura che il file sia eseguibile
- `./AMI`: Esegue l'applicazione

---

## 🔍 Perché succede?

### Gatekeeper di macOS

macOS **Gatekeeper** blocca le app che:
1. Non provengono dal Mac App Store
2. Non sono firmate con un certificato **Developer ID**

AMI è **open source** e distribuito su GitHub. Puoi:
- ✅ Verificare il codice sorgente su https://github.com/dgiovannetti/AMI
- ✅ Buildare l'app da solo con `python build.py`
- ✅ Ispezionare ogni file prima di eseguirlo

### È sicuro?

**Sì, AMI è sicuro:**
- ✅ **Open source** - codice completamente ispezionabile
- ✅ **MIT License** - trasparente e auditabile
- ✅ **No telemetria** - nessun dato inviato a server esterni
- ✅ **No network shady** - solo ping ICMP e HTTP test verso host configurabili
- ✅ **No privilegi root** - AMI NON richiede sudo

**Cosa fa AMI:**
- Ping a host configurabili (default: 8.8.8.8, 1.1.1.1, github.com)
- HTTP request a Google per verificare accesso web
- Legge/scrive `config.json` e `ami_log.csv` localmente
- Mostra notifiche di sistema native

**Cosa NON fa:**
- ❌ Non raccoglie dati personali
- ❌ Non si connette a server di terze parti (eccetto i test configurati)
- ❌ Non modifica file di sistema
- ❌ Non richiede permessi elevati

---

## 🛡️ Per sviluppatori: Code Signing

Se vuoi distribuire AMI senza il warning di Gatekeeper, devi firmarlo.

### Requisiti

1. **Apple Developer Account** ($99/anno)
   - Iscriviti su https://developer.apple.com
   
2. **Developer ID Application Certificate**
   - Scarica da Apple Developer Portal
   - Installa in Keychain Access

### Firma l'app

```bash
# Dopo aver buildato con PyInstaller
codesign --force --sign "Developer ID Application: Your Name (TEAM_ID)" dist/AMI

# Verifica la firma
codesign --verify --verbose dist/AMI

# Notarize (opzionale ma consigliato)
xcrun notarytool submit dist/AMI-Package.zip \
  --apple-id your-email@example.com \
  --team-id YOUR_TEAM_ID \
  --password APP_SPECIFIC_PASSWORD
```

### Automatizzare con GitHub Actions

Aggiungi secrets al repository:
- `APPLE_DEVELOPER_ID`: Il tuo certificato (base64)
- `APPLE_TEAM_ID`: Il tuo Team ID
- `APPLE_ID`: La tua Apple ID
- `APPLE_PASSWORD`: App-specific password

Modifica `.github/workflows/build.yml`:

```yaml
- name: Sign macOS app
  if: runner.os == 'macOS'
  run: |
    echo ${{ secrets.APPLE_DEVELOPER_ID }} | base64 --decode > certificate.p12
    security create-keychain -p actions build.keychain
    security import certificate.p12 -k build.keychain -P "" -T /usr/bin/codesign
    security set-key-partition-list -S apple-tool:,apple: -s -k actions build.keychain
    codesign --force --sign "Developer ID Application" dist/AMI
```

---

## 📚 Risorse aggiuntive

- [Apple Developer - Code Signing](https://developer.apple.com/support/code-signing/)
- [Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Gatekeeper FAQ](https://support.apple.com/en-us/HT202491)

---

## 🆘 Troubleshooting

### "L'app è danneggiata e non può essere aperta"

Questo succede se l'attributo di quarantena è corrotto:

```bash
xattr -cr /path/to/AMI-Package/AMI
```

### "AMI" non può essere aperto perché lo sviluppatore non può essere verificato

Usa il Metodo 1 (click destro + Apri) descritto sopra.

### L'app non appare nel menu bar

1. Controlla Activity Monitor - cerca "AMI"
2. Se è in esecuzione ma non visibile:
   - Verifica che le preferenze di sistema permettano icone nel menu bar
   - Riavvia l'app
3. Controlla i log in Console.app per errori

### Permessi richiesti

AMI potrebbe richiedere permessi per:
- ✅ **Network** - per ping e HTTP test (automatico)
- ⚠️ **Notifiche** - per toast (chiederà al primo avvio)

**Non richiede:**
- ❌ Accesso completo al disco
- ❌ Accessibilità
- ❌ Registrazione schermo
- ❌ Microfono/Camera

---

**AMI è open source e sicuro. Il warning di Gatekeeper è una precauzione standard di macOS per app distribuite fuori dal Mac App Store.**

*"Sai se sei davvero online."*

© 2025 CiaoIM™ di Daniel Giovannetti
