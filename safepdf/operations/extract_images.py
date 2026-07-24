"""
extract_images.py — Extract all embedded images from a PDF.

Usage:
    python -m safepdf extract-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}]

Arguments:
    input               Path to the input PDF file
    -o, --output        Folder to save extracted images (default: <input_stem>_images/)
    --format            Output image format: png or jpeg (default: png)

Behaviour:
    - Images are saved as p<page>_img<index>.<format>
    - Duplicate images (same xref) are only extracted once
    - A warning is shown if no images are found

Examples:
    safepdf extract-images brochure.pdf
    safepdf extract-images brochure.pdf -o imgs/ --format jpeg
"""

import logging
from pathlib import Path

import fitz

from safepdf.utils import atomic_write_bytes, validate_pdf, warn_if_nonempty

log = logging.getLogger(__name__)


def _image_bytes(doc: fitz.Document, xref: int, smask: int, fmt: str) -> bytes:
    """Decode an embedded image and encode it in the requested format."""
    base = fitz.Pixmap(doc, xref)
    pix = base

    if smask:
        try:
            mask = fitz.Pixmap(doc, smask)
            pix = fitz.Pixmap(base, mask)
        except Exception as exc:
            log.debug("Could not apply soft mask %d to image %d: %s", smask, xref, exc)

    if fmt == "jpeg" and (pix.alpha or pix.colorspace not in (fitz.csGRAY, fitz.csRGB)):
        pix = fitz.Pixmap(fitz.csRGB, pix)

    if fmt == "jpeg":
        return pix.tobytes("jpeg", jpg_quality=95)
    return pix.tobytes("png")


def run(input_path: str, output_folder: str | None = None, fmt: str = "png") -> bool:
    path = Path(input_path)
    if not validate_pdf(path):
        return False

    if fmt not in ("png", "jpeg"):
        log.error("Unsupported format '%s'. Choose 'png' or 'jpeg'.", fmt)
        return False

    out_dir = Path(output_folder) if output_folder else path.parent / f"{path.stem}_images"
    warn_if_nonempty(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    seen_xrefs: set[int] = set()
    total_saved = 0

    try:
        with fitz.open(str(path)) as doc:
            for page_num, page in enumerate(doc, start=1):
                for img_index, img in enumerate(page.get_images(full=True), start=1):
                    xref = img[0]
                    smask = img[1]
                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)

                    try:
                        image_bytes = _image_bytes(doc, xref, smask, fmt)
                        ext = fmt
                        out_name = f"p{page_num:03d}_img{img_index:02d}.{ext}"
                        out_path = out_dir / out_name
                        atomic_write_bytes(out_path, image_bytes)
                        log.info("Saved: %s", out_name)
                        total_saved += 1
                    except Exception as e:
                        log.warning("Could not extract image xref %d: %s", xref, e)

        if total_saved == 0:
            log.warning("No images found in '%s'.", path.name)
        else:
            log.info("Extracted %d image(s) to '%s'.", total_saved, out_dir)
        return True

    except Exception as e:
        log.error("Error extracting images from '%s': %s", path, e)
        return False


def cli_run(args) -> bool:
    return run(args.input, args.output, args.format)
