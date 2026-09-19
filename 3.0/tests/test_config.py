"""Tests for config loading, defaults, and migration."""

import json
from pathlib import Path

import jsonschema

from ami.core.config import DEFAULT_CONFIG, _migrate_from_2x


def test_default_config_matches_schema():
    schema_path = Path(__file__).resolve().parents[1] / "config.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=DEFAULT_CONFIG, schema=schema)


def test_default_lookup_public_network_is_on():
    assert DEFAULT_CONFIG["privacy"]["lookup_public_network"] is True


def test_migrate_adds_speed_test_section():
    legacy = {
        "app": {"version": "2.1.0"},
        "monitoring": DEFAULT_CONFIG["monitoring"],
        "thresholds": DEFAULT_CONFIG["thresholds"],
        "notifications": DEFAULT_CONFIG["notifications"],
        "logging": DEFAULT_CONFIG["logging"],
        "api": DEFAULT_CONFIG["api"],
        "startup": DEFAULT_CONFIG["startup"],
        "ui": DEFAULT_CONFIG["ui"],
        "updates": DEFAULT_CONFIG["updates"],
    }
    migrated = _migrate_from_2x(legacy)
    assert "speed_test" in migrated
    assert migrated["app"]["version"].startswith("3.")
    assert migrated["privacy"]["lookup_public_network"] is True


def test_migrate_keeps_explicit_privacy_opt_out():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg["privacy"]["lookup_public_network"] = False
    migrated = _migrate_from_2x(cfg)
    assert migrated["privacy"]["lookup_public_network"] is False


def test_migrate_rewrites_deprecated_speed_url():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg["speed_test"]["test_url"] = "https://speed.cloudflare.com/__down?bytes=52428800"
    migrated = _migrate_from_2x(cfg)
    assert "cloudflare.com" not in migrated["speed_test"]["test_url"]
