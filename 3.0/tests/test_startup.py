"""Tests for auto-start helpers."""

import sys

from ami.services import startup as st


def test_launch_arguments_dev_mode():
    args = st._launch_arguments()
    assert args is not None
    assert args[-2:] == ["-m", "ami.main"]


def test_launch_environment_dev_mode():
    if getattr(sys, "frozen", False):
        return
    env = st._launch_environment()
    assert "PYTHONPATH" in env
    assert env["PYTHONPATH"].endswith("/src")
