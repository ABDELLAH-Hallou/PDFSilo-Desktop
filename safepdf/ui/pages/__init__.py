"""Operation pages for the SafePDF desktop interface."""

from safepdf.ui.pages.base_operation_page import OperationPage
from safepdf.ui.pages.document_pages import (
    ExtractRangePage,
    MergePage,
    RotatePage,
    SplitPage,
)
from safepdf.ui.pages.home_page import HomePage
from safepdf.ui.pages.image_pages import (
    AddImagesPage,
    ExtractImagesPage,
    ImagesToPdfPage,
    ReorderPage,
    ToImagesPage,
)
from safepdf.ui.pages.placeholder_page import OperationPlaceholderPage
from safepdf.ui.pages.registry import (
    PAGE_DEFINITIONS,
    PAGE_INDEX_BY_KEY,
    PageDefinition,
)
from safepdf.ui.pages.transform_pages import (
    CompressPage,
    DecryptPage,
    EncryptPage,
    WatermarkPage,
)

OPERATION_PAGE_FACTORIES = {
    "merge": MergePage,
    "split": SplitPage,
    "rotate": RotatePage,
    "extract_pages": ExtractRangePage,
    "compress": CompressPage,
    "encrypt": EncryptPage,
    "decrypt": DecryptPage,
    "watermark": WatermarkPage,
    "extract_images": ExtractImagesPage,
    "to_images": ToImagesPage,
    "reorder": ReorderPage,
    "add_images": AddImagesPage,
    "images_to_pdf": ImagesToPdfPage,
}

__all__ = [
    "AddImagesPage",
    "CompressPage",
    "DecryptPage",
    "EncryptPage",
    "ExtractImagesPage",
    "ExtractRangePage",
    "HomePage",
    "ImagesToPdfPage",
    "MergePage",
    "OPERATION_PAGE_FACTORIES",
    "OperationPage",
    "OperationPlaceholderPage",
    "PAGE_DEFINITIONS",
    "PAGE_INDEX_BY_KEY",
    "PageDefinition",
    "ReorderPage",
    "RotatePage",
    "SplitPage",
    "ToImagesPage",
    "WatermarkPage",
]
