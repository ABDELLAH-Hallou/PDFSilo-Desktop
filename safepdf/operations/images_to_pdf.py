"""
images_to_pdf.py — Merge a folder of images into a single PDF, one page per image.

Usage:
    python -m safepdf images-to-pdf <folder> [-o OUTPUT] [-s {A4,Letter}]
                                    [--fit] [--margin MARGIN]

Arguments:
    folder              Folder containing image files to merge
    -o, --output        Output PDF file path (default: <folder_name>.pdf)
    -s, --size          Target page size: A4 or Letter (default: A4)
    --fit               Scale image to fill the page while preserving aspect
                        ratio (default: image is centred at its natural size,
                        clipped if larger than the page)
    --margin            Margin in points around the image when --fit is used
                        (default: 36 — half an inch)

Behaviour:
    - Supported formats: PNG, JPEG, BMP, TIFF, GIF, WebP
    - Files are sorted by the first integer in their filename, then
      lexicographically — matching the same natural order used by concat
    - Landscape images automatically get a landscape page
    - Each image is centred on its page

Examples:
    safepdf images-to-pdf ./scans/
    safepdf images-to-pdf ./scans/ -o book.pdf --fit --margin 20
    safepdf images-to-pdf ./photos/ -s Letter -o album.pdf
"""

import logging
import math
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
from safepdf.core.validation import require_directory
from safepdf.presentation import present_operation
from safepdf.utils import (
    IMAGE_EXTENSIONS,
    PAGE_SIZES,
    get_sorted_image_files,
)

log = logging.getLogger(__name__)


def execute(
    folder: Path,
    output_path: Path | None = None,
    target_size: str = "A4",
    fit: bool = True,
    margin: float = 36.0,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Merge every image in *folder* into a single PDF.

    Parameters
    ----------
    folder:
        Directory containing image files.
    output_path:
        Destination PDF (defaults to ``<folder_name>.pdf`` in the parent dir).
    target_size:
        Page canvas size — ``"A4"`` or ``"Letter"``.
    fit:
        When *True* the image is scaled to fill the page (minus *margin*)
        while preserving aspect ratio.  When *False* the image is embedded
        at its natural DPI size and centred; it may be clipped if larger
        than the page.
    margin:
        Padding (in points) around the image on all sides when *fit=True*.

    Returns
    -------
    bool
        *True* on success, *False* on any error.
    """
    if target_size not in PAGE_SIZES:
        raise InvalidInputError(
            f"Unsupported page size '{target_size}'. Choose from: {list(PAGE_SIZES)}"
        )
    if not math.isfinite(margin) or margin < 0:
        raise InvalidInputError("Margin must be a non-negative finite number.")

    folder_path = require_directory(folder)

    image_files = [Path(path) for path in get_sorted_image_files(folder_path)]
    if not image_files:
        raise InvalidInputError(
            f"No supported images found in '{folder_path}'. Supported formats: "
            f"{', '.join(sorted(IMAGE_EXTENSIONS))}"
        )

    out = output_path or folder_path.parent / f"{folder_path.name}.pdf"

    target_w, target_h = PAGE_SIZES[target_size]
    if fit and margin * 2 >= min(target_w, target_h):
        raise InvalidInputError(
            f"Margin {margin:.1f} is too large for {target_size} pages; "
            f"it must be less than {min(target_w, target_h) / 2:.1f}."
        )

    output_doc = fitz.open()
    warnings = []
    processed_files = 0

    try:
        total_files = len(image_files)
        for file_number, img_path in enumerate(image_files, start=1):
            check_cancelled(is_cancelled)
            try:
                # Open the image via fitz to get natural dimensions
                with fitz.open(str(img_path)) as img_doc:
                    pix = img_doc[0].get_pixmap()
                    nat_w, nat_h = pix.width, pix.height
            except Exception as exc:
                warnings.append(f"Skipping '{img_path.name}': {exc}")
                report_progress(
                    progress,
                    file_number,
                    total_files,
                    f"Skipped image {file_number} of {total_files}: {img_path.name}.",
                )
                continue

            # Choose portrait/landscape canvas to match the image orientation
            if nat_w > nat_h:
                pw, ph = max(target_w, target_h), min(target_w, target_h)
            else:
                pw, ph = min(target_w, target_h), max(target_w, target_h)

            page = output_doc.new_page(width=pw, height=ph)

            if fit:
                # Scale to fill the page minus margins, preserving aspect ratio
                avail_w = pw - 2 * margin
                avail_h = ph - 2 * margin
                scale = min(avail_w / nat_w, avail_h / nat_h) if (nat_w and nat_h) else 1.0
                draw_w = nat_w * scale
                draw_h = nat_h * scale
            else:
                # Natural size, centred (may clip if image is too large)
                draw_w = float(nat_w)
                draw_h = float(nat_h)

            x0 = (pw - draw_w) / 2
            y0 = (ph - draw_h) / 2
            rect = fitz.Rect(x0, y0, x0 + draw_w, y0 + draw_h)
            page.insert_image(rect, filename=str(img_path))
            processed_files += 1
            report_progress(
                progress,
                file_number,
                total_files,
                f"Added image {file_number} of {total_files}: {img_path.name}.",
            )

        check_cancelled(is_cancelled)
        if output_doc.page_count == 0:
            raise InvalidInputError(
                "No images could be processed. No output file was created."
            )

        page_count = output_doc.page_count
        save_document(output_doc, out)

    except SafePdfError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not create PDF from images in '{folder_path}': {exc}"
        ) from exc

    finally:
        output_doc.close()

    return OperationResult(
        output_paths=[out],
        source_paths=image_files,
        processed_pages=page_count,
        processed_files=processed_files,
        skipped_files=len(image_files) - processed_files,
        warnings=warnings,
        metadata={
            "target_size": target_size,
            "fit": fit,
            "margin": margin,
        },
        message=(
            f"Created '{out}' with {page_count} page(s) "
            f"from {processed_files} image(s)."
        ),
    )


def run(
    folder: str,
    output_path: str | None = None,
    target_size: str = "A4",
    fit: bool = True,
    margin: float = 36.0,
) -> bool:
    # Preserve the historical direct-Python API for unsupported page sizes.
    if target_size not in PAGE_SIZES:
        raise ValueError(
            f"Unsupported page size '{target_size}'. Choose from: {list(PAGE_SIZES)}"
        )
    return present_operation(
        lambda: execute(
            Path(folder),
            Path(output_path) if output_path else None,
            target_size,
            fit,
            margin,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.folder),
            Path(args.output) if args.output else None,
            args.size,
            args.fit,
            args.margin,
        ),
        log,
    )
