"""Framework-independent SafePDF operation contracts."""

from safepdf.core.errors import (
    InvalidInputError,
    OperationCancelledError,
    OutputWriteError,
    PdfPasswordError,
    PdfProcessingError,
    SafePdfError,
)
from safepdf.core.models import OperationResult

__all__ = [
    "InvalidInputError",
    "OperationCancelledError",
    "OperationResult",
    "OutputWriteError",
    "PdfPasswordError",
    "PdfProcessingError",
    "SafePdfError",
]

