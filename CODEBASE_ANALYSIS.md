# SafePDF Codebase Analysis

_Analysis date: 24 July 2026_

## Executive summary

SafePDF is a compact, privacy-focused Python toolkit for local PDF processing.
It retains its complete command-line interface and now has a functional
PySide6 desktop interface. The desktop window exposes all 13 operations through
validated, cancellable screens backed by the same processing layer as the CLI.

The codebase contains 13 PDF operations implemented with PyMuPDF:

- Merge and split PDFs
- Rotate, extract, and reorder pages
- Compress, encrypt, and decrypt documents
- Add watermarks
- Extract or render images
- Insert images and build PDFs from image folders

The overall design is straightforward and maintainable. Each operation lives in
its own module and now exposes a structured `execute(...) -> OperationResult`
core API. The original `run(...) -> bool` interface and `cli_run(args)` adapter
remain as compatibility presentation layers. The automated test suite is broad
and currently passes. Phase 1 remediation added behavioral coverage for
compression quality, image formats, permission restrictions, numeric
validation, atomic output, and licensing.

## Phase 1 remediation status

The following findings were resolved on 24 July 2026:

| Finding | Resolution |
|---|---|
| Compression quality ignored | Compression now invokes PyMuPDF's image rewriter with the requested quality. |
| Extracted images renamed instead of converted | Images are decoded and explicitly encoded as PNG or JPEG. |
| Restricted encryption reused the user password | Restrictions now require a distinct owner password. |
| Numeric and geometry validation gaps | Opacity, colors, font size, image geometry, coordinates, and margins are validated. |
| Partial file replacement | Outputs are staged beside their destinations and atomically replaced. |
| License mismatch | README and the standalone `LICENSE` file now consistently use BSD 2-Clause. |

Command-line password exposure, image-DPI interpretation, and complete
folder-level transactionality remain future work.

## Phase 2 packaging status

Project packaging was added on 24 July 2026:

- `pyproject.toml` defines SafePDF 0.1.0 for Python 3.10+.
- PyMuPDF and PySide6 are declared runtime dependencies.
- pytest, pytest-qt, and build are available through the `dev` extra.
- `safepdf` and `safepdf-gui` are installed console entry points.
- A minimal PySide6 bootstrap window provides a working GUI entry point.
- An editable install and distributable wheel were built successfully.

## Phase 3 core separation status

Core operations were separated from CLI presentation behavior on 24 July 2026:

- `safepdf.core.OperationResult` reports output paths, messages, warnings,
  source paths, processing counts, file sizes, elapsed time, and metadata.
- Expected failures use `SafePdfError` subclasses for invalid input, passwords,
  output writes, PDF processing, and cancellation.
- All 13 operation modules expose `execute(...) -> OperationResult` and perform
  no CLI logging in that core path.
- Wrapped PyMuPDF and filesystem failures use exception chaining so diagnostic
  context remains available through `__cause__`.
- `safepdf.presentation.present_operation` translates structured outcomes into
  logging and the existing boolean return contract.
- Existing `run(...)` and `cli_run(args)` callers remain compatible.
- CLI success and failure exit codes were verified.

## Phase 4 progress and cancellation status

Framework-independent progress and cancellation were added on 24 July 2026:

- `ProgressCallback` and `CancellationCheck` callable aliases are defined in
  `safepdf.core.progress` without importing PySide6.
- Every operation's `execute(...)` function accepts the callbacks as optional
  keyword-only arguments, preserving all existing callers.
- Iterative operations report completed page, file, or image units and poll for
  cancellation between units and before publishing output.
- Cooperative cancellation raises `OperationCancelledError` directly.
- Folder-producing operations stage work beside the destination. Cancelling
  removes the staging directory and leaves existing destination files intact.
- Single-file operations continue to use atomic output replacement.

## Phase 5 desktop structure status

The PySide6 application structure was created on 24 July 2026:

- The installed `safepdf-gui` entry point creates and configures a
  process-wide `QApplication`.
- `MainWindow` provides the empty desktop shell for the navigation work in
  Phase 6.
- Application identity values are centralized rather than repeated throughout
  widgets.
- Cross-platform color, spacing, typography, and control constants are
  centralized in `safepdf.ui.theme`.
- A scalable SVG icon is packaged in the wheel and assigned at application and
  window level.
- Package locations now exist for future dialogs, pages, reusable widgets, and
  worker infrastructure.

Windows startup was validated through Qt's event loop using the offscreen
platform. The same smoke test is ready for native Linux and macOS runners, but
those platforms were not available in this workspace.

## Phase 6 application shell status

The main application shell was implemented on 24 July 2026:

- A fixed-width sidebar lists Home and all 13 PDF operations.
- A synchronized `QStackedWidget` contains the Home page and operation
  placeholders, using stable page keys for future screen replacement.
- The global status bar supports messages, determinate or indeterminate
  progress, and a latest-output display.
- File, navigation, tools, and help menus expose keyboard-accessible actions.
- A PDF-filtered `QFileDialog` supports initial file selection without
  persisting the selected path.
- Window geometry, window state, and selected navigation page are restored
  through `QSettings`.
- Settings persistence uses an explicit three-key allowlist. Passwords, input
  paths, output paths, and document data are never written to `QSettings`.

## Phase 7 reusable widget status

The shared operation-widget layer was implemented on 24 July 2026:

- One configurable `PathPicker` provides browsing, manual entry, validation,
  invalid-state styling, keyboard labels, drag/drop, and signals.
- Specialized pickers cover single and multiple PDFs, images, existing input
  folders, output files, and output directories.
- `DropZone` provides a focused, keyboard-activatable target with configurable
  file, folder, extension, and multiplicity rules.
- `OperationButtons` provides consistent run/cancel state and signals.
- `ProgressDisplay` supports determinate and indeterminate work.
- `ResultSummary` renders `OperationResult` messages, metrics, warnings, and
  output paths.
- `OutputActions` safely opens an existing output or its containing folder
  through the desktop.
- `OperationPanel` composes these operation-lifecycle widgets for reuse by all
  future operation pages.

## Phase 8 background execution status

The reusable background execution layer was implemented on 24 July 2026:

- `OperationWorker` runs structured core callables through `QRunnable` and
  `QThreadPool`, never through a widget event handler.
- The worker injects the core `progress` and `is_cancelled` callbacks and
  translates outcomes into success, failure, cancellation, and completion
  signals.
- `CancellationToken` uses a thread-safe `threading.Event`.
- `OperationRunner` permits only one active worker, forwards worker events
  through GUI-thread QObject slots, and rejects duplicate starts.
- `OperationController` binds the runner to `OperationPanel` and operation-form
  controls. It preserves and restores each control's previous enabled state
  after success, failure, cancellation, or startup failure.
- Expected `SafePdfError` messages remain distinct from unexpected exceptions,
  while unexpected tracebacks are retained in application logs.

## Phase 9 operation screen status

All operation screens were implemented on 24 July 2026:

- `OperationPage` centralizes form layout, validation, worker/controller
  ownership, progress, cancellation, status, and structured results.
- Concrete pages now cover merge, split, rotate, range extraction, reorder,
  PDF rendering, image-to-PDF conversion, embedded-image extraction, image
  insertion, compression, watermarking, encryption, and decryption.
- Each page invokes the corresponding structured `execute(...)` API through
  the Phase 8 worker; PyMuPDF work does not run in widget event handlers.
- Required paths and operation-specific values are validated before Run is
  enabled. Expected backend validation errors remain visible in the result
  panel when document-dependent checks cannot be performed in advance.
- The main shell mirrors local progress and output state and locks navigation
  while an operation is active.
- Password fields are masked and cleared after encryption or decryption. They
  are not persisted through `QSettings`.

## Phase 10 preview and page-model status

PDF preview and thumbnail-based reordering were implemented on 25 July 2026:

- `ThumbnailService` uses a dedicated `QThreadPool` capped at two concurrent
  jobs. It returns detached `QImage` data and leaves `QPixmap` construction to
  GUI-thread widgets.
- A bounded LRU cache identifies thumbnails by resolved path, modification
  time, file size, page index, and scale. File-signature changes evict stale
  entries, and active widgets refresh through `QFileSystemWatcher`.
- PyMuPDF documents use context managers and render pixmaps are released as
  soon as their samples have been copied.
- All PDF-based operation screens expose either a navigable `PdfPreview` or,
  for Reorder, a thumbnail `PageReorderEditor`.
- Invalid, missing, and encrypted PDFs show explicit preview placeholders.
- `PdfPageListModel` retains original zero-based source indexes while allowing
  internal drag/drop, extended selection, duplication, deletion, reversal,
  and reset.
- Page-list edits remain in memory. Only the confirmed Run action invokes the
  existing reorder operation and writes its separate output.

## Phase 11 password security status

Password handling was hardened on 25 July 2026:

- `PasswordField` provides masked-by-default entry, explicit Show/Hide state,
  accessible labels, and secure clearing that restores masking.
- Encryption requires confirmation of newly entered user and owner passwords,
  explains both roles, and requires a distinct owner password whenever
  permissions are restricted.
- Decryption accepts either password role through the same masked field.
- All password and confirmation fields are cleared after every operation
  completion path.
- The `QSettings` three-key allowlist excludes all form values and secrets.
- Security regression tests verify that passwords never appear in operation
  results, warnings, progress messages, expected errors, or logs.
- CLI password arguments are optional. Missing values use hidden
  `getpass.getpass()` prompts, with confirmation for new encryption passwords.
  Explicit arguments remain available for existing automation but are
  documented as less secure.

## Repository profile

| Area | Result |
|---|---:|
| Python source files | 54 |
| Application source lines | Approximately 7,572 |
| Test files | 25 |
| Test lines | Approximately 3,886 |
| CLI commands | 13 |
| Runtime dependencies | PyMuPDF and PySide6 |
| Test result | 323 passed |
| Test runtime | 32.66 seconds |
| Python version used for validation | 3.14.2 |

A local virtual environment of approximately 85 MiB and generated bytecode
caches are present in the directory. They are covered by `.gitignore`, but this
directory was not a Git working tree at the time of analysis.

## Architecture

The main execution flow is:

```text
argparse CLI / legacy Python API          PySide6 UI
               |                              |
               v                              v
       presentation adapter          OperationController
               |                              |
               |                      OperationRunner
               |                              |
               |                  QThreadPool / QRunnable
               |                              |
               +--------------+---------------+
                              |
                              v
                   operation execute(...)
                             |
                    +--------+--------+
                    |                 |
             OperationResult    SafePdfError
                    |                 |
                    +--------+--------+
                             |
                             v
                         PyMuPDF
                             |
                             v
                      local filesystem
```

The important components are:

- [`safepdf/__main__.py`](safepdf/__main__.py) starts the CLI.
- [`safepdf/cli.py`](safepdf/cli.py) defines arguments and dispatches commands.
- [`safepdf/core/`](safepdf/core/) contains structured results, typed errors,
  core validation, and output publishing helpers.
- [`safepdf/presentation.py`](safepdf/presentation.py) adapts structured core
  outcomes to logging and legacy boolean returns.
- [`safepdf/utils.py`](safepdf/utils.py) contains shared page sizes, sorting,
  logging setup, and atomic-path helpers.
- [`safepdf/operations/`](safepdf/operations/) contains one module per PDF
  operation.
- [`safepdf/ui/workers.py`](safepdf/ui/workers.py) contains cancellation,
  worker, runner, and UI-controller infrastructure.
- [`safepdf/ui/widgets/`](safepdf/ui/widgets/) contains reusable operation-form
  and lifecycle widgets.
- [`tests/`](tests/) contains unit and integration-style tests using real,
  temporary PyMuPDF documents.

No networking, telemetry, account integration, or cloud processing was found.
The privacy claim that operations run locally is consistent with the
implementation.

## Strengths

### Clear module boundaries

Each operation is isolated in a small module. This makes the code easy to read,
test, and modify without introducing unnecessary coupling.

### Consistent operation interface

The `execute(...) -> OperationResult` API gives Python and future GUI callers
typed outcomes without presentation concerns. The combination of
`run(...) -> bool` and `cli_run(args)` preserves the original CLI dispatch and
direct-call contract.

### Good baseline validation

The implementation validates several important inputs, including:

- PDF paths and extensions
- Page ranges and page numbers
- Rotation angles
- Output image formats
- Render DPI
- Compression quality bounds
- Supported image extensions

### Strong automated test breadth

The test suite exercises all operation modules with real PDFs and images rather
than relying entirely on mocks. All 323 tests passed after Phase 11.

### Resource management

Most documents are closed through context managers or `finally` blocks, which
reduces the likelihood of locked files and native resource leaks.

## High-priority findings

### 1. Compression quality was ignored

Status: **Resolved in Phase 1**

Compression now calls `Document.rewrite_images(quality=quality)` before saving,
and a regression test verifies that the selected value reaches the image
rewriter.

Original finding:

[`safepdf/operations/compress.py`](safepdf/operations/compress.py) accepts and
validates a `quality` value from 1 to 100, but the value is never used during
the save operation.

The implementation performs object cleanup and stream deflation:

```python
doc.save(
    str(out_path),
    garbage=4,
    deflate=True,
    deflate_images=True,
    deflate_fonts=True,
    clean=True,
)
```

This can reduce file size, but it does not re-encode raster images at the
requested quality. A quality of `1` and a quality of `100` therefore use the
same processing path.

This contradicts both the CLI help and README, which describe the option as
image quality control.

The existing compression tests verify bounds, file creation, and PDF validity,
but do not compare image encoding or output size across quality values.

Recommended action:

- Implement actual image extraction and recompression at the requested quality,
  then replace the images in the PDF; or
- Remove the `quality` option and describe the feature accurately as lossless
  stream and object optimization.

### 2. Extracted images were renamed instead of converted

Status: **Resolved in Phase 1**

Embedded images are now decoded and explicitly encoded as PNG or JPEG.
Regression tests verify both output file signatures.

Original finding:

[`safepdf/operations/extract_images.py`](safepdf/operations/extract_images.py)
uses `doc.extract_image(xref)` and writes the returned original bytes directly:

```python
image_bytes = base_image["image"]
out_path.write_bytes(image_bytes)
```

The selected `--format` only determines the filename extension. It does not
transcode the bytes. For example, extracting an embedded PNG with
`--format jpeg` produces PNG data in a file named `*.jpeg`.

The current JPEG test checks only that the operation returns `True`; it does
not inspect the output signature or decode the output as JPEG.

Recommended action:

- If the requested format matches the embedded format, write the original
  bytes directly.
- Otherwise decode the image into a pixmap and explicitly encode it as PNG or
  JPEG.
- Add tests that verify magic bytes and successfully reopen the generated file
  as the requested format.

### 3. Passwords are exposed through command-line arguments

Status: **Resolved in Phase 11**

The `encrypt` and `decrypt` commands no longer require `-p/--password`.
Omitted values are read through hidden interactive prompts, and new encryption
passwords are confirmed. Explicit arguments remain supported for automation
and are documented as potentially visible in shell history and process lists.

This behavior is especially undesirable for a privacy-focused application.

Recommended action:

- Make the password argument optional.
- Prompt with `getpass.getpass()` when it is not supplied.
- Optionally support environment variables or protected file descriptors for
  automation.
- Document the security implications of supplying passwords directly on the
  command line.

### 4. Owner-password default weakened permission restrictions

Status: **Resolved in Phase 1**

Restricted encryption now requires an owner password that differs from the
user password. Tests authenticate as the user and verify the permission mask.

Original finding:

[`safepdf/operations/encrypt.py`](safepdf/operations/encrypt.py) defaults the
owner password to the user password:

```python
owner_pw = owner_password or user_password
```

The owner credential normally bypasses PDF permission restrictions. Using the
same credential for both roles can therefore undermine `--no-print`,
`--no-copy`, and `--no-edit`.

Recommended action:

- Require a distinct owner password when permission restrictions are selected;
  or
- Generate a strong random owner password when none is provided and clearly
  explain the recovery implications.
- Add tests that authenticate as a user and verify the resulting permission
  flags.

### 5. License label and license text disagreed

Status: **Resolved in Phase 1**

The README and root-level `LICENSE` file now consistently identify the project
as BSD 2-Clause licensed.

Original finding:

The README labels the license as “MIT License,” but the included wording is the
BSD 2-Clause license. There is also no standalone `LICENSE` file.

Recommended action:

- Decide which license is intended.
- Add the canonical text in a root-level `LICENSE` file.
- Make the README label match that file.

## Medium-priority findings

### Natural image size does not respect image DPI

The `images-to-pdf --no-fit` path treats pixel dimensions as PDF point
dimensions. Since one PDF point is 1/72 inch, a 300-DPI image is not embedded
at its real-world natural size unless its DPI metadata is taken into account.

Either respect image resolution metadata or describe this mode as
“one image pixel per PDF point.”

### Numeric input validation was incomplete

Status: **Resolved in Phase 1 for the identified inputs**

Several values are parsed but not explicitly constrained:

- Watermark opacity is documented as `0.0` to `1.0`.
- Watermark RGB components are documented as `0.0` to `1.0`.
- Watermark font size should be positive.
- Image width and height should be positive.
- Image coordinates should be checked against the target page.
- Image-to-PDF margins should not make the available rectangle negative.

Some invalid values eventually fail inside PyMuPDF, but early validation would
produce clearer errors and prevent inconsistent behavior.

### Partial output can remain after failure

Status: **Partially resolved**

Individual files are written to temporary sibling paths and atomically
published. In Phase 4, `split`, `to-images`, and `extract-images` were changed
to build their files in sibling staging directories. Processing failures and
cancellation therefore remove staged work without changing existing
destination files.

Final folder publication still replaces files individually. A filesystem
failure during that short publication step can leave some files published.
Complete directory-level replacement or a rollback journal would be required
for full transactionality when merging output into an existing directory.

### Broad exception handling weakens the Python API

Status: **Resolved in Phase 3**

All operation modules now expose a structured core function that raises typed
`SafePdfError` subclasses. Expected invalid input, password, output-write, and
PDF-processing failures can be distinguished by library and GUI callers.
Original lower-level exceptions are retained through exception chaining.

CLI logging and the legacy boolean result are handled by a shared presentation
adapter outside the core execution path. The adapter still guards against
unexpected exceptions at the presentation boundary so the CLI remains
backward compatible.

### PDF sorting is not fully deterministic

PDF files are sorted only by the first number found in the filename. Files
without numbers, or files with the same first number, retain the filesystem
enumeration order.

Use a key such as:

```python
(extract_number_from_filename(path.name), path.name.lower())
```

### Watermark placement is not visually centered

The watermark text begins at the page center and rotates around that point.
Long watermarks may therefore extend mostly toward one side or be clipped.
Measure the text width and offset its origin so the text's center aligns with
the page center.

### Some resource handling can be simplified

`decrypt.py` manually closes the document. An exception after opening but
before `close()` can leak the resource. Similar manual image-document handling
appears in the image insertion modules. Context managers should be used
consistently.

## Packaging and repository hygiene

The project now has standards-based package metadata, CLI and GUI entry points,
runtime and development dependencies, and a verified wheel build. It still has
no:

- Dependency lock file
- Continuous integration configuration

`pyproject.toml` is now the authoritative installation definition.
`requirements.txt` remains as a compatibility path for runtime installation.

Recommended action:

- Pin or lock the tested dependency set for reproducible builds.
- Add a CI workflow that runs the suite on the supported Python versions.
- Regenerate or remove the stale `tree.txt`, which does not list all current
  modules.

## Test assessment

The suite provides strong coverage of:

- Successful output creation
- Default output names
- Page counts and common PDF geometry
- Invalid paths and extensions
- Page-range and rotation validation
- CLI adapter delegation
- Encryption and decryption basics
- Image-file ordering

Phase 1 added assertions for:

- Compression quality propagation to the image rewriter.
- PNG and JPEG output signatures.
- User permission flags on restricted encryption.
- Invalid opacity, RGB, dimensions, coordinates, and margins.
- Atomic replacement and destination preservation after failure.
- README and standalone license consistency.

Phase 3 added assertions for:

- Structured result defaults and operation-level metadata.
- Typed validation, password, output-write, and PDF-processing errors.
- Preservation of underlying exception context.
- Warning delivery without core logging.
- CLI translation of structured successes and expected failures.
- Availability of the structured API across all 13 operations.

Phase 4 added assertions for:

- Keyword-only callback availability across all 13 operations.
- Page-, file-, and image-level progress sequences.
- Typed cooperative cancellation.
- Removal of staged folder output after cancellation.
- Preservation of existing folder contents and single-file destinations.

Phase 5 added assertions for:

- Main-window construction and expected placeholder content.
- Application identity and desktop metadata.
- Theme application and idempotence.
- SVG validity, Qt rendering, and package-data configuration.
- Entry-point startup, window display, and clean event-loop shutdown.

Phase 6 added assertions for:

- Sidebar and stacked-page synchronization across every navigation entry.
- Home, previous-page, next-page, and stable-key navigation.
- Global status, determinate and indeterminate progress, and output display.
- Application menus, action shortcuts, and header actions.
- PDF file-dialog selection.
- Window geometry and selected-page restoration.
- The strict `QSettings` allowlist and absence of sensitive paths or passwords.

Phase 7 added assertions for:

- Picker validation, invalid styling, accessors, and stable signals.
- Native dialog routing for single, multiple, directory, and save modes.
- Picker and standalone drop-zone acceptance and rejection.
- Keyboard buddies, accessible control names, and drop-zone activation.
- Run/cancel state and signal behavior.
- Determinate, indeterminate, and reset progress states.
- Structured success, warning, metric, output, and failure presentation.
- Existing-output and containing-folder desktop actions.
- End-to-end `OperationPanel` lifecycle coordination.

Phase 8 added assertions for:

- Worker execution outside the GUI thread.
- GUI-thread delivery of progress and terminal signals.
- Success, typed failure, unexpected failure, cancellation, and completion
  signal ordering.
- Thread-safe, idempotent cancellation.
- Duplicate-start rejection.
- Exact form-control restoration after success, failure, and cancellation.
- Startup test isolation from later queued worker events.

Phase 9 added assertions for:

- A concrete, shared-contract screen for every operation navigation entry.
- End-to-end UI-to-worker execution of all 13 operations using real PDFs and
  images.
- Inline page-list, page-range, watermark-color, and password validation.
- Expected core-error presentation and form restoration.
- Password clearing after encryption and decryption.
- Shell-level progress, navigation locking, cooperative cancellation, and
  state restoration.

Phase 10 added assertions for:

- Preview rendering on a worker thread and `QImage` delivery.
- Dedicated render-pool concurrency limits.
- Cache hits and invalidation after file-signature and scale changes.
- Encrypted and invalid PDF placeholders.
- Preview page navigation and GUI-thread `QPixmap` presentation.
- Preview integration across PDF operation screens.
- Lazy list-model thumbnails and stable original-page index roles.
- Drag/drop, duplication, deletion, reversal, reset, and source-file
  preservation.

Phase 11 added assertions for:

- Masked defaults, explicit visibility toggles, and masking restoration.
- User and owner role guidance, confirmation, and restricted-owner rules.
- Clearing of all password and confirmation fields after operations.
- Complete password exclusion from `QSettings`.
- Optional CLI password arguments and hidden interactive prompting.
- Confirmation mismatch handling without secret reflection.
- Backward-compatible explicit arguments and prompt-before-dispatch behavior.
- Secret exclusion from results, warnings, progress, errors, and logs.

Important missing assertions still include:

- Compression output-size and perceptual-quality comparisons on image-heavy
  documents.
- Complete folder rollback after a multi-file operation fails.
- Corrupt, empty, unusually large, and encrypted input documents.
- Metadata, links, forms, annotations, and bookmarks survive operations where
  preservation is expected.

## Recommended implementation order

1. Add complete folder-level transactional publication where appropriate.
2. Correct natural-DPI image placement.
3. Add dependency locking and CI.
4. Validate and package the application on native Windows, Linux, and macOS.
5. Add preview-aware page-range and rotation selection.
6. Add protected automation inputs such as file descriptors if required.

## Final assessment

SafePDF has a good foundation: its architecture is small, comprehensible, and
well tested. Phase 1 corrected the compression, extracted-image, restricted
encryption, validation, atomic-output, and licensing findings. Phase 3 added a
structured, typed core API while preserving CLI behavior. Phase 4 added
framework-independent progress, cooperative cancellation, and cancellation-safe
folder staging. Phase 5 established the themed and packaged PySide6 application
structure. Phase 6 added the complete navigation shell and strictly
non-sensitive UI-state persistence. Phase 7 added a validated, accessible
widget layer shared by every operation form. Phase 8 added tested background
execution, GUI-thread signal delivery, and cooperative cancellation. Phase 9
completed functional GUI coverage for all 13 operations with real end-to-end
tests. Phase 10 added cached background previews and non-destructive
thumbnail-based page reordering. Phase 11 added confirmed GUI passwords and
secure interactive CLI prompting without breaking explicit-argument
automation. Native Linux and macOS startup validation and the remaining
architectural improvements should be addressed as the PySide6 migration
progresses.
