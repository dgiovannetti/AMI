# 🎉 AMI v2.1.0 - Update Release

**"Sai se sei davvero online."**

Update release con miglioramenti per macOS: finestra compatta dello stato, nome dell'app corretto nella Dock e nel menu bar, e bundle .app nativo.

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
- Package include AMI.app pronto per il drag su Applications

---

## 📦 Installazione macOS

1. Scarica `AMI-macOS.zip` (o `AMI-macOS-Installer.dmg` se disponibile)
2. Estrai e apri `AMI.app` con doppio click
3. Se Gatekeeper blocca: tasto destro su AMI.app → Apri → Apri
4. L'app appare nella Dock come "AMI"

---

## 📚 Documentazione

- **Release Notes**: [Dettagli v2.1.0](https://github.com/dgiovannetti/AMI/blob/main/RELEASE_NOTES_v2.1.0.md)
- **README**: [Documentazione principale](https://github.com/dgiovannetti/AMI/blob/main/README.md)
- **macOS Security**: [MACOS_SECURITY.md](https://github.com/dgiovannetti/AMI/blob/main/MACOS_SECURITY.md)

---

## 🐛 Known Issues

Nessuno segnalato. [Apri un issue](https://github.com/dgiovannetti/AMI/issues) se riscontri problemi.

---

<p align="center">
  <strong>© 2025 CiaoIM™ by Daniel Giovannetti</strong><br>
  <a href="https://github.com/dgiovannetti/AMI">GitHub</a> | 
  <a href="https://ciaoim.tech/projects/ami">Website</a>
</p>
