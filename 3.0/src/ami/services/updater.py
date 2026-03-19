"""
AMI 3.0 - OTA updates from GitHub Releases.
SHA256 checksum verification; forced update after max postponements.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, Optional

import requests
from packaging import version
from packaging.version import InvalidVersion

from ami import __version__ as AMI_VERSION


def format_size(bytes_size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


class UpdateManager:
    def __init__(
        self,
        current_version: str | None = None,
        github_repo: str = "dgiovannetti/AMI",
        max_postponements: int = 3,
    ):
        self.current_version = current_version or AMI_VERSION
        self.github_repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.postpone_file = Path.home() / ".ami_update_postponed"
        self.max_postponements = max_postponements
        self.token = os.environ.get("AMI_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
        self.base_headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            self.base_headers["Authorization"] = f"Bearer {self.token}"

    def check_for_updates(self) -> Optional[Dict]:
        try:
            response = requests.get(self.api_url, headers=self.base_headers, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            try:
                latest_v = version.parse(latest_version)
                current_v = version.parse(self.current_version)
            except InvalidVersion as e:
                print(f"[UPDATE] Invalid version string from GitHub or app: {e}")
                return None
            if latest_v <= current_v:
                return None
            asset = self._find_platform_asset(release_data.get("assets", []))
            if not asset:
                return None
            download_url = asset.get("url") if self.token else asset.get("browser_download_url")
            body = release_data.get("body") or ""
            asset_name = asset.get("name") or ""
            return {
                "version": latest_version,
                "download_url": download_url,
                "release_notes": body or "No release notes available",
                "size": asset.get("size", 0),
                "checksum": self._checksum_for_asset(body, asset_name),
                "asset_name": asset_name,
            }
        except Exception as e:
            print(f"[UPDATE] Error checking for updates: {e}")
            return None

    def _find_platform_asset(self, assets: list) -> Optional[Dict]:
        plat = sys.platform
        for asset in assets:
            name = asset.get("name", "").lower()
            if plat == "win32" and "windows" in name and name.endswith(".zip"):
                return asset
            if plat == "darwin" and "macos" in name and name.endswith(".zip"):
                return asset
            if plat.startswith("linux") and "linux" in name and name.endswith(".zip"):
                return asset
        return None

    def _checksum_for_asset(self, body: str, asset_name: str) -> Optional[str]:
        """
        Find SHA256 for the platform ZIP using the GitHub release body.
        Supports sha256sum-style lines and CI-appended markdown (filename + sha256:...).
        """
        if not body.strip() or not asset_name.strip():
            return None
        key = asset_name.strip().lower()
        for line in body.splitlines():
            stripped = line.strip()
            m = re.match(r"^([a-fA-F0-9]{64})\s+[\*]?(\S+)", stripped)
            if m:
                fn = m.group(2).strip().lower()
                if fn == key or fn.endswith("/" + key) or key in fn:
                    return m.group(1).lower()
        for line in body.splitlines():
            if key not in line.lower():
                continue
            for m in re.finditer(
                r"sha256\s*[=:`']\s*`?([a-fA-F0-9]{64})`?", line, re.IGNORECASE
            ):
                return m.group(1).lower()
            m = re.search(r"sha256:\s*`([a-fA-F0-9]{64})`", line, re.IGNORECASE)
            if m:
                return m.group(1).lower()
        return None

    def get_postpone_count(self) -> int:
        if not self.postpone_file.exists():
            return 0
        try:
            with open(self.postpone_file) as f:
                return json.load(f).get("count", 0)
        except Exception:
            return 0

    def increment_postpone_count(self) -> None:
        count = self.get_postpone_count() + 1
        self.postpone_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.postpone_file, "w") as f:
            json.dump({"count": count}, f)

    def reset_postpone_count(self) -> None:
        if self.postpone_file.exists():
            self.postpone_file.unlink()

    def can_postpone(self) -> bool:
        return self.get_postpone_count() < self.max_postponements

    def download_update(
        self,
        download_url: str,
        checksum: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Optional[Path]:
        try:
            temp_dir = Path(tempfile.gettempdir()) / "ami_update"
            temp_dir.mkdir(exist_ok=True)
            filename = download_url.split("/")[-1].split("?")[0] or "update.zip"
            download_path = temp_dir / filename
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            if "api.github.com" in download_url:
                headers["Accept"] = "application/octet-stream"
            response = requests.get(
                download_url, headers=headers, stream=True, timeout=(15, 120)
            )
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            last_pct = -1

            def maybe_progress() -> None:
                nonlocal last_pct
                if not progress_callback or total_size <= 0:
                    return
                pct = min(99, int(100 * downloaded / total_size))
                if pct != last_pct:
                    last_pct = pct
                    try:
                        progress_callback(pct)
                    except Exception:
                        pass

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        maybe_progress()
            if progress_callback:
                try:
                    progress_callback(100)
                except Exception:
                    pass
            if checksum:
                cs = checksum.strip()
                if len(cs) == 64 and all(c in "0123456789abcdefABCDEF" for c in cs):
                    if not self._verify_checksum(download_path, cs):
                        download_path.unlink(missing_ok=True)
                        return None
                else:
                    print("[UPDATE] Checksum in release notes invalid or missing; skipping verify")
            return download_path
        except Exception as e:
            print(f"[UPDATE] Download failed: {e}")
            return None

    def _verify_checksum(self, file_path: Path, expected: str) -> bool:
        import hashlib
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest().lower() == expected.lower().strip()

    def install_update(self, package_path: Path) -> bool:
        try:
            import zipfile
            extract_dir = package_path.parent / "extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(package_path, "r") as z:
                z.extractall(extract_dir)
            if sys.platform == "win32":
                new_exe = self._find_file(extract_dir, "AMI.exe")
            else:
                new_exe = self._find_file(extract_dir, "AMI")
            if not new_exe:
                return False
            if not getattr(sys, "frozen", False):
                return False
            current_exe = Path(sys.executable)
            if sys.platform == "win32":
                return self._install_windows(current_exe, new_exe)
            return self._install_unix(current_exe, new_exe)
        except Exception as e:
            print(f"[UPDATE] Installation failed: {e}")
            return False

    def _find_file(self, directory: Path, filename: str) -> Optional[Path]:
        for root, _, files in os.walk(directory):
            if filename in files:
                return Path(root) / filename
        return None

    def _install_windows(self, current_exe: Path, new_exe: Path) -> bool:
        batch = current_exe.parent / "_update.bat"
        pid = os.getpid()
        batch.write_text(f"""@echo off
set PID={pid}
:waitpid
tasklist /FI "PID eq %PID%" | findstr /I "%PID%" >nul
if %errorlevel%==0 ( timeout /t 1 /nobreak >nul & goto waitpid )
del /f /q "{current_exe}"
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""")
        subprocess.Popen(
            ["cmd", "/c", str(batch)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True

    def _install_unix(self, current_exe: Path, new_exe: Path) -> bool:
        script = current_exe.parent / "_update.sh"
        pid = os.getpid()
        # No "exec … &" (ambiguous); launch detached then remove script.
        script.write_text(f"""#!/bin/bash
PID={pid}
for i in $(seq 1 75); do kill -0 "$PID" 2>/dev/null || break; sleep 0.2; done
sleep 0.35
rm -f "{current_exe}"
mv "{new_exe}" "{current_exe}"
chmod +x "{current_exe}"
nohup "{current_exe}" >/dev/null 2>&1 &
sleep 0.5
rm -f "$0"
""")
        script.chmod(0o755)
        subprocess.Popen(["/bin/bash", str(script)])
        return True

    def perform_update(self, update_info: Dict) -> bool:
        path = self.download_update(
            update_info["download_url"],
            update_info.get("checksum"),
        )
        if not path:
            return False
        if self.install_update(path):
            self.reset_postpone_count()
            sys.exit(0)
        return False
