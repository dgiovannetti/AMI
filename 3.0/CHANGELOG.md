# Changelog - AMI 3.0

## Unreleased

- **OTA / release notes**: Il workflow `release-3.0.yml` appende al body della GitHub Release il blocco **Checksum OTA** (markdown allineato a `UpdateManager._checksum_for_asset`). L'updater associa l'hash al nome dello ZIP della piattaforma.

- **OTA / updater**: `check_for_updates` gestisce `InvalidVersion`; checksum solo se stringa hex 64 caratteri (evita fallimenti da note release malformate); download con timeout `(connect, read)` e progress reale; cartella `extracted` ripulita prima di ogni estrazione; script Unix usa `nohup` al posto di `exec … &`. **Update dialog**: non chiudibile durante download attivo; niente «postpone» implicito dopo un tentativo di install fallito; aggiornamento obbligatorio: dopo fallimento la chiusura chiede di riprovare; thread resettato in modo coerente. **Tray**: un solo controllo aggiornamenti alla volta (`_update_check_busy`).

- **CI / Windows & release**: **Un solo workflow di integrazione** — **`build.yml`** (Windows + macOS da `3.0/`, con filtro path su `3.0/**` per evitare build duplicate). Rimossi i workflow ridondanti `build-3.0.yml` e `build-windows.yml`. **`release-3.0.yml`** invariato: su **tag `v*`** allega gli ZIP alla Release + `SHA256SUMS.txt`. **`build_windows.bat`** punta a `3.0/`. **YAML**: `working-directory: "3.0"` (quoted) per evitare che `3.0` sia interpretato come numero.

## 3.1.4

- **Branding**: Copyright **© 2025–2026**; default `app.website` is **[ciaoim.tech/projects/ami](https://ciaoim.tech/projects/ami)** (full URL in `config.json`). Migration updates legacy `website: "ciaoim.tech"` and the previous one-line copyright string when loading config.
- **Dashboard**: Footer shows copyright plus a clickable **ciaoim.tech** link (opens the configured site).
- **About (tray)**: Copyright line from config; links to **ciaoim.tech** and **GitHub** repo.
- **Dashboard — GitHub**: Live **stargazers** count from the GitHub API (refresh on open + every 10 min, throttled), with links to the repo and **Star** (opens GitHub in the browser; starring still uses the site’s Star button when logged in).

## 3.1.3

- **Hetzner test files**: `speed.hetzner.de` is deprecated. Default `test_url` is now **FSN1** `https://fsn1-speed.hetzner.com/100MB.bin`. Built-in fallbacks include **nbg1**, **hel1**, **ash**, **hil**, **sin** regional endpoints (same `100MB.bin` path). Config migration rewrites old `speed.hetzner.de` URLs automatically.

## 3.1.2

- **Speed test reliability**: If the primary `test_url` fails (e.g. Cloudflare `__down` returns 403), AMI tries built-in fallback mirrors (Hetzner, OVH, thinkbroadband) automatically.
- **UI refresh**: After each speed test, the tray/dashboard refresh immediately via a queued signal (no need to wait for the next ping poll).
- **Tray menu**: New **Speed test now** action; first scheduled test runs ~15 s after startup (was 60 s).
- **HTTP**: `Accept-Encoding: identity` on speed test requests to avoid inflated byte counts from compression.
- **Default `test_url`**: Hetzner regional host (see 3.1.3); Cloudflare remains available as a fallback mirror.

## 3.1.1

- **Speed test accuracy**: Throughput is measured only over the **timed** download window. DNS, TCP, TLS, and time until the first byte of that window are **excluded** from the Mbps calculation (fixes artificially low speeds on fast links).
- **Warmup**: New `speed_test.warmup_mb` (default 2 MB, 0–20 in Settings). Bytes read during warmup are not timed, improving TCP slow-start behavior before measurement. Total data = warmup + timed download size.
- **HTTP timeout**: Uses `(connect_timeout, read_timeout)` for `requests` (connect capped at 10 s).
- **Default test URL**: Cloudflare `__down` with `bytes=104857600` (100 MB) so URL length supports large warmup + download settings.
- **Migration**: Configs with the previous 50 MB Cloudflare default URL are upgraded to 100 MB; `warmup_mb` backfilled when missing.
- **User-Agent**: Speed test requests use a browser-like `User-Agent` so CDNs (e.g. Cloudflare) are less likely to return 403 to `python-requests`.

## 3.1.0

- **Speed test**: Download throughput measurement (Mbps/Gbps) with configurable interval, timeout, test URL, and download size. Three tiers (Slow / Medium / Fast) shown in tray tooltip, menu, and dashboard StatCard. All parameters configurable in Settings → Speed test tab. API `/status` includes optional `speed_mbps` and `speed_tier`.

## 3.0.0

- **Architecture**: New package layout under `src/ami/` with clear separation of core, services, and UI. Config validation via JSON schema and migration from 2.x config.
- **Themes**: Light, dark, and auto (system) theme support across dashboard, settings, splash, compact window, and update dialog.
- **API**: Optional `api.auth_token` for Bearer authentication on `/status`, `/health`, `/stats`.
- **Monitor**: Support for multiple HTTP test URLs (`http_test_urls`); primary `http_test_url` unchanged.
- **Settings**: New API tab (enable, port, auth token); theme selector; validation and error messages.
- **Versioning**: Single source of version in `ami.__version__` (3.0.0); used by app and OTA updater.
- **Dashboard**: Theme-aware StatCards and charts; responsive grid; compact mode for small windows.
- **OTA**: Same GitHub Releases flow with SHA256 checksum; forced update after max postponements.
- **Build**: PyInstaller onedir build; `build.py` and package layout for 3.0; config and schema included in bundle.
