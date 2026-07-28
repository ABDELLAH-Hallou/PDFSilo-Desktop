"""Reusable background execution infrastructure for PDFSilo operations."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from threading import Event
from typing import Any

from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QWidget

from pdfsilo.core import (
    OperationCancelledError,
    OperationResult,
    PdfSiloError,
)
from pdfsilo.ui.widgets.operation_panel import OperationPanel
from pdfsilo.updater import UpdaterError

log = logging.getLogger(__name__)

OperationCallable = Callable[..., OperationResult]


class CancellationToken:
    """Thread-safe cooperative cancellation state shared with one worker."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        """Request cancellation. Calling this repeatedly is safe."""
        self._event.set()

    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""
        return self._event.is_set()


class WorkerSignals(QObject):
    """Signals emitted by an ``OperationWorker`` from its pool thread."""

    progress = Signal(int, int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()


class OperationWorker(QRunnable):
    """Execute one structured core operation outside Qt's UI thread."""

    def __init__(
        self,
        operation: OperationCallable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        if "progress" in kwargs or "is_cancelled" in kwargs:
            raise ValueError(
                "Worker callbacks are managed internally; do not pass "
                "'progress' or 'is_cancelled'."
            )
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.cancellation = CancellationToken()
        self.setAutoDelete(True)

    def cancel(self) -> None:
        """Request cooperative cancellation."""
        self.cancellation.cancel()

    def _report_progress(
        self,
        current: int,
        total: int,
        message: str,
    ) -> None:
        self.signals.progress.emit(current, total, message)

    @Slot()
    def run(self) -> None:
        """Run the core callable and always emit ``finished``."""
        try:
            if self.cancellation.is_cancelled():
                raise OperationCancelledError("Operation cancelled.")
            result = self.operation(
                *self.args,
                progress=self._report_progress,
                is_cancelled=self.cancellation.is_cancelled,
                **self.kwargs,
            )
        except OperationCancelledError:
            self.signals.cancelled.emit()
        except PdfSiloError as exc:
            self.signals.failed.emit(str(exc))
        except Exception as exc:
            log.exception("Unexpected background operation failure.")
            detail = str(exc).strip() or type(exc).__name__
            self.signals.failed.emit(f"Unexpected operation failure: {detail}")
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class OperationRunner(QObject):
    """Own one active worker and forward all outcomes on the GUI thread."""

    started = Signal()
    progress = Signal(int, int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()
    runningChanged = Signal(bool)
    duplicateStartRejected = Signal()
    cancellationRequested = Signal()

    def __init__(
        self,
        thread_pool: QThreadPool | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self._worker: OperationWorker | None = None

    def is_running(self) -> bool:
        return self._worker is not None

    def start(
        self,
        operation: OperationCallable,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Start one operation, rejecting duplicate starts while active."""
        if self._worker is not None:
            self.duplicateStartRejected.emit()
            return False

        worker = OperationWorker(operation, *args, **kwargs)
        worker.signals.progress.connect(self._forward_progress)
        worker.signals.succeeded.connect(self._forward_success)
        worker.signals.failed.connect(self._forward_failure)
        worker.signals.cancelled.connect(self._forward_cancellation)
        worker.signals.finished.connect(self._worker_finished)
        self._worker = worker
        self.runningChanged.emit(True)
        self.started.emit()

        try:
            self.thread_pool.start(worker)
        except Exception as exc:
            self._worker = None
            self.runningChanged.emit(False)
            detail = str(exc).strip() or type(exc).__name__
            self.failed.emit(f"Could not start background operation: {detail}")
            self.finished.emit()
            return False
        return True

    def cancel(self) -> bool:
        """Request cancellation of the active operation, if present."""
        if self._worker is None:
            return False
        self._worker.cancel()
        self.cancellationRequested.emit()
        return True

    @Slot(int, int, str)
    def _forward_progress(
        self,
        current: int,
        total: int,
        message: str,
    ) -> None:
        self.progress.emit(current, total, message)

    @Slot(object)
    def _forward_success(self, result: OperationResult) -> None:
        self.succeeded.emit(result)

    @Slot(str)
    def _forward_failure(self, message: str) -> None:
        self.failed.emit(message)

    @Slot()
    def _forward_cancellation(self) -> None:
        self.cancelled.emit()

    @Slot()
    def _worker_finished(self) -> None:
        self._worker = None
        self.runningChanged.emit(False)
        self.finished.emit()


class UpdateWorker(QRunnable):
    """Run a framework-independent updater task outside the UI thread."""

    def __init__(
        self,
        task: Callable[..., object],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        if "progress" in kwargs or "is_cancelled" in kwargs:
            raise ValueError(
                "Worker callbacks are managed internally; do not pass "
                "'progress' or 'is_cancelled'."
            )
        self.task = task
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.cancellation = CancellationToken()
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self.cancellation.cancel()

    def _report_progress(
        self,
        current: int,
        total: int,
        message: str,
    ) -> None:
        self.signals.progress.emit(current, total, message)

    @Slot()
    def run(self) -> None:
        try:
            result = self.task(
                *self.args,
                progress=self._report_progress,
                is_cancelled=self.cancellation.is_cancelled,
                **self.kwargs,
            )
        except UpdaterError as exc:
            self.signals.failed.emit(str(exc))
        except Exception as exc:
            log.exception("Unexpected background updater failure.")
            detail = str(exc).strip() or type(exc).__name__
            self.signals.failed.emit(f"Unexpected updater failure: {detail}")
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class UpdateRunner(QObject):
    """Own one updater worker and forward its signals on the GUI thread."""

    started = Signal()
    progress = Signal(int, int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()
    runningChanged = Signal(bool)

    def __init__(
        self,
        thread_pool: QThreadPool | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.thread_pool = thread_pool or QThreadPool.globalInstance()
        self._worker: UpdateWorker | None = None

    def is_running(self) -> bool:
        return self._worker is not None

    def start(
        self,
        task: Callable[..., object],
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        if self._worker is not None:
            return False
        worker = UpdateWorker(task, *args, **kwargs)
        worker.signals.progress.connect(self.progress.emit)
        worker.signals.succeeded.connect(self.succeeded.emit)
        worker.signals.failed.connect(self.failed.emit)
        worker.signals.finished.connect(self._worker_finished)
        self._worker = worker
        self.runningChanged.emit(True)
        self.started.emit()
        try:
            self.thread_pool.start(worker)
        except Exception as exc:
            self._worker = None
            self.runningChanged.emit(False)
            detail = str(exc).strip() or type(exc).__name__
            self.failed.emit(f"Could not start updater task: {detail}")
            self.finished.emit()
            return False
        return True

    def cancel(self) -> bool:
        if self._worker is None:
            return False
        self._worker.cancel()
        return True

    @Slot()
    def _worker_finished(self) -> None:
        self._worker = None
        self.runningChanged.emit(False)
        self.finished.emit()


class OperationController(QObject):
    """Bind an ``OperationRunner`` to shared widgets and form controls."""

    def __init__(
        self,
        panel: OperationPanel,
        form_controls: Iterable[QWidget] = (),
        *,
        runner: OperationRunner | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.panel = panel
        self.form_controls = tuple(form_controls)
        self.runner = runner or OperationRunner(parent=self)
        self._enabled_before_run: dict[QWidget, bool] = {}

        self.panel.cancelRequested.connect(self.runner.cancel)
        self.runner.runningChanged.connect(self._set_running)
        self.runner.progress.connect(self.panel.set_progress)
        self.runner.succeeded.connect(self.panel.show_result)
        self.runner.failed.connect(self.panel.show_error)
        self.runner.cancelled.connect(self.panel.show_cancelled)

    def start(
        self,
        operation: OperationCallable,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Validate duplicate state through the runner and start work."""
        return self.runner.start(operation, *args, **kwargs)

    def cancel(self) -> bool:
        """Request cancellation through the bound runner."""
        return self.runner.cancel()

    def is_running(self) -> bool:
        return self.runner.is_running()

    @Slot(bool)
    def _set_running(self, running: bool) -> None:
        if running:
            self._enabled_before_run = {
                control: control.isEnabled() for control in self.form_controls
            }
            for control in self.form_controls:
                control.setEnabled(False)
        else:
            for control, was_enabled in self._enabled_before_run.items():
                control.setEnabled(was_enabled)
            self._enabled_before_run.clear()
        self.panel.set_running(running)


__all__ = [
    "CancellationToken",
    "OperationController",
    "OperationRunner",
    "OperationWorker",
    "UpdateRunner",
    "UpdateWorker",
    "WorkerSignals",
]
