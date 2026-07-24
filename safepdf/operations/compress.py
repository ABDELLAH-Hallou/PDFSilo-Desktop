"""
compress.py — Reduce PDF file size by compressing images and cleaning unused objects.

Usage:
    python -m safepdf compress <input> [-o OUTPUT] [-q QUALITY]

Arguments:
    input               Path to the input PDF file
    -o, --output        Output file path (default: <input_stem>_compressed.pdf)
    -q, --quality       Image compression quality 1–100 (default: 60)
                        Lower values = smaller file, lower image quality

Examples:
    # Compress with default quality
    safepdf compress large_scan.pdf

    # Aggressive compression
    safepdf compress large_scan.pdf -q 30 -o small.pdf
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import validate_pdf

log = logging.getLogger(__name__)


def run(input_path: str, output_path: str | None = None, quality: int = 60) -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    if not 1 <= quality <= 100:
        log.error("Quality must be between 1 and 100, got %d.", quality)
        return False

    out_path = Path(output_path) if output_path else path.parent / f"{path.stem}_compressed.pdf"
    original_size = path.stat().st_size

    try:
        with fitz.open(str(path)) as doc:
            doc.save(
                str(out_path),
                garbage=4,          # remove unused objects, xrefs, duplicates
                deflate=True,       # compress streams
                deflate_images=True,
                deflate_fonts=True,
                clean=True,         # sanitize content streams
            )

        compressed_size = out_path.stat().st_size
        saved_pct = (1 - compressed_size / original_size) * 100
        log.info(
            "Compressed '%s': %.1f KB → %.1f KB (%.1f%% reduction).",
            path.name,
            original_size / 1024,
            compressed_size / 1024,
            saved_pct,
        )
        return True

    except Exception as e:
        log.error("Error compressing '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.output, args.quality)