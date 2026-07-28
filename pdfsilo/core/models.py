"""Structured values returned by successful PDFSilo operations."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class OperationResult:
    """Describe the outputs and useful metrics from a successful operation."""

    output_paths: list[Path]
    message: str
    warnings: list[str] = field(default_factory=list)
    source_paths: list[Path] = field(default_factory=list)
    processed_pages: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    original_size: int | None = None
    resulting_size: int | None = None
    elapsed_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
