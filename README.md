# PDFSilo

**A privacy-first, open-source toolkit — all PDF operations run locally on your
machine. No document uploads, no accounts, and no telemetry.**

PDFSilo is a desktop and command-line toolkit for working with PDF and image
files — split, merge, rotate, compress, encrypt, watermark, extract, reorder,
and insert images — all with consistent page-size normalization. Your
sensitive documents never leave your computer.

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

From an authorized checkout of the private development repository:

```bash
python -m pip install .
```

For an editable development installation with test tooling:

```bash
python -m pip install -e ".[dev]"
```

Run the complete core, CLI, and pytest-qt UI suite with:

```bash
python -m pytest
```

The UI tests use mocked operation contracts for precise parameter assertions
and a separate real-PDF integration layer for end-to-end validation.

### Build the Windows desktop application

Install the deployment tooling, then create and validate the initial
directory-based build:

```powershell
python -m pip install -e ".[dev,deploy]"
.\scripts\build_windows.ps1
.\scripts\test_windows_package.ps1
```

The application directory is written under `dist/windows`. Keep the directory
together; the executable depends on the bundled Qt, Python, PDF, and resource
files beside it. Installer creation and release signing are separate gates:

```powershell
.\scripts\build_windows_installer.ps1 -Version 0.1.0
.\scripts\sign_windows_artifacts.ps1 `
  -CertificateThumbprint "YOUR_CERTIFICATE_THUMBPRINT" `
  -ArtifactPath @(
    ".\dist\windows\PDFSilo.dist\PDFSilo.exe",
    ".\dist\installer\PDFSilo-Setup-0.1.0-x64.exe"
  )
```

See [Windows packaging](packaging/windows/README.md) for prerequisites,
clean-machine validation, signing, and release requirements.

### Continuous integration and Windows releases

The regular CI workflow installs PDFSilo from `pyproject.toml`, runs Ruff,
builds the Python package, tests the core on Python 3.10-3.14, and runs the
headless UI tests on Ubuntu, Windows, and Intel macOS.

Run the same quality gates locally with:

```bash
python -m pip install -e ".[dev]"
python -m ruff check pdfsilo tests scripts
python -m ruff format --check pdfsilo tests scripts
python -m pytest
```

Native release builds are deliberately tag-only. Before pushing a tag:

1. Make the version agree in `pyproject.toml`, `pdfsilo/__init__.py`, and
   `pysidedeploy.spec`.
2. Configure a protected GitHub environment named `release`.
3. Add a fine-grained `PDFSILO_RELEASE_REPOSITORY_TOKEN` environment secret
   with Contents write access to the public release-only `PDFSilo` repository.
4. For a signed release, add `WINDOWS_SIGNING_CERTIFICATE_BASE64` and
   `WINDOWS_SIGNING_CERTIFICATE_PASSWORD` to that environment.
5. Push a stable tag such as `v0.1.0`.

`v0.1.0` is a documented unsigned bootstrap exception. Windows displays
**Unknown publisher**, and SmartScreen can require **More info -> Run anyway**.
The release still requires complete tests, SHA-256 checksums, and a fresh
Windows install/test/uninstall pass. Every other version fails instead of
publishing unsigned output. See [ADR 0008](docs/adr/0008-ci-matrix-and-tag-gated-signed-releases.md)
and [ADR 0009](docs/adr/0009-unsigned-v0-1-0-bootstrap-release.md).

Download release files only from the
[public release channel](https://github.com/ABDELLAH-Hallou/PDFSilo/releases)
or a link on `pdfsilo.com`, and compare the downloaded file with its `.sha256`
companion. The public repository contains release downloads and a short README,
not the private application source or build infrastructure.
SHA-256 detects changed bytes but does not establish who published the file.
Windows x64 is currently the only native release target; Linux and macOS are
CI test targets until their packaging and signing work is complete.

---

## Documentation

- [Codebase analysis](CODEBASE_ANALYSIS.md) — current architecture, quality
  assessment, resolved findings, and remaining risks.
- [PySide6 migration plan](PYSIDE6_MIGRATION_PLAN.md) — completed migration
  phases and pending packaging/CI work.
- [Architecture overview](docs/ARCHITECTURE.md) — runtime boundaries, data
  flow, UI structure, persistence, and resources.
- [Architecture decisions](docs/adr/README.md) — accepted design decisions and
  their consequences.
- [Resolved UI issues](Fixes/Things.to.fix.md) — visual review findings and their
  implementation status.
- [Update feature plan](New%20Features/UPDATE_NOTIFICATION_AND_AUTOUPDATE_PLAN.md)
  — implemented notification/download boundary and deferred signed installation.

---

## Usage

```bash
pdfsilo <command> [options]
pdfsilo <command> --help
pdfsilo-gui
```

The CLI can also be run directly from a source checkout with
`python -m pdfsilo <command> [options]`.

The desktop entry point opens a responsive workspace for all 13 PDF workflows.
Its dashboard provides shortcuts to common tools, while the collapsible
sidebar (`Ctrl+B`) keeps every operation within reach. On wide windows, files
and options sit beside a dedicated document preview; at narrower sizes these
cards stack automatically. Each screen provides validated input and output
selection, operation-specific options, run/cancel controls, progress, status,
structured results, and output-opening actions. Multi-file PDF and image
workflows use ordered lists: files can be added over multiple selections,
dragged into position, moved with keyboard-accessible buttons, or removed.

PDFSilo supports **System default**, **Light**, and **Dark** appearance modes.
Choose one from **Tools → Appearance** or open Settings with `Ctrl+,`. System
default follows the operating-system color scheme and updates while the
application is running. The light workspace uses the PDFSilo indigo and teal
brand system; dark mode uses neutral charcoal surfaces with indigo and teal
reserved for actions and status.

Settings are grouped into **Appearance**, **Workflow**, and **Startup and
privacy**:

| Setting | Default | Effect |
|---|---:|---|
| Theme | System default | Follow the OS or force light/dark mode |
| Show input document previews | On | Render PDF previews beside forms |
| Ask before replacing an output | On | Keep results staged until replacement is confirmed |
| Open containing folder after saving | Off | Open the system file manager after publication |
| Restore window size and position | On | Restore optional window geometry and state |
| Reopen the last-used tool | On | Return to the previous operation screen |
| Automatically check for updates | Off | Contact GitHub at most once per day for release metadata |

**Restore defaults** returns these preferences to their conservative defaults.
Only the choices above, the optional window state, the last tool index, the
last update-check time, and an optionally skipped version are stored. PDFSilo
never stores document paths, document contents, recent files, or passwords in
`QSettings`.

### Updates and network privacy

PDF processing never uses the network. Update checking is the sole optional
network feature:

- Automatic checks are off by default and can be enabled under **Settings →
  Startup and privacy**.
- **Help → Check for Updates…** performs an explicit manual check at any time.
- A check sends one unauthenticated HTTPS GET to PDFSilo's public GitHub
  Releases endpoint. It sends no document data, paths, credentials, telemetry,
  or machine identifier.
- Available releases appear in a non-blocking banner. A version can be skipped.
- PDFSilo can download an artifact to a per-user cache and verify its published
  SHA-256 checksum.
- Downloaded programs are not executed automatically. Install/restart remains
  deferred until signed native installers and signature verification are
  available.

The desktop identity uses the packaged `logo.png` wordmark in the sidebar and
`icon.png` for the application, windows, and About dialog. The same artwork is
used in both themes; dark mode gives the wordmark a small neutral contrast
plate instead of recolouring it.

PDF work runs through a reusable thread-pool worker with GUI-thread signal
delivery, cooperative cancellation, duplicate-start protection, and form-state
restoration. PDF inputs have asynchronous previews with file-aware caching.
The document preview renders a crisp working
image, supports fit and 50–300% zoom, and lets merge users switch among every
input document. Page-size normalization is shown on the preview canvas.
PDF-producing screens stage their result for review and publish it only after
**Save result** is selected; **Discard result** removes the temporary output.
The reorder screen provides thumbnail
drag-and-drop plus selection, duplication, deletion, reversal, and reset
without changing the source file before Run is confirmed.

---

## Python API

Every operation exposes an `execute(...)` function for application and GUI
code. It accepts `pathlib.Path` values, returns an `OperationResult`, and raises
typed `PdfSiloError` exceptions for expected failures:

```python
from pathlib import Path

from pdfsilo.core import PdfSiloError
from pdfsilo.operations.split import execute

try:
    result = execute(Path("document.pdf"))
except PdfSiloError as exc:
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

from pdfsilo.operations.split import execute

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

For a fuller component map and the decisions behind these boundaries, see
[Architecture](docs/ARCHITECTURE.md) and the
[ADR index](docs/adr/README.md).

---

## Commands

### `concat` — Merge PDFs

Merges all PDF files in a folder into a single normalized PDF. Pages from different source sizes are re-rendered to a consistent target size, preserving aspect ratio and centering content.

```bash
python -m pdfsilo concat <folder> [-o OUTPUT] [-s {A4,Letter}]
```

| Argument | Description | Default |
|---|---|---|
| `folder` | Folder containing PDF files | *(required)* |
| `-o`, `--output` | Output file path | `<folder_name>.pdf` |
| `-s`, `--size` | Target page size: `A4` or `Letter` | `A4` |

```bash
python -m pdfsilo concat ./reports
python -m pdfsilo concat ./reports -o merged.pdf -s Letter
```

---

### `split` — Split into pages

Splits a single PDF into one file per page.

```bash
python -m pdfsilo split <input> [-o OUTPUT_FOLDER]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Folder to save split pages | `<input_stem>_pages/` |

```bash
python -m pdfsilo split document.pdf
python -m pdfsilo split document.pdf -o ./pages
```

---

### `rotate` — Rotate pages

Rotates all or specific pages by 90, 180, or 270 degrees.

```bash
python -m pdfsilo rotate <input> -a {90,180,270} [-p PAGES] [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-a`, `--angle` | Rotation angle: `90`, `180`, `270` | *(required)* |
| `-p`, `--pages` | Comma-separated page numbers, 1-indexed | all pages |
| `-o`, `--output` | Output file path | `<input_stem>_rotated.pdf` |

```bash
python -m pdfsilo rotate scan.pdf -a 90
python -m pdfsilo rotate scan.pdf -a 180 -p 1,3,5
```

---

### `extract-range` — Extract pages

Extracts a page range into a new PDF.

```bash
python -m pdfsilo extract-range <input> -s START -e END [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-s`, `--start` | First page to extract, 1-indexed | *(required)* |
| `-e`, `--end` | Last page to extract, 1-indexed, inclusive | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_p<start>-p<end>.pdf` |

```bash
python -m pdfsilo extract-range report.pdf -s 5 -e 12
python -m pdfsilo extract-range report.pdf -s 3 -e 3 -o cover.pdf
```

---

### `compress` — Reduce file size

Compresses streams, fonts, and images to reduce PDF file size.

```bash
python -m pdfsilo compress <input> [-o OUTPUT] [-q QUALITY]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_compressed.pdf` |
| `-q`, `--quality` | Image quality 1–100 | `60` |

```bash
python -m pdfsilo compress large_scan.pdf
python -m pdfsilo compress large_scan.pdf -q 30 -o small.pdf
```

---

### `encrypt` — Password-protect

Encrypts a PDF with AES-256, with optional permission restrictions.

```bash
python -m pdfsilo encrypt <input> [-p PASSWORD] [-o OUTPUT]
                           [--owner-password PW] [--no-print] [--no-copy] [--no-edit]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-p`, `--password` | User password to open the document | secure interactive prompt |
| `--owner-password` | Owner password for permissions; prompted securely, required, and distinct when restrictions are used | same as user password when unrestricted |
| `-o`, `--output` | Output file path | `<input_stem>_encrypted.pdf` |
| `--no-print` | Disallow printing | — |
| `--no-copy` | Disallow copying | — |
| `--no-edit` | Disallow editing | — |

```bash
# Recommended: enter and confirm passwords through hidden prompts
python -m pdfsilo encrypt contract.pdf
python -m pdfsilo encrypt contract.pdf --no-copy

# Explicit arguments remain available for automation
python -m pdfsilo encrypt contract.pdf -p s3cr3t
```

Supplying a password as a command-line argument can expose it through shell
history or process listings. Omit password arguments for interactive use.

---

### `decrypt` — Remove password

Unlocks a password-protected PDF you own.

```bash
python -m pdfsilo decrypt <input> [-p PASSWORD] [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-p`, `--password` | Password to unlock the document | secure interactive prompt |
| `-o`, `--output` | Output file path | `<input_stem>_decrypted.pdf` |

```bash
python -m pdfsilo decrypt contract_encrypted.pdf
```

---

### `watermark` — Stamp text

Stamps a text watermark on every page.

```bash
python -m pdfsilo watermark <input> -t TEXT [-o OUTPUT]
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
python -m pdfsilo watermark report.pdf -t "DRAFT"
python -m pdfsilo watermark report.pdf -t "CONFIDENTIAL" --opacity 0.2 --color 1,0,0
```

---

### `extract-images` — Pull embedded images

Extracts all embedded images from a PDF as PNG or JPEG files.

```bash
python -m pdfsilo extract-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Folder to save images | `<input_stem>_images/` |
| `--format` | Output format: `png` or `jpeg` | `png` |

```bash
python -m pdfsilo extract-images brochure.pdf
python -m pdfsilo extract-images brochure.pdf -o imgs/ --format jpeg
```

---

### `to-images` — Render pages as images

Renders each page as a raster image at a given DPI.

```bash
python -m pdfsilo to-images <input> [-o OUTPUT_FOLDER] [--format {png,jpeg}] [--dpi DPI]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-o`, `--output` | Folder to save rendered images | `<input_stem>_rendered/` |
| `--format` | Output format: `png` or `jpeg` | `png` |
| `--dpi` | Render resolution | `150` |

```bash
python -m pdfsilo to-images presentation.pdf
python -m pdfsilo to-images presentation.pdf --dpi 300 --format jpeg
```

---

### `reorder` — Rearrange pages

Rearranges pages in a custom order. Pages may be omitted (deleted) or repeated (duplicated).

```bash
python -m pdfsilo reorder <input> -r ORDER [-o OUTPUT]
```

| Argument | Description | Default |
|---|---|---|
| `input` | Input PDF file | *(required)* |
| `-r`, `--order` | Comma-separated new page order, 1-indexed | *(required)* |
| `-o`, `--output` | Output file path | `<input_stem>_reordered.pdf` |

```bash
python -m pdfsilo reorder doc.pdf -r 4,3,2,1      # reverse
python -m pdfsilo reorder doc.pdf -r 3,1,2,4      # move page 3 to front
python -m pdfsilo reorder doc.pdf -r 1,1,3,4      # duplicate cover, drop page 2
```

---

### `add-images` — Insert images into a PDF

Stamps one or more image files onto an existing PDF — either on chosen pages or as freshly appended blank pages.
Supported formats: **PNG, JPEG, BMP, TIFF, GIF, WebP**.

```bash
python -m pdfsilo add-images <input> -i IMG [IMG …] [-o OUTPUT]
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
python -m pdfsilo add-images report.pdf -i logo.png --page 1 --position 400,750 --width 100

# Append each photo as a new page at the end
python -m pdfsilo add-images report.pdf -i photo1.jpg photo2.png --append

# Place two images sequentially on pages 1 and 2
python -m pdfsilo add-images report.pdf -i header.png footer.png
```

---

### `images-to-pdf` — Merge a folder of images into a PDF

Collects every image in a folder (sorted by the first number in the filename, then alphabetically) and produces a single PDF with one image per page — the image equivalent of `concat`.
Supported formats: **PNG, JPEG, BMP, TIFF, GIF, WebP**.

```bash
python -m pdfsilo images-to-pdf <folder> [-o OUTPUT] [-s {A4,Letter}]
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
python -m pdfsilo images-to-pdf ./scans/

# Letter-size album with tighter margins
python -m pdfsilo images-to-pdf ./photos/ -s Letter --margin 20 -o album.pdf

# Embed at natural resolution, centred (no scaling)
python -m pdfsilo images-to-pdf ./artwork/ --no-fit -o gallery.pdf
```

---

### `update` — Check for a newer release

Checks PDFSilo's public GitHub Releases feed without downloading or installing
anything.

```bash
pdfsilo update --check
python -m pdfsilo update --check
```

The command prints the current/latest version and release-notes URL. It uses
the same framework-independent updater as the desktop interface.

## Typical workflows

```bash
# Split → reorder → merge
python -m pdfsilo split document.pdf -o pages/
python -m pdfsilo concat pages/ -o document_final.pdf

# Prepare a document for distribution
python -m pdfsilo compress report.pdf -o report_small.pdf
python -m pdfsilo watermark report_small.pdf -t "CONFIDENTIAL"
python -m pdfsilo encrypt report_small_watermarked.pdf -p s3cr3t --no-copy

# Build a PDF from a folder of scanned images
python -m pdfsilo images-to-pdf ./scans/ -o scan_book.pdf

# Add a cover image then compress the result
python -m pdfsilo add-images report.pdf -i cover.png --page 1 --position 72,72
python -m pdfsilo compress report_with_images.pdf -q 70
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
