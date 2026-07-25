"""Framework-independent PDFSilo operation contracts."""

from pdfsilo.core.errors import (
    InvalidInputError,
    OperationCancelledError,
    OutputWriteError,
    PdfPasswordError,
    PdfProcessingError,
    PdfSiloError,
)
from pdfsilo.core.models import OperationResult
from pdfsilo.core.progress import CancellationCheck, ProgressCallback

__all__ = [
    "CancellationCheck",
    "InvalidInputError",
    "OperationCancelledError",
    "OperationResult",
    "OutputWriteError",
    "PdfPasswordError",
    "PdfProcessingError",
    "ProgressCallback",
    "PdfSiloError",
]
