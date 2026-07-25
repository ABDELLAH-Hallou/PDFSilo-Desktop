"""Shared form, validation, worker, progress, and result behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QFormLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from safepdf.core import OperationResult
from safepdf.ui.pages.registry import PageDefinition
from safepdf.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XS
from safepdf.ui.widgets import (
    OperationPanel,
    PathPicker,
    PdfPreview,
    MultiplePdfPicker,
    SinglePdfPicker,
)
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
        self.pdf_preview: PdfPreview | None = None
        self._responsive_orientation = Qt.Orientation.Horizontal
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

        header = QFrame(content)
        header.setObjectName("operationHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, SPACE_XS)
        header_layout.setSpacing(SPACE_XS)

        eyebrow = QLabel("PDF TOOL", header)
        eyebrow.setObjectName("pageEyebrowLabel")

        title = QLabel(definition.title, header)
        title.setObjectName("pageTitleLabel")

        description = QLabel(definition.description, header)
        description.setObjectName("pageDescriptionLabel")
        description.setWordWrap(True)
        header_layout.addWidget(eyebrow)
        header_layout.addWidget(title)
        header_layout.addWidget(description)

        self.workspace = QWidget(content)
        self.workspace.setObjectName("operationWorkspace")
        workspace_layout = QVBoxLayout(self.workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self.operation_splitter = QSplitter(
            Qt.Orientation.Horizontal,
            self.workspace,
        )
        self.operation_splitter.setObjectName("operationSplitter")
        self.operation_splitter.setChildrenCollapsible(False)

        self.form_container = QWidget(self.operation_splitter)
        self.form_container.setObjectName("operationForm")
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setContentsMargins(
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
        )
        self.form_layout.setHorizontalSpacing(SPACE_MD)
        self.form_layout.setVerticalSpacing(SPACE_MD)
        self.form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.form_layout.setRowWrapPolicy(
            QFormLayout.RowWrapPolicy.WrapLongRows
        )
        self.form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        form_heading = QWidget(self.form_container)
        form_heading.setObjectName("formHeading")
        form_heading_layout = QVBoxLayout(form_heading)
        form_heading_layout.setContentsMargins(0, 0, 0, SPACE_XS)
        form_heading_layout.setSpacing(2)
        form_title = QLabel("Files and options", form_heading)
        form_title.setObjectName("panelTitleLabel")
        form_description = QLabel(
            "Choose your inputs, output, and processing preferences.",
            form_heading,
        )
        form_description.setObjectName("panelDescriptionLabel")
        form_description.setWordWrap(True)
        form_heading_layout.addWidget(form_title)
        form_heading_layout.addWidget(form_description)
        self.form_layout.addRow(form_heading)

        self.preview_card = QFrame(self.operation_splitter)
        self.preview_card.setObjectName("previewCard")
        preview_layout = QVBoxLayout(self.preview_card)
        preview_layout.setContentsMargins(
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
        )
        preview_layout.setSpacing(SPACE_MD)
        preview_title = QLabel("Document preview", self.preview_card)
        preview_title.setObjectName("previewTitleLabel")
        preview_description = QLabel(
            "Preview pages before running the operation.",
            self.preview_card,
        )
        preview_description.setObjectName("panelDescriptionLabel")
        preview_description.setWordWrap(True)
        self.preview_content_layout = QVBoxLayout()
        self.preview_content_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_content_layout.setSpacing(0)
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(preview_description)
        preview_layout.addLayout(self.preview_content_layout, 1)
        self.preview_card.hide()

        self.operation_splitter.addWidget(self.form_container)
        self.operation_splitter.addWidget(self.preview_card)
        self.operation_splitter.setStretchFactor(0, 3)
        self.operation_splitter.setStretchFactor(1, 2)
        workspace_layout.addWidget(self.operation_splitter)

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

        content_layout.addWidget(header)
        content_layout.addWidget(self.workspace)
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
        label_widget.setObjectName("optionLabel")
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

    def finish_setup(self, *, add_pdf_preview: bool = True) -> None:
        """Perform initial validation after a subclass creates its form."""
        if add_pdf_preview and self.pdf_preview is None:
            input_picker = next(
                (
                    picker
                    for picker in self._pickers
                    if isinstance(
                        picker,
                        (SinglePdfPicker, MultiplePdfPicker),
                    )
                ),
                None,
            )
            if input_picker is not None:
                self.pdf_preview = PdfPreview(self.preview_card)
                self.preview_content_layout.addWidget(self.pdf_preview)
                self.preview_card.show()
                input_picker.pathChanged.connect(self.pdf_preview.set_pdf)
                self.operation_splitter.setSizes([620, 380])
        self._refresh_validation()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Stack the workspace cards when horizontal space is constrained."""
        super().resizeEvent(event)
        orientation = (
            Qt.Orientation.Horizontal
            if event.size().width() >= 820
            else Qt.Orientation.Vertical
        )
        if orientation == self._responsive_orientation:
            return
        self._responsive_orientation = orientation
        self.operation_splitter.setOrientation(orientation)
        if orientation is Qt.Orientation.Horizontal:
            self.operation_splitter.setSizes([620, 380])
        else:
            self.operation_splitter.setSizes([520, 360])

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
