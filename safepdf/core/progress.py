"""Framework-independent progress and cooperative cancellation contracts."""

from collections.abc import Callable

from safepdf.core.errors import OperationCancelledError

ProgressCallback = Callable[[int, int, str], None]
CancellationCheck = Callable[[], bool]


def check_cancelled(is_cancelled: CancellationCheck | None) -> None:
    """Raise the expected cancellation error when the caller requests it."""
    if is_cancelled is not None and is_cancelled():
        raise OperationCancelledError("Operation cancelled.")


def report_progress(
    progress: ProgressCallback | None,
    current: int,
    total: int,
    message: str,
) -> None:
    """Emit progress when a callback was supplied by the presentation layer."""
    if progress is not None:
        progress(current, total, message)
