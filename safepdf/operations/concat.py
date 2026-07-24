"""
concat.py — Merge multiple PDFs into one normalized PDF.

Usage:
    python -m safepdf concat <folder> [-o OUTPUT] [-s {A4,Letter}]

Arguments:
    folder              Folder containing PDF files to merge
    -o, --output        Output file path (default: <folder_name>.pdf)
    -s, --size          Target page size: A4 or Letter (default: A4)

Behaviour:
    - Files are sorted numerically by the first integer in their filename
    - Each page is scaled to fit the target canvas, preserving aspect ratio
    - Landscape pages are detected and target dimensions flipped accordingly
    - Content is centered on the output page
"""

import logging
from pathlib import Path

import fitz

from safepdf.core import InvalidInputError, OperationResult, PdfProcessingError, SafePdfError
from safepdf.core.output import save_document
from safepdf.core.validation import require_pdf
from safepdf.presentation import present_operation
from safepdf.utils import PAGE_SIZES, get_sorted_pdf_files

log = logging.getLogger(__name__)


def execute(
    input_files: list[Path],
    output_file: Path,
    target_size: str = "A4",
) -> OperationResult:
    """Merge PDFs into normalized pages and return structured details."""
    if target_size not in PAGE_SIZES:
        raise InvalidInputError(
            f"Unsupported page size '{target_size}'. "
            f"Choose from: {list(PAGE_SIZES)}."
        )
    if not input_files:
        raise InvalidInputError("No PDF files were provided.")

    target_w, target_h = PAGE_SIZES[target_size]
    output_doc = fitz.open()
    warnings = []
    processed_files = 0

    try:
        for pdf_path in input_files:
            try:
                path = require_pdf(pdf_path)
            except InvalidInputError as exc:
                warnings.append(str(exc))
                continue

            try:
                with fitz.open(str(path)) as src_doc:
                    for page in src_doc:
                        src_w, src_h = page.rect.width, page.rect.height

                        if src_w > src_h:
                            tw, th = max(target_w, target_h), min(target_w, target_h)
                        else:
                            tw, th = min(target_w, target_h), max(target_w, target_h)

                        scale = min(tw / src_w, th / src_h)
                        scaled_w, scaled_h = src_w * scale, src_h * scale
                        x_offset = (tw - scaled_w) / 2
                        y_offset = (th - scaled_h) / 2

                        new_page = output_doc.new_page(width=tw, height=th)
                        new_page.show_pdf_page(
                            fitz.Rect(x_offset, y_offset,
                                      x_offset + scaled_w, y_offset + scaled_h),
                            src_doc,
                            page.number,
                        )

                    processed_files += 1

            except Exception as exc:
                warnings.append(f"Could not process '{path}': {exc}")

        if output_doc.page_count > 0:
            page_count = output_doc.page_count
            save_document(output_doc, output_file)
        else:
            raise InvalidInputError("No pages to write. No output file was created.")

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not concatenate PDFs into '{output_file}': {exc}"
        ) from exc

    finally:
        output_doc.close()

    return OperationResult(
        output_paths=[output_file],
        source_paths=input_files,
        processed_pages=page_count,
        processed_files=processed_files,
        skipped_files=len(input_files) - processed_files,
        warnings=warnings,
        metadata={"target_size": target_size},
        message=f"Created '{output_file}' with {page_count} pages.",
    )


def run(input_files: list[str], output_file: str, target_size: str = "A4") -> bool:
    # Preserve the historical direct-Python API for unsupported page sizes.
    if target_size not in PAGE_SIZES:
        raise ValueError(
            f"Unsupported page size '{target_size}'. Choose from: {list(PAGE_SIZES)}"
        )
    return present_operation(
        lambda: execute(
            [Path(path) for path in input_files],
            Path(output_file),
            target_size,
        ),
        log,
    )


def cli_run(args) -> bool:
    folder = Path(args.folder)
    output = args.output or f"{folder.name}.pdf"
    input_files = get_sorted_pdf_files(folder)
    return present_operation(
        lambda: execute(
            [Path(path) for path in input_files],
            Path(output),
            args.size,
        ),
        log,
    )
