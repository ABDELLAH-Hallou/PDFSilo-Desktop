"""Network-free coverage for the framework-independent updater."""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path
from urllib.error import URLError

import pytest

from pdfsilo.updater import (
    UpdateCheckFailedError,
    UpdateInfo,
    UpdateVerificationError,
    check_for_update,
    download_verified_update,
    is_newer_version,
    verify_update,
)
from pdfsilo.updater.service import RELEASE_API_URL


class FakeResponse(io.BytesIO):
    def __init__(self, content: bytes, *, length: bool = True) -> None:
        super().__init__(content)
        self.headers = {"Content-Length": str(len(content))} if length else {}


def _asset_name(version: str = "0.2.0") -> str:
    if sys.platform == "win32":
        return f"PDFSilo-Setup-{version}.exe"
    if sys.platform == "darwin":
        return f"PDFSilo-{version}.dmg"
    return f"PDFSilo-{version}.AppImage"


def _release_payload(
    *,
    version: str = "0.2.0",
    digest: str = "a" * 64,
    include_checksum_asset: bool = False,
) -> dict[str, object]:
    name = _asset_name(version)
    assets: list[dict[str, object]] = [
        {
            "name": name,
            "browser_download_url": (
                f"https://github.com/ABDELLAH-Hallou/PDFSilo-Desktop/"
                f"releases/download/v{version}/{name}"
            ),
            "digest": f"sha256:{digest}" if digest else None,
        }
    ]
    if include_checksum_asset:
        assets.append(
            {
                "name": f"{name}.sha256",
                "browser_download_url": (
                    f"https://github.com/ABDELLAH-Hallou/PDFSilo-Desktop/"
                    f"releases/download/v{version}/{name}.sha256"
                ),
            }
        )
    return {
        "tag_name": f"v{version}",
        "html_url": (
            "https://github.com/ABDELLAH-Hallou/PDFSilo-Desktop/"
            f"releases/tag/v{version}"
        ),
        "published_at": "2026-07-27T12:00:00Z",
        "assets": assets,
    }


def test_semantic_version_comparison() -> None:
    assert is_newer_version("0.2.0", "0.1.0")
    assert is_newer_version("1.0.0", "1.0.0-rc.1")
    assert not is_newer_version("0.1.0", "0.1.0")
    assert not is_newer_version("0.1.0-rc.1", "0.1.0")
    with pytest.raises(ValueError):
        is_newer_version("latest", "0.1.0")


def test_check_parses_one_fixed_github_request() -> None:
    requests = []

    def opener(request, **_kwargs):
        requests.append(request)
        return FakeResponse(json.dumps(_release_payload()).encode())

    info = check_for_update(current_version="0.1.0", opener=opener)

    assert isinstance(info, UpdateInfo)
    assert info.version == "0.2.0"
    assert info.checksum_sha256 == "a" * 64
    assert info.asset_name == _asset_name()
    assert [request.full_url for request in requests] == [RELEASE_API_URL]
    assert "PDFSilo/" in requests[0].get_header("User-agent")


def test_check_returns_none_when_running_version_is_current() -> None:
    def opener(_request, **_kwargs):
        return FakeResponse(json.dumps(_release_payload()).encode())

    assert check_for_update(current_version="0.2.0", opener=opener) is None


def test_check_wraps_network_errors_without_sensitive_context() -> None:
    def opener(_request, **_kwargs):
        raise URLError("offline")

    with pytest.raises(UpdateCheckFailedError, match="offline"):
        check_for_update(opener=opener)


def test_download_fetches_checksum_and_verifies_asset(tmp_path: Path) -> None:
    content = b"signed-installer-placeholder"
    checksum = hashlib.sha256(content).hexdigest()
    payload = _release_payload(
        digest="",
        include_checksum_asset=True,
    )
    name = _asset_name()
    download_url = payload["assets"][0]["browser_download_url"]
    checksum_url = payload["assets"][1]["browser_download_url"]

    def opener(request, **_kwargs):
        if request.full_url == RELEASE_API_URL:
            return FakeResponse(json.dumps(payload).encode())
        if request.full_url == checksum_url:
            return FakeResponse(f"{checksum}  {name}\n".encode())
        if request.full_url == download_url:
            return FakeResponse(content)
        raise AssertionError(request.full_url)

    info = check_for_update(current_version="0.1.0", opener=opener)
    assert info is not None
    output = download_verified_update(
        info,
        destination_directory=tmp_path,
        opener=opener,
    )

    assert output == tmp_path / name
    assert output.read_bytes() == content


def test_checksum_mismatch_deletes_download(tmp_path: Path) -> None:
    content = b"tampered"
    info = UpdateInfo(
        version="0.2.0",
        download_url=f"https://github.com/example/{_asset_name()}",
        checksum_sha256="0" * 64,
        signature_url=None,
        release_notes_url="https://github.com/example/releases/v0.2.0",
        published_at="",
        asset_name=_asset_name(),
    )

    def opener(_request, **_kwargs):
        return FakeResponse(content)

    with pytest.raises(UpdateVerificationError):
        download_verified_update(
            info,
            destination_directory=tmp_path,
            opener=opener,
        )
    assert list(tmp_path.iterdir()) == []


def test_verify_rejects_invalid_expected_digest(tmp_path: Path) -> None:
    path = tmp_path / "update.exe"
    path.write_bytes(b"content")
    with pytest.raises(UpdateVerificationError):
        verify_update(path, "not-a-sha256")
