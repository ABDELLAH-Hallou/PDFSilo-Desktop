"""Shared form, validation, worker, progress, and result behavior."""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QCoreApplication, Qt, Signal, Slot
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QFormLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.core import OperationResult
from pdfsilo.ui.pages.registry import PageDefinition
from pdfsilo.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XS
from pdfsilo.ui.widgets import (
    OperationPanel,
    OutputFilePicker,
    PathPicker,
    PdfPreview,
    MultiplePdfPicker,
    SinglePdfPicker,
)
from pdfsilo.ui.workers import OperationCallable, OperationController

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
        self._staged_path: Path | None = None
        self._staged_destination: Path | None = None
        self._staged_result: OperationResult | None = None
        self._supports_input_preview = False
        self._show_input_previews = True
        self._confirm_overwrite = True
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
        self.operation_panel.saveRequested.connect(self._save_staged_output)
        self.operation_panel.discardRequested.connect(
            self._discard_staged_output
        )
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
        runner.failed.connect(self._failed_or_cancelled)
        runner.cancelled.connect(
            lambda: self.statusChanged.emit(
                f"{self.definition.label} cancelled."
            )
        )
        runner.cancelled.connect(self._failed_or_cancelled)
        runner.finished.connect(self.progressCleared.emit)
        runner.runningChanged.connect(self.runningChanged.emit)
        runner.runningChanged.connect(self._running_changed)

        self.operation_panel.set_can_run(False)
        application = QCoreApplication.instance()
        if application is not None:
            application.aboutToQuit.connect(self._discard_staged_output)

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
        self._supports_input_preview = add_pdf_preview
        if self._show_input_previews:
            self._ensure_input_preview()
        self._refresh_validation()

    def set_input_previews_enabled(self, enabled: bool) -> None:
        """Show or suppress optional input previews for this operation."""
        self._show_input_previews = enabled
        if enabled:
            self._ensure_input_preview()
        elif self._staged_result is None:
            self.preview_card.hide()

    def set_confirm_overwrite(self, enabled: bool) -> None:
        """Control whether publishing over an existing file needs consent."""
        self._confirm_overwrite = enabled

    def _ensure_input_preview(self) -> None:
        if not self._supports_input_preview:
            return
        if self.pdf_preview is not None:
            self.preview_card.show()
            return
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
        if input_picker is None:
            return
        self.pdf_preview = PdfPreview(self.preview_card)
        self.preview_content_layout.addWidget(self.pdf_preview)
        self.preview_card.show()
        if isinstance(input_picker, MultiplePdfPicker):
            input_picker.pathsChanged.connect(self.pdf_preview.set_pdfs)
            self.pdf_preview.set_pdfs(input_picker.paths())
        else:
            input_picker.pathChanged.connect(self.pdf_preview.set_pdf)
            self.pdf_preview.set_pdf(input_picker.path())
        self.operation_splitter.setSizes([620, 380])

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
        output_picker = next(
            (
                picker
                for picker in self._pickers
                if isinstance(picker, OutputFilePicker)
            ),
            None,
        )
        if output_picker is not None:
            destination = output_picker.path()
            assert destination is not None
            self._prepare_staged_output(destination)
            assert self._staged_path is not None
            args = self._replace_path(args, destination, self._staged_path)
            kwargs = self._replace_path(
                kwargs,
                destination,
                self._staged_path,
            )
        if not self.controller.start(operation, *args, **kwargs):
            self._discard_staged_output()
            self.statusChanged.emit(
                f"{self.definition.label} is already running."
            )

    @Slot(object)
    def _operation_succeeded(self, result: OperationResult) -> None:
        if (
            self._staged_path is not None
            and self._staged_destination is not None
            and self._staged_path.is_file()
        ):
            self._staged_result = result
            self.operation_panel.show_review_result(
                result,
                self._staged_destination,
            )
            self._show_staged_preview()
            self.form_container.setEnabled(False)
            self.statusChanged.emit(
                "Processing complete. Review the result, then choose Save "
                "result or Discard result."
            )
            return
        self.statusChanged.emit(result.message)
        output = result.output_paths[0] if result.output_paths else None
        self.outputChanged.emit(output)

    @Slot(bool)
    def _running_changed(self, running: bool) -> None:
        if not running:
            self._refresh_validation()
            if self._staged_result is not None:
                self.form_container.setEnabled(False)
                self.operation_panel.set_can_run(False)

    def _prepare_staged_output(self, destination: Path) -> None:
        self._discard_staged_output()
        self._staged_destination = destination
        self._staged_path = destination.with_name(
            f".{destination.stem}.{uuid4().hex}.preview{destination.suffix}"
        )

    @staticmethod
    def _replace_path(
        value: Any,
        source: Path,
        replacement: Path,
    ) -> Any:
        if isinstance(value, Path):
            return replacement if value == source else value
        if isinstance(value, tuple):
            return tuple(
                OperationPage._replace_path(item, source, replacement)
                for item in value
            )
        if isinstance(value, list):
            return [
                OperationPage._replace_path(item, source, replacement)
                for item in value
            ]
        if isinstance(value, dict):
            return {
                key: OperationPage._replace_path(item, source, replacement)
                for key, item in value.items()
            }
        return value

    def _show_staged_preview(self) -> None:
        assert self._staged_path is not None
        if self.pdf_preview is None:
            self.pdf_preview = PdfPreview(self.preview_card)
            self.preview_content_layout.addWidget(self.pdf_preview)
            self.preview_card.show()
            self.operation_splitter.setSizes([620, 380])
        if not self.pdf_preview.property("stagedSaveSignalsConnected"):
            self.pdf_preview.previewReady.connect(
                self._staged_preview_finished
            )
            self.pdf_preview.previewFailed.connect(
                self._staged_preview_finished
            )
            self.pdf_preview.setProperty("stagedSaveSignalsConnected", True)
        # PyMuPDF may briefly hold the staged file open on Windows. Saving is
        # enabled as soon as preview rendering closes the document.
        self.operation_panel.save_button.setEnabled(False)
        self.operation_panel.discard_button.setEnabled(False)
        self.pdf_preview.set_pdf(self._staged_path)

    @Slot()
    def _staged_preview_finished(self, *_args: object) -> None:
        if (
            self._staged_result is not None
            and self.pdf_preview is not None
            and self.pdf_preview.source_path() == self._staged_path
        ):
            self.operation_panel.save_button.setEnabled(True)
            self.operation_panel.discard_button.setEnabled(True)

    @Slot()
    def _save_staged_output(self) -> None:
        staged = self._staged_path
        destination = self._staged_destination
        result = self._staged_result
        if staged is None or destination is None or result is None:
            return
        if destination.exists() and self._confirm_overwrite:
            choice = QMessageBox.question(
                self,
                "Replace existing output?",
                (
                    f"'{destination.name}' already exists.\n\n"
                    "Replace it with the reviewed result?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.Cancel
                ),
                QMessageBox.StandardButton.Cancel,
            )
            if choice is not QMessageBox.StandardButton.Yes:
                self.statusChanged.emit(
                    "Save cancelled. The reviewed result is still available."
                )
                return
        try:
            os.replace(staged, destination)
        except OSError as exc:
            message = f"Could not save '{destination}': {exc}"
            self.operation_panel.show_error(message)
            self.statusChanged.emit(message)
            return

        final_result = replace(
            result,
            output_paths=[destination],
            message=f"Saved '{destination}'.",
        )
        self._staged_path = None
        self._staged_destination = None
        self._staged_result = None
        self.form_container.setEnabled(True)
        self.operation_panel.save_button.setEnabled(True)
        self.operation_panel.discard_button.setEnabled(True)
        self.operation_panel.show_result(final_result)
        if self.pdf_preview is not None:
            self.pdf_preview.set_pdf(destination)
        self.statusChanged.emit(final_result.message)
        self.outputChanged.emit(destination)
        self._refresh_validation()

    @Slot()
    def _discard_staged_output(self) -> None:
        staged = self._staged_path
        if staged is not None:
            try:
                staged.unlink(missing_ok=True)
            except OSError:
                # A preview worker can still own the file during application
                # shutdown. It remains hidden and is never published.
                pass
        had_result = self._staged_result is not None
        self._staged_path = None
        self._staged_destination = None
        self._staged_result = None
        self.operation_panel.save_button.setEnabled(True)
        self.operation_panel.discard_button.setEnabled(True)
        if had_result:
            self.operation_panel.review_actions.hide()
            self.operation_panel.result.clear()
            self.form_container.setEnabled(True)
            self._restore_input_preview()
            self.statusChanged.emit("The generated result was discarded.")
            self._refresh_validation()

    @Slot()
    def _failed_or_cancelled(self, *_args: object) -> None:
        self._discard_staged_output()

    def _restore_input_preview(self) -> None:
        if self.pdf_preview is None:
            return
        if not self._show_input_previews:
            self.preview_card.hide()
            return
        self.preview_card.show()
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
        if isinstance(input_picker, MultiplePdfPicker):
            self.pdf_preview.set_pdfs(input_picker.paths())
        elif isinstance(input_picker, SinglePdfPicker):
            self.pdf_preview.set_pdf(input_picker.path())


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
