"""Tests for reusable Phase 7 input and operation widgets."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from safepdf.core import OperationResult
from safepdf.ui.widgets import (
    DropZone,
    FolderPicker,
    ImageFilePicker,
    MultiplePdfPicker,
    OperationButtons,
    OperationPanel,
    OutputActions,
    OutputDirectoryPicker,
    OutputFilePicker,
    ProgressDisplay,
    ResultSummary,
    SinglePdfPicker,
)


def test_single_pdf_picker_validates_and_emits_stable_signals(
    qtbot,
    tmp_pdf: Path,
):
    picker = SinglePdfPicker()
    qtbot.addWidget(picker)
    paths_seen = []
    path_seen = []
    validity_seen = []
    validation_seen = []
    picker.pathsChanged.connect(paths_seen.append)
    picker.pathChanged.connect(path_seen.append)
    picker.validityChanged.connect(validity_seen.append)
    picker.validationChanged.connect(
        lambda valid, message: validation_seen.append((valid, message))
    )

    picker.set_path(tmp_pdf)

    assert picker.path() == tmp_pdf
    assert picker.paths() == [tmp_pdf]
    assert picker.is_valid()
    assert picker.line_edit.property("validationState") == "valid"
    assert paths_seen == [[tmp_pdf]]
    assert path_seen == [tmp_pdf]
    assert validity_seen == [True]
    assert validation_seen == [(True, "")]

    picker.clear()
    assert picker.path() is None
    assert not picker.is_valid()
    assert validity_seen == [True, False]


@pytest.mark.parametrize(
    ("invalid_name", "message"),
    [
        ("missing.pdf", "File not found"),
        ("wrong.txt", "must use one of"),
    ],
)
def test_single_pdf_picker_shows_clear_invalid_state(
    qtbot,
    tmp_path: Path,
    invalid_name: str,
    message: str,
):
    picker = SinglePdfPicker()
    qtbot.addWidget(picker)

    picker.set_path(tmp_path / invalid_name)

    assert not picker.is_valid()
    assert picker.line_edit.property("validationState") == "invalid"
    assert picker.error_label.isVisibleTo(picker)
    assert message in picker.validation_message()


def test_multiple_pdf_picker_accepts_multiple_existing_files(
    qtbot,
    tmp_pdf_folder: Path,
):
    picker = MultiplePdfPicker()
    qtbot.addWidget(picker)
    pdfs = sorted(tmp_pdf_folder.glob("*.pdf"))

    picker.set_paths(pdfs)

    assert picker.paths() == pdfs
    assert picker.is_valid()
    assert all(str(path) in picker.line_edit.text() for path in pdfs)


def test_ordered_file_picker_appends_reorders_and_removes_files(
    qtbot,
    monkeypatch,
    tmp_pdf_folder: Path,
):
    picker = MultiplePdfPicker()
    qtbot.addWidget(picker)
    pdfs = sorted(tmp_pdf_folder.glob("*.pdf"))
    dialog_results = iter(
        [
            ([str(pdfs[1])], "PDF"),
            ([str(pdfs[0]), str(pdfs[2])], "PDF"),
        ]
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *_args, **_kwargs: next(dialog_results),
    )

    picker.add_button.click()
    picker.add_button.click()

    assert picker.paths() == [pdfs[1], pdfs[0], pdfs[2]]
    assert picker.file_list.count() == 3
    picker.file_list.setCurrentRow(1)
    picker.move_up_button.click()
    assert picker.paths() == [pdfs[0], pdfs[1], pdfs[2]]

    picker.file_list.setCurrentRow(1)
    picker.remove_button.click()
    assert picker.paths() == [pdfs[0], pdfs[2]]
    assert picker.file_list.item(0).text().startswith("1.")
    assert picker.file_list.item(1).text().startswith("2.")


def test_image_picker_accepts_images_and_rejects_pdf(
    qtbot,
    tmp_two_png_images: list[Path],
    tmp_pdf: Path,
):
    picker = ImageFilePicker()
    qtbot.addWidget(picker)

    picker.set_images(tmp_two_png_images)
    assert picker.is_valid()

    picker.set_paths([tmp_pdf])
    assert not picker.is_valid()
    assert ".png" in picker.validation_message()


def test_folder_picker_validates_existing_directory(
    qtbot,
    tmp_path: Path,
):
    picker = FolderPicker()
    qtbot.addWidget(picker)

    picker.set_path(tmp_path)
    assert picker.is_valid()

    picker.set_path(tmp_path / "missing")
    assert not picker.is_valid()
    assert "Folder not found" in picker.validation_message()


def test_output_file_picker_validates_suffix_and_parent(
    qtbot,
    tmp_path: Path,
):
    picker = OutputFilePicker()
    qtbot.addWidget(picker)

    picker.set_path(tmp_path / "output.pdf")
    assert picker.is_valid()

    picker.set_path(tmp_path / "output.txt")
    assert not picker.is_valid()

    picker.set_path(tmp_path / "missing" / "output.pdf")
    assert not picker.is_valid()
    assert "does not exist" in picker.validation_message()


def test_output_directory_picker_accepts_existing_or_creatable_folder(
    qtbot,
    tmp_path: Path,
    tmp_pdf: Path,
):
    picker = OutputDirectoryPicker()
    qtbot.addWidget(picker)

    picker.set_path(tmp_path)
    assert picker.is_valid()

    picker.set_path(tmp_path / "new-output")
    assert picker.is_valid()

    picker.set_path(tmp_pdf)
    assert not picker.is_valid()
    assert "not a folder" in picker.validation_message()


def test_picker_browse_uses_appropriate_dialogs(
    qtbot,
    monkeypatch,
    tmp_pdf: Path,
    tmp_pdf_folder: Path,
    tmp_path: Path,
):
    single = SinglePdfPicker()
    multiple = MultiplePdfPicker()
    folder = FolderPicker()
    output = OutputFilePicker()
    output_directory = OutputDirectoryPicker()
    for picker in (single, multiple, folder, output, output_directory):
        qtbot.addWidget(picker)

    pdfs = sorted(tmp_pdf_folder.glob("*.pdf"))
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: (str(tmp_pdf), "PDF"),
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *_args, **_kwargs: ([str(path) for path in pdfs], "PDF"),
    )
    directory_values = iter([str(tmp_path), str(tmp_path / "new-output")])
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: next(directory_values),
    )
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(tmp_path / "output.pdf"), "PDF"),
    )

    single.browse()
    multiple.browse()
    folder.browse()
    output.browse()
    output_directory.browse()

    assert single.path() == tmp_pdf
    assert multiple.paths() == pdfs
    assert folder.path() == tmp_path
    assert output.path() == tmp_path / "output.pdf"
    assert output_directory.path() == tmp_path / "new-output"


def test_picker_drag_drop_api_accepts_only_compatible_paths(
    qtbot,
    tmp_pdf: Path,
    tmp_png_image: Path,
):
    picker = SinglePdfPicker()
    qtbot.addWidget(picker)

    assert picker.accepts_dropped_paths([tmp_pdf])
    assert picker.accept_dropped_paths([tmp_pdf])
    assert picker.path() == tmp_pdf

    assert not picker.accepts_dropped_paths([tmp_png_image])
    assert not picker.accept_dropped_paths([tmp_png_image])
    assert picker.line_edit.property("validationState") == "invalid"


def test_picker_controls_are_keyboard_accessible(qtbot):
    picker = SinglePdfPicker()
    qtbot.addWidget(picker)

    assert picker.label.buddy() is picker.line_edit
    assert picker.line_edit.focusPolicy() != Qt.FocusPolicy.NoFocus
    assert picker.browse_button.focusPolicy() != Qt.FocusPolicy.NoFocus
    assert picker.line_edit.accessibleName() == "PDF file"
    assert picker.browse_button.accessibleName()


def test_drop_zone_emits_acceptance_rejection_and_keyboard_activation(
    qtbot,
    tmp_pdf: Path,
    tmp_png_image: Path,
):
    zone = DropZone(allowed_suffixes={".pdf"})
    qtbot.addWidget(zone)
    dropped = []
    rejected = []
    zone.pathsDropped.connect(dropped.append)
    zone.dropRejected.connect(rejected.append)

    assert zone.accept_paths([tmp_pdf])
    assert dropped == [[tmp_pdf]]
    assert zone.property("validationState") == "valid"

    assert not zone.accept_paths([tmp_png_image])
    assert rejected and "must use one of" in rejected[-1]
    assert zone.property("validationState") == "invalid"

    zone.show()
    zone.setFocus()
    with qtbot.waitSignal(zone.activated):
        qtbot.keyClick(zone, Qt.Key.Key_Return)


def test_operation_buttons_expose_run_cancel_state_and_signals(qtbot):
    buttons = OperationButtons()
    qtbot.addWidget(buttons)
    run_requests = []
    cancel_requests = []
    buttons.runRequested.connect(lambda: run_requests.append(True))
    buttons.cancelRequested.connect(lambda: cancel_requests.append(True))

    buttons.run_button.click()
    assert run_requests == [True]

    buttons.set_running(True)
    assert buttons.is_running()
    assert not buttons.run_button.isEnabled()
    assert not buttons.cancel_button.isHidden()

    buttons.cancel_button.click()
    assert cancel_requests == [True]
    assert not buttons.cancel_button.isEnabled()

    buttons.set_running(False)
    buttons.set_can_run(False)
    buttons.run_button.click()
    assert run_requests == [True]


def test_progress_display_supports_all_states(qtbot):
    display = ProgressDisplay()
    qtbot.addWidget(display)

    assert display.isHidden()
    display.set_progress(2, 5, "Page 2")
    assert not display.isHidden()
    assert (
        display.progress_bar.minimum(),
        display.progress_bar.maximum(),
        display.progress_bar.value(),
    ) == (0, 5, 2)
    assert display.progress_bar.format() == "2 / 5"
    assert display.message_label.text() == "Page 2"

    display.set_indeterminate("Preparing")
    assert (display.progress_bar.minimum(), display.progress_bar.maximum()) == (
        0,
        0,
    )

    display.reset()
    assert display.isHidden()


def test_result_summary_renders_structured_result_and_output_signal(
    qtbot,
    tmp_path: Path,
):
    output = tmp_path / "output.pdf"
    output.write_bytes(b"pdf")
    result = OperationResult(
        output_paths=[output],
        message="Created output.",
        warnings=["One warning"],
        processed_pages=3,
        processed_files=1,
        original_size=2048,
        resulting_size=1024,
        elapsed_seconds=1.25,
    )
    summary = ResultSummary()
    qtbot.addWidget(summary)
    activated = []
    summary.outputActivated.connect(activated.append)

    summary.show_result(result)

    assert summary.property("resultState") == "success"
    assert summary.status_label.text() == "Completed"
    assert summary.message_label.text() == "Created output."
    assert "3 page(s)" in summary.metrics_label.text()
    assert "2.0 KB → 1.0 KB" in summary.metrics_label.text()
    assert summary.warning_list.count() == 1
    assert summary.output_list.count() == 1

    summary.output_list.itemDoubleClicked.emit(summary.output_list.item(0))
    assert activated == [output]

    summary.show_error("Expected failure")
    assert summary.property("resultState") == "error"
    assert summary.message_label.text() == "Expected failure"
    assert summary.output_list.isHidden()

    summary.show_cancelled()
    assert summary.property("resultState") == "cancelled"
    assert summary.status_label.text() == "Cancelled"


def test_output_actions_open_output_and_containing_folder(
    qtbot,
    monkeypatch,
    tmp_path: Path,
):
    output = tmp_path / "output.pdf"
    output.write_bytes(b"pdf")
    actions = OutputActions()
    qtbot.addWidget(actions)
    opened_urls = []
    requested_outputs = []
    requested_folders = []
    actions.openOutputRequested.connect(requested_outputs.append)
    actions.openFolderRequested.connect(requested_folders.append)
    monkeypatch.setattr(
        QDesktopServices,
        "openUrl",
        lambda url: opened_urls.append(url.toLocalFile()) or True,
    )

    actions.set_output_path(output)
    assert actions.open_output()
    assert actions.open_containing_folder()

    assert requested_outputs == [output]
    assert requested_folders == [tmp_path]
    assert [Path(path) for path in opened_urls] == [output, tmp_path]


def test_output_actions_report_missing_output(qtbot, tmp_path: Path):
    actions = OutputActions()
    qtbot.addWidget(actions)
    failures = []
    actions.openFailed.connect(failures.append)

    actions.set_output_path(tmp_path / "missing.pdf")

    assert not actions.open_output()
    assert failures == ["The output path is no longer available."]


def test_operation_panel_coordinates_run_progress_result_and_error(
    qtbot,
    tmp_path: Path,
):
    output = tmp_path / "output.pdf"
    output.write_bytes(b"pdf")
    panel = OperationPanel()
    qtbot.addWidget(panel)
    run_requests = []
    cancel_requests = []
    panel.runRequested.connect(lambda: run_requests.append(True))
    panel.cancelRequested.connect(lambda: cancel_requests.append(True))

    panel.buttons.run_button.click()
    assert run_requests == [True]

    panel.set_running(True)
    panel.set_progress(1, 2, "Working")
    panel.buttons.cancel_button.click()
    assert cancel_requests == [True]

    result = OperationResult(
        output_paths=[output],
        message="Done",
        processed_files=1,
    )
    panel.show_result(result)
    assert not panel.buttons.is_running()
    assert panel.progress.isHidden()
    assert not panel.result.isHidden()
    assert not panel.output_actions.isHidden()
    assert panel.output_actions.output_path() == output

    panel.show_error("Failed")
    assert panel.result.property("resultState") == "error"
    assert panel.output_actions.isHidden()
