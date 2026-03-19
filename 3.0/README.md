# AMI 3.0 - Active Monitor of Internet

**"Sai se sei davvero online."**

AMI 3.0 is a cross-platform desktop app that monitors internet connectivity in real time. It distinguishes between local network and actual internet (ping + HTTP checks), supports dark/light themes, optional API with auth token, and OTA updates.

## What's new in 3.0

- **Architecture**: Clean separation of core, services, and UI; config validated with JSON schema; migration from 2.x config.
- **Themes**: Light, dark, and auto (system) with consistent styling across dashboard, settings, and compact window.
- **API**: Optional Bearer token for `/status`, `/health`, `/stats` endpoints.
- **Monitor**: Optional multiple HTTP test URLs; same multi-host ping and thresholds.
- **Settings**: New API tab (enable/port/auth token); theme selector; validation and defaults.
- **Single source of version**: `ami.__version__` (e.g. **3.1.4**) used by app and OTA.

## Requirements

- Python 3.10+
- See `requirements.txt`

## Run from source

```bash
cd 3.0
pip install -r requirements.txt
python run.py
```

In alternativa: `PYTHONPATH=src python -m ami.main`

Assicurati che `config.json` e `config.schema.json` siano in `3.0/`. Le icone sono in `resources/`.

## Configuration

- **Path**: When running from source, `3.0/config.json`. When running from the built app, user config dir (e.g. `~/Library/Preferences/AMI/config.json` on macOS).
- **Schema**: `config.schema.json` is used to validate config; invalid or legacy keys are migrated on load.
- **2.x → 3.0**: If an existing 2.x config is found in the user config dir, it is migrated (version set to 3.0.0, new keys defaulted).

Key options:

- `monitoring.ping_hosts`, `http_test_url`, `http_test_urls` (optional), `polling_interval`, `timeout`, `enable_http_test`
- `thresholds.unstable_latency_ms`, `unstable_loss_percent`
- `notifications.enabled`, `silent_mode`, `notify_on_disconnect`, `notify_on_reconnect`, `notify_on_unstable`
- `logging.enabled`, `log_file`, `max_log_size_mb`
- `api.enabled`, `api.port`, `api.auth_token` (optional)
- `ui.theme` (`auto` | `light` | `dark`), `show_dashboard_on_start`, `compact_status_window`
- `updates.enabled`, `check_on_startup`, `check_interval_hours`, `github_repo`, `max_postponements`
- `speed_test` (enabled, interval, `test_url`, `download_size_mb`, `warmup_mb`, `timeout_seconds`, tier Mbps thresholds): timed window after optional warmup; `test_url` should serve at least **warmup + download** bytes. Default is Hetzner **FSN1** (`https://fsn1-speed.hetzner.com/100MB.bin`); other regions use the same path on `nbg1-speed`, `hel1-speed`, `ash-speed`, `hil-speed`, `sin-speed` (the old `speed.hetzner.de` host is deprecated). If the primary URL fails, AMI tries built-in fallback mirrors automatically.

## Build

```bash
cd 3.0
pip install -r requirements.txt pyinstaller
python build.py
```

Output: `dist/AMI-Package/` (onedir: `AMI.exe` on Windows, `AMI` on macOS, plus `config.json`, `config.schema.json`, `resources/`).

### Windows (da root del repo)

- Script: `build_windows.bat` (nella root, sopra `3.0/`).
- In CI: workflow **Build AMI** (`.github/workflows/build.yml`) — Windows + macOS da `3.0/` (su push/PR solo se cambiano `3.0/**` o il workflow; *workflow_dispatch* sempre disponibile).
- Su ogni **tag `v*`** lo workflow **Release AMI 3.0** genera `AMI-<tag>-windows.zip` e `AMI-<tag>-macos.zip` e li allega alla GitHub Release (nomi compatibili con l’updater OTA). Puoi rilanciare a mano con *Run workflow* indicando un tag già esistente.

## Project structure

```
3.0/
├── pyproject.toml
├── requirements.txt
├── config.json
├── config.schema.json
├── build.py
├── src/ami/
│   ├── __init__.py      # __version__
│   ├── main.py          # entry
│   ├── core/            # config, paths, models
│   ├── services/        # monitor, logger, notifier, api, updater
│   └── ui/              # tray, dashboard, settings, splash, update_dialog, compact, themes
├── resources/
└── docs/
```

## Differences from 2.x

- Package name is `ami`; run with `python -m ami.main`.
- Config is validated with `config.schema.json` and migrated from 2.x.
- UI theme (light/dark/auto) is applied globally.
- API can be protected with `api.auth_token`.
- Version is read from `ami.__version__` (single source).

---

© 2025–2026 CiaoIM™ by Daniel Giovannetti · [ciaoim.tech/projects/ami](https://ciaoim.tech/projects/ami)
