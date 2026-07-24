"""Operation pages for the SafePDF desktop interface."""

from safepdf.ui.pages.home_page import HomePage
from safepdf.ui.pages.placeholder_page import OperationPlaceholderPage
from safepdf.ui.pages.registry import (
    PAGE_DEFINITIONS,
    PAGE_INDEX_BY_KEY,
    PageDefinition,
)

__all__ = [
    "HomePage",
    "OperationPlaceholderPage",
    "PAGE_DEFINITIONS",
    "PAGE_INDEX_BY_KEY",
    "PageDefinition",
]
