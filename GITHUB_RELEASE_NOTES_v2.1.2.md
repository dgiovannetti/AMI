# 🎉 AMI v2.1.2 - Startup Performance Update

**"Sai se sei davvero online." / "Know if you're really online."**

---

## English

Performance and stability update: faster startup, splash screen fix, and build improvements.

### What's New in v2.1.2

**Faster Startup**
- Splash closes when first connection status is received (min 1.5s display)
- Onedir build: no extraction at runtime (faster subsequent launches)
- ISP/VPN info deferred to second check for quicker initial status
- Dashboard no longer opens by default on start (reduces matplotlib load)

**Stability**
- Fixed "chiusura inattesa" (unexpected closure) when closing splash screen
- Upx compression disabled for faster binary loading

### macOS Installation

1. Download `AMI-macOS.zip` or `AMI-macOS-Installer.dmg`
2. Extract and double-click `AMI.app`
3. If Gatekeeper blocks: right-click AMI.app → Open → Open

---

## Italiano

Aggiornamento prestazioni e stabilità: avvio più veloce, correzione splash e miglioramenti build.

### Novità in v2.1.2

**Avvio più veloce**
- Lo splash si chiude al primo status di connessione (min 1.5s)
- Build onedir: nessuna estrazione a runtime (avvii successivi più rapidi)
- Info ISP/VPN al secondo check per status iniziale più rapido
- Dashboard non si apre più di default all'avvio

**Stabilità**
- Corretto "chiusura inattesa" nella chiusura dello splash
- Compressione Upx disabilitata per caricamento più veloce

### Installazione macOS

1. Scarica `AMI-macOS.zip` o `AMI-macOS-Installer.dmg`
2. Estrai e apri `AMI.app` con doppio click
3. Se Gatekeeper blocca: tasto destro su AMI.app → Apri → Apri

---

## Documentation / Documentazione

- **Release Notes**: [v2.1.2 details](https://github.com/dgiovannetti/AMI/blob/main/RELEASE_NOTES_v2.1.2.md)
- **README**: [Main documentation](https://github.com/dgiovannetti/AMI/blob/main/README.md)
- **macOS Security**: [MACOS_SECURITY.md](https://github.com/dgiovannetti/AMI/blob/main/MACOS_SECURITY.md)

---

<p align="center">
  <strong>© 2025 CiaoIM™ by Daniel Giovannetti</strong><br>
  <a href="https://github.com/dgiovannetti/AMI">GitHub</a> | 
  <a href="https://ciaoim.tech/projects/ami">Website</a>
</p>
