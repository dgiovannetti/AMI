"""
AMI 3.0 - Cross-platform auto-start (Windows Run key, macOS LaunchAgent).
"""

from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

APP_NAME = "AMI"
MACOS_LABEL = "tech.ciaoim.ami"
MACOS_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{MACOS_LABEL}.plist"
WIN_STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _executable_command() -> str | None:
    """Return a shell command to launch AMI, or None if auto-start is not supported."""
    args = _launch_arguments()
    if not args:
        return None
    import shlex

    return " ".join(shlex.quote(a) for a in args)


def _launch_arguments() -> list[str] | None:
    if getattr(sys, "frozen", False):
        exe = os.path.abspath(sys.executable)
        if sys.platform == "darwin" and exe.endswith("/MacOS/AMI"):
            return [exe]
        if sys.platform == "win32" and exe.lower().endswith(".exe"):
            return [exe]
        return [exe]

    main_mod = Path(__file__).resolve().parents[1] / "main.py"
    src_dir = main_mod.parent.parent
    if not main_mod.is_file():
        return None
    return [sys.executable, "-m", "ami.main"]


def _launch_environment() -> dict[str, str]:
    if getattr(sys, "frozen", False):
        return {}
    src_dir = Path(__file__).resolve().parents[2]
    return {"PYTHONPATH": str(src_dir)}


def _launch_working_directory() -> str | None:
    if getattr(sys, "frozen", False):
        return None
    return str(Path(__file__).resolve().parents[3])


def is_autostart_enabled() -> bool:
    if sys.platform == "win32":
        return _win_is_enabled()
    if sys.platform == "darwin":
        return MACOS_PLIST.is_file()
    return False


def enable_autostart() -> bool:
    cmd = _executable_command()
    if cmd is None:
        return False
    if sys.platform == "win32":
        return _win_enable(cmd)
    if sys.platform == "darwin":
        return _macos_enable(cmd)
    return False


def disable_autostart() -> bool:
    if sys.platform == "win32":
        return _win_disable()
    if sys.platform == "darwin":
        return _macos_disable()
    return False


def sync_autostart(enabled: bool) -> bool:
    """Apply config value to the OS; returns success."""
    if enabled:
        return enable_autostart()
    return disable_autostart()


def _win_is_enabled() -> bool:
    try:
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_STARTUP_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def _win_enable(command: str) -> bool:
    try:
        import winreg

        cmd = _executable_command()
        if not cmd:
            return False
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _win_disable() -> bool:
    try:
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _macos_enable(command: str) -> bool:
    try:
        MACOS_PLIST.parent.mkdir(parents=True, exist_ok=True)
        parts = _launch_arguments()
        if not parts:
            return False
        plist: dict = {
            "Label": MACOS_LABEL,
            "ProgramArguments": parts,
            "RunAtLoad": True,
            # Rilancia solo dopo crash/uscita anomala (non dopo Exit dal menu).
            "KeepAlive": {"SuccessfulExit": False},
        }
        env = _launch_environment()
        if env:
            plist["EnvironmentVariables"] = env
        workdir = _launch_working_directory()
        if workdir:
            plist["WorkingDirectory"] = workdir
        log_dir = Path.home() / "Library" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        plist["StandardOutPath"] = str(log_dir / "ami.stdout.log")
        plist["StandardErrorPath"] = str(log_dir / "ami.stderr.log")
        with MACOS_PLIST.open("wb") as f:
            plistlib.dump(plist, f)
        _macos_launchctl_load()
        return True
    except Exception:
        return False


def _macos_disable() -> bool:
    try:
        _macos_launchctl_unload()
        if MACOS_PLIST.is_file():
            MACOS_PLIST.unlink()
        return True
    except Exception:
        return False


def _macos_launchctl_load() -> None:
    if sys.platform != "darwin" or not MACOS_PLIST.is_file():
        return
    import subprocess

    uid = os.getuid()
    target = f"gui/{uid}/{MACOS_LABEL}"
    # bootout first so a rewritten plist is picked up
    subprocess.run(
        ["launchctl", "bootout", f"gui/{uid}", str(MACOS_PLIST)],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["launchctl", "bootstrap", f"gui/{uid}", str(MACOS_PLIST)],
        check=False,
        capture_output=True,
    )
    subprocess.run(["launchctl", "enable", target], check=False, capture_output=True)
    subprocess.run(["launchctl", "kickstart", "-k", target], check=False, capture_output=True)


def _macos_launchctl_unload() -> None:
    if sys.platform != "darwin":
        return
    import subprocess

    uid = os.getuid()
    if MACOS_PLIST.is_file():
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}", str(MACOS_PLIST)],
            check=False,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}/{MACOS_LABEL}"],
            check=False,
            capture_output=True,
        )


def _split_command(command: str) -> list[str]:
    """Minimal quoted-string split for ProgramArguments."""
    import shlex

    return shlex.split(command, posix=(sys.platform != "win32"))
