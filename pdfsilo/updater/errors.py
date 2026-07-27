"""Expected failures raised by PDFSilo's framework-independent updater."""


class UpdaterError(Exception):
    """Base class for expected update errors."""


class UpdateCheckFailedError(UpdaterError):
    """Release metadata could not be retrieved or understood."""


class UpdateDownloadError(UpdaterError):
    """A release asset could not be downloaded safely."""


class UpdateVerificationError(UpdaterError):
    """A downloaded release asset failed integrity verification."""


class UpdateApplyError(UpdaterError):
    """A verified update could not be handed to the platform installer."""


__all__ = [
    "UpdateApplyError",
    "UpdateCheckFailedError",
    "UpdateDownloadError",
    "UpdateVerificationError",
    "UpdaterError",
]
