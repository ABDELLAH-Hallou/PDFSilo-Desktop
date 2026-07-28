"""
compress.py — Reduce PDF file size by compressing images and cleaning unused objects.

Usage:
    python -m pdfsilo compress <input> [-o OUTPUT] [-q QUALITY]

Arguments:
    input               Path to the input PDF file
    -o, --output        Output file path (default: <input_stem>_compressed.pdf)
    -q, --quality       Image compression quality 1–100 (default: 60)
                        Lower values = smaller file, lower image quality

Examples:
    # Compress with default quality
    pdfsilo compress large_scan.pdf

    # Aggressive compression
    pdfsilo compress large_scan.pdf -q 30 -o small.pdf
"""

import logging
from pathlib import Path

import fitz

from pdfsilo.core import (
    CancellationCheck,
    InvalidInputError,
    OperationResult,
    PdfProcessingError,
    PdfSiloError,
    ProgressCallback,
)
from pdfsilo.core.output import save_document
from pdfsilo.core.progress import check_cancelled, report_progress
from pdfsilo.core.validation import require_pdf
from pdfsilo.presentation import present_operation

log = logging.getLogger(__name__)


def execute(
    input_path: Path,
    output_path: Path | None = None,
    quality: int = 60,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Compress a PDF and return size metrics."""
    path = require_pdf(input_path)
    if not 1 <= quality <= 100:
        raise InvalidInputError(f"Quality must be between 1 and 100, got {quality}.")

    out_path = output_path or path.parent / f"{path.stem}_compressed.pdf"
    original_size = path.stat().st_size

    try:
        check_cancelled(is_cancelled)
        with fitz.open(str(path)) as doc:
            page_count = doc.page_count
            doc.rewrite_images(quality=quality)
            report_progress(
                progress,
                1,
                1,
                f"Compressed images in '{path.name}'.",
            )
            check_cancelled(is_cancelled)
            save_document(
                doc,
                out_path,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True,
            )

        compressed_size = out_path.stat().st_size
        saved_pct = (1 - compressed_size / original_size) * 100

    except PdfSiloError:
        raise
    except Exception as exc:
        raise PdfProcessingError(f"Could not compress PDF '{path}': {exc}") from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=page_count,
        processed_files=1,
        original_size=original_size,
        resulting_size=compressed_size,
        metadata={"quality": quality, "reduction_percent": saved_pct},
        message=(
            f"Compressed '{path.name}': {original_size / 1024:.1f} KB → "
            f"{compressed_size / 1024:.1f} KB ({saved_pct:.1f}% reduction)."
        ),
    )


def run(input_path: str, output_path: str | None = None, quality: int = 60) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            Path(output_path) if output_path else None,
            quality,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            Path(args.output) if args.output else None,
            args.quality,
        ),
        log,
    )
