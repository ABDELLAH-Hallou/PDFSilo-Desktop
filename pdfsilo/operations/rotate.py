"""
rotate.py — Rotate pages in a PDF.

Usage:
    python -m pdfsilo rotate <input> -a {90,180,270} [-p PAGES] [-o OUTPUT]

Arguments:
    input               Path to the input PDF file
    -a, --angle         Rotation angle: 90, 180, or 270 degrees (required)
    -p, --pages         Comma-separated page numbers to rotate, 1-indexed
                        (default: all pages)
    -o, --output        Output file path (default: <input_stem>_rotated.pdf)

Examples:
    # Rotate all pages 90 degrees clockwise
    pdfsilo rotate scan.pdf -a 90

    # Rotate only pages 1 and 3 by 180 degrees
    pdfsilo rotate scan.pdf -a 180 -p 1,3
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

VALID_ANGLES = {90, 180, 270}


def parse_pages(pages_str: str, total: int) -> list[int]:
    """Parse a comma-separated page string into 0-indexed page numbers."""
    result, warnings = _parse_pages(pages_str, total)
    for warning in warnings:
        log.warning("%s", warning)
    return result


def _parse_pages(pages_str: str, total: int) -> tuple[list[int], list[str]]:
    """Parse pages without logging and return targets plus warnings."""
    result = []
    warnings = []
    for part in pages_str.split(","):
        part = part.strip()
        try:
            n = int(part)
            if 1 <= n <= total:
                result.append(n - 1)
            else:
                warnings.append(f"Page {n} out of range (1–{total}). Skipping.")
        except ValueError:
            warnings.append(f"Invalid page number '{part}'. Skipping.")
    return result, warnings


def execute(
    input_path: Path,
    angle: int,
    pages: str | None = None,
    output_path: Path | None = None,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Rotate selected PDF pages and return structured output information."""
    if angle not in VALID_ANGLES:
        raise InvalidInputError(
            f"Invalid angle {angle}. Choose from: {sorted(VALID_ANGLES)}."
        )

    path = require_pdf(input_path)
    out_path = output_path or path.parent / f"{path.stem}_rotated.pdf"

    try:
        with fitz.open(str(path)) as doc:
            total = len(doc)
            if pages:
                targets, warnings = _parse_pages(pages, total)
            else:
                targets, warnings = list(range(total)), []

            target_count = len(targets)
            for current, i in enumerate(targets, start=1):
                check_cancelled(is_cancelled)
                page = doc[i]
                page.set_rotation((page.rotation + angle) % 360)
                report_progress(
                    progress,
                    current,
                    target_count,
                    f"Rotated page {current} of {target_count}.",
                )

            check_cancelled(is_cancelled)
            save_document(doc, out_path)

    except PdfSiloError:
        raise
    except Exception as exc:
        raise PdfProcessingError(f"Could not rotate PDF '{path}': {exc}") from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=len(targets),
        processed_files=1,
        warnings=warnings,
        metadata={"angle": angle, "page_indexes": targets},
        message=f"Rotated {len(targets)} pages by {angle}° and saved '{out_path}'.",
    )


def run(
    input_path: str,
    angle: int,
    pages: str | None = None,
    output_path: str | None = None,
) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            angle,
            pages,
            Path(output_path) if output_path else None,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            args.angle,
            args.pages,
            Path(args.output) if args.output else None,
        ),
        log,
    )
