"""
Guards against PyQt6 slot exceptions aborting the process (qFatal/SIGABRT on macOS).
Crash/diagnostic logs go to the user data dir (readable on Windows).
"""

from __future__ import annotations

import functools
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_installed = False
_crash_log_path: Path | None = None
_announced = False


def crash_log_path() -> Path:
    """Path to ami-crash.log under the user data directory."""
    global _crash_log_path
    if _crash_log_path is not None:
        return _crash_log_path
    try:
        from ami.core.paths import get_user_data_dir

        base = get_user_data_dir()
        base.mkdir(parents=True, exist_ok=True)
        _crash_log_path = base / "ami-crash.log"
    except Exception:
        # Last resort if platformdirs / paths fail at import time.
        if sys.platform == "win32":
            fallback = Path.home() / "AppData" / "Local" / "CiaoIM" / "AMI"
        else:
            fallback = Path("/tmp")
        try:
            fallback.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = Path.home()
        _crash_log_path = fallback / "ami-crash.log"
    return _crash_log_path


def quit_log_path() -> Path:
    """Path to ami-quit.log next to the crash log."""
    return crash_log_path().with_name("ami-quit.log")


def _append_log(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass


def _log_exception(context: str, exc: BaseException | None = None) -> None:
    tb = traceback.format_exc() if exc is None else "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    line = f"{datetime.now(timezone.utc).isoformat()} [{context}]\n{tb}\n"
    try:
        print(f"[AMI] {context}: {exc or 'see traceback'}", file=sys.stderr, flush=True)
    except Exception:
        pass
    _append_log(crash_log_path(), line)


def announce_crash_log_path() -> None:
    """Print crash log location once (so Windows testers know where to look)."""
    global _announced
    if _announced:
        return
    _announced = True
    try:
        print(f"[AMI] Crash log: {crash_log_path()}", file=sys.stderr, flush=True)
    except Exception:
        pass


def install_exception_handlers() -> None:
    """Install process-wide handlers so uncaught errors log instead of aborting Qt."""
    global _installed
    if _installed:
        return
    _installed = True
    announce_crash_log_path()

    prev = sys.excepthook

    def _excepthook(etype, value, tb) -> None:
        try:
            text = "".join(traceback.format_exception(etype, value, tb))
            _append_log(
                crash_log_path(),
                f"{datetime.now(timezone.utc).isoformat()} [sys.excepthook]\n{text}\n",
            )
            print(f"[AMI] Uncaught exception:\n{text}", file=sys.stderr, flush=True)
        except Exception:
            pass
        # Do not re-raise into Qt's fatal path; keep process alive when possible.
        if prev is not None and prev is not sys.__excepthook__:
            try:
                prev(etype, value, tb)
            except Exception:
                pass

    sys.excepthook = _excepthook

    try:
        from PyQt6.QtCore import QtMsgType, qInstallMessageHandler

        def _qt_message_handler(mode, context, message: str) -> None:
            try:
                # Never let QtFatalMsg kill us without a trail.
                level = {
                    QtMsgType.QtDebugMsg: "DEBUG",
                    QtMsgType.QtInfoMsg: "INFO",
                    QtMsgType.QtWarningMsg: "WARNING",
                    QtMsgType.QtCriticalMsg: "CRITICAL",
                    QtMsgType.QtFatalMsg: "FATAL",
                }.get(mode, "MSG")
                line = (
                    f"{datetime.now(timezone.utc).isoformat()} [Qt/{level}] {message}\n"
                )
                _append_log(crash_log_path(), line)
                if mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
                    print(f"[AMI Qt {level}] {message}", file=sys.stderr, flush=True)
            except Exception:
                pass

        qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass


def safe_slot(fn: F) -> F:
    """Wrap a Qt slot/callback so exceptions are logged and never escape to qFatal."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            _log_exception(f"slot:{fn.__qualname__}", exc)
            return None

    return wrapper  # type: ignore[return-value]
