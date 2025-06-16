class TextExtractionError(Exception):
    """Base class for exceptions in the text extraction module."""
    pass

class UnsupportedFileTypeError(TextExtractionError):
    """Custom exception for unsupported file types."""
    pass

class PdfExtractionError(TextExtractionError):
    """Custom exception for errors during PDF text extraction."""
    pass

class EpubExtractionError(TextExtractionError):
    """Custom exception for errors during EPUB text extraction."""
    pass 