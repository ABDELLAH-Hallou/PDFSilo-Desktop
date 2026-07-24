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
- [x] Keep all existing tests passing (226 tests as of 24 July 2026).

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

- [ ] Define framework-independent progress and cancellation protocols.
- [ ] Add progress reporting to long-running operations.
- [ ] Add cooperative cancellation checks.
- [ ] Clean temporary output after cancellation.
- [ ] Add progress and cancellation tests at the core level.

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

- [ ] Create the `safepdf.ui` package.
- [ ] Add the GUI entry point.
- [ ] Add application metadata and an icon.
- [ ] Establish theme, spacing, and typography constants.
- [ ] Confirm that an empty main window starts on each target platform.

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

- [ ] Create the main window.
- [ ] Create sidebar navigation.
- [ ] Add a stacked content area.
- [ ] Add global status and progress controls.
- [ ] Add application-level menus and keyboard shortcuts.
- [ ] Restore window size and position with `QSettings`.
- [ ] Do not store passwords in `QSettings`.

## Phase 7: Create reusable input widgets

Most operations share the same interaction patterns. Implement these once:

- [ ] Single PDF picker
- [ ] Multiple PDF picker
- [ ] Image-file picker
- [ ] Folder picker
- [ ] Output file picker
- [ ] Output directory picker
- [ ] Drag-and-drop zone
- [ ] Run and cancel buttons
- [ ] Progress display
- [ ] Result summary
- [ ] Open output button
- [ ] Open containing-folder button

Each picker should provide:

- Path validation
- Clear invalid-state styling
- Keyboard accessibility
- Drag-and-drop support where relevant
- A stable signal-based API

Avoid duplicating path handling and validation across 13 operation pages.

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

- [ ] Implement a reusable operation worker.
- [ ] Connect framework-independent progress callbacks to Qt signals.
- [ ] Implement a thread-safe cancellation flag.
- [ ] Prevent duplicate operation starts.
- [ ] Restore UI state after every completion path.
- [ ] Test success, failure, and cancellation signals.

## Phase 9: Implement operation screens incrementally

Implement operations in an order that establishes reusable patterns early.

### Stage A: Basic document workflows

- [ ] Merge PDFs
- [ ] Split PDF
- [ ] Rotate pages
- [ ] Extract page range

These screens establish file selection, output handling, validation, workers,
and progress reporting.

### Stage B: Page and image workflows

- [ ] Reorder pages
- [ ] Render PDF pages to images
- [ ] Build PDF from images
- [ ] Extract embedded images
- [ ] Add images to PDF

### Stage C: Document transformation and security

- [ ] Compress PDF
- [ ] Add watermark
- [ ] Encrypt PDF
- [ ] Decrypt PDF

Every operation screen should include:

- Input selection
- Output selection
- Operation-specific options
- Inline validation
- Run and cancel controls
- Progress and status
- Result summary

## Phase 10: Add PDF preview and thumbnails

Use PyMuPDF to render low-resolution previews. Convert pixmaps to `QImage`, then
display them through `QPixmap`.

Preview rendering should:

- [ ] Run outside the main UI thread.
- [ ] Cache thumbnails using file path, modification time, page, and scale.
- [ ] Limit simultaneous render jobs.
- [ ] Release documents and pixmaps promptly.
- [ ] Invalidate cached images when the source changes.
- [ ] Display a clear placeholder for encrypted or invalid PDFs.

For page reordering:

- [ ] Use `QListView` with a custom page model.
- [ ] Store original page indexes in the model.
- [ ] Enable internal drag-and-drop.
- [ ] Support selection, duplication, deletion, and reversal.
- [ ] Do not modify the source PDF until the user confirms the operation.

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
