"""
AMI Auto-Updater
Handles automatic updates from GitHub Releases with forced update after 3 postponements
"""

import os
import sys
import json
import hashlib
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
import requests
from packaging import version


class UpdateManager:
    """Manages application updates from GitHub"""
    
    def __init__(self, current_version: str, github_repo: str):
        """
        Initialize update manager
        
        Args:
            current_version: Current app version (e.g., "1.0.0")
            github_repo: GitHub repository (e.g., "dgiovannetti/AMI")
        """
        self.current_version = current_version
        self.github_repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.postpone_file = Path.home() / '.ami_update_postponed'
        self.max_postponements = 3
        
    def check_for_updates(self) -> Optional[Dict]:
        """
        Check if a new version is available
        
        Returns:
            Dict with update info if available, None otherwise
            {
                'version': '1.1.0',
                'download_url': 'https://...',
                'release_notes': '...',
                'checksum': 'sha256:...',
                'size': 12345678
            }
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                # Find the appropriate asset for current platform
                asset = self._find_platform_asset(release_data['assets'])
                
                if asset:
                    return {
                        'version': latest_version,
                        'download_url': asset['browser_download_url'],
                        'release_notes': release_data.get('body', 'No release notes available'),
                        'size': asset['size'],
                        'checksum': self._extract_checksum(release_data.get('body', ''))
                    }
            
            return None
            
        except Exception as e:
            print(f"[UPDATE] Error checking for updates: {e}")
            return None
    
    def _find_platform_asset(self, assets: list) -> Optional[Dict]:
        """Find the correct download asset for current platform"""
        platform = sys.platform
        
        for asset in assets:
            name = asset['name'].lower()
            
            if platform == 'win32' and 'windows' in name and name.endswith('.zip'):
                return asset
            elif platform == 'darwin' and 'macos' in name and name.endswith('.zip'):
                return asset
            elif platform.startswith('linux') and 'linux' in name and name.endswith('.zip'):
                return asset
        
        return None
    
    def _extract_checksum(self, release_body: str) -> Optional[str]:
        """Extract SHA256 checksum from release notes"""
        # Look for lines like: SHA256: abc123...
        for line in release_body.split('\n'):
            if 'sha256' in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    return parts[1].strip()
        return None
    
    def get_postpone_count(self) -> int:
        """Get number of times update has been postponed"""
        if not self.postpone_file.exists():
            return 0
        
        try:
            with open(self.postpone_file, 'r') as f:
                data = json.load(f)
                return data.get('count', 0)
        except:
            return 0
    
    def increment_postpone_count(self):
        """Increment postponement counter"""
        count = self.get_postpone_count() + 1
        
        with open(self.postpone_file, 'w') as f:
            json.dump({'count': count}, f)
    
    def reset_postpone_count(self):
        """Reset postponement counter (after update or skip)"""
        if self.postpone_file.exists():
            self.postpone_file.unlink()
    
    def can_postpone(self) -> bool:
        """Check if update can still be postponed"""
        return self.get_postpone_count() < self.max_postponements
    
    def download_update(self, download_url: str, checksum: Optional[str] = None) -> Optional[Path]:
        """
        Download update package
        
        Args:
            download_url: URL to download from
            checksum: Expected SHA256 checksum
            
        Returns:
            Path to downloaded file, or None on failure
        """
        try:
            # Create temp file
            temp_dir = Path(tempfile.gettempdir()) / 'ami_update'
            temp_dir.mkdir(exist_ok=True)
            
            filename = download_url.split('/')[-1]
            download_path = temp_dir / filename
            
            # Download with progress
            print(f"[UPDATE] Downloading from {download_url}...")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"[UPDATE] Progress: {progress:.1f}%", end='\r')
            
            print("\n[UPDATE] Download complete")
            
            # Verify checksum if provided
            if checksum:
                if not self._verify_checksum(download_path, checksum):
                    print("[UPDATE] Checksum verification failed!")
                    download_path.unlink()
                    return None
                print("[UPDATE] Checksum verified")
            
            return download_path
            
        except Exception as e:
            print(f"[UPDATE] Download failed: {e}")
            return None
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file SHA256 checksum"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        actual_checksum = sha256.hexdigest()
        return actual_checksum.lower() == expected_checksum.lower()
    
    def install_update(self, package_path: Path) -> bool:
        """
        Install downloaded update
        
        Args:
            package_path: Path to downloaded ZIP package
            
        Returns:
            True if installation successful
        """
        try:
            import zipfile
            
            # Extract to temp directory
            extract_dir = package_path.parent / 'extracted'
            extract_dir.mkdir(exist_ok=True)
            
            print(f"[UPDATE] Extracting {package_path}...")
            with zipfile.ZipFile(package_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find the new executable
            if sys.platform == 'win32':
                new_exe = self._find_file(extract_dir, 'AMI.exe')
            else:
                new_exe = self._find_file(extract_dir, 'AMI')
            
            if not new_exe:
                print("[UPDATE] Could not find executable in package")
                return False
            
            # Get current executable path
            if getattr(sys, 'frozen', False):
                current_exe = Path(sys.executable)
            else:
                # Running from source - can't update
                print("[UPDATE] Cannot update when running from source")
                return False
            
            # Prepare update script
            if sys.platform == 'win32':
                return self._install_windows(current_exe, new_exe)
            else:
                return self._install_unix(current_exe, new_exe)
            
        except Exception as e:
            print(f"[UPDATE] Installation failed: {e}")
            return False
    
    def _find_file(self, directory: Path, filename: str) -> Optional[Path]:
        """Recursively find a file in directory"""
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return Path(root) / filename
        return None
    
    def _install_windows(self, current_exe: Path, new_exe: Path) -> bool:
        """Install update on Windows"""
        # Create batch script to replace exe and restart
        batch_script = current_exe.parent / '_update.bat'
        pid = os.getpid()

        batch_content = f"""@echo off
set PID={pid}
echo Updating AMI...
REM Wait for current process to exit
:waitpid
tasklist /FI "PID eq %PID%" | findstr /I "%PID%" >nul
if %errorlevel%==0 (
  timeout /t 1 /nobreak >nul
  goto waitpid
)
del /f /q "{current_exe}"
move /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        
        with open(batch_script, 'w') as f:
            f.write(batch_content)
        
        # Run batch script and exit
        subprocess.Popen(['cmd', '/c', str(batch_script)], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
    
    def _install_unix(self, current_exe: Path, new_exe: Path) -> bool:
        """Install update on Unix/macOS"""
        # Create shell script to replace exe and restart
        script_path = current_exe.parent / '_update.sh'
        pid = os.getpid()

        script_content = f"""#!/bin/bash
PID={pid}
echo "Updating AMI..."
# Wait up to ~10s for current process to exit
for i in $(seq 1 50); do
  if kill -0 "$PID" 2>/dev/null; then
    sleep 0.2
  else
    break
  fi
done
sleep 0.2
rm -f "{current_exe}"
mv "{new_exe}" "{current_exe}"
chmod +x "{current_exe}"
"{current_exe}" &
rm "$0"
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        
        # Run script and exit
        subprocess.Popen(['/bin/bash', str(script_path)])
        
        return True
    
    def perform_update(self, update_info: Dict) -> bool:
        """
        Complete update process: download and install
        
        Args:
            update_info: Update information from check_for_updates()
            
        Returns:
            True if update successful (app will restart)
        """
        # Download
        package_path = self.download_update(
            update_info['download_url'],
            update_info.get('checksum')
        )
        
        if not package_path:
            return False
        
        # Install
        success = self.install_update(package_path)
        
        if success:
            # Reset postpone count
            self.reset_postpone_count()
            
            # Exit app (update script will restart it)
            print("[UPDATE] Update installed. Restarting...")
            sys.exit(0)
        
        return success


def format_size(bytes_size: int) -> str:
    """Format byte size to human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
