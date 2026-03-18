# Changelog - AMI 3.0

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
