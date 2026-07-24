"""
split.py — Split a PDF into one file per page.

Usage:
    python -m safepdf split <input> [-o OUTPUT_FOLDER]

Arguments:
    input               Path to the PDF file to split
    -o, --output        Folder to save split pages (default: <input_stem>_pages/)

Behaviour:
    - Each page is saved as page_001.pdf, page_002.pdf, ...
    - Output folder is created automatically if it does not exist
    - A warning is shown if the output folder already contains files
"""

import logging
from pathlib import Path

import fitz

from safepdf.core import (
    CancellationCheck,
    OperationResult,
    PdfProcessingError,
    ProgressCallback,
    SafePdfError,
)
from safepdf.core.errors import OutputWriteError
from safepdf.core.output import (
    publish_staged_files,
    save_document,
    temporary_output_directory,
)
from safepdf.core.progress import check_cancelled, report_progress
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation

log = logging.getLogger(__name__)


def execute(
    input_path: Path,
    output_folder: Path | None = None,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Split a PDF and return structured output information."""
    path = require_pdf(input_path)
    out_dir = output_folder or path.parent / f"{path.stem}_pages"
    warnings = []
    if out_dir.exists():
        if not out_dir.is_dir():
            raise OutputWriteError(
                f"Output path '{out_dir}' exists and is not a directory."
            )
        if any(out_dir.iterdir()):
            warnings.append(
                f"Output folder '{out_dir}' is not empty — files may be overwritten."
            )

    try:
        with fitz.open(str(path)) as src_doc:
            total = len(src_doc)
            with temporary_output_directory(out_dir) as staging_dir:
                staged_paths = []

                for page_num in range(total):
                    check_cancelled(is_cancelled)
                    out_doc = fitz.open()
                    try:
                        out_doc.insert_pdf(
                            src_doc,
                            from_page=page_num,
                            to_page=page_num,
                        )
                        staged_path = (
                            staging_dir / f"page_{page_num + 1:03d}.pdf"
                        )
                        save_document(out_doc, staged_path)
                        staged_paths.append(staged_path)
                    finally:
                        out_doc.close()

                    report_progress(
                        progress,
                        page_num + 1,
                        total,
                        f"Split page {page_num + 1} of {total}.",
                    )

                check_cancelled(is_cancelled)
                output_paths = publish_staged_files(staged_paths, out_dir)

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not split PDF '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=output_paths,
        source_paths=[path],
        processed_pages=total,
        processed_files=1,
        warnings=warnings,
        message=f"Split {total} pages into '{out_dir}'.",
    )


def run(input_path: str, output_folder: str | None = None) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            Path(output_folder) if output_folder else None,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            Path(args.output) if args.output else None,
        ),
        log,
    )
