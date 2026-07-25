"""Reusable run/cancel, progress, result, and output controls."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from safepdf.core import OperationResult
from safepdf.ui.widgets.output_actions import OutputActions
from safepdf.ui.widgets.result_summary import ResultSummary


class OperationButtons(QWidget):
    """Expose consistent run and cooperative-cancel requests."""

    runRequested = Signal()
    cancelRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("operationButtons")
        self._can_run = True
        self._running = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.run_button = QPushButton("&Run operation", self)
        self.run_button.setObjectName("runButton")
        self.run_button.setProperty("primary", True)
        self.run_button.setAccessibleName("Run operation")
        self.run_button.clicked.connect(self._request_run)

        self.cancel_button = QPushButton("&Cancel", self)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setAccessibleName("Cancel operation")
        self.cancel_button.clicked.connect(self._request_cancel)
        self.cancel_button.hide()

        layout.addStretch(1)
        layout.addWidget(self.run_button)
        layout.addWidget(self.cancel_button)

        self.run_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.run_shortcut.activated.connect(self._request_run)
        self.cancel_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.cancel_shortcut.activated.connect(self._request_cancel)

    def set_can_run(self, can_run: bool) -> None:
        self._can_run = can_run
        self.run_button.setEnabled(can_run and not self._running)

    def set_running(self, running: bool) -> None:
        self._running = running
        self.run_button.setEnabled(self._can_run and not running)
        self.cancel_button.setVisible(running)
        self.cancel_button.setEnabled(running)

    def is_running(self) -> bool:
        return self._running

    def _request_run(self) -> None:
        if self.run_button.isEnabled():
            self.runRequested.emit()

    def _request_cancel(self) -> None:
        if self._running and self.cancel_button.isEnabled():
            self.cancel_button.setEnabled(False)
            self.cancelRequested.emit()


class ProgressDisplay(QWidget):
    """Display operation-local determinate or indeterminate progress."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("progressDisplay")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("progressMessageLabel")
        self.message_label.setWordWrap(True)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("operationProgressBar")
        self.progress_bar.setTextVisible(True)

        layout.addWidget(self.message_label)
        layout.addWidget(self.progress_bar)
        self.reset()

    def set_progress(self, current: int, total: int, message: str = "") -> None:
        if total <= 0:
            self.set_indeterminate(message)
            return
        bounded_current = min(max(0, current), total)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(bounded_current)
        self.progress_bar.setFormat(f"{bounded_current} / {total}")
        self.message_label.setText(message)
        self.show()

    def set_indeterminate(self, message: str = "Working…") -> None:
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Working…")
        self.message_label.setText(message)
        self.show()

    def reset(self) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.reset()
        self.progress_bar.setFormat("%p%")
        self.message_label.clear()
        self.hide()


class OperationPanel(QWidget):
    """Compose the shared controls used by every operation page."""

    runRequested = Signal()
    cancelRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("operationPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        heading_row = QHBoxLayout()
        heading_row.setContentsMargins(0, 0, 0, 0)
        heading_row.setSpacing(12)

        labels = QWidget(self)
        labels_layout = QVBoxLayout(labels)
        labels_layout.setContentsMargins(0, 0, 0, 0)
        labels_layout.setSpacing(2)
        title = QLabel("Ready to process", labels)
        title.setObjectName("panelTitleLabel")
        description = QLabel(
            "Review the settings above, then run this operation.",
            labels,
        )
        description.setObjectName("panelDescriptionLabel")
        description.setWordWrap(True)
        labels_layout.addWidget(title)
        labels_layout.addWidget(description)

        self.buttons = OperationButtons(self)
        self.progress = ProgressDisplay(self)
        self.result = ResultSummary(self)
        self.output_actions = OutputActions(self)
        self.output_actions.hide()

        self.buttons.runRequested.connect(self.runRequested.emit)
        self.buttons.cancelRequested.connect(self.cancelRequested.emit)

        heading_row.addWidget(labels, 1)
        heading_row.addWidget(self.buttons)
        layout.addLayout(heading_row)
        layout.addWidget(self.progress)
        layout.addWidget(self.result)
        layout.addWidget(self.output_actions)

    def set_can_run(self, can_run: bool) -> None:
        self.buttons.set_can_run(can_run)

    def set_running(self, running: bool) -> None:
        self.buttons.set_running(running)
        if running:
            self.result.clear()
            self.output_actions.set_output_path(None)
            self.output_actions.hide()

    def set_progress(self, current: int, total: int, message: str = "") -> None:
        self.progress.set_progress(current, total, message)

    def show_result(self, result: OperationResult) -> None:
        self.buttons.set_running(False)
        self.progress.reset()
        self.result.show_result(result)
        output_path = result.output_paths[0] if result.output_paths else None
        self.output_actions.set_output_path(output_path)
        self.output_actions.setVisible(output_path is not None)

    def show_error(self, message: str) -> None:
        self.buttons.set_running(False)
        self.progress.reset()
        self.result.show_error(message)
        self.output_actions.set_output_path(None)
        self.output_actions.hide()

    def show_cancelled(self) -> None:
        self.buttons.set_running(False)
        self.progress.reset()
        self.result.show_cancelled()
        self.output_actions.set_output_path(None)
        self.output_actions.hide()
