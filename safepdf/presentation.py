"""Adapters shared by SafePDF's CLI and legacy boolean Python API."""

import logging
from collections.abc import Callable

from safepdf.core import OperationResult, SafePdfError


def present_operation(
    operation: Callable[[], OperationResult],
    logger: logging.Logger,
) -> bool:
    """Log a structured operation result and expose legacy boolean success."""
    try:
        result = operation()
    except SafePdfError as exc:
        logger.error("%s", exc)
        return False
    except Exception:
        logger.exception("Unexpected SafePDF failure.")
        return False

    for warning in result.warnings:
        logger.warning("%s", warning)
    logger.info("%s", result.message)
    return True
