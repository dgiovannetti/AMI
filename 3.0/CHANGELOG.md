# Changelog - AMI 3.0

## 3.1.2

- **Speed test reliability**: If the primary `test_url` fails (e.g. Cloudflare `__down` returns 403), AMI tries built-in fallback mirrors (Hetzner, OVH, thinkbroadband) automatically.
- **UI refresh**: After each speed test, the tray/dashboard refresh immediately via a queued signal (no need to wait for the next ping poll).
- **Tray menu**: New **Speed test now** action; first scheduled test runs ~15 s after startup (was 60 s).
- **HTTP**: `Accept-Encoding: identity` on speed test requests to avoid inflated byte counts from compression.
- **Default `test_url`**: `https://speed.hetzner.de/100MB.bin` (works more reliably than Cloudflare for scripted clients); Cloudflare remains available as a fallback mirror.

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
