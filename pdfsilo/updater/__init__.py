"""Framework-independent update checking and verified download support."""

from pdfsilo.updater.errors import (
    UpdateApplyError,
    UpdateCheckFailedError,
    UpdateDownloadError,
    UpdaterError,
    UpdateVerificationError,
)
from pdfsilo.updater.models import UpdateInfo
from pdfsilo.updater.service import (
    RELEASE_API_URL,
    check_for_update,
    download_update,
    download_verified_update,
    is_newer_version,
    update_cache_directory,
    verify_update,
)

__all__ = [
    "RELEASE_API_URL",
    "UpdateApplyError",
    "UpdateCheckFailedError",
    "UpdateDownloadError",
    "UpdateInfo",
    "UpdateVerificationError",
    "UpdaterError",
    "check_for_update",
    "download_update",
    "download_verified_update",
    "is_newer_version",
    "update_cache_directory",
    "verify_update",
]
