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
- **macOS:** `AMI-v3.1.4-macos.zip` → extract `AMI-Package/AMI.app` (double-click **AMI.app**; see [MACOS_SECURITY.md](MACOS_SECURITY.md) if Gatekeeper prompts)

Also attached: **`SHA256SUMS.txt`** (authoritative hashes; CI may also append a **Checksum OTA** block to the release body).

### Upgrade notes

- Config migration updates legacy `website` / copyright strings when loading. Full log: [`3.0/CHANGELOG.md`](3.0/CHANGELOG.md).

### Install from source

`cd 3.0 && pip install -r requirements.txt && PYTHONPATH=src python -m ami.main`

---

## Italiano

**AMI 3.1.4** aggiorna marchio e collegamenti (copyright, stelle GitHub in dashboard) senza cambiare il motore di monitoraggio.

### Download

- **Windows:** `AMI-v3.1.4-windows.zip` → `AMI-Package/AMI.exe`
- **macOS:** `AMI-v3.1.4-macos.zip` → `AMI-Package/AMI.app` (bundle firmato ad-hoc in CI; messaggio “Python” in Gatekeeper mitigato rispetto al binario sciolto)

In allegato anche **`SHA256SUMS.txt`** (hash aggiornati ogni volta che ricarichi gli ZIP sulla stessa tag).

---

### Checksum OTA (AMI updater)

Usa le righe in **`SHA256SUMS.txt`** allegato alla release (o il blocco **Checksum OTA** aggiunto dal workflow). Dopo ogni nuovo upload degli ZIP su **v3.1.4**, i valori SHA256 cambiano: non copiare hash obsoleti da commit precedenti.

---

<p align="center">
  <b>AMI — Active Monitor of Internet</b><br/>
  <a href="https://github.com/dgiovannetti/AMI">GitHub</a>
</p>

<p align="center"><sub>Apache-2.0 · CiaoIM™ by Daniel Giovannetti</sub></p>
