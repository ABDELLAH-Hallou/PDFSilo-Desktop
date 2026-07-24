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


def execute(
    input_path: Path,
    start: int,
    end: int,
    output_path: Path | None = None,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Extract an inclusive page range and return structured output details."""
    path = require_pdf(input_path)
    out_path = output_path or path.parent / f"{path.stem}_p{start}-p{end}.pdf"

    try:
        with fitz.open(str(path)) as src_doc:
            total = len(src_doc)

            if start < 1 or end > total or start > end:
                raise InvalidInputError(
                    f"Invalid range {start}–{end} for a {total}-page document."
                )

            out_doc = fitz.open()
            try:
                pages_to_extract = end - start + 1
                for current, page_index in enumerate(
                    range(start - 1, end),
                    start=1,
                ):
                    check_cancelled(is_cancelled)
                    out_doc.insert_pdf(
                        src_doc,
                        from_page=page_index,
                        to_page=page_index,
                    )
                    report_progress(
                        progress,
                        current,
                        pages_to_extract,
                        f"Extracted page {current} of {pages_to_extract}.",
                    )

                check_cancelled(is_cancelled)
                save_document(out_doc, out_path)
                extracted_pages = out_doc.page_count
            finally:
                out_doc.close()

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not extract pages from '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path],
        processed_pages=extracted_pages,
        processed_files=1,
        metadata={"start_page": start, "end_page": end},
        message=(
            f"Extracted pages {start}–{end} to '{out_path}' "
            f"({extracted_pages} pages)."
        ),
    )


def run(input_path: str, start: int, end: int, output_path: str | None = None) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            start,
            end,
            Path(output_path) if output_path else None,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            args.start,
            args.end,
            Path(args.output) if args.output else None,
        ),
        log,
    )
