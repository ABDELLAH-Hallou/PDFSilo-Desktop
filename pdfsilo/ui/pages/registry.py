"""Stable navigation definitions for PDFSilo operation pages."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageDefinition:
    """Describe one entry in the main navigation and content stack."""

    key: str
    label: str
    title: str
    description: str


PAGE_DEFINITIONS = (
    PageDefinition(
        "home",
        "Home",
        "Welcome to PDFSilo",
        "Choose an operation from the sidebar to work with a PDF locally.",
    ),
    PageDefinition(
        "merge", "Merge", "Merge PDFs", "Combine PDF files into one document."
    ),
    PageDefinition("split", "Split", "Split PDF", "Save each page as a separate PDF."),
    PageDefinition(
        "rotate", "Rotate", "Rotate Pages", "Rotate all or selected PDF pages."
    ),
    PageDefinition(
        "extract_pages",
        "Extract Pages",
        "Extract Pages",
        "Copy a selected page range into a new PDF.",
    ),
    PageDefinition(
        "compress",
        "Compress",
        "Compress PDF",
        "Reduce the size of a PDF and its embedded images.",
    ),
    PageDefinition(
        "encrypt",
        "Encrypt",
        "Encrypt PDF",
        "Protect a PDF with a password and permissions.",
    ),
    PageDefinition(
        "decrypt",
        "Decrypt",
        "Decrypt PDF",
        "Remove password protection from a PDF you own.",
    ),
    PageDefinition(
        "watermark",
        "Watermark",
        "Add Watermark",
        "Stamp text across every page of a PDF.",
    ),
    PageDefinition(
        "extract_images",
        "Extract Images",
        "Extract Images",
        "Save embedded PDF images as PNG or JPEG files.",
    ),
    PageDefinition(
        "to_images",
        "PDF to Images",
        "Render PDF Pages",
        "Render PDF pages as PNG or JPEG images.",
    ),
    PageDefinition(
        "reorder",
        "Reorder",
        "Reorder Pages",
        "Rearrange, duplicate, or omit PDF pages.",
    ),
    PageDefinition(
        "add_images",
        "Add Images",
        "Add Images",
        "Place images onto existing or newly appended PDF pages.",
    ),
    PageDefinition(
        "images_to_pdf",
        "Images to PDF",
        "Images to PDF",
        "Build a PDF from a folder of image files.",
    ),
)

PAGE_INDEX_BY_KEY = {
    definition.key: index for index, definition in enumerate(PAGE_DEFINITIONS)
}
