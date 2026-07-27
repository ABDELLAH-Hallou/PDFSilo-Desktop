# ADR 0002: Run work outside the Qt UI thread

- Status: Accepted
- Date: 24 July 2026

## Context

PyMuPDF rendering, compression, merging, and image processing can take long
enough to freeze Qt's event loop. Qt widgets are also not safe to access from
worker threads.

## Decision

Core operations report progress and poll cancellation through plain callable
protocols that do not depend on Qt. The desktop uses `QThreadPool` and reusable
workers to adapt those callbacks to signals. A `threading.Event` provides
cooperative, thread-safe cancellation.

Operation execution and preview rendering use separate worker paths. Preview
jobs are limited to two concurrent tasks and return `QImage`; the GUI thread
creates and displays `QPixmap`.

## Consequences

- The interface stays responsive during long operations.
- Cancellation occurs between meaningful units rather than interrupting
  PyMuPDF unsafely mid-call.
- Every terminal path must emit completion and restore form controls.
- Worker tests must verify thread identity, signal order, duplicate-start
  protection, and cancellation.
