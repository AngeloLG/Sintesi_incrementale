import logging
from .base_extractor import TextExtractor

logger = logging.getLogger(__name__)

class TxtExtractor(TextExtractor):
    """Extracts text from a plain .txt file."""

    def extract(self, file_path: str) -> str:
        """
        Reads and returns the content of a .txt file.

        Args:
            file_path (str): The path to the .txt file.

        Returns:
            str: The content of the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If an error occurs during file reading.
        """
        logger.info(f"Inizio estrazione testo dal file TXT: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Estrazione testo da {file_path} completata con successo. Caratteri estratti: {len(content)}")
            return content
        except FileNotFoundError:
            logger.error(f"File non trovato: {file_path}")
            raise
        except IOError as e:
            logger.error(f"Errore I/O durante la lettura del file {file_path}: {e}")
            raise IOError(f"Impossibile leggere il file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Errore imprevisto durante l'estrazione da {file_path}: {e}")
            raise Exception(f"Errore imprevisto durante l'estrazione da {file_path}: {e}") 