# PDFSilo Architecture

_Updated: 27 July 2026_

## Overview

PDFSilo has two presentation layers over one local processing engine:

```text
Installed CLI / python -m pdfsilo       PySide6 desktop application
                  \                       /
                   \                     /
                    structured operation API
                     results · errors · progress
                         · cancellation
                              |
                         PyMuPDF operations
                              |
                       local filesystem only
```

The core and operation packages do not import Qt. This keeps PDF behavior
available to the CLI, independently testable, and reusable by other Python
clients.

## Package responsibilities

| Package or module | Responsibility |
|---|---|
| `pdfsilo.core` | Structured results, typed errors, validation, progress/cancellation protocols, and atomic output helpers |
| `pdfsilo.operations` | The 13 PyMuPDF-backed document and image operations |
| `pdfsilo.updater` | Qt-free release checks, semantic-version comparison, downloads, and SHA-256 verification |
| `pdfsilo.presentation` | Compatibility translation from structured outcomes to logged boolean results |
| `pdfsilo.cli` | Argument parsing, secure interactive password prompts, exit codes, and operation dispatch |
| `pdfsilo.ui.pages` | Validated operation forms and the Home dashboard |
| `pdfsilo.ui.widgets` | Reusable pickers, ordered inputs, previews, page lists, operation controls, and result actions |
| `pdfsilo.ui.workers` | Qt thread-pool adaptation for core progress, cancellation, and results |
| `pdfsilo.ui.theme` | System/light/dark theme management, semantic colors, spacing, and typography |
| `pdfsilo.ui.preferences` | The allowlisted non-sensitive settings contract |
| `pdfsilo.ui.resources` | Packaged PNG identity artwork and functional SVG control icons |

## Operation contract

Each operation exposes an `execute(...) -> OperationResult` function. Expected
failures raise a `PdfSiloError` subclass. Long-running operations accept
optional framework-independent callbacks:

```python
ProgressCallback = Callable[[int, int, str], None]
CancellationCheck = Callable[[], bool]
```

The CLI converts results and expected errors into messages and exit behavior.
The desktop worker converts the same contract into Qt signals. Neither
presentation layer owns PDF-processing rules.

Legacy `run(...) -> bool` and `cli_run(args)` adapters remain available for
backward compatibility.

## Desktop execution flow

1. An operation page validates its form.
2. `OperationController` disables mutable controls and starts one worker.
3. `OperationWorker` executes the operation on `QThreadPool`.
4. Core progress callbacks become Qt signals delivered on the GUI thread.
5. A thread-safe cancellation token is checked between meaningful work units.
6. Success, expected failure, unexpected failure, or cancellation updates the
   page and global status.
7. Controls are restored on every completion path.

Qt widgets are accessed only from the main thread. Thumbnail rendering uses a
separate thread pool limited to two concurrent jobs, returns detached
`QImage` data, and creates `QPixmap` objects only in the GUI thread.

## Output safety

Single-file operations write to temporary paths and publish through atomic
replacement where practical. Folder operations stage output beside the final
destination and remove their staging area on cancellation.

PDF-producing desktop workflows add another review boundary: the worker
creates a temporary result, the user previews it, and **Save result** publishes
it. **Discard result** removes the staged file. Existing destinations require
confirmation by default.

## Preview and page ordering

PDF previews are asynchronous and cached by resolved path, modification time,
file size, page index, and scale. Source changes invalidate cached images.
Encrypted, invalid, or missing PDFs display explicit placeholders.

Merge and image inputs are ordered collections. Users can add files over
multiple selections, drag items, use keyboard-accessible move buttons, remove
items, and clear the list. The reorder page retains original page indexes in a
custom model; duplication, deletion, reversal, and drag/drop remain in memory
until the user runs the operation.

## Settings and privacy boundary

`QSettings` stores only the following allowlisted keys:

- `appearance/theme`
- `startup/restore_window`
- `startup/reopen_last_tool`
- `workflow/show_input_previews`
- `workflow/confirm_overwrite`
- `workflow/open_output_folder`
- `updates/check_automatically`
- `updates/last_check_timestamp` when a check has occurred
- `updates/skipped_version` when the user skips a release
- `window/geometry` and `window/state` when restoration is enabled
- `navigation/current_index` when reopening the last tool is enabled

It does not store input or output paths, recent-document lists, document
contents, or passwords. Password fields are masked by default, explicitly
clear after operations, and never enter logs, results, errors, progress
messages, or settings.

## Update boundary

PDF operations remain fully local. Update checking is a separate,
framework-independent capability governed by
[ADR 0006](adr/0006-opt-in-update-checks-and-user-initiated-install.md):

1. Automatic checks are disabled by default and throttled to once per 24 hours
   when enabled.
2. Manual checks are always available through Help or `pdfsilo update --check`.
3. The updater sends an unauthenticated HTTPS GET only to the fixed public
   GitHub Releases endpoint. It sends no document or machine data.
4. The Qt worker adapts the updater callbacks without performing networking on
   the GUI thread.
5. A non-blocking banner announces non-skipped releases.
6. Downloads are staged in a per-user cache and must match a published SHA-256
   digest.
7. Downloaded programs are not executed until signed native installers and
   platform-specific signature verification are implemented.

## Theme and identity

The application supports System default, Light, and Dark modes. System mode
tracks Qt's operating-system color scheme while the application is running.

- Light mode uses near-white document surfaces with indigo primary actions and
  a restrained teal accent.
- Dark mode uses neutral charcoal surfaces (`#181A1F`, `#1D2026`,
  `#23262D`, and `#2A2E36`) rather than a blue/navy canvas.
- Indigo and teal remain semantic accents in both modes.

The active identity assets are:

- `pdfsilo/ui/resources/logo.png` — sidebar wordmark
- `pdfsilo/ui/resources/icon.png` — application, window, and About icon

The uploaded PNG files contain transparent promotional margins, so the
resource loader crops only that empty canvas at runtime and scales the artwork
smoothly. It does not recolor or reshape the design. Functional sidebar and
spin-control icons remain SVG resources.

## Test boundaries

The suite combines:

- Core and operation tests using real PDFs and images
- CLI parser, dispatch, password, and exit-code tests
- `pytest-qt` widget, navigation, worker, theme, settings, and security tests
- Mocked UI-to-service contract tests for all 13 operation pages
- A smaller real-PyMuPDF UI integration layer

Current validation details are recorded in
[`CODEBASE_ANALYSIS.md`](../CODEBASE_ANALYSIS.md).

## Related decisions

See the [ADR index](adr/README.md) for the accepted architecture decisions that
define the core/UI boundary, worker model, output publication, settings
contract, and visual identity.
