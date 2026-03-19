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

The updater resolves the SHA256 for **the ZIP asset you download** (Windows/macOS) from the GitHub release **body**:

1. **sha256sum-style lines** copied into the notes: `deadbeef...  AMI-vX.Y.Z-windows.zip`
2. **CI-appended block** (workflow `release-3.0.yml`): each line lists the filename and `sha256:`\`64-hex\`` in markdown.

If no valid 64-character hex hash is found for that filename, verification is skipped (download still works). Mismatch aborts the update.

Maintainership: after each tagged release, the workflow uploads `SHA256SUMS.txt` and appends a `### Checksum OTA (AMI updater)` section so clients can verify.

## Postponement storage

Postponement count is stored in `~/.ami_update_postponed` (JSON with `count`). It is reset after a successful install or when the user skips that version.

## 3.0–specific notes

- Version is taken from `ami.__version__`; no need to duplicate in `config.json` for the running app.
- For 3.x releases, assets must be named like `AMI-v*-*-windows.zip` / `AMI-v*-*-macos.zip` (substring `windows` / `macos` + `.zip`). See `.github/workflows/release-3.0.yml`.
- **macOS (3.1.4+):** the ZIP extracts to `AMI-Package/` containing **`AMI.app`**. The updater replaces the **entire `.app` bundle** and relaunches with `open -n`. Older flat `AMI` binaries in the zip are still supported as a fallback if no `AMI.app` is present.
