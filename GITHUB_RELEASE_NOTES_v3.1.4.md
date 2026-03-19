# AMI v3.1.4 — *Sai se sei davvero online.*

<p align="center">
  <strong>Branding refresh · GitHub pulse · landing &amp; OTA</strong>
</p>

---

## English

**AMI 3.1.4** polishes presentation (copyright 2025–2026, footer links, live GitHub stars on the dashboard) while keeping the same monitoring core (ping + HTTP, LAN vs internet, speed test, themes).

### Highlights

| | |
| --- | --- |
| **© 2025–2026** | Copyright range in defaults, About, LICENSE/NOTICE, and docs. |
| **Landing** | Pagina progetto: [`index.html`](https://github.com/dgiovannetti/AMI/blob/main/index.html) nel repo (es. GitHub Pages se abilitato). |
| **GitHub stars** | Dashboard shows a **live star count** for this repo (refresh on open + every ~10 min). |
| **OTA** | Release workflow appends a **Checksum OTA** block below; the app matches **your platform ZIP** and verifies **SHA256** before install. |

### Download (this release)

- **Windows:** `AMI-v3.1.4-windows.zip` → extract `AMI-Package/AMI.exe`
- **macOS:** `AMI-v3.1.4-macos.zip` → extract `AMI-Package/AMI`

Also attached: **`SHA256SUMS.txt`** (same hashes as in the notes below).

### Upgrade notes

- Config migration updates legacy `website` / copyright strings when loading. Full log: [`3.0/CHANGELOG.md`](3.0/CHANGELOG.md).

### Install from source

`cd 3.0 && pip install -r requirements.txt && PYTHONPATH=src python -m ami.main`

---

## Italiano

**AMI 3.1.4** aggiorna marchio e collegamenti (copyright, stelle GitHub in dashboard) senza cambiare il motore di monitoraggio.

### Download

- **Windows:** `AMI-v3.1.4-windows.zip`
- **macOS:** `AMI-v3.1.4-macos.zip`

In allegato anche **`SHA256SUMS.txt`**.

---

### Checksum OTA (AMI updater)

SHA256 delle zip (stesso contenuto del file `SHA256SUMS.txt` allegato). L'app usa queste righe per verificare il download.

- `AMI-v3.1.4-macos.zip` → sha256:`007fda8f241d3aec46877186152afbd9ef6ab3f7d1cad79ad54dc3cf6e1efd6b`
- `AMI-v3.1.4-windows.zip` → sha256:`e4708acca4bd4d3009ba960beb03f75b7f5ac556f3b9ef051bcc5bc4f080650d`

---

<p align="center">
  <b>AMI — Active Monitor of Internet</b><br/>
  <a href="https://github.com/dgiovannetti/AMI">GitHub</a>
</p>

<p align="center"><sub>Apache-2.0 · CiaoIM™ by Daniel Giovannetti</sub></p>
