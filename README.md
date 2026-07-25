# SafePDF

**A privacy-first, open-source toolkit — all PDF operations run locally on your machine. No uploads, no accounts, no third parties.**

SafePDF is a command-line toolkit for working with PDF and image files — split, merge, rotate, compress, encrypt, watermark, extract, reorder, and insert images — all with consistent page-size normalization. Your sensitive documents never leave your computer.

---

## Requirements

- Python 3.10+
- [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`)
- [PySide6](https://doc.qt.io/qtforpython-6/) for the desktop interface

```bash
python -m pip install .
```

---

## Installation

```bash
git clone https://github.com/ABDELLAH-Hallou/SafePDF
cd SafePDF
python -m pip install .
```

For an editable development installation with test tooling:

```bash
python -m pip install -e ".[dev]"
```

---

## Usage

```bash
safepdf <command> [options]
safepdf <command> --help
safepdf-gui
```

The CLI can also be run directly from a source checkout with
`python -m safepdf <command> [options]`.

The desktop entry point opens a complete operation interface for all 13 PDF
workflows. Each screen provides validated input and output selection,
operation-specific options, run/cancel controls, progress, status, structured
results, and output-opening actions. PDF work runs through a reusable
thread-pool worker with GUI-thread signal delivery, cooperative cancellation,
duplicate-start protection, and form-state restoration. PDF inputs have
asynchronous low-resolution previews with file-aware thumbnail caching.
The reorder screen provides thumbnail drag-and-drop plus selection,
duplication, deletion, reversal, and reset without changing the source file
before Run is confirmed.

---

## Python API

Every operation exposes an `execute(...)` function for application and GUI
code. It accepts `pathlib.Path` values, returns an `OperationResult`, and raises
typed `SafePdfError` exceptions for expected failures:

```python
from pathlib import Path

from safepdf.core import SafePdfError
from safepdf.operations.split import execute

try:
    result = execute(Path("document.pdf"))
except SafePdfError as exc:
    print(f"Could not split the PDF: {exc}")
else:
    print(result.message)
    print(result.output_paths)
```

The existing operation-level `run(...) -> bool` functions remain available for
backward compatibility. New Python integrations should prefer `execute(...)`
so they can consume structured results and handle specific error subclasses.

Long-running operations also accept framework-independent progress and
cancellation callbacks:

```python
from pathlib import Path
from threading import Event

from safepdf.operations.split import execute

cancel_requested = Event()

result = execute(
    Path("document.pdf"),
    progress=lambda current, total, message: print(
        f"{current}/{total}: {message}"
    ),
    is_cancelled=cancel_requested.is_set,
)
```

The PySide6 worker layer connects these callbacks to Qt signals and a
thread-safe cancellation flag without importing Qt into PDF operations.

---

## Commands

### `concat` — Merge PDFs

Merges all PDF files in a folder into a single normalized PDF. Pages from different source sizes are re-rendered to a consistent target size, preserving aspect ratio and centering content.

```bash
python -m safepdf concat <folder> [-o OUTPUT] [-s {A4,Letter}]
```

| Argument | Description | Default |
|---|---|---|
| `folder` | Folder containing PDF files | *(required)* |
| `-o`, `--output` | Output file path | `<folder_name>.pdf` |
| `-s`, `--size` | Target page size: `A4` or `Letter` | `A4` |

```bash
python -m safepdf concat ./reports
python -m safepdf concat ./reports -o merged.pdf -s Letter
```

---

### `split` — Split into pages

Splits a single PDF into one file per page.

```bash
python -m safepdf split <input> [-o OUTPUT_FOLDER]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Folder to save split pages | `<input_stem>_pages/` |

```bash
python -m safepdf split document.pdf
python -m safepdf split document.pdf -o ./pages
```

---

### `rotate` — Rotate pages

Rotates all or specific pages by 90, 180, or 270 degrees.

```bash
python -m safepdf rotate <input> -a {90,180,270} [-p PAGES] [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-a`, `--angle` | Rotation angle: `90`, `180`, `270` | *(required)* |
| `-p`, `--pages` | Comma-separated page numbers, 1-indexed | all pages |
| `-o`, `--output` | Output file path | `<input_stem>_rotated.pdf` |

```bash
python -m safepdf rotate scan.pdf -a 90
python -m safepdf rotate scan.pdf -a 180 -p 1,3,5
```

---

### `extract-range` — Extract pages

Extracts a page range into a new PDF.

```bash
python -m safepdf extract-range <input> -s START -e END [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-s`, `--start` | First page to extract, 1-indexed | *(required)* |
| `-e`, `--end` | Last page to extract, 1-indexed, inclusive | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_p<start>-p<end>.pdf` |

```bash
python -m safepdf extract-range report.pdf -s 5 -e 12
python -m safepdf extract-range report.pdf -s 3 -e 3 -o cover.pdf
```

---

### `compress` — Reduce file size

Compresses streams, fonts, and images to reduce PDF file size.

```bash
python -m safepdf compress <input> [-o OUTPUT] [-q QUALITY]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_compressed.pdf` |
| `-q`, `--quality` | Image quality 1–100 | `60` |

```bash
python -m safepdf compress large_scan.pdf
python -m safepdf compress large_scan.pdf -q 30 -o small.pdf
```

---

### `encrypt` — Password-protect

Encrypts a PDF with AES-256, with optional permission restrictions.

```bash
python -m safepdf encrypt <input> -p PASSWORD [-o OUTPUT]
                           [--owner-password PW] [--no-print] [--no-copy] [--no-edit]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-p`, `--password` | User password to open the document | *(required)* |
| `--owner-password` | Owner password for permissions; required and must differ when restrictions are used | same as `-p` when unrestricted |
| `-o`, `--output` | Output file path | `<input_stem>_encrypted.pdf` |
| `--no-print` | Disallow printing | — |
| `--no-copy` | Disallow copying | — |
| `--no-edit` | Disallow editing | — |

```bash
python -m safepdf encrypt contract.pdf -p s3cr3t
python -m safepdf encrypt contract.pdf -p s3cr3t --owner-password adm1n --no-copy
```

---

### `decrypt` — Remove password

Unlocks a password-protected PDF you own.

```bash
python -m safepdf decrypt <input> -p PASSWORD [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-p`, `--password` | Password to unlock the document | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_decrypted.pdf` |

```bash
python -m safepdf decrypt contract_encrypted.pdf -p s3cr3t
```

---

### `watermark` — Stamp text

Stamps a text watermark on every page.

```bash
python -m safepdf watermark <input> -t TEXT [-o OUTPUT]
                             [--opacity OPACITY] [--angle ANGLE] [--size SIZE] [--color R,G,B]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-t`, `--text` | Watermark text | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_watermarked.pdf` |
| `--opacity` | Opacity 0.0–1.0 | `0.15` |
| `--angle` | Rotation angle in degrees | `45` |
| `--size` | Font size in points | `60` |
| `--color` | Color as `R,G,B` floats 0.0–1.0 | `0.5,0.5,0.5` |

```bash
python -m safepdf watermark report.pdf -t "DRAFT"
python -m safepdf watermark report.pdf -t "CONFIDENTIAL" --opacity 0.2 --color 1,0,0
```

---

### `extract-images` — Pull embedded images

Extracts all embedded images from a PDF as PNG or JPEG files.

```bash
python -m safepdf extract-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Folder to save images | `<input_stem>_images/` |
| `--format` | Output format: `png` or `jpeg` | `png` |

```bash
python -m safepdf extract-images brochure.pdf
python -m safepdf extract-images brochure.pdf -o imgs/ --format jpeg
```

---

### `to-images` — Render pages as images

Renders each page as a raster image at a given DPI.

```bash
python -m safepdf to-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}] [--dpi DPI]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Folder to save rendered images | `<input_stem>_rendered/` |
| `--format` | Output format: `png` or `jpeg` | `png` |
| `--dpi` | Render resolution | `150` |

```bash
python -m safepdf to-images presentation.pdf
python -m safepdf to-images presentation.pdf --dpi 300 --format jpeg
```

---

### `reorder` — Rearrange pages

Rearranges pages in a custom order. Pages may be omitted (deleted) or repeated (duplicated).

```bash
python -m safepdf reorder <input> -r ORDER [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-r`, `--order` | Comma-separated new page order, 1-indexed | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_reordered.pdf` |

```bash
python -m safepdf reorder doc.pdf -r 4,3,2,1      # reverse
python -m safepdf reorder doc.pdf -r 3,1,2,4      # move page 3 to front
python -m safepdf reorder doc.pdf -r 1,1,3,4      # duplicate cover, drop page 2
```

---

### `add-images` — Insert images into a PDF

Stamps one or more image files onto an existing PDF — either on chosen pages or as freshly appended blank pages.
Supported formats: **PNG, JPEG, BMP, TIFF, GIF, WebP**.

```bash
python -m safepdf add-images <input> -i IMG [IMG …] [-o OUTPUT]
                              [--page PAGE] [--position X,Y]
                              [--width W] [--height H] [--append]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-i`, `--images` | One or more image files to insert | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_with_images.pdf` |
| `--page` | 1-indexed page to stamp every image on | sequential (page 1, 2, …) |
| `--position` | Top-left corner as `X,Y` in points | `72,72` |
| `--width` | Target width in points | auto-fit to page |
| `--height` | Target height in points | preserve aspect ratio |
| `--append` | Add a new blank A4 page for each image | — |

```bash
# Stamp a logo onto page 1 at a specific position
python -m safepdf add-images report.pdf -i logo.png --page 1 --position 400,750 --width 100

# Append each photo as a new page at the end
python -m safepdf add-images report.pdf -i photo1.jpg photo2.png --append

# Place two images sequentially on pages 1 and 2
python -m safepdf add-images report.pdf -i header.png footer.png
```

---

### `images-to-pdf` — Merge a folder of images into a PDF

Collects every image in a folder (sorted by the first number in the filename, then alphabetically) and produces a single PDF with one image per page — the image equivalent of `concat`.
Supported formats: **PNG, JPEG, BMP, TIFF, GIF, WebP**.

```bash
python -m safepdf images-to-pdf <folder> [-o OUTPUT] [-s {A4,Letter}]
                                 [--fit | --no-fit] [--margin MARGIN]
```

| Argument | Description | Default |
|---|---|---|
| `folder` | Folder containing image files | *(required)* |
| `-o`, `--output` | Output PDF file path | `<folder_name>.pdf` |
| `-s`, `--size` | Target page size: `A4` or `Letter` | `A4` |
| `--fit` / `--no-fit` | Scale image to fill page / embed at natural size | `--fit` |
| `--margin` | Padding in points around the image (with `--fit`) | `36` |

```bash
# Convert a scans folder → scans.pdf (A4, auto-fit)
python -m safepdf images-to-pdf ./scans/

# Letter-size album with tighter margins
python -m safepdf images-to-pdf ./photos/ -s Letter --margin 20 -o album.pdf

# Embed at natural resolution, centred (no scaling)
python -m safepdf images-to-pdf ./artwork/ --no-fit -o gallery.pdf
```

## Typical workflows

```bash
# Split → reorder → merge
python -m safepdf split document.pdf -o pages/
python -m safepdf concat pages/ -o document_final.pdf

# Prepare a document for distribution
python -m safepdf compress report.pdf -o report_small.pdf
python -m safepdf watermark report_small.pdf -t "CONFIDENTIAL"
python -m safepdf encrypt report_small_watermarked.pdf -p s3cr3t --no-copy

# Build a PDF from a folder of scanned images
python -m safepdf images-to-pdf ./scans/ -o scan_book.pdf

# Add a cover image then compress the result
python -m safepdf add-images report.pdf -i cover.png --page 1 --position 72,72
python -m safepdf compress report_with_images.pdf -q 70
```

---

## Page size reference

| Name | Width (pt) | Height (pt) | Inches |
|---|---|---|---|
| A4 | 595 | 842 | 8.27 × 11.69 |
| Letter | 612 | 792 | 8.5 × 11.0 |

*1 point = 1/72 inch*

---

## License

```
BSD 2-Clause License

Copyright (c) 2026-present Abdellah HALLOU

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS 
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, 
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON 
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR 
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF 
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF 
SUCH DAMAGE.
```
