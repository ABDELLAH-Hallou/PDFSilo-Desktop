"""
add_images.py — Insert images into a PDF document.

Usage:
    python -m pdfsilo add-images <input> -i IMG [IMG …] [-o OUTPUT]
                                 [--page PAGE] [--position X,Y]
                                 [--width WIDTH] [--height HEIGHT]
                                 [--append]

Arguments:
    input               Path to the input PDF file
    -i, --images        One or more image files to insert (required)
    -o, --output        Output file path (default: <input_stem>_with_images.pdf)
    --page              1-indexed page number to stamp each image on
                        (default: stamp sequentially starting from page 1)
    --position          Top-left corner of the image as "X,Y" in points
                        (default: "72,72" — 1-inch from top-left)
    --width             Target width in points (default: preserve aspect ratio
                        scaled to fit the page width minus two margins)
    --height            Target height in points (optional, overrides aspect ratio)
    --append            Append a new blank page for each image instead of
                        stamping on an existing page

Examples:
    pdfsilo add-images report.pdf -i logo.png
    pdfsilo add-images report.pdf -i photo1.jpg photo2.png --append
    pdfsilo add-images report.pdf -i stamp.png --page 1 --position 400,700 --width 100
"""

import logging
import math
from pathlib import Path

import fitz

from pdfsilo.core import (
    CancellationCheck,
    InvalidInputError,
    OperationResult,
    PdfProcessingError,
    ProgressCallback,
    PdfSiloError,
)
from pdfsilo.core.output import save_document
from pdfsilo.core.progress import check_cancelled, report_progress
from pdfsilo.core.validation import require_pdf
from pdfsilo.presentation import present_operation

log = logging.getLogger(__name__)

# Supported image extensions (fitz can handle all of these natively)
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}


def _parse_position(pos_str: str) -> tuple[float, float]:
    """Parse a 'X,Y' string into a (float, float) tuple."""
    parts = pos_str.split(",")
    if len(parts) != 2:
        raise ValueError(f"Position must be 'X,Y', got: {pos_str!r}")
    x, y = float(parts[0].strip()), float(parts[1].strip())
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("Position coordinates must be finite numbers")
    if x < 0 or y < 0:
        raise ValueError("Position coordinates cannot be negative")
    return x, y


def _image_rect(
    page: fitz.Page,
    x: float,
    y: float,
    img_width: int,
    img_height: int,
    target_width: float | None,
    target_height: float | None,
) -> fitz.Rect:
    """Compute the destination rectangle for the image on *page*."""
    margin = 72.0  # 1 inch default margin used when auto-sizing
    if img_width <= 0 or img_height <= 0:
        raise ValueError("Image dimensions must be positive")
    if x >= page.rect.width or y >= page.rect.height:
        raise ValueError("Image position must be inside the target page")

    if target_width is None and target_height is None:
        # Auto-fit inside the remaining page area while preserving aspect ratio.
        available_w = page.rect.width - x - margin
        available_h = page.rect.height - y - margin
        if available_w <= 0 or available_h <= 0:
            raise ValueError("Image position leaves no drawable page area")
        scale = min(available_w / img_width, available_h / img_height)
        tw = img_width * scale
        th = img_height * scale
    elif target_width is not None and target_height is not None:
        tw, th = float(target_width), float(target_height)
    elif target_width is not None:
        tw = float(target_width)
        th = img_height * (tw / img_width) if img_width else tw
    else:
        th = float(target_height)  # type: ignore[arg-type]
        tw = img_width * (th / img_height) if img_height else th

    rect = fitz.Rect(x, y, x + tw, y + th)
    if rect.width <= 0 or rect.height <= 0:
        raise ValueError("Image dimensions must be positive")
    if rect.x1 > page.rect.width or rect.y1 > page.rect.height:
        raise ValueError("Image rectangle extends beyond the target page")
    return rect


def execute(
    input_path: Path,
    image_paths: list[Path],
    output_path: Path | None = None,
    page: int | None = None,
    position: str = "72,72",
    width: float | None = None,
    height: float | None = None,
    append: bool = False,
    *,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    """Insert *image_paths* into the PDF at *input_path*.

    Parameters
    ----------
    input_path:
        Source PDF file.
    image_paths:
        List of image files to insert.
    output_path:
        Destination PDF (defaults to ``<stem>_with_images.pdf``).
    page:
        1-indexed page number to stamp every image on.  When *None* images
        are placed on successive pages (page 1, 2, …).
    position:
        Top-left corner as ``"X,Y"`` in PDF points (default ``"72,72"``).
    width:
        Target width in points.  *None* = auto (page width − margins).
    height:
        Target height in points.  *None* = preserve aspect ratio.
    append:
        When *True* a blank A4 page is appended for each image instead of
        stamping onto existing pages.

    Returns
    -------
    bool
        *True* on success, *False* on any error.
    """
    path = require_pdf(input_path)

    # Validate image paths
    image_paths_checked: list[Path] = []
    for p in image_paths:
        if not p.is_file():
            raise InvalidInputError(f"Image file not found: '{p}'")
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise InvalidInputError(
                f"Unsupported image format '{p.suffix}'. Supported: "
                f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        image_paths_checked.append(p)

    if not image_paths_checked:
        raise InvalidInputError("No image files provided.")

    for label, value in (("Width", width), ("Height", height)):
        if value is not None and (not math.isfinite(value) or value <= 0):
            raise InvalidInputError(
                f"{label} must be a positive finite number."
            )

    try:
        x, y = _parse_position(position)
    except ValueError as exc:
        raise InvalidInputError(f"Invalid position: {exc}") from exc

    out_path = output_path or path.parent / f"{path.stem}_with_images.pdf"

    try:
        with fitz.open(str(path)) as doc:
            original_pages = doc.page_count
            for idx, img_path in enumerate(image_paths_checked):
                check_cancelled(is_cancelled)
                # --- Open the image to read its natural dimensions ---
                try:
                    with fitz.open(str(img_path)) as img_doc:
                        pix = img_doc[0].get_pixmap()
                        natural_w, natural_h = pix.width, pix.height
                except Exception as exc:
                    raise InvalidInputError(
                        f"Cannot read image '{img_path}': {exc}"
                    ) from exc

                if append:
                    # Add a new blank A4 page for each image
                    target_page = doc.new_page(width=595, height=842)
                else:
                    if page is not None:
                        # Fixed page (1-indexed)
                        pg_idx = page - 1
                        if pg_idx < 0 or pg_idx >= doc.page_count:
                            raise InvalidInputError(
                                f"Page {page} out of range "
                                f"(document has {doc.page_count} page(s))."
                            )
                        target_page = doc[pg_idx]
                    else:
                        # Sequential placement; cycle if more images than pages
                        pg_idx = idx % doc.page_count
                        target_page = doc[pg_idx]

                try:
                    rect = _image_rect(
                        target_page,
                        x,
                        y,
                        natural_w,
                        natural_h,
                        width,
                        height,
                    )
                except ValueError as exc:
                    raise InvalidInputError(
                        f"Invalid image geometry: {exc}"
                    ) from exc
                target_page.insert_image(rect, filename=str(img_path))
                report_progress(
                    progress,
                    idx + 1,
                    len(image_paths_checked),
                    (
                        f"Added image {idx + 1} of "
                        f"{len(image_paths_checked)}: {img_path.name}."
                    ),
                )

            resulting_pages = doc.page_count
            check_cancelled(is_cancelled)
            save_document(doc, out_path)

    except PdfSiloError:
        raise
    except Exception as exc:
        raise PdfProcessingError(
            f"Could not add images to PDF '{path}': {exc}"
        ) from exc

    return OperationResult(
        output_paths=[out_path],
        source_paths=[path, *image_paths_checked],
        processed_pages=resulting_pages,
        processed_files=len(image_paths_checked),
        metadata={
            "append": append,
            "original_pages": original_pages,
            "resulting_pages": resulting_pages,
            "target_page": page,
            "position": (x, y),
            "width": width,
            "height": height,
        },
        message=(
            f"Added {len(image_paths_checked)} image(s) and saved '{out_path}'."
        ),
    )


def run(
    input_path: str,
    image_paths: list[str],
    output_path: str | None = None,
    page: int | None = None,
    position: str = "72,72",
    width: float | None = None,
    height: float | None = None,
    append: bool = False,
) -> bool:
    return present_operation(
        lambda: execute(
            Path(input_path),
            [Path(path) for path in image_paths],
            Path(output_path) if output_path else None,
            page,
            position,
            width,
            height,
            append,
        ),
        log,
    )


def cli_run(args) -> bool:
    return present_operation(
        lambda: execute(
            Path(args.input),
            [Path(path) for path in args.images],
            Path(args.output) if args.output else None,
            args.page,
            args.position,
            args.width,
            args.height,
            args.append,
        ),
        log,
    )
