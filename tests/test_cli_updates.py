"""CLI parity tests for explicit update checks."""

from pdfsilo.cli import _check_for_cli_update, build_parser
from pdfsilo.updater import UpdateCheckFailedError, UpdateInfo


def test_update_command_parses() -> None:
    args = build_parser().parse_args(["update", "--check"])
    assert args.command == "update"
    assert args.check is True


def test_cli_reports_newer_version(monkeypatch, capsys) -> None:
    info = UpdateInfo(
        version="0.2.0",
        download_url="https://github.com/example/update.exe",
        checksum_sha256="a" * 64,
        signature_url=None,
        release_notes_url="https://github.com/example/releases/v0.2.0",
        published_at="",
    )
    monkeypatch.setattr("pdfsilo.cli.check_for_update", lambda: info)
    assert _check_for_cli_update(object())
    output = capsys.readouterr().out
    assert "0.2.0 is available" in output
    assert "Release notes:" in output


def test_cli_reports_check_failure(monkeypatch, capsys) -> None:
    def fail():
        raise UpdateCheckFailedError("offline")

    monkeypatch.setattr("pdfsilo.cli.check_for_update", fail)
    assert not _check_for_cli_update(object())
    assert "offline" in capsys.readouterr().err
