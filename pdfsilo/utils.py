import logging
import os
import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

log = logging.getLogger(__name__)

PAGE_SIZES = {
    "A4": (595, 842),
    "Letter": (612, 792),
}


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )


def validate_pdf(path: Path) -> bool:
    if not path.exists():
        log.error("File '%s' not found.", path)
        return False
    if not path.is_file():
        log.error("'%s' is not a file.", path)
        return False
    if path.suffix.lower() != ".pdf":
        log.error("'%s' is not a PDF file.", path)
        return False
    return True


def extract_number_from_filename(filename: str) -> int:
    match = re.search(r"\d+", filename)
    return int(match.group()) if match else 0


def get_sorted_pdf_files(folder: Path) -> list[str]:
    files = [f for f in folder.glob("*.pdf") if f.is_file()]
    files.sort(key=lambda f: extract_number_from_filename(f.name))
    return [str(f) for f in files]


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}


def get_sorted_image_files(folder: Path) -> list[str]:
    """Return image files in *folder* sorted by the first integer in their name.

    Falls back to lexicographic order for files with no embedded number, which
    preserves alphabetical ordering (e.g. ``apple.png`` < ``banana.png``).
    """
    files = [
        f
        for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    files.sort(key=lambda f: (extract_number_from_filename(f.name), f.name.lower()))
    return [str(f) for f in files]


def warn_if_nonempty(folder: Path) -> None:
    if folder.exists() and any(folder.iterdir()):
        log.warning(
            "Output folder '%s' is not empty — files may be overwritten.", folder
        )


@contextmanager
def atomic_output_path(destination: Path) -> Generator[Path, None, None]:
    """Yield a temporary sibling path and atomically publish it on success.

    The temporary file lives beside *destination*, so ``os.replace`` stays on
    the same filesystem and is atomic on supported platforms. Existing output
    is left untouched if the caller raises before the context exits.
    """
    destination = Path(destination)
    parent = destination.parent
    if not parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: '{parent}'")

    temporary = parent / (f".{destination.stem}.{uuid4().hex}.tmp{destination.suffix}")

    try:
        yield temporary
        if not temporary.is_file():
            raise FileNotFoundError(
                f"Operation did not create temporary output: '{temporary}'"
            )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_bytes(destination: Path, data: bytes) -> None:
    """Write *data* without exposing a partial destination file."""
    with atomic_output_path(destination) as temporary:
        temporary.write_bytes(data)
