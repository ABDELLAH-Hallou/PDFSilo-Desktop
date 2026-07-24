"""Tests for Phase 8 background execution and UI lifecycle handling."""

from pathlib import Path
from threading import Event, get_ident
from time import sleep

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QLineEdit, QPushButton

from safepdf.core import (
    InvalidInputError,
    OperationCancelledError,
    OperationResult,
)
from safepdf.ui.widgets import OperationPanel
from safepdf.ui.workers import (
    CancellationToken,
    OperationController,
    OperationRunner,
    OperationWorker,
)


def test_cancellation_token_is_thread_safe_and_idempotent():
    token = CancellationToken()

    assert not token.is_cancelled()
    token.cancel()
    token.cancel()
    assert token.is_cancelled()


def test_worker_rejects_caller_managed_callbacks():
    def operation(**_kwargs):
        return OperationResult([], "done")

    with pytest.raises(ValueError, match="managed internally"):
        OperationWorker(operation, progress=lambda *_args: None)

    with pytest.raises(ValueError, match="managed internally"):
        OperationWorker(operation, is_cancelled=lambda: False)


def test_runner_emits_progress_and_success_on_gui_thread(qtbot, tmp_path: Path):
    runner = OperationRunner()
    main_thread = get_ident()
    worker_threads = []
    signal_threads = []
    progress_events = []
    results = []
    events = []

    runner.started.connect(lambda: events.append("started"))
    runner.progress.connect(
        lambda current, total, message: (
            progress_events.append((current, total, message)),
            signal_threads.append(get_ident()),
            events.append("progress"),
        )
    )
    runner.succeeded.connect(
        lambda result: (
            results.append(result),
            signal_threads.append(get_ident()),
            events.append("succeeded"),
        )
    )
    runner.finished.connect(lambda: events.append("finished"))

    output = tmp_path / "output.pdf"

    def operation(*, progress, is_cancelled):
        worker_threads.append(get_ident())
        assert not is_cancelled()
        progress(1, 2, "First unit")
        progress(2, 2, "Second unit")
        return OperationResult([output], "done", processed_pages=2)

    with qtbot.waitSignal(runner.finished, timeout=3000):
        assert runner.start(operation)

    assert worker_threads and worker_threads[0] != main_thread
    assert signal_threads and all(
        thread_id == main_thread for thread_id in signal_threads
    )
    assert progress_events == [
        (1, 2, "First unit"),
        (2, 2, "Second unit"),
    ]
    assert len(results) == 1
    assert results[0].processed_pages == 2
    assert events == [
        "started",
        "progress",
        "progress",
        "succeeded",
        "finished",
    ]
    assert not runner.is_running()


def test_runner_emits_expected_failure_and_finished(qtbot):
    runner = OperationRunner()
    failures = []
    successes = []
    cancellations = []
    runner.failed.connect(failures.append)
    runner.succeeded.connect(successes.append)
    runner.cancelled.connect(lambda: cancellations.append(True))

    def operation(**_kwargs):
        raise InvalidInputError("Invalid form value.")

    with qtbot.waitSignal(runner.finished, timeout=3000):
        assert runner.start(operation)

    assert failures == ["Invalid form value."]
    assert successes == []
    assert cancellations == []
    assert not runner.is_running()


def test_runner_converts_unexpected_failure_and_finishes(qtbot):
    runner = OperationRunner()
    failures = []
    runner.failed.connect(failures.append)

    def operation(**_kwargs):
        raise RuntimeError("native failure")

    with qtbot.waitSignal(runner.finished, timeout=3000):
        assert runner.start(operation)

    assert failures == ["Unexpected operation failure: native failure"]
    assert not runner.is_running()


def test_runner_cooperatively_cancels_active_operation(qtbot):
    runner = OperationRunner()
    operation_started = Event()
    cancellations = []
    failures = []
    successes = []
    runner.cancelled.connect(lambda: cancellations.append(True))
    runner.failed.connect(failures.append)
    runner.succeeded.connect(successes.append)

    def operation(*, progress, is_cancelled):
        operation_started.set()
        for current in range(1, 501):
            if is_cancelled():
                raise OperationCancelledError("Operation cancelled.")
            progress(current, 500, f"Unit {current}")
            sleep(0.002)
        return OperationResult([], "unexpected completion")

    with qtbot.waitSignal(runner.finished, timeout=5000):
        assert runner.start(operation)
        qtbot.waitUntil(operation_started.is_set, timeout=1000)
        assert runner.cancel()

    assert cancellations == [True]
    assert failures == []
    assert successes == []
    assert not runner.is_running()
    assert not runner.cancel()


def test_runner_rejects_duplicate_starts(qtbot):
    runner = OperationRunner()
    operation_started = Event()
    release_operation = Event()
    duplicate_rejections = []
    runner.duplicateStartRejected.connect(
        lambda: duplicate_rejections.append(True)
    )

    def blocking_operation(*, progress, is_cancelled):
        operation_started.set()
        release_operation.wait(timeout=3)
        if is_cancelled():
            raise OperationCancelledError()
        return OperationResult([], "done")

    try:
        assert runner.start(blocking_operation)
        qtbot.waitUntil(operation_started.is_set, timeout=1000)
        assert not runner.start(blocking_operation)
        assert duplicate_rejections == [True]

        with qtbot.waitSignal(runner.finished, timeout=3000):
            release_operation.set()
    finally:
        release_operation.set()

    assert not runner.is_running()


def test_controller_restores_exact_control_state_after_success(
    qtbot,
    tmp_path: Path,
):
    panel = OperationPanel()
    enabled_control = QLineEdit()
    disabled_control = QPushButton()
    disabled_control.setEnabled(False)
    for widget in (panel, enabled_control, disabled_control):
        qtbot.addWidget(widget)

    controller = OperationController(
        panel,
        [enabled_control, disabled_control],
    )
    output = tmp_path / "output.pdf"
    output.write_bytes(b"pdf")

    def operation(**_kwargs):
        return OperationResult([output], "Completed.")

    with qtbot.waitSignal(controller.runner.finished, timeout=3000):
        assert controller.start(operation)
        assert not enabled_control.isEnabled()
        assert not disabled_control.isEnabled()
        assert panel.buttons.is_running()

    assert enabled_control.isEnabled()
    assert not disabled_control.isEnabled()
    assert not panel.buttons.is_running()
    assert panel.result.property("resultState") == "success"
    assert panel.output_actions.output_path() == output


def test_controller_restores_controls_after_failure(qtbot):
    panel = OperationPanel()
    control = QLineEdit()
    qtbot.addWidget(panel)
    qtbot.addWidget(control)
    controller = OperationController(panel, [control])

    def operation(**_kwargs):
        raise InvalidInputError("Expected failure.")

    with qtbot.waitSignal(controller.runner.finished, timeout=3000):
        assert controller.start(operation)
        assert not control.isEnabled()

    assert control.isEnabled()
    assert not panel.buttons.is_running()
    assert panel.result.property("resultState") == "error"
    assert panel.result.message_label.text() == "Expected failure."


def test_controller_cancel_button_restores_controls(qtbot):
    panel = OperationPanel()
    control = QLineEdit()
    qtbot.addWidget(panel)
    qtbot.addWidget(control)
    controller = OperationController(panel, [control])
    operation_started = Event()

    def operation(*, is_cancelled, **_kwargs):
        operation_started.set()
        while not is_cancelled():
            sleep(0.002)
        raise OperationCancelledError()

    with qtbot.waitSignal(controller.runner.finished, timeout=5000):
        assert controller.start(operation)
        qtbot.waitUntil(operation_started.is_set, timeout=1000)
        panel.buttons.cancel_button.click()

    assert control.isEnabled()
    assert not panel.buttons.is_running()
    assert panel.result.property("resultState") == "cancelled"
    assert panel.result.status_label.text() == "Cancelled"

