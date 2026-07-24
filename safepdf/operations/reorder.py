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

from safepdf.core import (
    CancellationCheck,
    InvalidInputError,
    OperationResult,
    PdfProcessingError,
    ProgressCallback,
    SafePdfError,
)
from safepdf.core.output import save_document
from safepdf.core.progress import check_cancelled, report_progress
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation

log = logging.getLogger(__name__)


def parse_order(order_str: str, total: int) -> list[int] | None:
    """Legacy parser that logs invalid tokens and returns ``None``."""
    try:
        return _parse_order(order_str, total)
    except InvalidInputError as exc:
        log.error("%s", exc)
        return None


def _parse_order(order_str: str, total: int) -> list[int]:
    """Parse a page order without logging, raising typed input errors."""
    result = []
    for part in order_str.split(","):
        part = part.strip()
        try:
            n = int(part)
            if 1 <= n <= total:
                result.append(n - 1)  # convert to 0-indexed
            else:
                raise InvalidInputError(
                    f"Page {n} out of range (1–{total})."
                )
        except ValueError:
            raise InvalidInputError(f"Invalid page number '{part}'.") from None
    if not result:
        raise InvalidInputError("Page order cannot be empty.")
    return result


def execute(
    input_path: Path,
    order: str,
    output_path: Path | None = None,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Reorder PDF pages and return structured output information."""
    path = require_pdf(input_path)
    out_path = output_path or path.parent / f"{path.stem}_reordered.pdf"

    try:
        with fitz.open(str(path)) as src_doc:
            total = len(src_doc)
            page_order = _parse_order(order, total)

            out_doc = fitz.open()
            try:
                output_page_count = len(page_order)
                for current, idx in enumerate(page_order, start=1):
                    check_cancelled(is_cancelled)
                    out_doc.insert_pdf(src_doc, from_page=idx, to_page=idx)
                    report_progress(
                        progress,
                        current,
                        output_page_count,
                        f"Reordered page {current} of {output_page_count}.",
                    )

                check_cancelled(is_cancelled)
                save_document(out_doc, out_path)
            finally:
                out_doc.close()

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not reorder PDF '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=len(page_order),
        processed_files=1,
        metadata={"original_pages": total, "page_order": page_order},
        message=(
            f"Reordered {total} pages into {len(page_order)} pages at '{out_path}'."
        ),
    )


def run(input_path: str, order: str, output_path: str | None = None) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            order,
            Path(output_path) if output_path else None,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            args.order,
            Path(args.output) if args.output else None,
        ),
        log,
    )
