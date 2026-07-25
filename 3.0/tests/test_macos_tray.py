"""Tests for macOS tray helpers (no GUI required)."""

import sys

from ami.ui.macos_status_item import _status_label_for_path


def test_status_label_for_path():
    assert _status_label_for_path("/tmp/status_green.png") == "AMI ✓"
    assert _status_label_for_path("/tmp/status_yellow.png") == "AMI !"
    assert _status_label_for_path("/tmp/status_red.png") == "AMI ✕"
    assert _status_label_for_path("/tmp/unknown.png") == "AMI ●"


def test_process_init_events_helper():
    if sys.platform != "darwin":
        return
    from ami.ui.tray_app import _process_init_events

    assert callable(_process_init_events)
