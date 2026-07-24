"""Typed atomic-output helpers for core operations."""

import os
import shutil
import tempfile
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from safepdf.core.errors import OutputWriteError
from safepdf.utils import atomic_output_path, atomic_write_bytes


@contextmanager
def temporary_output_directory(destination: Path) -> Generator[Path, None, None]:
    """Create a sibling staging directory and always remove it on exit."""
    parent = destination.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=parent,
            )
        )
    except OSError as exc:
        raise OutputWriteError(
            f"Could not create temporary output for '{destination}': {exc}"
        ) from exc

    try:
        yield temporary
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def publish_staged_files(
    staged_paths: Iterable[Path],
    destination: Path,
) -> list[Path]:
    """Atomically publish staged files into an output directory."""
    try:
        destination.mkdir(parents=True, exist_ok=True)
        output_paths = []
        for staged_path in staged_paths:
            output_path = destination / staged_path.name
            os.replace(staged_path, output_path)
            output_paths.append(output_path)
        return output_paths
    except OSError as exc:
        raise OutputWriteError(
            f"Could not publish output files to '{destination}': {exc}"
        ) from exc


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
