"""Typed errors raised by PDFSilo's framework-independent operation layer."""


class PdfSiloError(Exception):
    """Base class for expected PDFSilo errors."""


class InvalidInputError(PdfSiloError):
    """An input path, option, page selection, or geometry is invalid."""


class PdfPasswordError(PdfSiloError):
    """A PDF password is missing, invalid, or unsafe for the requested action."""


class OutputWriteError(PdfSiloError):
    """An operation could not publish its requested output."""


class PdfProcessingError(PdfSiloError):
    """PyMuPDF could not read or transform the supplied document."""


class OperationCancelledError(PdfSiloError):
    """The caller cancelled an operation before it completed."""

