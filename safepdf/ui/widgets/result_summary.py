"""Reusable structured operation-result presentation."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from safepdf.core import OperationResult


def _format_size(size: int | None) -> str | None:
    if size is None:
        return None
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return None


class ResultSummary(QWidget):
    """Show success, failure, metrics, warnings, and generated outputs."""

    outputActivated = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("resultSummary")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("resultState", "neutral")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("resultStatusLabel")

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("resultMessageLabel")
        self.message_label.setWordWrap(True)

        self.metrics_label = QLabel("", self)
        self.metrics_label.setObjectName("resultMetricsLabel")
        self.metrics_label.setWordWrap(True)

        self.warning_list = QListWidget(self)
        self.warning_list.setObjectName("resultWarningList")
        self.warning_list.setAccessibleName("Operation warnings")
        self.warning_list.setMaximumHeight(96)
        self.warning_list.hide()

        self.output_list = QListWidget(self)
        self.output_list.setObjectName("resultOutputList")
        self.output_list.setAccessibleName("Generated output files")
        self.output_list.setMaximumHeight(120)
        self.output_list.itemDoubleClicked.connect(self._activate_output)
        self.output_list.hide()

        layout.addWidget(self.status_label)
        layout.addWidget(self.message_label)
        layout.addWidget(self.metrics_label)
        layout.addWidget(self.warning_list)
        layout.addWidget(self.output_list)
        self.hide()

    def show_result(self, result: OperationResult) -> None:
        """Render a successful structured operation result."""
        self._set_result_state("success")
        self.status_label.setText("Completed")
        self.message_label.setText(result.message)

        metrics = []
        if result.processed_pages:
            metrics.append(f"{result.processed_pages} page(s)")
        if result.processed_files:
            metrics.append(f"{result.processed_files} file(s)")
        if result.skipped_files:
            metrics.append(f"{result.skipped_files} skipped")
        original = _format_size(result.original_size)
        resulting = _format_size(result.resulting_size)
        if original and resulting:
            metrics.append(f"{original} → {resulting}")
        if result.elapsed_seconds is not None:
            metrics.append(f"{result.elapsed_seconds:.2f} s")
        self.metrics_label.setText(" · ".join(metrics))
        self.metrics_label.setVisible(bool(metrics))

        self.warning_list.clear()
        self.warning_list.addItems(result.warnings)
        self.warning_list.setVisible(bool(result.warnings))

        self.output_list.clear()
        for output_path in result.output_paths:
            item = QListWidgetItem(str(output_path))
            item.setData(Qt.ItemDataRole.UserRole, output_path)
            item.setToolTip(str(output_path))
            self.output_list.addItem(item)
        self.output_list.setVisible(bool(result.output_paths))
        self.show()

    def show_error(self, message: str) -> None:
        """Render an operation failure without exposing diagnostic internals."""
        self._set_result_state("error")
        self.status_label.setText("Operation failed")
        self.message_label.setText(message)
        self.metrics_label.clear()
        self.metrics_label.hide()
        self.warning_list.clear()
        self.warning_list.hide()
        self.output_list.clear()
        self.output_list.hide()
        self.show()

    def show_cancelled(self, message: str = "Operation cancelled.") -> None:
        """Render cooperative cancellation as a distinct, expected outcome."""
        self._set_result_state("cancelled")
        self.status_label.setText("Cancelled")
        self.message_label.setText(message)
        self.metrics_label.clear()
        self.metrics_label.hide()
        self.warning_list.clear()
        self.warning_list.hide()
        self.output_list.clear()
        self.output_list.hide()
        self.show()

    def clear(self) -> None:
        """Reset and hide all result content."""
        self._set_result_state("neutral")
        self.status_label.clear()
        self.message_label.clear()
        self.metrics_label.clear()
        self.warning_list.clear()
        self.output_list.clear()
        self.hide()

    def _set_result_state(self, state: str) -> None:
        self.setProperty("resultState", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _activate_output(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, Path):
            self.outputActivated.emit(path)
