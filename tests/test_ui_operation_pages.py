"""End-to-end tests for Phase 9 operation screens."""

from pathlib import Path
from threading import Event
from time import sleep

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings

from safepdf.core import OperationCancelledError, OperationResult
from safepdf.ui.main_window import MainWindow
from safepdf.ui.pages import (
    OPERATION_PAGE_FACTORIES,
    PAGE_DEFINITIONS,
    AddImagesPage,
    CompressPage,
    DecryptPage,
    EncryptPage,
    ExtractImagesPage,
    ExtractRangePage,
    ImagesToPdfPage,
    MergePage,
    OperationPage,
    ReorderPage,
    RotatePage,
    SplitPage,
    ToImagesPage,
    WatermarkPage,
)
from safepdf.ui.widgets import OperationPanel

DEFINITIONS = {
    definition.key: definition
    for definition in PAGE_DEFINITIONS
}


def _page(qtbot, page_type, key: str):
    page = page_type(DEFINITIONS[key])
    qtbot.addWidget(page)
    return page


def _run_successfully(qtbot, page: OperationPage, timeout: int = 10_000):
    results = []
    failures = []
    progress_events = []
    page.controller.runner.succeeded.connect(results.append)
    page.controller.runner.failed.connect(failures.append)
    page.controller.runner.progress.connect(
        lambda current, total, message: progress_events.append(
            (current, total, message)
        )
    )

    assert page.panel.buttons.run_button.isEnabled()
    with qtbot.waitSignal(page.controller.runner.finished, timeout=timeout):
        page.panel.buttons.run_button.click()

    assert failures == []
    assert len(results) == 1
    assert isinstance(results[0], OperationResult)
    assert page.panel.result.property("resultState") == "success"
    assert not page.controller.is_running()
    return results[0], progress_events


def test_registry_has_a_concrete_screen_for_every_operation(qtbot):
    assert set(OPERATION_PAGE_FACTORIES) == {
        definition.key
        for definition in PAGE_DEFINITIONS
        if definition.key != "home"
    }

    for key, factory in OPERATION_PAGE_FACTORIES.items():
        page = factory(DEFINITIONS[key])
        qtbot.addWidget(page)
        assert isinstance(page, OperationPage)
        assert page.findChild(OperationPanel, "operationPanel") is page.panel
        assert page.input_picker is not None
        assert page.output_picker is not None
        assert not page.panel.buttons.run_button.isEnabled()


def test_merge_screen_runs_in_background(qtbot, tmp_pdf_folder, tmp_path):
    page = _page(qtbot, MergePage, "merge")
    page.input_picker.set_paths(sorted(tmp_pdf_folder.glob("*.pdf")))
    output = tmp_path / "merged-output.pdf"
    page.output_picker.set_path(output)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.output_paths == [output]
    assert result.processed_files == 3
    assert len(progress) == 3


def test_split_screen_runs_in_background(qtbot, tmp_multi_pdf, tmp_path):
    page = _page(qtbot, SplitPage, "split")
    page.input_picker.set_path(tmp_multi_pdf)
    output = tmp_path / "split-output"
    page.output_picker.set_path(output)

    result, progress = _run_successfully(qtbot, page)

    assert len(result.output_paths) == 5
    assert all(path.is_file() for path in result.output_paths)
    assert len(progress) == 5


def test_rotate_screen_runs_in_background(qtbot, tmp_multi_pdf, tmp_path):
    page = _page(qtbot, RotatePage, "rotate")
    page.input_picker.set_path(tmp_multi_pdf)
    output = tmp_path / "rotated-output.pdf"
    page.output_picker.set_path(output)
    page.pages_edit.setText("1,3")
    page.angle_combo.setCurrentText("180")

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.processed_pages == 2
    assert len(progress) == 2


def test_extract_range_screen_runs_in_background(
    qtbot,
    tmp_multi_pdf,
    tmp_path,
):
    page = _page(qtbot, ExtractRangePage, "extract_pages")
    page.input_picker.set_path(tmp_multi_pdf)
    output = tmp_path / "range-output.pdf"
    page.output_picker.set_path(output)
    page.start_spin.setValue(2)
    page.end_spin.setValue(4)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.processed_pages == 3
    assert len(progress) == 3


def test_reorder_screen_runs_in_background(qtbot, tmp_multi_pdf, tmp_path):
    page = _page(qtbot, ReorderPage, "reorder")
    with qtbot.waitSignal(
        page.page_editor.documentLoaded,
        timeout=5_000,
    ):
        page.input_picker.set_path(tmp_multi_pdf)
    output = tmp_path / "reordered-output.pdf"
    page.output_picker.set_path(output)
    page.page_editor.model.remove_rows([1, 3])
    page.page_editor.model.reverse()

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.processed_pages == 3
    assert len(progress) == 3


def test_pdf_to_images_screen_runs_in_background(
    qtbot,
    tmp_multi_pdf,
    tmp_path,
):
    page = _page(qtbot, ToImagesPage, "to_images")
    page.input_picker.set_path(tmp_multi_pdf)
    output = tmp_path / "rendered-output"
    page.output_picker.set_path(output)
    page.dpi_spin.setValue(72)

    result, progress = _run_successfully(qtbot, page)

    assert len(result.output_paths) == 5
    assert all(path.suffix == ".png" for path in result.output_paths)
    assert len(progress) == 5


def test_images_to_pdf_screen_runs_in_background(
    qtbot,
    tmp_image_folder,
    tmp_path,
):
    page = _page(qtbot, ImagesToPdfPage, "images_to_pdf")
    page.input_picker.set_path(tmp_image_folder)
    output = tmp_path / "images-output.pdf"
    page.output_picker.set_path(output)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.processed_pages == 3
    assert len(progress) == 3


def test_extract_images_screen_runs_in_background(
    qtbot,
    pdf_with_image,
    tmp_path,
):
    page = _page(qtbot, ExtractImagesPage, "extract_images")
    page.input_picker.set_path(pdf_with_image)
    output = tmp_path / "extracted-images"
    page.output_picker.set_path(output)

    result, progress = _run_successfully(qtbot, page)

    assert len(result.output_paths) == 1
    assert result.output_paths[0].is_file()
    assert len(progress) == 1


def test_add_images_screen_runs_in_background(
    qtbot,
    tmp_pdf,
    tmp_two_png_images,
    tmp_path,
):
    page = _page(qtbot, AddImagesPage, "add_images")
    page.input_picker.set_path(tmp_pdf)
    page.images_picker.set_paths(tmp_two_png_images)
    output = tmp_path / "with-images-output.pdf"
    page.output_picker.set_path(output)
    page.append_checkbox.setChecked(True)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.metadata["resulting_pages"] == 3
    assert len(progress) == 2


def test_compress_screen_runs_in_background(qtbot, pdf_with_image, tmp_path):
    page = _page(qtbot, CompressPage, "compress")
    page.input_picker.set_path(pdf_with_image)
    output = tmp_path / "compressed-output.pdf"
    page.output_picker.set_path(output)
    page.quality_spin.setValue(45)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.metadata["quality"] == 45
    assert len(progress) == 1


def test_watermark_screen_runs_in_background(qtbot, tmp_pdf, tmp_path):
    page = _page(qtbot, WatermarkPage, "watermark")
    page.input_picker.set_path(tmp_pdf)
    output = tmp_path / "watermark-output.pdf"
    page.output_picker.set_path(output)
    page.text_edit.setText("DRAFT")
    page.color_edit.setText("0.1,0.2,0.3")

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.metadata["text"] == "DRAFT"
    assert len(progress) == 1


def test_encrypt_screen_runs_and_clears_passwords(qtbot, tmp_pdf, tmp_path):
    page = _page(qtbot, EncryptPage, "encrypt")
    page.input_picker.set_path(tmp_pdf)
    output = tmp_path / "encrypted-output.pdf"
    page.output_picker.set_path(output)
    page.user_password_edit.setText("user-secret")
    page.user_password_confirmation_edit.setText("user-secret")
    page.owner_password_edit.setText("owner-secret")
    page.owner_password_confirmation_edit.setText("owner-secret")
    page.allow_copy_checkbox.setChecked(False)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.metadata["allow_copy"] is False
    assert len(progress) == 1
    assert page.user_password_edit.text() == ""
    assert page.user_password_confirmation_edit.text() == ""
    assert page.owner_password_edit.text() == ""
    assert page.owner_password_confirmation_edit.text() == ""


def test_decrypt_screen_runs_and_clears_password(
    qtbot,
    encrypted_pdf,
    tmp_path,
):
    encrypted_path, password = encrypted_pdf
    page = _page(qtbot, DecryptPage, "decrypt")
    page.input_picker.set_path(encrypted_path)
    output = tmp_path / "decrypted-output.pdf"
    page.output_picker.set_path(output)
    page.password_edit.setText(password)

    result, progress = _run_successfully(qtbot, page)

    assert output.is_file()
    assert result.metadata["was_encrypted"] is True
    assert len(progress) == 1
    assert page.password_edit.text() == ""


def test_inline_validation_blocks_invalid_options(qtbot, tmp_pdf, tmp_path):
    rotate_page = _page(qtbot, RotatePage, "rotate")
    rotate_page.input_picker.set_path(tmp_pdf)
    rotate_page.output_picker.set_path(tmp_path / "rotate.pdf")
    rotate_page.pages_edit.setText("1,two")
    assert not rotate_page.panel.buttons.run_button.isEnabled()
    assert "positive integers" in rotate_page.validation_label.text()

    watermark_page = _page(qtbot, WatermarkPage, "watermark")
    watermark_page.input_picker.set_path(tmp_pdf)
    watermark_page.output_picker.set_path(tmp_path / "watermark.pdf")
    watermark_page.text_edit.setText("DRAFT")
    watermark_page.color_edit.setText("2,0,0")
    assert not watermark_page.panel.buttons.run_button.isEnabled()
    assert "between 0.0 and 1.0" in watermark_page.validation_label.text()


def test_expected_core_failure_is_shown_and_form_is_restored(
    qtbot,
    tmp_pdf,
    tmp_path,
):
    page = _page(qtbot, ExtractRangePage, "extract_pages")
    page.input_picker.set_path(tmp_pdf)
    page.output_picker.set_path(tmp_path / "invalid-range.pdf")
    page.end_spin.setValue(2)

    failures = []
    page.controller.runner.failed.connect(failures.append)
    with qtbot.waitSignal(page.controller.runner.finished, timeout=5_000):
        page.panel.buttons.run_button.click()

    assert failures
    assert "Invalid range" in failures[0]
    assert page.panel.result.property("resultState") == "error"
    assert page.form_container.isEnabled()
    assert page.panel.buttons.run_button.isEnabled()


def test_main_shell_locks_navigation_and_handles_cancellation(
    qtbot,
    tmp_path,
):
    settings = QSettings(
        str(tmp_path / "operation-page-settings.ini"),
        QSettings.Format.IniFormat,
    )
    window = MainWindow(settings)
    qtbot.addWidget(window)
    window.navigate_to("merge")
    page = window.page_stack.currentWidget()
    assert isinstance(page, MergePage)

    operation_started = Event()

    def cancellable_operation(*, progress, is_cancelled):
        operation_started.set()
        for current in range(1, 1_000):
            if is_cancelled():
                raise OperationCancelledError()
            progress(current, 1_000, f"Unit {current}")
            sleep(0.001)
        return OperationResult([], "Unexpected completion.")

    with qtbot.waitSignal(page.controller.runner.finished, timeout=5_000):
        assert page.controller.start(cancellable_operation)
        qtbot.waitUntil(operation_started.is_set, timeout=1_000)
        qtbot.waitUntil(lambda: not window.navigation.isEnabled())
        assert not window.open_action.isEnabled()
        qtbot.waitUntil(lambda: not window.progress_bar.isHidden())
        assert page.controller.cancel()

    assert window.navigation.isEnabled()
    assert window.open_action.isEnabled()
    assert window.progress_bar.isHidden()
    assert page.panel.result.property("resultState") == "cancelled"
