# AMI v3.1.4 — *Sai se sei davvero online.*

<p align="center">
  <strong>Branding refresh · GitHub pulse · Home on the web</strong>
</p>

---

## English

**AMI 3.1.4** polishes how the app presents itself and connects you to the project—without changing the core you rely on for real connectivity checks.

### Highlights

| | |
| --- | --- |
| **© 2025–2026** | Copyright range updated across config defaults, About, and docs. |
| **Official site** | One tap to **[ciaoim.tech/projects/ami](https://ciaoim.tech/projects/ami)** from the dashboard footer and the tray **About** dialog (driven by `app.website` in `config.json`). |
| **GitHub stars** | Dashboard shows a **live star count** for this repo, auto-refreshed (on open + every 10 minutes, rate-friendly). Links to the repo and a **Star** shortcut that opens GitHub—log in there and tap **Star** on the page. |
| **Docs** | Root `README` badge and copy point to **3.1.4** and the current **3.0/** tree. |

### Upgrade notes

- Existing configs: if `website` was the short host `ciaoim.tech`, it migrates to the full AMI project URL on load.
- Full changelog: [`3.0/CHANGELOG.md`](3.0/CHANGELOG.md).

### Install

- **From source:** `cd 3.0 && pip install -r requirements.txt && PYTHONPATH=src python -m ami.main`
- **Binaries:** grab **AMI-Package** artifacts from CI for this tag when available, or build with `python build.py` inside `3.0/`.

---

## Italiano

**AMI 3.1.4** rifinisce presentazione e collegamenti al progetto, mantenendo invariata la logica di monitoraggio (ping + HTTP, LAN vs Internet).

### In sintesi

- **Copyright © 2025–2026** su default, About e documentazione.
- **Sito ufficiale**: link a **[ciaoim.tech/projects/ami](https://ciaoim.tech/projects/ami)** nel footer della dashboard e in **Informazioni** dal tray (`app.website` in `config.json`).
- **Stelle GitHub**: contatore **aggiornato** sul dashboard, refresh all’apertura e ogni ~10 minuti; link al repo e scorciatoia **Star** (apre GitHub — la star vera si conferma dal pulsante sul sito, se sei loggato).
- **README** aggiornato con versione **3.1.4** e riferimento al codice in **`3.0/`**.

### Aggiornamento

Le config con `website: "ciaoim.tech"` vengono portate all’URL completo della pagina AMI al caricamento.

---

<p align="center">
  <b>AMI — Active Monitor of Internet</b><br/>
  <a href="https://ciaoim.tech/projects/ami">ciaoim.tech/projects/ami</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/dgiovannetti/AMI">GitHub</a>
</p>

<p align="center"><sub>Apache-2.0 · CiaoIM™ by Daniel Giovannetti</sub></p>
