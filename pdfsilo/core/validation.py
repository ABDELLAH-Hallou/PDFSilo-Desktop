"""Validation helpers that raise typed errors without logging."""

from pathlib import Path

from pdfsilo.core.errors import InvalidInputError


def require_pdf(path: Path) -> Path:
    """Return *path* when it identifies a PDF file, otherwise raise."""
    if not path.exists():
        raise InvalidInputError(f"File '{path}' not found.")
    if not path.is_file():
        raise InvalidInputError(f"'{path}' is not a file.")
    if path.suffix.lower() != ".pdf":
        raise InvalidInputError(f"'{path}' is not a PDF file.")
    return path


def require_directory(path: Path) -> Path:
    """Return *path* when it identifies a directory, otherwise raise."""
    if not path.is_dir():
        raise InvalidInputError(f"'{path}' is not a directory.")
    return path
