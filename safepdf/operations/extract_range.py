"""
extract_range.py — Extract a page range from a PDF into a new file.

Usage:
    python -m safepdf extract-range <input> -s START -e END [-o OUTPUT]

Arguments:
    input               Path to the input PDF file
    -s, --start         First page to extract, 1-indexed (required)
    -e, --end           Last page to extract, 1-indexed, inclusive (required)
    -o, --output        Output file path (default: <input_stem>_p<start>-p<end>.pdf)

Examples:
    # Extract pages 5 to 12
    safepdf extract-range report.pdf -s 5 -e 12

    # Extract a single page
    safepdf extract-range report.pdf -s 3 -e 3 -o cover.pdf
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import atomic_output_path, validate_pdf

log = logging.getLogger(__name__)


def run(input_path: str, start: int, end: int, output_path: str | None = None) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    out_path = Path(output_path) if output_path else \
        path.parent / f"{path.stem}_p{start}-p{end}.pdf"

    try:
        with fitz.open(str(path)) as src_doc:
            total = len(src_doc)

            if start < 1 or end > total or start > end:
                log.error(
                    "Invalid range %d–%d for a %d-page document.", start, end, total
                )
                return False

            out_doc = fitz.open()
            try:
                out_doc.insert_pdf(src_doc, from_page=start - 1, to_page=end - 1)
                with atomic_output_path(out_path) as temporary:
                    out_doc.save(str(temporary))
                log.info(
                    "Extracted pages %d–%d → '%s' (%d pages).",
                    start, end, out_path, out_doc.page_count,
                )
                return True
            finally:
                out_doc.close()

    except Exception as e:
        log.error("Error extracting range from '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.start, args.end, args.output)
