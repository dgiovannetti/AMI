"""
Guards against PyQt6 slot exceptions aborting the process (qFatal/SIGABRT on macOS).
"""

from __future__ import annotations

import functools
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_CRASH_LOG = "/tmp/ami-crash.log"
_installed = False


def _log_exception(context: str, exc: BaseException | None = None) -> None:
    tb = traceback.format_exc() if exc is None else "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    line = f"{datetime.now(timezone.utc).isoformat()} [{context}]\n{tb}\n"
    try:
        print(f"[AMI] {context}: {exc or 'see traceback'}", file=sys.stderr, flush=True)
    except Exception:
        pass
    try:
        with open(_CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def install_exception_handlers() -> None:
    """Install process-wide handlers so uncaught errors log instead of aborting Qt."""
    global _installed
    if _installed:
        return
    _installed = True

    prev = sys.excepthook

    def _excepthook(etype, value, tb) -> None:
        try:
            text = "".join(traceback.format_exception(etype, value, tb))
            with open(_CRASH_LOG, "a", encoding="utf-8") as f:
                f.write(
                    f"{datetime.now(timezone.utc).isoformat()} [sys.excepthook]\n{text}\n"
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
                with open(_CRASH_LOG, "a", encoding="utf-8") as f:
                    f.write(line)
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
