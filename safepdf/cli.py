"""
cli.py — SafePDF unified command-line interface.

Usage:
    python -m safepdf <command> [options]

Commands:
    concat          Merge a folder of PDFs into one normalized PDF
    split           Split a PDF into one file per page
    rotate          Rotate pages by 90 / 180 / 270 degrees
    extract-range   Extract a page range into a new PDF
    compress        Reduce file size by compressing streams and images
    encrypt         Password-protect a PDF (AES-256)
    decrypt         Remove password from a PDF you own
    watermark       Stamp a text watermark on every page
    extract-images  Pull all embedded images out of a PDF
    to-images       Render every page as a PNG or JPEG
    reorder         Rearrange pages in a custom order
    add-images      Insert images into a PDF
    images-to-pdf   Merge a folder of images into a single PDF

Run `python -m safepdf <command> --help` for command-specific options.
"""

import sys
import argparse

from safepdf.utils import setup_logging, PAGE_SIZES
from safepdf.operations import (
    concat, split, rotate, extract_range,
    compress, encrypt, decrypt, watermark,
    extract_images, to_images, reorder, add_images, images_to_pdf,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safepdf",
        description="SafePDF — privacy-first, local PDF toolkit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── concat ────────────────────────────────────────────────────────────────
    p = sub.add_parser("concat", help="Merge a folder of PDFs into one normalized PDF")
    p.add_argument("folder", help="Folder containing PDF files")
    p.add_argument("-o", "--output", default=None, help="Output file path")
    p.add_argument("-s", "--size", choices=list(PAGE_SIZES), default="A4",
                   help="Target page size (default: A4)")

    # ── split ─────────────────────────────────────────────────────────────────
    p = sub.add_parser("split", help="Split a PDF into one file per page")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-o", "--output", default=None, help="Output folder")

    # ── rotate ────────────────────────────────────────────────────────────────
    p = sub.add_parser("rotate", help="Rotate pages in a PDF")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-a", "--angle", type=int, choices=[90, 180, 270], required=True,
                   help="Rotation angle in degrees")
    p.add_argument("-p", "--pages", default=None,
                   help="Comma-separated page numbers to rotate (default: all)")
    p.add_argument("-o", "--output", default=None, help="Output file path")

    # ── extract-range ─────────────────────────────────────────────────────────
    p = sub.add_parser("extract-range", help="Extract a page range into a new PDF")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-s", "--start", type=int, required=True, help="First page (1-indexed)")
    p.add_argument("-e", "--end", type=int, required=True, help="Last page (1-indexed, inclusive)")
    p.add_argument("-o", "--output", default=None, help="Output file path")

    # ── compress ──────────────────────────────────────────────────────────────
    p = sub.add_parser("compress", help="Reduce PDF file size")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-o", "--output", default=None, help="Output file path")
    p.add_argument("-q", "--quality", type=int, default=60,
                   help="Image quality 1–100 (default: 60)")

    # ── encrypt ───────────────────────────────────────────────────────────────
    p = sub.add_parser("encrypt", help="Password-protect a PDF (AES-256)")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-p", "--password", required=True, help="User password")
    p.add_argument(
        "--owner-password",
        default=None,
        help="Owner password (required and must differ when restrictions are used)",
    )
    p.add_argument("-o", "--output", default=None, help="Output file path")
    p.add_argument("--no-print", action="store_true", help="Disallow printing")
    p.add_argument("--no-copy", action="store_true", help="Disallow copying")
    p.add_argument("--no-edit", action="store_true", help="Disallow editing")

    # ── decrypt ───────────────────────────────────────────────────────────────
    p = sub.add_parser("decrypt", help="Remove password from a PDF")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-p", "--password", required=True, help="Password to unlock the document")
    p.add_argument("-o", "--output", default=None, help="Output file path")

    # ── watermark ─────────────────────────────────────────────────────────────
    p = sub.add_parser("watermark", help="Stamp a text watermark on every page")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-t", "--text", required=True, help="Watermark text")
    p.add_argument("-o", "--output", default=None, help="Output file path")
    p.add_argument("--opacity", type=float, default=0.15, help="Opacity 0.0–1.0 (default: 0.15)")
    p.add_argument("--angle", type=float, default=45, help="Rotation angle (default: 45)")
    p.add_argument("--size", type=float, default=60, help="Font size in points (default: 60)")
    p.add_argument("--color", default="0.5,0.5,0.5",
                   help="Text color as R,G,B floats (default: 0.5,0.5,0.5)")

    # ── extract-images ────────────────────────────────────────────────────────
    p = sub.add_parser("extract-images", help="Extract all embedded images from a PDF")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-o", "--output", default=None, help="Output folder")
    p.add_argument("--format", choices=["png", "jpeg"], default="png",
                   help="Image format (default: png)")

    # ── to-images ─────────────────────────────────────────────────────────────
    p = sub.add_parser("to-images", help="Render each page as a PNG or JPEG")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-o", "--output", default=None, help="Output folder")
    p.add_argument("--format", choices=["png", "jpeg"], default="png",
                   help="Image format (default: png)")
    p.add_argument("--dpi", type=int, default=150, help="Render resolution (default: 150)")

    # ── reorder ───────────────────────────────────────────────────────────────
    p = sub.add_parser("reorder", help="Rearrange pages in a custom order")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-r", "--order", required=True,
                   help="Comma-separated new page order, e.g. '3,1,2,4'")
    p.add_argument("-o", "--output", default=None, help="Output file path")

    # ── add-images ────────────────────────────────────────────────────────────
    p = sub.add_parser("add-images", help="Insert images into a PDF")
    p.add_argument("input", help="Input PDF file")
    p.add_argument("-i", "--images", nargs="+", required=True,
                   help="Image file(s) to insert (PNG, JPEG, BMP, TIFF, WebP, GIF)")
    p.add_argument("-o", "--output", default=None, help="Output file path")
    p.add_argument("--page", type=int, default=None,
                   help="1-indexed page to stamp every image on (default: sequential)")
    p.add_argument("--position", default="72,72",
                   help="Top-left corner as 'X,Y' in points (default: 72,72)")
    p.add_argument("--width", type=float, default=None,
                   help="Target width in points (default: auto-fit)")
    p.add_argument("--height", type=float, default=None,
                   help="Target height in points (default: preserve aspect ratio)")
    p.add_argument("--append", action="store_true",
                   help="Append a new blank page for each image instead of stamping")

    # ── images-to-pdf ─────────────────────────────────────────────────────────
    p = sub.add_parser("images-to-pdf",
                       help="Merge a folder of images into a single PDF")
    p.add_argument("folder", help="Folder containing image files")
    p.add_argument("-o", "--output", default=None, help="Output PDF file path")
    p.add_argument("-s", "--size", choices=list(PAGE_SIZES), default="A4",
                   help="Target page size (default: A4)")
    p.add_argument("--fit", action="store_true", default=True,
                   help="Scale images to fill the page (default: True)")
    p.add_argument("--no-fit", dest="fit", action="store_false",
                   help="Embed images at natural size, centred")
    p.add_argument("--margin", type=float, default=36.0,
                   help="Margin in points around the image (default: 36)")

    return parser


COMMAND_MAP = {
    "concat":         concat.cli_run,
    "split":          split.cli_run,
    "rotate":         rotate.cli_run,
    "extract-range":  extract_range.cli_run,
    "compress":       compress.cli_run,
    "encrypt":        encrypt.cli_run,
    "decrypt":        decrypt.cli_run,
    "watermark":      watermark.cli_run,
    "extract-images": extract_images.cli_run,
    "to-images":      to_images.cli_run,
    "reorder":        reorder.cli_run,
    "add-images":     add_images.cli_run,
    "images-to-pdf":  images_to_pdf.cli_run,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)
    success = COMMAND_MAP[args.command](args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
