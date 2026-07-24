import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

PAGE_SIZES = {
    "A4":     (595, 842),
    "Letter": (612, 792),
}


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format="%(levelname)s: %(message)s")


def validate_pdf(path: Path) -> bool:
    if not path.exists():
        log.error("File '%s' not found.", path)
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
    files = [f for f in folder.iterdir()
             if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    files.sort(key=lambda f: (extract_number_from_filename(f.name), f.name.lower()))
    return [str(f) for f in files]



def warn_if_nonempty(folder: Path) -> None:
    if folder.exists() and any(folder.iterdir()):
        log.warning("Output folder '%s' is not empty — files may be overwritten.", folder)