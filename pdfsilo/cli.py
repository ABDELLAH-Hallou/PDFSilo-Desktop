"""
cli.py — PDFSilo unified command-line interface.

Usage:
    python -m pdfsilo <command> [options]

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
    update           Check the public release feed for a newer version

Run `python -m pdfsilo <command> --help` for command-specific options.
"""

import argparse
import getpass
import sys
from collections.abc import Callable

from pdfsilo import __version__
from pdfsilo.updater import UpdaterError, check_for_update
from pdfsilo.utils import setup_logging, PAGE_SIZES
from pdfsilo.operations import (
    concat, split, rotate, extract_range,
    compress, encrypt, decrypt, watermark,
    extract_images, to_images, reorder, add_images, images_to_pdf,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdfsilo",
        description="PDFSilo — privacy-first, local PDF toolkit.",
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
    p.add_argument(
        "-p",
        "--password",
        default=None,
        help=(
            "User password (omit to enter it securely; command-line "
            "passwords may be visible to other processes)"
        ),
    )
    p.add_argument(
        "--owner-password",
        default=None,
        help=(
            "Owner password (prompted securely when restrictions require "
            "one; command-line passwords may be visible to other processes)"
        ),
    )
    p.add_argument("-o", "--output", default=None, help="Output file path")
    p.add_argument("--no-print", action="store_true", help="Disallow printing")
    p.add_argument("--no-copy", action="store_true", help="Disallow copying")
    p.add_argument("--no-edit", action="store_true", help="Disallow editing")

    # ── decrypt ───────────────────────────────────────────────────────────────
    p = sub.add_parser("decrypt", help="Remove password from a PDF")
    p.add_argument("input", help="Input PDF file")
    p.add_argument(
        "-p",
        "--password",
        default=None,
        help=(
            "Password to unlock the document (omit to enter it securely; "
            "command-line passwords may be visible to other processes)"
        ),
    )
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

    # ── update ────────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "update",
        help="Check GitHub for a newer PDFSilo release",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Check for an update without downloading anything",
    )

    return parser


def _check_for_cli_update(_args: argparse.Namespace) -> bool:
    """Present the updater core through the command-line interface."""
    try:
        info = check_for_update()
    except UpdaterError as exc:
        print(str(exc), file=sys.stderr)
        return False
    if info is None:
        print(f"PDFSilo {__version__} is up to date.")
        return True
    print(
        f"PDFSilo {info.version} is available "
        f"(current: {__version__})."
    )
    print(f"Release notes: {info.release_notes_url}")
    return True


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
    "update":          _check_for_cli_update,
}


PasswordPrompt = Callable[[str], str]


def _prompt_confirmed_password(
    prompt: PasswordPrompt,
    *,
    label: str,
) -> str:
    password = prompt(f"{label}: ")
    if not password:
        raise ValueError(f"{label} cannot be empty.")
    confirmation = prompt(f"Confirm {label.lower()}: ")
    if password != confirmation:
        raise ValueError(f"{label} confirmation does not match.")
    return password


def resolve_interactive_passwords(
    args: argparse.Namespace,
    prompt: PasswordPrompt | None = None,
) -> None:
    """Populate omitted CLI secrets without exposing typed input on screen."""
    password_prompt = prompt or getpass.getpass
    if args.command == "encrypt":
        if args.password is None:
            args.password = _prompt_confirmed_password(
                password_prompt,
                label="User password",
            )

        restrictions_requested = (
            args.no_print or args.no_copy or args.no_edit
        )
        if restrictions_requested and args.owner_password is None:
            args.owner_password = _prompt_confirmed_password(
                password_prompt,
                label="Owner password",
            )
    elif args.command == "decrypt" and args.password is None:
        password = password_prompt("PDF password: ")
        if not password:
            raise ValueError("PDF password cannot be empty.")
        args.password = password


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        resolve_interactive_passwords(args)
    except (EOFError, KeyboardInterrupt):
        parser.error("Password input was cancelled.")
    except ValueError as exc:
        parser.error(str(exc))
    setup_logging(args.log_level)
    success = COMMAND_MAP[args.command](args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
