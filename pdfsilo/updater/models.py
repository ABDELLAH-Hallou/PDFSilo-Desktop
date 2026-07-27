"""Structured updater results shared by CLI and desktop presentation layers."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    """A newer platform-specific release available for download."""

    version: str
    download_url: str
    checksum_sha256: str
    signature_url: str | None
    release_notes_url: str
    published_at: str
    mandatory: bool = False
    asset_name: str = ""
    checksum_url: str | None = None


__all__ = ["UpdateInfo"]
