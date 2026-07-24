"""
reorder.py — Rearrange pages in a PDF by specifying a new page order.

Usage:
    python -m safepdf reorder <input> -r ORDER [-o OUTPUT]

Arguments:
    input               Path to the input PDF file
    -r, --order         Comma-separated new page order, 1-indexed.
                        Pages may be omitted (to delete) or repeated (to duplicate).
                        (required)
    -o, --output        Output file path (default: <input_stem>_reordered.pdf)

Examples:
    # Reverse a 4-page PDF
    safepdf reorder doc.pdf -r 4,3,2,1

    # Move page 3 to the front
    safepdf reorder doc.pdf -r 3,1,2,4

    # Duplicate the cover page and drop page 2
    safepdf reorder doc.pdf -r 1,1,3,4
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import validate_pdf

log = logging.getLogger(__name__)


def parse_order(order_str: str, total: int) -> list[int] | None:
    result = []
    for part in order_str.split(","):
        part = part.strip()
        try:
            n = int(part)
            if 1 <= n <= total:
                result.append(n - 1)  # convert to 0-indexed
            else:
                log.error("Page %d out of range (1–%d).", n, total)
                return None
        except ValueError:
            log.error("Invalid page number '%s'.", part)
            return None
    return result


def run(input_path: str, order: str, output_path: str | None = None) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    out_path = Path(output_path) if output_path else path.parent / f"{path.stem}_reordered.pdf"

    try:
        with fitz.open(str(path)) as src_doc:
            total = len(src_doc)
            page_order = parse_order(order, total)
            if page_order is None:
                return False

            out_doc = fitz.open()
            try:
                for idx in page_order:
                    out_doc.insert_pdf(src_doc, from_page=idx, to_page=idx)

                out_doc.save(str(out_path))
                log.info(
                    "Reordered %d → %d pages, saved to '%s'.",
                    total, len(page_order), out_path,
                )
                return True
            finally:
                out_doc.close()

    except Exception as e:
        log.error("Error reordering '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.order, args.output)