"""OTA download refuses a package without a matching SHA256 (no network)."""

import hashlib
import tempfile
from pathlib import Path

from ami.services.updater import UpdateManager


def _manager(tmp_path: Path, monkeypatch) -> UpdateManager:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    return UpdateManager(current_version="3.2.2")


class _Resp:
    def __init__(self, payload: bytes):
        self._payload = payload
        self.headers = {"content-length": str(len(payload))}

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int = 65536):
        yield self._payload


def test_checksum_for_asset_from_release_body():
    digest = "a" * 64
    body = f"AMI-v3.2.2-macos.zip sha256: `{digest}`\n"
    found = UpdateManager()._checksum_for_asset(body, "AMI-v3.2.2-macos.zip")
    assert found == digest
    assert UpdateManager()._checksum_for_asset("no hash here", "AMI-v3.2.2-macos.zip") is None


def test_download_refuses_missing_checksum(tmp_path, monkeypatch):
    mgr = _manager(tmp_path, monkeypatch)

    def boom(*_a, **_k):
        raise AssertionError("must not download without a checksum")

    monkeypatch.setattr("ami.services.updater.requests.get", boom)
    assert mgr.download_update("https://example.com/AMI-macos.zip", None) is None
    assert mgr.last_download_error == "Checksum missing or invalid; update refused"


def test_download_refuses_malformed_checksum(tmp_path, monkeypatch):
    mgr = _manager(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "ami.services.updater.requests.get",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not download")),
    )
    assert mgr.download_update("https://example.com/AMI-macos.zip", "not-a-hash") is None
    assert "invalid" in (mgr.last_download_error or "")


def test_download_refuses_checksum_mismatch(tmp_path, monkeypatch):
    mgr = _manager(tmp_path, monkeypatch)
    payload = b"not-the-release"
    monkeypatch.setattr(
        "ami.services.updater.requests.get",
        lambda *_a, **_k: _Resp(payload),
    )
    wrong = "b" * 64
    assert mgr.download_update("https://example.com/AMI-macos.zip", wrong) is None
    assert mgr.last_download_error == "Checksum mismatch; update refused"
    assert not (tmp_path / "ami_update" / "AMI-macos.zip").exists()


def test_download_accepts_matching_checksum(tmp_path, monkeypatch):
    mgr = _manager(tmp_path, monkeypatch)
    payload = b"release-bytes"
    monkeypatch.setattr(
        "ami.services.updater.requests.get",
        lambda *_a, **_k: _Resp(payload),
    )
    digest = hashlib.sha256(payload).hexdigest()
    path = mgr.download_update("https://example.com/AMI-macos.zip", digest)
    assert path is not None
    assert path.read_bytes() == payload
    assert mgr.last_download_error is None
