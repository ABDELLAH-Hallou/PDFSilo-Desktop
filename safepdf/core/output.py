"""Typed atomic-output helpers for core operations."""

from pathlib import Path
from typing import Any

from safepdf.core.errors import OutputWriteError
from safepdf.utils import atomic_output_path, atomic_write_bytes


def save_document(document: Any, destination: Path, **save_options: Any) -> None:
    """Atomically save a PyMuPDF document or raise ``OutputWriteError``."""
    try:
        with atomic_output_path(destination) as temporary:
            document.save(str(temporary), **save_options)
    except Exception as exc:
        raise OutputWriteError(
            f"Could not write PDF output '{destination}': {exc}"
        ) from exc


def write_bytes(destination: Path, data: bytes) -> None:
    """Atomically write bytes or raise ``OutputWriteError``."""
    try:
        atomic_write_bytes(destination, data)
    except Exception as exc:
        raise OutputWriteError(
            f"Could not write output '{destination}': {exc}"
        ) from exc


def save_pixmap(pixmap: Any, destination: Path, **save_options: Any) -> None:
    """Atomically save a PyMuPDF pixmap or raise ``OutputWriteError``."""
    try:
        with atomic_output_path(destination) as temporary:
            pixmap.save(str(temporary), **save_options)
    except Exception as exc:
        raise OutputWriteError(
            f"Could not write image output '{destination}': {exc}"
        ) from exc
