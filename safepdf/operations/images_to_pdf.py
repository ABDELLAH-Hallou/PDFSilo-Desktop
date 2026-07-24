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
from pathlib import Path

import fitz

from safepdf.utils import PAGE_SIZES, get_sorted_image_files, IMAGE_EXTENSIONS

log = logging.getLogger(__name__)


def run(
    folder: str,
    output_path: str | None = None,
    target_size: str = "A4",
    fit: bool = True,
    margin: float = 36.0,
) -> bool:
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
        raise ValueError(
            f"Unsupported page size '{target_size}'. Choose from: {list(PAGE_SIZES)}"
        )

    folder_path = Path(folder)
    if not folder_path.is_dir():
        log.error("'%s' is not a directory.", folder_path)
        return False

    image_files = get_sorted_image_files(folder_path)
    if not image_files:
        log.error(
            "No supported images found in '%s'. Supported formats: %s",
            folder_path,
            ", ".join(sorted(IMAGE_EXTENSIONS)),
        )
        return False

    out = Path(output_path) if output_path else folder_path.parent / f"{folder_path.name}.pdf"

    target_w, target_h = PAGE_SIZES[target_size]
    output_doc = fitz.open()

    try:
        for img_path_str in image_files:
            img_path = Path(img_path_str)
            try:
                # Open the image via fitz to get natural dimensions
                img_doc = fitz.open(str(img_path))
                pix = img_doc[0].get_pixmap()
                nat_w, nat_h = pix.width, pix.height
                img_doc.close()
            except Exception as exc:
                log.warning("Skipping '%s': %s", img_path.name, exc)
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

            log.debug("Added '%s' → page %d", img_path.name, output_doc.page_count)

        if output_doc.page_count == 0:
            log.warning("No images could be processed. No output file created.")
            return False

        output_doc.save(str(out))
        log.info(
            "Created '%s' with %d page(s) from %d image(s).",
            out, output_doc.page_count, len(image_files),
        )
        return True

    except Exception as exc:
        log.error("Unexpected error: %s", exc)
        return False

    finally:
        output_doc.close()


def cli_run(args) -> bool:
    return run(
        folder=args.folder,
        output_path=args.output,
        target_size=args.size,
        fit=args.fit,
        margin=args.margin,
    )
