"""Adapters shared by PDFSilo's CLI and legacy boolean Python API."""

import logging
from collections.abc import Callable

from pdfsilo.core import OperationResult, PdfSiloError


def present_operation(
    operation: Callable[[], OperationResult],
    logger: logging.Logger,
) -> bool:
    """Log a structured operation result and expose legacy boolean success."""
    try:
        result = operation()
    except PdfSiloError as exc:
        logger.error("%s", exc)
        return False
    except Exception:
        logger.exception("Unexpected PDFSilo failure.")
        return False

    for warning in result.warnings:
        logger.warning("%s", warning)
    logger.info("%s", result.message)
    return True
