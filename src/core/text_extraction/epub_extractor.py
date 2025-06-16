import logging
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup # Required for parsing HTML content within EPUB
from .base_extractor import TextExtractor
from .exceptions import EpubExtractionError # Import from new exceptions file

logger = logging.getLogger(__name__)

class EpubExtractor(TextExtractor):
    """Extracts text from an .epub file using EbookLib and BeautifulSoup."""

    def extract(self, file_path: str) -> str:
        """
        Reads and returns the text content of an .epub file.
        It concatenates the text content from all HTML items in the EPUB spine.

        Args:
            file_path (str): The path to the .epub file.

        Returns:
            str: The concatenated text content from the EPUB.
                 Returns an empty string if no text can be extracted.

        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: For errors during EPUB processing or other unexpected errors.
        """
        logger.info(f"Inizio estrazione testo dal file EPUB: {file_path}")
        try:
            book = epub.read_epub(file_path)
            text_parts = []

            # Iterate through items in the spine (main content flow)
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                try:
                    content = item.get_content()
                    # Use BeautifulSoup to parse HTML and extract text
                    soup = BeautifulSoup(content, 'html.parser')
                    # Get all text, strip leading/trailing whitespace from each text segment,
                    # and then join them with a space. Also remove excessive newlines.
                    item_text = ' '.join(s.strip() for s in soup.stripped_strings)
                    if item_text:
                        text_parts.append(item_text)
                except Exception as e_item:
                    logger.warning(f"Errore durante l'elaborazione dell'item {item.get_name()} nel file EPUB {file_path}: {e_item}", exc_info=True)
            
            full_text = "\n\n".join(text_parts) # Join chapters/sections with double newline for paragraph separation
            if not full_text.strip():
                logger.warning(f"Nessun testo estraibile trovato nel file EPUB: {file_path} (potrebbe essere vuoto o malformato).")
            else:
                logger.info(f"Estrazione testo da {file_path} completata. Caratteri estratti: {len(full_text)}")
            return full_text
        except FileNotFoundError:
            logger.error(f"File non trovato: {file_path}")
            raise
        except ebooklib.epub.EpubException as e: # More specific catch
            logger.error(f"Errore EbookLib durante l'elaborazione del file EPUB {file_path}: {e}", exc_info=True) # Added exc_info
            raise EpubExtractionError(f"Errore durante l'elaborazione del file EPUB (EbookLib): {file_path}. Dettagli: {e}")
        except Exception as e:
            logger.error(f"Errore imprevisto durante l'elaborazione del file EPUB {file_path}: {e}", exc_info=True)
            raise EpubExtractionError(f"Impossibile elaborare il file EPUB {file_path}. Dettagli: {e}") 