"""
rotate.py — Rotate pages in a PDF.

Usage:
    python -m safepdf rotate <input> -a {90,180,270} [-p PAGES] [-o OUTPUT]

Arguments:
    input               Path to the input PDF file
    -a, --angle         Rotation angle: 90, 180, or 270 degrees (required)
    -p, --pages         Comma-separated page numbers to rotate, 1-indexed
                        (default: all pages)
    -o, --output        Output file path (default: <input_stem>_rotated.pdf)

Examples:
    # Rotate all pages 90 degrees clockwise
    safepdf rotate scan.pdf -a 90

    # Rotate only pages 1 and 3 by 180 degrees
    safepdf rotate scan.pdf -a 180 -p 1,3
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import atomic_output_path, validate_pdf

log = logging.getLogger(__name__)

VALID_ANGLES = {90, 180, 270}


def parse_pages(pages_str: str, total: int) -> list[int]:
    """Parse a comma-separated page string into 0-indexed page numbers."""
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        try:
            n = int(part)
            if 1 <= n <= total:
                result.append(n - 1)
            else:
                log.warning("Page %d out of range (1–%d). Skipping.", n, total)
        except ValueError:
            log.warning("Invalid page number '%s'. Skipping.", part)
    return result


def run(input_path: str, angle: int, pages: str | None = None, output_path: str | None = None) -> bool:
    if angle not in VALID_ANGLES:
        log.error("Invalid angle %d. Choose from: %s", angle, VALID_ANGLES)
        return False

    path = Path(input_path)
    if not validate_pdf(path):
        return False

    out_path = Path(output_path) if output_path else path.parent / f"{path.stem}_rotated.pdf"

    try:
        with atomic_output_path(out_path) as temporary:
            with fitz.open(str(path)) as doc:
                total = len(doc)
                targets = parse_pages(pages, total) if pages else list(range(total))

                for i in targets:
                    page = doc[i]
                    page.set_rotation((page.rotation + angle) % 360)
                    log.info("Rotated page %d by %d°", i + 1, angle)

                doc.save(str(temporary))
            log.info("Saved rotated PDF to '%s'.", out_path)
            return True

    except Exception as e:
        log.error("Error rotating '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.angle, args.pages, args.output)
