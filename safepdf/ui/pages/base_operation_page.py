"""Shared form, validation, worker, progress, and result behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from safepdf.core import OperationResult
from safepdf.ui.pages.registry import PageDefinition
from safepdf.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM
from safepdf.ui.widgets import OperationPanel, PathPicker
from safepdf.ui.workers import OperationCallable, OperationController

OperationInvocation = tuple[
    OperationCallable,
    tuple[Any, ...],
    dict[str, Any],
]


class OperationPage(QWidget):
    """Base class used by every worker-driven operation screen."""

    statusChanged = Signal(str)
    progressChanged = Signal(int, int, str)
    progressCleared = Signal()
    outputChanged = Signal(object)
    runningChanged = Signal(bool)

    def __init__(self, definition: PageDefinition) -> None:
        super().__init__()
        self.definition = definition
        self._pickers: list[PathPicker] = []
        self.setObjectName(f"{definition.key}Page")

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setObjectName("operationPageScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget(scroll)
        content.setObjectName("operationPageContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
        )
        content_layout.setSpacing(SPACE_MD)

        title = QLabel(definition.title, content)
        title.setObjectName("pageTitleLabel")

        description = QLabel(definition.description, content)
        description.setObjectName("pageDescriptionLabel")
        description.setWordWrap(True)

        self.form_container = QWidget(content)
        self.form_container.setObjectName("operationForm")
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setContentsMargins(0, SPACE_SM, 0, 0)
        self.form_layout.setHorizontalSpacing(SPACE_MD)
        self.form_layout.setVerticalSpacing(SPACE_SM)
        self.form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.validation_label = QLabel("", content)
        self.validation_label.setObjectName("formErrorLabel")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()

        self.operation_panel = OperationPanel(content)
        # A concise alias is useful to callers and UI tests.
        self.panel = self.operation_panel
        self.controller = OperationController(
            self.operation_panel,
            [self.form_container],
            parent=self,
        )

        content_layout.addWidget(title)
        content_layout.addWidget(description)
        content_layout.addWidget(self.form_container)
        content_layout.addWidget(self.validation_label)
        content_layout.addWidget(self.operation_panel)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        runner = self.controller.runner
        self.operation_panel.runRequested.connect(self._start_operation)
        runner.started.connect(
            lambda: self.statusChanged.emit(
                f"{self.definition.label} started."
            )
        )
        runner.progress.connect(self.progressChanged.emit)
        runner.progress.connect(
            lambda _current, _total, message: (
                self.statusChanged.emit(message) if message else None
            )
        )
        runner.succeeded.connect(self._operation_succeeded)
        runner.failed.connect(
            lambda message: self.statusChanged.emit(
                f"{self.definition.label} failed: {message}"
            )
        )
        runner.cancelled.connect(
            lambda: self.statusChanged.emit(
                f"{self.definition.label} cancelled."
            )
        )
        runner.finished.connect(self.progressCleared.emit)
        runner.runningChanged.connect(self.runningChanged.emit)
        runner.runningChanged.connect(self._running_changed)

        self.operation_panel.set_can_run(False)

    def add_picker(self, picker: PathPicker) -> PathPicker:
        """Add a full-width path picker and include it in validation."""
        self._pickers.append(picker)
        self.form_layout.addRow(picker)
        picker.validationChanged.connect(self._refresh_validation)
        return picker

    def add_option(
        self,
        label: str,
        widget: QWidget,
        *,
        buddy: QWidget | None = None,
    ) -> QWidget:
        """Add a labelled operation-specific control."""
        label_widget = QLabel(label, self.form_container)
        label_widget.setBuddy(buddy or widget)
        self.form_layout.addRow(label_widget, widget)
        return widget

    def watch(self, signal: object) -> None:
        """Revalidate when a Qt signal changes an operation option."""
        connect = getattr(signal, "connect")
        connect(self._refresh_validation)

    def specific_validation_error(self) -> str:
        """Return an operation-specific validation error, if any."""
        return ""

    def validation_error(self) -> str:
        """Return the first picker or operation-specific validation error."""
        for picker in self._pickers:
            if not picker.is_valid():
                return picker.validation_message()
        return self.specific_validation_error()

    def operation_invocation(self) -> OperationInvocation:
        """Build the core callable and arguments for this page."""
        raise NotImplementedError

    def finish_setup(self) -> None:
        """Perform initial validation after a subclass creates its form."""
        self._refresh_validation()

    @Slot()
    def _refresh_validation(self, *_args: object) -> None:
        error = self.validation_error()
        self.validation_label.setText(error)
        self.validation_label.setVisible(bool(error))
        self.operation_panel.set_can_run(
            not error and not self.controller.is_running()
        )

    @Slot()
    def _start_operation(self) -> None:
        error = self.validation_error()
        if error:
            self._refresh_validation()
            self.statusChanged.emit(error)
            return

        operation, args, kwargs = self.operation_invocation()
        if not self.controller.start(operation, *args, **kwargs):
            self.statusChanged.emit(
                f"{self.definition.label} is already running."
            )

    @Slot(object)
    def _operation_succeeded(self, result: OperationResult) -> None:
        self.statusChanged.emit(result.message)
        output = result.output_paths[0] if result.output_paths else None
        self.outputChanged.emit(output)

    @Slot(bool)
    def _running_changed(self, running: bool) -> None:
        if not running:
            self._refresh_validation()


def set_default_output(
    output_picker: PathPicker,
    source: Path | None,
    suffix: str,
) -> None:
    """Populate a derived output path without replacing a user's choice."""
    if source is not None and output_picker.path() is None:
        output_picker.set_path(source.with_name(f"{source.stem}{suffix}"))


__all__ = [
    "OperationInvocation",
    "OperationPage",
    "set_default_output",
]
