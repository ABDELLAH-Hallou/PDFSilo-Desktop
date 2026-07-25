# SafePDF PySide6 Migration Plan

_Created: 24 July 2026_

## Objective

Convert SafePDF from a command-line-only toolkit into a cross-platform PySide6
desktop application while preserving:

- The existing CLI
- Local-only PDF processing
- The current PyMuPDF operation engine
- Automated test coverage
- Clear separation between presentation and processing logic

The PySide6 interface should be added as a second presentation layer. PDF
operations must not be rewritten inside Qt widgets or button handlers.

## Target architecture

```text
PySide6 UI                 Command-line interface
     |                              |
     +---------------+--------------+
                     |
                     v
          Application/service layer
                     |
          +----------+----------+
          |          |          |
       Results     Progress   Cancellation
          |          |          |
          +----------+----------+
                     |
                     v
            Core PDF operations
                     |
                     v
                  PyMuPDF
                     |
                     v
              Local filesystem
```

The core processing layer must not import PySide6. This keeps it independently
testable and usable from both the CLI and desktop application.

## Phase 1: Stabilize the processing layer

Before exposing the operations through a graphical interface, address the
important backend issues identified in
[`CODEBASE_ANALYSIS.md`](CODEBASE_ANALYSIS.md):

- [x] Make compression quality affect actual image compression, or remove the
      misleading quality option.
- [x] Properly convert extracted images to the requested PNG or JPEG format.
- [x] Correct owner-password behavior for restricted encrypted PDFs.
- [x] Add validation for opacity, color components, dimensions, coordinates,
      and margins.
- [x] Use temporary files and atomic replacement where practical.
- [x] Resolve the license label and license-text mismatch.
- [x] Add regression tests for each corrected behavior.
- [x] Keep all existing tests passing (287 tests as of 24 July 2026).

## Phase 2: Add project packaging

Create a root-level `pyproject.toml` containing:

- [x] Project name and version
- [x] Python version requirement
- [x] PyMuPDF runtime dependency
- [x] PySide6 UI dependency
- [x] Optional development dependencies
- [x] pytest and pytest-qt test dependencies
- [x] CLI entry point
- [x] GUI entry point
- [x] Build-system configuration

Suggested entry points:

```toml
[project.scripts]
safepdf = "safepdf.cli:main"
safepdf-gui = "safepdf.ui.main:main"
```

The application should remain usable through both:

```bash
safepdf <command> [options]
safepdf-gui
```

Phase 2 validation completed on 24 July 2026:

- Editable development installation completed successfully.
- `safepdf` and `safepdf-gui` were installed as console entry points.
- The GUI entry point launched successfully in offscreen smoke testing.
- `dist/safepdf-0.1.0-py3-none-any.whl` was built successfully.
- The complete suite passed with 199 tests.

## Phase 3: Separate the core from CLI behavior

The current operations accept strings, log their own errors, catch broad
exceptions, and return `True` or `False`. A GUI requires more structured
information.

### Structured results

Introduce a result model:

```python
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OperationResult:
    output_paths: list[Path]
    message: str
    warnings: list[str] = field(default_factory=list)
```

Possible additional fields include:

- Source files
- Number of processed pages
- Number of skipped files
- Original and resulting file sizes
- Elapsed time
- Operation-specific metadata

### Typed errors

Introduce application-specific exceptions:

```python
class SafePdfError(Exception):
    """Base class for expected SafePDF errors."""


class InvalidInputError(SafePdfError):
    pass


class PdfPasswordError(SafePdfError):
    pass


class OutputWriteError(SafePdfError):
    pass


class OperationCancelledError(SafePdfError):
    pass
```

Core operations should raise these exceptions. The two presentation layers can
handle them differently:

- The CLI logs the message and selects an exit code.
- The GUI displays an appropriate error or warning dialog.

### Implementation tasks

- [x] Introduce `OperationResult`.
- [x] Introduce typed SafePDF exceptions.
- [x] Move CLI-specific logging decisions out of core operations.
- [x] Preserve useful diagnostic context when wrapping PyMuPDF errors.
- [x] Update the CLI adapters to consume structured results.
- [x] Verify that CLI behavior remains backward compatible.

Phase 3 validation completed on 24 July 2026:

- All 13 operations expose a framework-independent `execute(...)` function
  that accepts `Path` values and returns `OperationResult`.
- Expected failures use typed `SafePdfError` subclasses. Wrapped PyMuPDF and
  filesystem errors retain their original exception through `__cause__`.
- The shared presentation adapter converts results and errors into the
  existing CLI logging and boolean contract.
- Legacy `run(...) -> bool` functions remain available for compatibility.
- CLI help exits with status 0 and expected operation failures exit with
  status 1.
- The complete suite passed with 226 tests.

## Phase 4: Add progress and cancellation

Long-running operations must report progress without depending on Qt:

```python
from collections.abc import Callable

ProgressCallback = Callable[[int, int, str], None]
CancellationCheck = Callable[[], bool]
```

An operation can then accept optional callbacks:

```python
def split_pdf(
    input_path: Path,
    output_directory: Path,
    progress: ProgressCallback | None = None,
    is_cancelled: CancellationCheck | None = None,
) -> OperationResult:
    ...
```

Progress should be emitted after each meaningful unit:

- Page processed
- File merged
- Image extracted
- Thumbnail rendered

Cancellation should be checked between those units. If cancellation is
requested, the operation should remove temporary output and raise
`OperationCancelledError`.

### Implementation tasks

- [x] Define framework-independent progress and cancellation protocols.
- [x] Add progress reporting to long-running operations.
- [x] Add cooperative cancellation checks.
- [x] Clean temporary output after cancellation.
- [x] Add progress and cancellation tests at the core level.

Phase 4 validation completed on 24 July 2026:

- `ProgressCallback` and `CancellationCheck` are plain Python callable aliases
  with no Qt dependency.
- All 13 `execute(...)` APIs accept optional, keyword-only `progress` and
  `is_cancelled` callbacks.
- Page, file, and image loops report progress after each completed unit and
  poll for cancellation between units and before final output publication.
- Cancellation raises `OperationCancelledError` without being wrapped as an
  unexpected processing failure.
- Split, rendered-image, and extracted-image outputs are built in sibling
  staging directories. Cancellation removes the staging directory and
  preserves any existing destination contents.
- Single-file operations retain their atomic-output behavior and do not replace
  an existing destination when cancelled before publication.
- The complete suite passed with 246 tests.

## Phase 5: Create the PySide6 application structure

Suggested project layout:

```text
safepdf/
├── core/
│   ├── __init__.py
│   ├── errors.py
│   ├── models.py
│   ├── services.py
│   └── operations/
├── cli.py
└── ui/
    ├── __init__.py
    ├── main.py
    ├── main_window.py
    ├── workers.py
    ├── resources/
    ├── dialogs/
    │   ├── error_dialog.py
    │   └── password_dialog.py
    ├── pages/
    │   ├── home_page.py
    │   ├── merge_page.py
    │   ├── split_page.py
    │   ├── rotate_page.py
    │   └── ...
    └── widgets/
        ├── file_picker.py
        ├── output_picker.py
        ├── drop_zone.py
        ├── pdf_preview.py
        └── operation_panel.py
```

Initial GUI entry point:

```python
import sys

from PySide6.QtWidgets import QApplication

from safepdf.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SafePDF")
    app.setOrganizationName("SafePDF")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

### Implementation tasks

- [x] Create the `safepdf.ui` package.
- [x] Add the GUI entry point.
- [x] Add application metadata and an icon.
- [x] Establish theme, spacing, and typography constants.
- [ ] Confirm that an empty main window starts on each target platform
      (Windows verified; native Linux and macOS runs remain pending).

Phase 5 implementation and Windows validation completed on 24 July 2026:

- `safepdf.ui` now contains the application entry point, `MainWindow`,
  metadata, theme tokens, packaged resources, and scaffold packages for
  dialogs, pages, widgets, and workers.
- `create_application()` configures application name, display name, version,
  organization, domain, desktop identifier, icon, system font, and stylesheet.
- A scalable SVG application icon is applied to both the application and main
  window.
- Color, spacing, typography, control-height, and border-radius constants are
  centralized in `safepdf.ui.theme`.
- The window was constructed and passed through a real Qt start/stop event loop
  using the offscreen Windows platform.
- The wheel was rebuilt and inspected; the UI modules and SVG icon are present.
- The complete suite passed with 252 tests.

The startup smoke test is platform-neutral and ready for Linux and macOS CI,
but those native Qt platforms cannot be executed from this Windows workspace.

## Phase 6: Build the main application shell

Use one main window with navigation between operation screens:

```text
┌─────────────────────────────────────────────────────┐
│ SafePDF                               Settings Help │
├───────────────┬─────────────────────────────────────┤
│ Home          │                                     │
│ Merge         │                                     │
│ Split         │       Current operation page        │
│ Rotate        │                                     │
│ Extract       │    Input, preview, and options      │
│ Compress      │                                     │
│ Encrypt       │                                     │
│ ...           │                                     │
├───────────────┴─────────────────────────────────────┤
│ Status · progress · output location                 │
└─────────────────────────────────────────────────────┘
```

Recommended Qt components:

- `QMainWindow` for the application shell
- `QListView` or `QListWidget` for navigation
- `QStackedWidget` for operation pages
- `QFileDialog` for files and directories
- `QProgressBar` for operation progress
- `QStatusBar` for concise status information
- `QSettings` for non-sensitive preferences

### Implementation tasks

- [x] Create the main window.
- [x] Create sidebar navigation.
- [x] Add a stacked content area.
- [x] Add global status and progress controls.
- [x] Add application-level menus and keyboard shortcuts.
- [x] Restore window size and position with `QSettings`.
- [x] Do not store passwords in `QSettings`.

Phase 6 validation completed on 24 July 2026:

- The main window contains a header, sidebar, stacked content area, and global
  status bar.
- Stable navigation entries exist for Home and all 13 PDF operations.
  Operation forms remain placeholders until their implementation phases.
- Navigation selection, stacked-page selection, Home, Previous, and Next
  actions remain synchronized.
- The status API supports concise messages, determinate and indeterminate
  progress, and a non-persistent output-location display.
- File, Navigate, Tools, and Help menus provide Open, Exit, page navigation,
  Settings, and About actions with keyboard shortcuts.
- The Open action uses a PDF-filtered `QFileDialog`.
- `QSettings` persists only `window/geometry`, `window/state`, and
  `navigation/current_index`. Input paths, output paths, document contents, and
  passwords are not persisted.
- Window size, valid on-screen position, and selected navigation page restore
  successfully.
- An offscreen visual render confirmed the header, sidebar, content, and status
  layout.
- The complete suite passed with 258 tests.

## Phase 7: Create reusable input widgets

Most operations share the same interaction patterns. Implement these once:

- [x] Single PDF picker
- [x] Multiple PDF picker
- [x] Image-file picker
- [x] Folder picker
- [x] Output file picker
- [x] Output directory picker
- [x] Drag-and-drop zone
- [x] Run and cancel buttons
- [x] Progress display
- [x] Result summary
- [x] Open output button
- [x] Open containing-folder button

Each picker should provide:

- Path validation
- Clear invalid-state styling
- Keyboard accessibility
- Drag-and-drop support where relevant
- A stable signal-based API

Avoid duplicating path handling and validation across 13 operation pages.

Phase 7 validation completed on 24 July 2026:

- All specialized path pickers derive from one configurable `PathPicker`
  implementation.
- Pickers expose stable `pathChanged`, `pathsChanged`, `validityChanged`, and
  `validationChanged` signals plus typed path accessors.
- Input pickers validate existence, file or directory type, supported
  extensions, required values, and single-versus-multiple selection.
- Output pickers validate the target type, extension, and existence of the
  destination parent.
- Validation state is visible through accessible messages and consistent
  neutral, valid, and invalid styling.
- Picker labels have keyboard buddies, browse controls have accessible names,
  and the drop zone can be activated with Enter, Return, or Space.
- Pickers and the standalone drop zone accept compatible local drag-and-drop
  paths and reject incompatible or missing paths.
- `OperationPanel` composes run/cancel controls, determinate or indeterminate
  progress, structured results, warnings, metrics, and output actions.
- Output actions verify the current path before asking the desktop to open the
  output or its containing folder.
- An offscreen visual render verified validation styling, drop-zone bounds,
  result-card density, and output controls.
- The complete suite passed with 276 tests.

## Phase 8: Run operations outside the UI thread

PyMuPDF work must not run on Qt's main thread. Otherwise, rendering,
compression, and large merges will freeze the application.

Use either:

- `QThreadPool` with `QRunnable`; or
- A worker `QObject` moved to a `QThread`

A reusable worker signal class can expose:

```python
from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    progress = Signal(int, int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()
```

The normal UI workflow should be:

1. Validate the form.
2. Disable controls that must not change while running.
3. Create and start the worker.
4. Update the progress display through signals.
5. Handle success, failure, or cancellation.
6. Restore the controls in the `finished` handler.

Qt widgets must only be accessed from the main UI thread.

### Implementation tasks

- [x] Implement a reusable operation worker.
- [x] Connect framework-independent progress callbacks to Qt signals.
- [x] Implement a thread-safe cancellation flag.
- [x] Prevent duplicate operation starts.
- [x] Restore UI state after every completion path.
- [x] Test success, failure, and cancellation signals.

Phase 8 validation completed on 24 July 2026:

- `OperationWorker` executes one structured core operation through
  `QThreadPool` and `QRunnable`.
- Worker-managed callbacks translate framework-independent progress and
  cancellation into Qt signals without importing Qt into the core.
- `CancellationToken` uses `threading.Event`, making repeated cancellation
  requests safe across threads.
- `OperationRunner` owns the active worker, forwards signals through GUI-thread
  slots, rejects duplicate starts, and always clears its running state.
- Expected `SafePdfError` failures, unexpected exceptions, cancellation,
  success, and final completion use distinct signal paths.
- `OperationController` binds a runner to `OperationPanel`, disables form
  controls while active, and restores each control to its exact previous
  enabled state after every terminal outcome.
- Run/cancel state, progress, result, error, cancellation, and output controls
  update only through GUI-thread signal handlers.
- Tests verify worker-versus-GUI thread identity, signal ordering, progress,
  expected and unexpected failure, cooperative cancellation, duplicate start
  rejection, and state restoration after success, failure, and cancellation.
- The Qt startup smoke test uses a local event loop so it does not terminate
  pytest's shared application before worker tests run.
- The complete suite passed with 287 tests.

## Phase 9: Implement operation screens incrementally

Implement operations in an order that establishes reusable patterns early.

### Stage A: Basic document workflows

- [x] Merge PDFs
- [x] Split PDF
- [x] Rotate pages
- [x] Extract page range

These screens establish file selection, output handling, validation, workers,
and progress reporting.

### Stage B: Page and image workflows

- [x] Reorder pages
- [x] Render PDF pages to images
- [x] Build PDF from images
- [x] Extract embedded images
- [x] Add images to PDF

### Stage C: Document transformation and security

- [x] Compress PDF
- [x] Add watermark
- [x] Encrypt PDF
- [x] Decrypt PDF

Every operation screen should include:

- Input selection
- Output selection
- Operation-specific options
- Inline validation
- Run and cancel controls
- Progress and status
- Result summary

Phase 9 validation completed on 24 July 2026:

- A shared `OperationPage` base owns the scrollable form layout, picker and
  option validation, operation panel, background controller, progress/status
  forwarding, cancellation, and structured result handling.
- All 13 navigation entries now open concrete operation screens; no operation
  relies on placeholder content.
- Each screen maps its controls to the existing framework-independent
  `execute(...)` API. PDF processing continues to run through the Phase 8
  thread-pool worker rather than Qt's main thread.
- Output paths are derived from the selected input when practical without
  replacing a destination chosen by the user.
- Inline checks cover required paths, page lists and ranges, page order,
  watermark text and color, and password/permission combinations. Numeric Qt
  controls constrain DPI, quality, opacity, margins, dimensions, coordinates,
  font size, and angles.
- The application shell receives operation status, progress, and output
  updates. Navigation and file replacement are disabled while work is active
  and restored on every completion path.
- Password controls use masked echo modes and are cleared after encryption or
  decryption finishes.
- Seventeen Phase 9 tests exercise every screen with real PDFs or images,
  validate failures, verify password clearing, and cover shell-level
  cancellation and navigation locking.
- The complete suite passed with 304 tests.

## Phase 10: Add PDF preview and thumbnails

Use PyMuPDF to render low-resolution previews. Convert pixmaps to `QImage`, then
display them through `QPixmap`.

Preview rendering should:

- [x] Run outside the main UI thread.
- [x] Cache thumbnails using file path, modification time, page, and scale.
- [x] Limit simultaneous render jobs.
- [x] Release documents and pixmaps promptly.
- [x] Invalidate cached images when the source changes.
- [x] Display a clear placeholder for encrypted or invalid PDFs.

For page reordering:

- [x] Use `QListView` with a custom page model.
- [x] Store original page indexes in the model.
- [x] Enable internal drag-and-drop.
- [x] Support selection, duplication, deletion, and reversal.
- [x] Do not modify the source PDF until the user confirms the operation.

Phase 10 validation completed on 25 July 2026:

- `ThumbnailService` renders through its own `QThreadPool`, limited to two
  simultaneous jobs, so preview work neither blocks Qt's main thread nor
  consumes operation-worker slots.
- PyMuPDF documents are scoped with context managers. Render tasks copy pixel
  data into detached `QImage` objects and release pixmaps before returning;
  widgets create `QPixmap` instances only on the GUI thread.
- The bounded LRU cache keys entries by resolved file path, nanosecond
  modification time, file size, zero-based page index, and render scale.
  Older entries for a changed source signature are removed automatically.
- Preview widgets watch their current source file and refresh after changes.
  Missing, invalid, and encrypted files display explicit placeholders.
- Standard PDF operation screens show a navigable preview. Reorder uses a
  custom `PdfPageListModel` and thumbnail `QListView`.
- Reorder entries retain immutable source-page indexes while their current
  positions change. Extended selection, internal drag/drop, duplication,
  deletion, reversal, and original-order reset are supported.
- Reorder editing changes only the in-memory model. The source PDF is not
  written; pressing Run passes the confirmed order to the existing atomic
  output operation.
- Nine Phase 10 tests cover worker-thread execution, cache behavior and
  invalidation, concurrency limits, placeholders, navigation, application
  integration, lazy model thumbnails, and non-destructive editing.
- The complete suite passed with 313 tests.

## Phase 11: Handle passwords securely

For encryption and decryption screens:

- [ ] Use `QLineEdit.Password`.
- [ ] Add an explicit show/hide password control.
- [ ] Require confirmation for newly created passwords.
- [ ] Explain user-password and owner-password roles.
- [ ] Require or recommend distinct passwords when restrictions are enabled.
- [ ] Never include passwords in logs, errors, or progress signals.
- [ ] Never store passwords in `QSettings`.
- [ ] Clear password fields after the operation.

The CLI should also support interactive password input instead of requiring
passwords in process arguments.

## Phase 12: Add UI-specific testing

Keep the existing core test suite and add `pytest-qt`.

### Widget and navigation tests

- [ ] Main window starts.
- [ ] Navigation selects the correct page.
- [ ] File and output pickers emit expected signals.
- [ ] Invalid inputs prevent execution.
- [ ] Keyboard navigation works.

### Worker tests

- [ ] Successful operations emit `succeeded`.
- [ ] Expected errors emit `failed`.
- [ ] Progress signals update the interface.
- [ ] Cancellation stops the operation.
- [ ] Controls are restored after completion.

### Security tests

- [ ] Password fields are masked by default.
- [ ] Passwords are not persisted.
- [ ] Passwords do not appear in logs.

### Integration tests

- [ ] Each operation page sends the correct parameters to the service layer.
- [ ] Selected end-to-end workflows produce valid output using real PDFs.
- [ ] Existing CLI behavior remains functional.

Most UI tests should mock the service layer. Use a smaller end-to-end suite for
real PyMuPDF processing.

## Phase 13: Package the desktop application

PySide6 provides `pyside6-deploy`, a deployment tool based on Nuitka. It can
produce executables for Windows, macOS, and Linux.

Official documentation:

- [Qt for Python deployment overview](https://doc.qt.io/qtforpython-6.8/deployment/index.html)
- [`pyside6-deploy` documentation](https://doc.qt.io/qtforpython-6.8/deployment/deployment-pyside6-deploy.html)

### Initial Windows release

- [ ] Create a directory-based build before attempting a single-file build.
- [ ] Include icons, translations, and other resources.
- [ ] Test the executable on a clean Windows virtual machine.
- [ ] Verify operation with Unicode and long file paths.
- [ ] Test large and encrypted PDFs.
- [ ] Add application name, version, company, and copyright metadata.
- [ ] Create an installer using Inno Setup, WiX, or MSIX.
- [ ] Code-sign the executable and installer before public distribution.

Build and test separately on each supported operating system. Do not assume a
Windows build can be repackaged for macOS or Linux.

## Phase 14: Add continuous integration

Create CI workflows that:

- [ ] Install the package from `pyproject.toml`.
- [ ] Run core tests.
- [ ] Run headless-compatible UI tests.
- [ ] Check formatting and static analysis.
- [ ] Build application artifacts for supported platforms.
- [ ] Preserve installers or build directories as CI artifacts.
- [ ] Run release builds only from tagged versions.

## Delivery milestones

### Milestone 1: Foundation

Deliverables:

- Backend defects corrected
- `pyproject.toml`
- Typed results and exceptions
- Progress and cancellation protocols
- CLI adapted to the new service layer
- Existing test suite passing

Exit criteria:

- The CLI retains feature parity.
- Core operations have no PySide6 dependency.
- Operation failures provide structured error information.

### Milestone 2: Usable desktop MVP

Deliverables:

- Main window and navigation
- Shared path-selection widgets
- Background operation worker
- Merge, split, rotate, and extract-range screens
- Progress and cancellation
- Initial Windows executable

Exit criteria:

- A nontechnical user can complete the four primary workflows without using a
  terminal.
- The interface remains responsive during processing.

### Milestone 3: Full feature parity

Deliverables:

- UI screens for all existing CLI commands
- Secure password dialogs
- Settings and recent locations
- PDF preview and thumbnails
- UI and integration tests

Exit criteria:

- Every CLI operation has an equivalent desktop workflow.
- Passwords are not persisted or exposed in logs.
- Core and UI test suites pass.

### Milestone 4: Polished PDF application

Deliverables:

- Visual drag-and-drop page reordering
- Thumbnail selection and batch actions
- Before-and-after previews
- Batch processing
- Installer and code signing
- Release and update strategy

Exit criteria:

- The application is suitable for distribution to users without Python
  installed.
- Installation, processing, and uninstallation are verified on clean systems.

## Definition of done

The migration is complete when:

- [ ] The CLI and PySide6 UI use the same core operation layer.
- [ ] All existing PDF capabilities are accessible from the GUI.
- [ ] Long-running work never blocks the main UI thread.
- [ ] Progress, cancellation, and detailed errors are supported.
- [ ] Password handling does not expose or persist secrets.
- [ ] Automated core, UI, and integration tests pass.
- [ ] Application packages run on clean target systems.
- [ ] Licensing and project metadata are correct.
- [ ] User and developer documentation describe both interfaces.

## Guiding principle

> PySide6 should be a client of the SafePDF processing engine, not part of the
> processing engine.

Following this rule preserves the CLI, keeps the core independently testable,
and prevents PDF behavior from becoming coupled to GUI state.
