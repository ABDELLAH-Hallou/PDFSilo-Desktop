"""Typed errors raised by SafePDF's framework-independent operation layer."""


class SafePdfError(Exception):
    """Base class for expected SafePDF errors."""


class InvalidInputError(SafePdfError):
    """An input path, option, page selection, or geometry is invalid."""


class PdfPasswordError(SafePdfError):
    """A PDF password is missing, invalid, or unsafe for the requested action."""


class OutputWriteError(SafePdfError):
    """An operation could not publish its requested output."""


class PdfProcessingError(SafePdfError):
    """PyMuPDF could not read or transform the supplied document."""


class OperationCancelledError(SafePdfError):
    """The caller cancelled an operation before it completed."""

