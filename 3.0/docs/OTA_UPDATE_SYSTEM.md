# AMI 3.0 OTA Update System

AMI 3.0 uses the same Over-The-Air update flow as 2.x: checks GitHub Releases, downloads the appropriate platform asset (Windows/macOS), verifies SHA256 when provided in release notes, and installs after user confirmation.

## Configuration

In `config.json`:

```json
{
  "updates": {
    "enabled": true,
    "check_on_startup": true,
    "check_interval_hours": 24,
    "github_repo": "dgiovannetti/AMI",
    "max_postponements": 3,
    "notify_on_update": true
  }
}
```

- **enabled**: Master switch for OTA.
- **check_on_startup**: Check for updates shortly after launch.
- **check_interval_hours**: Interval for periodic checks.
- **github_repo**: Repository to check (e.g. `owner/repo`).
- **max_postponements**: After this many "Remind Me Later", the update becomes mandatory.
- **notify_on_update**: Show a notification when an update is available.

## Version comparison

The current app version is read from `ami.__version__` (3.0.0). The updater compares this with the latest release `tag_name` on GitHub (e.g. `v3.0.1`). Only releases with a higher semantic version are offered.

## Platform assets

The updater looks for assets whose name contains the platform and ends with `.zip`:

- **Windows**: name contains `windows`, ends with `.zip`
- **macOS**: name contains `macos`, ends with `.zip`
- **Linux**: name contains `linux`, ends with `.zip`

## Checksum verification

If the release body contains a line with `sha256` and a value (e.g. `SHA256: abc123...`), the downloaded file is verified before installation. Mismatch causes the update to be aborted.

## Postponement storage

Postponement count is stored in `~/.ami_update_postponed` (JSON with `count`). It is reset after a successful install or when the user skips that version.

## 3.0–specific notes

- Version is taken from `ami.__version__`; no need to duplicate in `config.json` for the running app.
- For 3.0 releases, build and publish artifacts from the `3.0/` folder (e.g. `AMI-Windows.zip`, `AMI-macOS.zip`) so the OTA updater downloads the correct package.
