import os
from .base_extractor import TextExtractor
from .txt_extractor import TxtExtractor
from .pdf_extractor import PdfExtractor
from .epub_extractor import EpubExtractor
from .exceptions import UnsupportedFileTypeError, PdfExtractionError, EpubExtractionError

def get_text_extractor(file_path):
    """
    Factory function to get the appropriate text extractor based on file extension.

    Args:
        file_path (str): The path to the input file.

    Returns:
        An instance of a TextExtractor subclass (TxtExtractor, PdfExtractor, EpubExtractor).

    Raises:
        UnsupportedFileTypeError: If the file extension is not supported.
        FileNotFoundError: If the file_path does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File non trovato: {file_path}")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.txt':
        return TxtExtractor()
    elif ext == '.pdf':
        return PdfExtractor()
    elif ext == '.epub':
        return EpubExtractor()
    else:
        raise UnsupportedFileTypeError(f"Tipo di file non supportato: {ext} per il file {file_path}")

__all__ = [
    'TextExtractor', 
    'TxtExtractor', 
    'PdfExtractor', 
    'EpubExtractor', 
    'get_text_extractor', 
    'UnsupportedFileTypeError', 
    'PdfExtractionError', 
    'EpubExtractionError'
] 