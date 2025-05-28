import logging
from PyPDF2 import PdfReader
from .base_extractor import TextExtractor
from .exceptions import PdfExtractionError

logger = logging.getLogger(__name__)

class PdfExtractor(TextExtractor):
    """Extracts text from a .pdf file using PyPDF2."""

    def extract(self, file_path: str) -> str:
        """
        Reads and returns the text content of a .pdf file.

        Args:
            file_path (str): The path to the .pdf file.

        Returns:
            str: The concatenated text content of all pages.
                 Returns an empty string if no text can be extracted or if the PDF is empty.

        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: For errors during PDF processing by PyPDF2 or other unexpected errors.
        """
        logger.info(f"Inizio estrazione testo dal file PDF: {file_path}")
        try:
            reader = PdfReader(file_path)
            text = ""
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        logger.warning(f"Nessun testo trovato nella pagina {i+1} del file PDF: {file_path}")
                except Exception as e_page:
                    # Log the error for the specific page but try to continue if possible
                    logger.error(f"Errore durante l'estrazione del testo dalla pagina {i+1} del file PDF {file_path}: {e_page}", exc_info=True)
                    # Potremmo voler aggiungere un testo placeholder o semplicemente saltare la pagina
            
            if not text.strip():
                logger.warning(f"Nessun testo è stato estratto dal PDF: {file_path} (potrebbe essere vuoto o basato su immagini senza OCR).")
                # Non solleviamo un errore qui, ma restituiamo una stringa vuota.
                # La gestione del testo vuoto avverrà a monte.
            return text
        except Exception as e:
            logger.error(f"Errore imprevisto durante l'elaborazione del file PDF {file_path}: {e}", exc_info=True)
            raise PdfExtractionError(f"Impossibile elaborare il file PDF {file_path}. Dettagli: {e}") 