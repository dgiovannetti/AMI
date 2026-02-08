# AMI v2.1.0 - Update Release

**"Sai se sei davvero online." / "Know if you're really online."**

---

## English

Update release with macOS improvements: compact status window, correct app name in Dock and menu bar, and native .app bundle.

### What's New in v2.1.0

**Compact Status Window (macOS)**
- New always-visible window with connection status and latency
- Useful when the menu bar icon is not visible
- Shows symbol (✓/!/✕) and latency in ms
- "Menu" button to access the main menu
- Enable/disable in Settings → UI

**Correct App Name on macOS**
- App now appears as **"AMI"** in Dock and menu bar (no longer "Python")
- macOS build produces a native `.app` bundle (AMI.app)
- Double-click AMI.app to launch

### Technical changes
- **config.json**: new option `ui.compact_status_window` (default: true on macOS)
- **AMI_app.spec**: CFBundleName and CFBundleDisplayName for correct name
- **build.py**: uses spec file on macOS to generate .app bundle

### Compatibility
- macOS: 10.14+ (Mojave or later), Apple Silicon + Intel
- Upgrade from v2.0.0: no migration required

---

## Italiano

Release update con miglioramenti per macOS: finestra compatta dello stato, nome dell'app corretto nella Dock e nel menu bar, e bundle .app nativo.

### Novità in v2.1.0

**Finestra compatta dello stato (macOS)**
- Nuova finestra sempre visibile con stato connessione e latenza
- Utile quando l'icona nella menu bar non è visibile
- Mostra simbolo (✓/!/✕) e ms di latenza
- Pulsante "Menu" per accedere al menu principale
- Attivabile/disattivabile da Impostazioni → UI

**Nome app corretto su macOS**
- L'app ora appare come **"AMI"** nella Dock e nel menu bar (non più "Python")
- Build macOS produce un bundle `.app` nativo (AMI.app)
- Doppio click su AMI.app per avviare

### Cambiamenti tecnici
- **config.json**: nuova opzione `ui.compact_status_window` (default: true su macOS)
- **AMI_app.spec**: CFBundleName e CFBundleDisplayName per nome corretto
- **build.py**: usa spec file su macOS per generare .app bundle

### Compatibilità
- macOS: 10.14+ (Mojave o successivo), Apple Silicon + Intel
- Upgrade da v2.0.0: nessuna migrazione richiesta

---

<p align="center">
  <strong>© 2025 CiaoIM™ by Daniel Giovannetti</strong>
</p>
