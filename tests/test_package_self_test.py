"""Release validation for the frozen-application self-test workflow."""

import json
from pathlib import Path

from pdfsilo.ui.package_self_test import REPORT_NAME, run_package_self_test


def test_package_self_test_handles_unicode_and_nested_paths(
    tmp_path: Path,
) -> None:
    assert run_package_self_test(tmp_path, page_count=6) == 0
    report = json.loads((tmp_path / REPORT_NAME).read_text(encoding="utf-8"))
    assert report["success"] is True
    assert report["page_count"] == 6
    assert "été" in report["validation_path"]
    assert len(report["outputs"]) == 4
