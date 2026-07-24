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
from safepdf.core.progress import CancellationCheck, ProgressCallback

__all__ = [
    "CancellationCheck",
    "InvalidInputError",
    "OperationCancelledError",
    "OperationResult",
    "OutputWriteError",
    "PdfPasswordError",
    "PdfProcessingError",
    "ProgressCallback",
    "SafePdfError",
]
