"""Security-focused tests for GUI and interactive CLI password handling."""

import argparse
import logging
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QLabel, QLineEdit

from pdfsilo import cli
from pdfsilo.operations import decrypt, encrypt
from pdfsilo.ui.main_window import PERSISTED_SETTING_KEYS, MainWindow
from pdfsilo.ui.pages import PAGE_DEFINITIONS, DecryptPage, EncryptPage
from pdfsilo.ui.widgets import PasswordField

DEFINITIONS = {definition.key: definition for definition in PAGE_DEFINITIONS}


def test_password_field_masks_toggles_and_clears_securely(qtbot):
    field = PasswordField(
        line_edit_object_name="testPasswordEdit",
        accessible_name="Test password",
    )
    qtbot.addWidget(field)
    field.setText("private-value")

    assert field.line_edit.echoMode() == QLineEdit.EchoMode.Password
    assert not field.is_password_visible()
    assert field.visibility_button.text() == "Show"

    field.visibility_button.click()
    assert field.line_edit.echoMode() == QLineEdit.EchoMode.Normal
    assert field.is_password_visible()
    assert field.visibility_button.text() == "Hide"

    field.clear()
    assert field.text() == ""
    assert field.line_edit.echoMode() == QLineEdit.EchoMode.Password
    assert not field.visibility_button.isChecked()


def test_encrypt_page_explains_roles_and_requires_confirmations(
    qtbot,
    tmp_pdf,
):
    page = EncryptPage(DEFINITIONS["encrypt"])
    qtbot.addWidget(page)
    page.input_picker.set_path(tmp_pdf)
    role_text = " ".join(
        label.text() for label in page.findChildren(QLabel, "passwordRoleLabel")
    )

    assert "opens the PDF" in role_text
    assert "controls permissions" in role_text
    assert page.user_password_edit.echoMode() == QLineEdit.EchoMode.Password
    assert page.owner_password_edit.echoMode() == QLineEdit.EchoMode.Password

    page.user_password_edit.setText("reader-secret")
    assert "confirmation" in page.validation_label.text()
    page.user_password_confirmation_edit.setText("reader-secret")
    assert page.panel.buttons.run_button.isEnabled()

    page.allow_copy_checkbox.setChecked(False)
    assert "distinct owner password is required" in page.validation_label.text()
    page.owner_password_edit.setText("reader-secret")
    page.owner_password_confirmation_edit.setText("reader-secret")
    assert "must differ" in page.validation_label.text()

    page.owner_password_edit.setText("owner-secret")
    assert "confirmation does not match" in page.validation_label.text()
    page.owner_password_confirmation_edit.setText("owner-secret")
    assert page.panel.buttons.run_button.isEnabled()


def test_decrypt_page_uses_explicit_visibility_control(qtbot):
    page = DecryptPage(DEFINITIONS["decrypt"])
    qtbot.addWidget(page)

    assert page.password_edit.echoMode() == QLineEdit.EchoMode.Password
    page.password_field.visibility_button.click()
    assert page.password_edit.echoMode() == QLineEdit.EchoMode.Normal
    page.password_field.clear()
    assert page.password_edit.echoMode() == QLineEdit.EchoMode.Password


def test_passwords_are_not_persisted_in_qsettings(qtbot, tmp_path):
    settings = QSettings(
        str(tmp_path / "password-settings.ini"),
        QSettings.Format.IniFormat,
    )
    window = MainWindow(settings)
    qtbot.addWidget(window)
    window.navigate_to("encrypt")
    page = window.page_stack.currentWidget()
    assert isinstance(page, EncryptPage)
    secrets = (
        "reader-private",
        "owner-private",
    )
    page.user_password_edit.setText(secrets[0])
    page.user_password_confirmation_edit.setText(secrets[0])
    page.owner_password_edit.setText(secrets[1])
    page.owner_password_confirmation_edit.setText(secrets[1])

    window.close()
    settings.sync()
    settings_text = Path(settings.fileName()).read_text(encoding="utf-8")

    assert set(settings.allKeys()) <= PERSISTED_SETTING_KEYS
    assert all(secret not in settings_text for secret in secrets)
    assert "password" not in settings_text.lower()


def test_parser_accepts_omitted_passwords_for_interactive_entry():
    parser = cli.build_parser()

    encrypt_args = parser.parse_args(["encrypt", "input.pdf"])
    decrypt_args = parser.parse_args(["decrypt", "input.pdf"])

    assert encrypt_args.password is None
    assert encrypt_args.owner_password is None
    assert decrypt_args.password is None


def test_interactive_encrypt_prompts_with_confirmation():
    args = argparse.Namespace(
        command="encrypt",
        password=None,
        owner_password=None,
        no_print=False,
        no_copy=True,
        no_edit=False,
    )
    answers = iter(
        [
            "reader-secret",
            "reader-secret",
            "owner-secret",
            "owner-secret",
        ]
    )
    prompts = []

    cli.resolve_interactive_passwords(
        args,
        lambda message: (
            prompts.append(message),
            next(answers),
        )[1],
    )

    assert args.password == "reader-secret"
    assert args.owner_password == "owner-secret"
    assert prompts == [
        "User password: ",
        "Confirm user password: ",
        "Owner password: ",
        "Confirm owner password: ",
    ]


def test_interactive_decrypt_prompts_once_and_explicit_values_do_not_prompt():
    decrypt_args = argparse.Namespace(command="decrypt", password=None)
    cli.resolve_interactive_passwords(
        decrypt_args,
        lambda _message: "unlock-secret",
    )
    assert decrypt_args.password == "unlock-secret"

    explicit_args = argparse.Namespace(
        command="encrypt",
        password="reader-secret",
        owner_password="owner-secret",
        no_print=True,
        no_copy=False,
        no_edit=False,
    )
    cli.resolve_interactive_passwords(
        explicit_args,
        lambda _message: pytest.fail("Explicit secrets must not prompt."),
    )


def test_cli_main_resolves_password_before_dispatch(monkeypatch):
    captured = []
    monkeypatch.setattr(
        cli.sys,
        "argv",
        ["pdfsilo", "decrypt", "document.pdf"],
    )
    monkeypatch.setattr(
        cli.getpass,
        "getpass",
        lambda message: (
            captured.append(("prompt", message)),
            "unlock-secret",
        )[1],
    )
    monkeypatch.setitem(
        cli.COMMAND_MAP,
        "decrypt",
        lambda args: (
            captured.append(("dispatch", args.password)),
            True,
        )[1],
    )
    monkeypatch.setattr(cli, "setup_logging", lambda _level: None)

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 0
    assert captured == [
        ("prompt", "PDF password: "),
        ("dispatch", "unlock-secret"),
    ]


def test_interactive_confirmation_error_never_contains_secret():
    args = argparse.Namespace(
        command="encrypt",
        password=None,
        owner_password=None,
        no_print=False,
        no_copy=False,
        no_edit=False,
    )
    answers = iter(["do-not-expose", "different"])

    with pytest.raises(ValueError) as error:
        cli.resolve_interactive_passwords(
            args,
            lambda _message: next(answers),
        )

    assert "confirmation does not match" in str(error.value)
    assert "do-not-expose" not in str(error.value)


def test_passwords_do_not_appear_in_results_progress_or_logs(
    tmp_pdf,
    encrypted_pdf,
    tmp_path,
    caplog,
):
    secret = "never-log-this-secret"
    progress_messages = []
    result = encrypt.execute(
        tmp_pdf,
        secret,
        output_path=tmp_path / "secure.pdf",
        progress=lambda _current, _total, message: progress_messages.append(message),
    )

    encrypted_path, _correct_password = encrypted_pdf
    with caplog.at_level(logging.ERROR):
        assert (
            decrypt.run(
                str(encrypted_path),
                secret,
                str(tmp_path / "failed-decrypt.pdf"),
            )
            is False
        )

    visible_text = " ".join(
        [result.message, *result.warnings, *progress_messages, caplog.text]
    )
    assert secret not in visible_text
