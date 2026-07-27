"""Privacy-limited GitHub release checks and verified update downloads."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pdfsilo import __version__
from pdfsilo.core.progress import CancellationCheck, ProgressCallback
from pdfsilo.updater.errors import (
    UpdateCheckFailedError,
    UpdateDownloadError,
    UpdateVerificationError,
)
from pdfsilo.updater.models import UpdateInfo

RELEASE_API_URL = (
    "https://api.github.com/repos/ABDELLAH-Hallou/PDFSilo/releases/latest"
)
ALLOWED_METADATA_HOST = "api.github.com"
ALLOWED_DOWNLOAD_HOSTS = frozenset(
    {
        "github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    }
)
MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_CHECKSUM_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 15.0
_SEMVER_PATTERN = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?"
    r"(?:\+[0-9A-Za-z.-]+)?$"
)
_SHA256_PATTERN = re.compile(r"\b([0-9a-fA-F]{64})\b")

UrlOpener = Callable[..., BinaryIO]


def _version_key(version: str) -> tuple[int, int, int, tuple[tuple[int, Any], ...]]:
    match = _SEMVER_PATTERN.fullmatch(version.strip())
    if match is None:
        raise ValueError(f"Invalid semantic version: {version!r}")
    prerelease = match.group("prerelease")
    if prerelease is None:
        prerelease_key: tuple[tuple[int, Any], ...] = ((2, 0),)
    else:
        identifiers: list[tuple[int, Any]] = []
        for identifier in prerelease.split("."):
            if identifier.isdigit():
                identifiers.append((0, int(identifier)))
            else:
                identifiers.append((1, identifier.lower()))
        prerelease_key = ((1, 0), *identifiers)
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease_key,
    )


def is_newer_version(candidate: str, current: str = __version__) -> bool:
    """Return whether a semantic version is newer than the running version."""
    return _version_key(candidate) > _version_key(current)


def _validate_https_url(
    url: str,
    *,
    allowed_hosts: frozenset[str],
) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("Update URL is not an approved HTTPS endpoint.")


def _request(
    url: str,
    *,
    allowed_hosts: frozenset[str],
    timeout: float,
    opener: UrlOpener,
    max_bytes: int | None = None,
) -> bytes:
    _validate_https_url(url, allowed_hosts=allowed_hosts)
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"PDFSilo/{__version__}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    with opener(request, timeout=timeout) as response:
        if max_bytes is None:
            return response.read()
        content = response.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValueError("Update response exceeded the allowed size.")
        return content


def _platform_suffixes() -> tuple[str, ...]:
    if sys.platform == "win32":
        return (".msix", ".exe")
    if sys.platform == "darwin":
        return (".dmg",)
    return (".appimage",)


def _platform_markers() -> tuple[str, ...]:
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        return ("x86_64", "amd64", "x64")
    if machine in {"arm64", "aarch64"}:
        return ("arm64", "aarch64")
    return (machine,) if machine else ()


def _select_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    suffixes = _platform_suffixes()
    candidates = [
        asset
        for asset in assets
        if isinstance(asset.get("name"), str)
        and asset["name"].lower().endswith(suffixes)
        and isinstance(asset.get("browser_download_url"), str)
    ]
    if not candidates:
        return None
    markers = _platform_markers()
    matching_architecture = [
        asset
        for asset in candidates
        if any(marker in asset["name"].lower() for marker in markers)
    ]
    return (matching_architecture or candidates)[0]


def _companion_url(
    assets: list[dict[str, Any]],
    asset_name: str,
    suffix: str,
) -> str | None:
    expected = f"{asset_name}{suffix}".lower()
    for asset in assets:
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if (
            isinstance(name, str)
            and name.lower() == expected
            and isinstance(url, str)
        ):
            return url
    return None


def _digest_from_asset(asset: dict[str, Any]) -> str:
    digest = asset.get("digest")
    if not isinstance(digest, str):
        return ""
    algorithm, separator, value = digest.partition(":")
    if separator and algorithm.lower() == "sha256":
        value = value.strip().lower()
        if re.fullmatch(r"[0-9a-f]{64}", value):
            return value
    return ""


def check_for_update(
    *,
    current_version: str = __version__,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: UrlOpener = urlopen,
) -> UpdateInfo | None:
    """Return a newer GitHub release for this platform, if one exists."""
    if is_cancelled is not None and is_cancelled():
        raise UpdateCheckFailedError("Update check cancelled.")
    if progress is not None:
        progress(0, 1, "Checking for updates…")
    try:
        raw = _request(
            RELEASE_API_URL,
            allowed_hosts=frozenset({ALLOWED_METADATA_HOST}),
            timeout=timeout,
            opener=opener,
            max_bytes=MAX_METADATA_BYTES,
        )
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Release metadata is not an object.")
        tag = payload.get("tag_name")
        if not isinstance(tag, str):
            raise ValueError("Release metadata has no version tag.")
        version = tag.removeprefix("v")
        if not is_newer_version(version, current_version):
            if progress is not None:
                progress(1, 1, "PDFSilo is up to date.")
            return None
        assets = payload.get("assets")
        if not isinstance(assets, list):
            raise ValueError("Release metadata has no assets.")
        asset_records = [
            item for item in assets if isinstance(item, dict)
        ]
        asset = _select_asset(asset_records)
        if asset is None:
            raise ValueError("No update asset is available for this platform.")
        asset_name = asset["name"]
        download_url = asset["browser_download_url"]
        _validate_https_url(
            download_url,
            allowed_hosts=ALLOWED_DOWNLOAD_HOSTS,
        )
        checksum_url = _companion_url(
            asset_records,
            asset_name,
            ".sha256",
        )
        if checksum_url is not None:
            _validate_https_url(
                checksum_url,
                allowed_hosts=ALLOWED_DOWNLOAD_HOSTS,
            )
        signature_url = _companion_url(asset_records, asset_name, ".sig")
        if signature_url is not None:
            _validate_https_url(
                signature_url,
                allowed_hosts=ALLOWED_DOWNLOAD_HOSTS,
            )
        release_notes_url = payload.get("html_url")
        if not isinstance(release_notes_url, str):
            raise ValueError("Release metadata has no release-notes URL.")
        _validate_https_url(
            release_notes_url,
            allowed_hosts=frozenset({"github.com"}),
        )
        info = UpdateInfo(
            version=version,
            download_url=download_url,
            checksum_sha256=_digest_from_asset(asset),
            signature_url=signature_url,
            release_notes_url=release_notes_url,
            published_at=str(payload.get("published_at") or ""),
            mandatory=False,
            asset_name=asset_name,
            checksum_url=checksum_url,
        )
    except (HTTPError, URLError, OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise UpdateCheckFailedError(
            f"Could not check for PDFSilo updates: {exc}"
        ) from exc
    if is_cancelled is not None and is_cancelled():
        raise UpdateCheckFailedError("Update check cancelled.")
    if progress is not None:
        progress(1, 1, f"PDFSilo {info.version} is available.")
    return info


def update_cache_directory() -> Path:
    """Return PDFSilo's per-user update cache without creating it."""
    if sys.platform == "win32":
        root = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
        return root / "PDFSilo" / "updates"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "PDFSilo" / "updates"
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "pdfsilo" / "updates"


def _expected_checksum(
    info: UpdateInfo,
    *,
    timeout: float,
    opener: UrlOpener,
) -> str:
    if re.fullmatch(r"[0-9a-fA-F]{64}", info.checksum_sha256):
        return info.checksum_sha256.lower()
    if info.checksum_url is None:
        raise UpdateVerificationError(
            "The release does not provide a SHA-256 checksum."
        )
    try:
        raw = _request(
            info.checksum_url,
            allowed_hosts=ALLOWED_DOWNLOAD_HOSTS,
            timeout=timeout,
            opener=opener,
            max_bytes=MAX_CHECKSUM_BYTES,
        )
        match = _SHA256_PATTERN.search(raw.decode("ascii"))
    except (HTTPError, URLError, OSError, UnicodeError, ValueError) as exc:
        raise UpdateVerificationError(
            f"Could not retrieve the update checksum: {exc}"
        ) from exc
    if match is None:
        raise UpdateVerificationError(
            "The published checksum file is invalid."
        )
    return match.group(1).lower()


def download_update(
    info: UpdateInfo,
    *,
    destination_directory: Path | None = None,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: UrlOpener = urlopen,
) -> Path:
    """Download an update asset to a per-user staging directory."""
    destination = destination_directory or update_cache_directory()
    filename = Path(info.asset_name).name
    if not filename:
        filename = Path(urlparse(info.download_url).path).name
    if not filename:
        raise UpdateDownloadError("The update asset has no safe filename.")
    try:
        _validate_https_url(
            info.download_url,
            allowed_hosts=ALLOWED_DOWNLOAD_HOSTS,
        )
        destination.mkdir(parents=True, exist_ok=True)
        final_path = destination / filename
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{filename}.",
            suffix=".part",
            dir=destination,
        )
        temporary_path = Path(temporary_name)
        request = Request(
            info.download_url,
            headers={"User-Agent": f"PDFSilo/{__version__}"},
            method="GET",
        )
        with os.fdopen(descriptor, "wb") as output:
            with opener(request, timeout=timeout) as response:
                raw_total = response.headers.get("Content-Length")
                total = int(raw_total) if raw_total and raw_total.isdigit() else 0
                completed = 0
                while True:
                    if is_cancelled is not None and is_cancelled():
                        raise UpdateDownloadError("Update download cancelled.")
                    chunk = response.read(128 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    completed += len(chunk)
                    if progress is not None:
                        progress(
                            completed,
                            total,
                            "Downloading verified update…",
                        )
        os.replace(temporary_path, final_path)
        return final_path
    except UpdateDownloadError:
        if "temporary_path" in locals():
            temporary_path.unlink(missing_ok=True)
        raise
    except (HTTPError, URLError, OSError, ValueError) as exc:
        if "temporary_path" in locals():
            temporary_path.unlink(missing_ok=True)
        raise UpdateDownloadError(
            f"Could not download the PDFSilo update: {exc}"
        ) from exc


def verify_update(path: Path, expected_sha256: str) -> bool:
    """Verify one downloaded asset against its published SHA-256 digest."""
    expected = expected_sha256.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise UpdateVerificationError("The expected SHA-256 is invalid.")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise UpdateVerificationError(
            f"Could not read the downloaded update: {exc}"
        ) from exc
    if digest.hexdigest() != expected:
        raise UpdateVerificationError(
            "The downloaded update failed SHA-256 verification."
        )
    return True


def download_verified_update(
    info: UpdateInfo,
    *,
    destination_directory: Path | None = None,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    opener: UrlOpener = urlopen,
) -> Path:
    """Download an asset, verify its checksum, and delete it on mismatch."""
    checksum = _expected_checksum(info, timeout=timeout, opener=opener)
    path = download_update(
        info,
        destination_directory=destination_directory,
        progress=progress,
        is_cancelled=is_cancelled,
        timeout=timeout,
        opener=opener,
    )
    try:
        verify_update(path, checksum)
    except UpdateVerificationError:
        path.unlink(missing_ok=True)
        raise
    if progress is not None:
        progress(1, 1, "Update downloaded and verified.")
    return path


__all__ = [
    "ALLOWED_DOWNLOAD_HOSTS",
    "ALLOWED_METADATA_HOST",
    "DEFAULT_TIMEOUT_SECONDS",
    "RELEASE_API_URL",
    "check_for_update",
    "download_update",
    "download_verified_update",
    "is_newer_version",
    "update_cache_directory",
    "verify_update",
]
