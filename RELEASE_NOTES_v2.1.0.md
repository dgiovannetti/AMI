# AMI v2.1.0 - Update Release

**"Sai se sei davvero online."**

Release update con miglioramenti per macOS: finestra compatta dello stato, nome dell'app corretto nella Dock e nel menu bar, e bundle .app nativo.

---

## ✨ Novità in v2.1.0

### Finestra compatta dello stato (macOS)
- Nuova finestra sempre visibile con stato connessione e latenza
- Utile quando l'icona nella menu bar non è visibile
- Mostra simbolo (✓/!/✕) e ms di latenza
- Pulsante "Menu" per accedere al menu principale
- Attivabile/disattivabile da Impostazioni → UI

### Nome app corretto su macOS
- L'app ora appare come **"AMI"** nella Dock e nel menu bar (non più "Python")
- Build macOS produce un bundle `.app` nativo (AMI.app)
- Doppio click su AMI.app per avviare

### Build e distribuzione
- `build.py` su macOS crea automaticamente AMI.app
- QUICK_START aggiornato per istruzioni su AMI.app
- Package AMI-Package include AMI.app pronto per il drag su Applications

---

## 📦 Installazione

### macOS
1. Scarica `AMI-macOS.zip` (o `AMI-macOS-Installer.dmg` se disponibile)
2. Estrai e apri `AMI.app` con doppio click
3. Se Gatekeeper blocca: tasto destro su AMI.app → Apri → Apri
4. L'app appare nella Dock come "AMI"

---

## 🔧 Cambiamenti tecnici

- **config.json**: nuova opzione `ui.compact_status_window` (default: true su macOS)
- **AMI_app.spec**: CFBundleName e CFBundleDisplayName per nome corretto
- **build.py**: usa spec file su macOS per generare .app bundle

---

## 📋 Compatibilità

- macOS: 10.14+ (Mojave o successivo), Apple Silicon + Intel
- Upgrade da v2.0.0: nessuna migrazione richiesta
- Config esistenti rimangono valide

---

<p align="center">
  <strong>© 2025 CiaoIM™ by Daniel Giovannetti</strong>
</p>
