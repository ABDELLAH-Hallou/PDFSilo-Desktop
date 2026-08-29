# PDFSilo Codebase Analysis

_Initial analysis: 24 July 2026 · Updated: 27 July 2026_

## Executive summary

PDFSilo is a compact, privacy-focused Python toolkit for local PDF processing.
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
its own module and exposes a structured `execute(...) -> OperationResult` core
API. The original `run(...) -> bool` interface and `cli_run(args)` adapter
remain as compatibility presentation layers. The automated test suite covers
core, CLI, Qt widgets, workers, themes, settings, security, page contracts, and
real-PDF integration. Phase 1 remediation added behavioral coverage for
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

Explicit command-line password arguments remain available for automation and
are documented as less secure; interactive use now defaults to hidden prompts.
Image-DPI interpretation and complete folder-level transactionality remain
future work.

## Phase 2 packaging status

Project packaging was added on 24 July 2026:

- `pyproject.toml` defines PDFSilo 0.1.0 for Python 3.10+.
- PyMuPDF and PySide6 are declared runtime dependencies.
- pytest, pytest-qt, and build are available through the `dev` extra.
- `pdfsilo` and `pdfsilo-gui` are installed console entry points.
- A minimal PySide6 bootstrap window provides a working GUI entry point.
- An editable install and distributable wheel were built successfully.

## Phase 3 core separation status

Core operations were separated from CLI presentation behavior on 24 July 2026:

- `pdfsilo.core.OperationResult` reports output paths, messages, warnings,
  source paths, processing counts, file sizes, elapsed time, and metadata.
- Expected failures use `PdfSiloError` subclasses for invalid input, passwords,
  output writes, PDF processing, and cancellation.
- All 13 operation modules expose `execute(...) -> OperationResult` and perform
  no CLI logging in that core path.
- Wrapped PyMuPDF and filesystem failures use exception chaining so diagnostic
  context remains available through `__cause__`.
- `pdfsilo.presentation.present_operation` translates structured outcomes into
  logging and the existing boolean return contract.
- Existing `run(...)` and `cli_run(args)` callers remain compatible.
- CLI success and failure exit codes were verified.

## Phase 4 progress and cancellation status

Framework-independent progress and cancellation were added on 24 July 2026:

- `ProgressCallback` and `CancellationCheck` callable aliases are defined in
  `pdfsilo.core.progress` without importing PySide6.
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

- The installed `pdfsilo-gui` entry point creates and configures a
  process-wide `QApplication`.
- `MainWindow` provides the empty desktop shell for the navigation work in
  Phase 6.
- Application identity values are centralized rather than repeated throughout
  widgets.
- Cross-platform color, spacing, typography, and control constants are
  centralized in `pdfsilo.ui.theme`.
- The approved `icon.png` is packaged and assigned at application and window
  level, while `logo.png` supplies the sidebar wordmark. Runtime cropping
  removes only the transparent promotional canvas around the supplied artwork.
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
- The Settings dialog exposes Appearance, Workflow, and Startup and privacy
  tabs, including theme, preview, overwrite, post-save, window restoration,
  last-tool, and opt-in update-check preferences plus Restore defaults.
- Window geometry/state and the selected navigation page are restored only
  when their corresponding preferences are enabled.
- Settings persistence uses an explicit non-sensitive allowlist, including
  update-check throttle/skip metadata. Passwords, recent files, input paths,
  output paths, and document data are never written to `QSettings`.

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
- Expected `PdfSiloError` messages remain distinct from unexpected exceptions,
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
- The `QSettings` allowlist excludes all form values, document paths, recent
  files, and secrets.
- Security regression tests verify that passwords never appear in operation
  results, warnings, progress messages, expected errors, or logs.
- CLI password arguments are optional. Missing values use hidden
  `getpass.getpass()` prompts, with confirmation for new encryption passwords.
  Explicit arguments remain available for existing automation but are
  documented as less secure.

## Phase 12 UI testing status

The UI-specific coverage audit was completed on 25 July 2026:

- Main-window startup, navigation, picker signals, invalid-state blocking, and
  focused keyboard navigation are covered through `pytest-qt`.
- Worker tests cover background-thread execution, GUI-thread signal delivery,
  success, typed and unexpected failures, progress, cooperative cancellation,
  duplicate starts, and exact form-state restoration.
- Security tests cover masked defaults, visibility controls, password
  confirmation and clearing, settings exclusion, and secret-free logs and
  presentation messages.
- All 13 operation pages have mocked contract tests that assert their exact
  positional and keyword arguments after traversing real form validation and
  the asynchronous worker/controller path.
- Real-PDF and image tests remain a separate integration layer. A unified CLI
  smoke test also parses and executes a real operation through `cli.main()`.

## UI, settings, and identity refinement status

A focused product pass was completed on 26–27 July 2026:

- The application shell is responsive, with a collapsible sidebar and
  operation workspaces that move from side-by-side to stacked layouts.
- Ordered PDF and image inputs support incremental selection, drag/drop,
  accessible move controls, removal, and clearing.
- Previews render at higher working resolution, support fit and 50–300% zoom,
  include every merge source, and show target page normalization.
- PDF-producing screens stage successful output for review before Save result
  publishes it; Discard result removes the staged output.
- The settings surface now includes Appearance, Workflow, and Startup and
  privacy tabs with conservative defaults and a Restore defaults action.
- System default, Light, and Dark modes are supported. Dark mode uses neutral
  charcoal canvas and surfaces instead of blue/navy backgrounds, while indigo
  and teal remain accents.
- The supplied `logo.png` and `icon.png` are the only runtime identity assets.
  They are used consistently in both themes; functional sidebar and spin
  controls continue to use packaged SVG icons.
- The About dialog explains product capabilities, local-only privacy,
  licensing, and project support links.

The current component boundaries are documented in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Significant choices are tracked
in [`docs/adr/`](docs/adr/README.md).

## Update notification status

The opt-in update notification boundary was implemented on 27 July 2026:

- ADR 0006 records why update checks are the sole optional network capability.
- `pdfsilo.updater` contains semantic-version comparison, GitHub Releases
  parsing, platform asset selection, staged downloads, SHA-256 verification,
  and typed failures without importing Qt.
- Automatic checks are off by default, limited to once per 24 hours, and run
  through `QThreadPool` only after explicit opt-in.
- Manual checks are available through **Help → Check for Updates…** and
  `pdfsilo update --check`.
- New releases use a non-blocking banner with Update, Release notes, Skip this
  version, and dismiss actions.
- The update dialog downloads to a per-user cache, verifies the published
  checksum, deletes mismatches, and can open the containing folder.
- No downloaded program is executed. Install/restart remains blocked until
  Phase 13 supplies signed native artifacts and platform signature
  verification.
- Update traffic contains no PDF content, document paths, credentials,
  telemetry, or machine identifier.

## Native Windows packaging status

The Phase 13 Windows packaging layer was added on 28 July 2026:

- ADR 0007 selects an inspectable Nuitka `standalone` directory before any
  one-file experiment and records the per-user installer/signing boundary.
- The root `pysidedeploy.spec` pins deployment tools, includes packaged UI
  resources, selects the required Qt modules, and embeds application name,
  version, company, description, copyright, and icon metadata.
- `scripts/generate_windows_icon.py` derives the deployment ICO from the
  approved `icon.png`; the incorrect legacy SVG identity is not used.
- PowerShell helpers build the standalone directory, run the frozen
  application checks, compile the Inno Setup installer, and sign plus verify
  release artifacts without storing certificate secrets.
- The hidden packaged self-test starts the frozen GUI and exercises rotation,
  compression, restricted encryption, and decryption with a 120-page document
  under a deeply nested Unicode path.
- Cross-platform tests protect the deployment spec, metadata, resource/icon,
  and installer contracts.

The Inno Setup definition and Authenticode helper are release infrastructure,
not proof of a signed release. A clean Windows runner and signing with a
trusted certificate remain external release gates.

On 29 August 2026, a local Python 3.14/Nuitka 4.1.3 standalone build completed
successfully, including PyMuPDF's large generated wrapper. The versioned
executable passed GUI startup and a 120-page frozen workflow test covering
rotation, compression, encryption, decryption, Unicode names, and a deeply
nested 216-character path. Inno Setup 6.7.3 produced the x64 per-user installer;
its checksum matched, and silent install, installed-app self-test, and
uninstall succeeded. These results prove the local native path, but do not
replace signed candidate and fresh-runner evidence.

## Continuous integration and release automation status

Phase 14 was implemented on 28 July 2026:

- `.github/workflows/ci.yml` installs the editable project from
  `pyproject.toml`, enforces Ruff formatting/static analysis, builds the wheel
  and source distribution, and preserves those packages.
- Qt-free core and CLI tests run on Python 3.10 through 3.14 on Ubuntu.
  Headless UI tests run with Qt's offscreen platform on Ubuntu, Windows, and
  Intel macOS.
- `.github/workflows/release.yml` supports manual, non-publishing signed
  candidates and stable version tags. A reusable validator rejects non-stable
  versions, non-portable deployment paths, stale repository identity, and
  version disagreement before native compilation.
- The Windows release job uses Visual C++ Build Tools, runs the frozen
  self-test, requires protected signing secrets, signs and verifies both the
  executable and installer, and generates final SHA-256 and Authenticode
  metadata.
- A separate fresh Windows job downloads the signed installer, reverifies its
  checksum and Authenticode signature, installs it, runs the packaged workflow
  test, and uninstalls it before tag-triggered publication can start.
- Signed build directories are retained as Actions artifacts. The standalone
  ZIP, installer, checksums, signature report, and aggregate manifest are
  uploaded through the GitHub CLI with job-scoped `contents: write`.
- ADR 0008 records that Windows x64 is the only current native release target.
  Linux and macOS are test platforms until their native packaging and signing
  work is complete.

The workflow and its local contract tests are implemented, but no remote tag
build or signed GitHub Release is claimed yet. The protected `release`
environment and its certificate secrets must be configured before the first
tag is pushed.

## Delivery milestone status

- **Milestone 1 — Foundation: complete.** Backend corrections, structured
  results/errors, progress/cancellation, CLI adaptation, packaging metadata,
  and regression coverage are present. An AST-based test now enforces that
  `pdfsilo.core` and `pdfsilo.operations` do not import PySide6.
- **Milestone 2 — Desktop MVP: complete.** The main window, shared widgets,
  worker, four primary workflows, progress, cancellation, responsiveness,
  standalone executable, and per-user installer are implemented and tested.
- **Milestone 3 — Full feature parity: complete.** All 13 PDF operations have
  desktop screens; password, settings, previews, thumbnails, and UI/integration
  coverage are in place.
- **Milestone 4 — Polished distribution: in progress.** Visual page
  reordering and batch page-selection actions are complete, and the
  release/update strategy is defined. A dedicated before/after comparison,
  general multi-document batch queue, published signed installer, and
  clean-system install/process/uninstall evidence remain open.

Feature milestones can be completed out of delivery order: Milestone 3 has
feature parity even though Milestone 2's native executable gate is still open.
No milestone status treats checked-in packaging/signing automation as proof
that a signed artifact exists.

## Repository profile

| Area | Result |
|---|---:|
| Python source files | 64 |
| Application source lines | Approximately 11,840 |
| Test files | 32 |
| Test lines | Approximately 5,510 |
| CLI commands | 14 |
| Runtime dependencies | PyMuPDF and PySide6 |
| Test result | 389 passed |
| Test runtime | 102.16 seconds |
| Python version used for validation | 3.14.2 |

A local virtual environment of approximately 85 MiB and generated bytecode
caches may be present in development checkouts and are covered by `.gitignore`.
The repository is tracked with Git.

### Current validation

The full suite was run on 29 August 2026 with Python 3.14.2, PySide6/Qt 6.11.1,
pytest 9.0.3, and pytest-qt 4.5.0. All 389 collected tests passed in
102.16 seconds. This includes the original PDF operations, CLI and UI coverage,
the restored About runtime contract, the network-free updater tests, and the
Windows packaging contracts, frozen-workflow harness, and CI/release security
contracts.

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
             OperationResult    PdfSiloError
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

- [`pdfsilo/__main__.py`](pdfsilo/__main__.py) starts the CLI.
- [`pdfsilo/cli.py`](pdfsilo/cli.py) defines arguments and dispatches commands.
- [`pdfsilo/core/`](pdfsilo/core/) contains structured results, typed errors,
  core validation, and output publishing helpers.
- [`pdfsilo/presentation.py`](pdfsilo/presentation.py) adapts structured core
  outcomes to logging and legacy boolean returns.
- [`pdfsilo/utils.py`](pdfsilo/utils.py) contains shared page sizes, sorting,
  logging setup, and atomic-path helpers.
- [`pdfsilo/operations/`](pdfsilo/operations/) contains one module per PDF
  operation.
- [`pdfsilo/updater/`](pdfsilo/updater/) contains the non-Qt, opt-in release
  check and verified-download boundary.
- [`pdfsilo/ui/workers.py`](pdfsilo/ui/workers.py) contains cancellation,
  worker, runner, and UI-controller infrastructure.
- [`pdfsilo/ui/main_window.py`](pdfsilo/ui/main_window.py) owns navigation,
  application status, settings integration, and the responsive shell.
- [`pdfsilo/ui/pages/`](pdfsilo/ui/pages/) contains Home and the 13 concrete
  operation screens.
- [`pdfsilo/ui/widgets/`](pdfsilo/ui/widgets/) contains reusable operation-form
  and lifecycle widgets.
- [`pdfsilo/ui/theme.py`](pdfsilo/ui/theme.py) and
  [`pdfsilo/ui/preferences.py`](pdfsilo/ui/preferences.py) define the visual
  system and allowlisted persistence contract.
- [`pdfsilo/ui/resources/`](pdfsilo/ui/resources/) packages the approved PNG
  identity and functional SVG control icons.
- [`tests/`](tests/) contains unit and integration-style tests using real,
  temporary PyMuPDF documents.

The maintained architecture overview is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), with decisions recorded under
[`docs/adr/`](docs/adr/README.md).

No PDF operation, preview, telemetry, account integration, or cloud processing
uses the network. The only network-capable package is the separately governed
`pdfsilo.updater`: it contacts the fixed public GitHub Releases endpoint after
a manual request or explicit automatic-check opt-in. The privacy claim that
documents remain local is consistent with the implementation.

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

The suite combines mocked UI service contracts with real PDFs and images rather
than relying entirely on either approach. The Phase 12 checkpoint passed 338
tests, and later UI and identity work added further regression coverage.

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

[`pdfsilo/operations/compress.py`](pdfsilo/operations/compress.py) accepts and
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

[`pdfsilo/operations/extract_images.py`](pdfsilo/operations/extract_images.py)
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

[`pdfsilo/operations/encrypt.py`](pdfsilo/operations/encrypt.py) defaults the
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
`PdfSiloError` subclasses. Expected invalid input, password, output-write, and
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
runtime and development dependencies, a verified wheel build, and separate
ordinary-CI and signed-release workflows. It still has no dependency lock
file.

`pyproject.toml` is now the authoritative installation definition.
`requirements.txt` remains as a compatibility path for runtime installation.

Recommended action:

- Pin or lock the tested dependency set for reproducible builds.
- Keep `tree.txt` synchronized when package boundaries or key resources change.

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
- Identity PNG loading, functional SVG validity, Qt rendering, and package-data
  configuration.
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

Phase 12 added assertions for:

- Exact service-layer positional and keyword mappings for all 13 operation
  pages through their real worker path.
- Focus-driven keyboard navigation and stack synchronization.
- Unified CLI parsing, dispatch, exit status, and valid real output.

The subsequent UI refinement added assertions for:

- Responsive operation layouts and collapsible sidebar behavior.
- Incremental ordered inputs and visible move controls.
- Higher-resolution preview, zoom, multi-document selection, and target canvas.
- Staged Save result and Discard result publication.
- System/light/dark switching and neutral charcoal dark palette roles.
- Appearance, workflow, and startup/privacy settings plus restoration defaults.
- Settings allowlisting and removal of disabled restoration state.
- About-dialog product, privacy, license, and support content.
- Runtime use and wheel inclusion of `logo.png` and `icon.png`.

The update feature added assertions for:

- Semantic-version ordering and GitHub release parsing without live network
  access.
- Fixed metadata endpoint use and platform-specific asset selection.
- Up-to-date, available, malformed, and offline check outcomes.
- Companion checksum retrieval, successful verification, and deletion after a
  mismatch.
- Opt-in defaults, allowlisted update settings, throttling, skip persistence,
  and Restore defaults.
- The guarantee that disabled automatic checks make no network call.
- Updater worker execution off the GUI thread and GUI-thread result delivery.
- Banner and verified-download dialog behavior.
- `pdfsilo update --check` parsing, success output, and failure exit behavior.

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
3. Add dependency locking.
4. Validate and package the application on native Windows, Linux, and macOS.
5. Add preview-aware page-range and rotation selection.
6. Add protected automation inputs such as file descriptors if required.

## Final assessment

PDFSilo has a good foundation: its architecture is small, comprehensible, and
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
automation. Phase 12 completed the pytest-qt coverage matrix and added mocked
contracts for every operation page alongside the real-PDF integration suite.
The subsequent product pass improved responsive layouts, ordered inputs,
preview/review workflows, privacy-safe preferences, About content, theme
support, and PNG-based identity. The opt-in updater adds privacy-limited release
notification and checksum-verified delivery without executing unsigned code.
Phase 13 added Windows packaging and signing infrastructure, and Phase 14 added
cross-version/cross-platform CI plus a fail-closed tag-only signed release
pipeline. The application migration is functionally complete; the first
successful signed native release, install/restart integration, Linux/macOS
native packaging, dependency locking, and the remaining architectural
improvements are the next release work.
