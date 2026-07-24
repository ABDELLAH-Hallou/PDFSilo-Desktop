"""
add_images.py — Insert images into a PDF document.

Usage:
    python -m safepdf add-images <input> -i IMG [IMG …] [-o OUTPUT]
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
    safepdf add-images report.pdf -i logo.png
    safepdf add-images report.pdf -i photo1.jpg photo2.png --append
    safepdf add-images report.pdf -i stamp.png --page 1 --position 400,700 --width 100
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import validate_pdf

log = logging.getLogger(__name__)

# Supported image extensions (fitz can handle all of these natively)
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}


def _parse_position(pos_str: str) -> tuple[float, float]:
    """Parse a 'X,Y' string into a (float, float) tuple."""
    parts = pos_str.split(",")
    if len(parts) != 2:
        raise ValueError(f"Position must be 'X,Y', got: {pos_str!r}")
    return float(parts[0].strip()), float(parts[1].strip())


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

    if target_width is None and target_height is None:
        # Auto-fit: fill the page width minus margins
        available_w = page.rect.width - x - margin
        scale = available_w / img_width if img_width else 1.0
        tw = available_w
        th = img_height * scale
    elif target_width is not None and target_height is not None:
        tw, th = float(target_width), float(target_height)
    elif target_width is not None:
        tw = float(target_width)
        th = img_height * (tw / img_width) if img_width else tw
    else:
        th = float(target_height)  # type: ignore[arg-type]
        tw = img_width * (th / img_height) if img_height else th

    return fitz.Rect(x, y, x + tw, y + th)


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
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    # Validate image paths
    image_paths_checked: list[Path] = []
    for img in image_paths:
        p = Path(img)
        if not p.exists():
            log.error("Image file not found: '%s'", p)
            return False
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            log.error(
                "Unsupported image format '%s'. Supported: %s",
                p.suffix,
                ", ".join(sorted(SUPPORTED_EXTENSIONS)),
            )
            return False
        image_paths_checked.append(p)

    if not image_paths_checked:
        log.error("No image files provided.")
        return False

    try:
        x, y = _parse_position(position)
    except ValueError as exc:
        log.error("Invalid position: %s", exc)
        return False

    out_path = (
        Path(output_path)
        if output_path
        else path.parent / f"{path.stem}_with_images.pdf"
    )

    try:
        with fitz.open(str(path)) as doc:
            for idx, img_path in enumerate(image_paths_checked):
                # --- Open the image to read its natural dimensions ---
                try:
                    img_doc = fitz.open(str(img_path))
                    pix = img_doc[0].get_pixmap()
                    natural_w, natural_h = pix.width, pix.height
                    img_doc.close()
                except Exception as img_err:
                    log.error("Cannot read image '%s': %s", img_path, img_err)
                    return False

                if append:
                    # Add a new blank A4 page for each image
                    target_page = doc.new_page(width=595, height=842)
                else:
                    if page is not None:
                        # Fixed page (1-indexed)
                        pg_idx = page - 1
                        if pg_idx < 0 or pg_idx >= doc.page_count:
                            log.error(
                                "Page %d out of range (document has %d page(s)).",
                                page,
                                doc.page_count,
                            )
                            return False
                        target_page = doc[pg_idx]
                    else:
                        # Sequential placement; cycle if more images than pages
                        pg_idx = idx % doc.page_count
                        target_page = doc[pg_idx]

                rect = _image_rect(target_page, x, y, natural_w, natural_h, width, height)
                target_page.insert_image(rect, filename=str(img_path))

            doc.save(str(out_path))

        log.info("PDF with images saved to '%s'.", out_path)
        return True

    except Exception as exc:
        log.error("Error adding images to '%s': %s", path, exc)
        return False


def cli_run(args) -> bool:
    return run(
        input_path=args.input,
        image_paths=args.images,
        output_path=args.output,
        page=args.page,
        position=args.position,
        width=args.width,
        height=args.height,
        append=args.append,
    )
