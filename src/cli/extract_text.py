import argparse
import logging
import os
import sys

from ..core.text_extraction import get_text_extractor, UnsupportedFileTypeError, TextExtractionError

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the output directory name (same as the synthesis tool)
OUTPUT_DIRECTORY_NAME = "output"

def extract_text(input_file_path: str) -> str:
    """
    Estrae il testo da un file (PDF, EPUB, TXT) e lo salva nella directory output.
    
    Args:
        input_file_path (str): Percorso del file di input per l'estrazione del testo.
        
    Returns:
        str: Il percorso del file di output dove è stato salvato il testo estratto.
        
    Raises:
        UnsupportedFileTypeError: Se il tipo di file non è supportato.
        TextExtractionError: Se si verifica un errore durante l'estrazione.
        FileNotFoundError: Se il file di input non esiste.
        IOError: Se si verifica un errore durante la scrittura del file di output.
    """
    # Determine the absolute path for the output directory at the project root
    output_dir_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), OUTPUT_DIRECTORY_NAME)

    # Create the output directory if it doesn't exist
    try:
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)
            logger.info(f"Created output directory: {output_dir_path}")
    except OSError as e:
        logger.error(f"Error creating output directory {output_dir_path}: {e}")
        raise IOError(f"Could not create output directory: {e}")

    if not os.path.exists(input_file_path):
        logger.error(f"Error: File not found at '{input_file_path}'")
        raise FileNotFoundError(f"File not found at '{input_file_path}'")

    try:
        logger.info(f"Attempting to extract text from: {input_file_path}")
        extractor = get_text_extractor(input_file_path)
        extracted_text = extractor.extract(input_file_path)

        # --- SEZIONE PER LA PULIZIA GUTENBERG (replicata da main.py) ---
        cleanup_phrase = "*** END OF THE PROJECT GUTENBERG EBOOK"
        phrase_index = extracted_text.find(cleanup_phrase)

        if phrase_index != -1:
            logger.info(f"Gutenberg cleanup: Found end phrase at index {phrase_index}.")
            original_length_before_cleanup = len(extracted_text)
            extracted_text = extracted_text[:phrase_index]
            logger.info(f"Gutenberg cleanup: Text truncated. New length: {len(extracted_text)} (removed {original_length_before_cleanup - len(extracted_text)} chars).")
        else:
            logger.info("Gutenberg cleanup: End phrase not found. Text not truncated.")
        # --- FINE SEZIONE PULIZIA ---
        
        if extracted_text.strip():
            logger.info(f"Text extracted successfully from {input_file_path}.")
            
            # Create a directory for this book in the output directory
            base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
            book_dir = os.path.join(output_dir_path, base_filename)
            
            try:
                if not os.path.exists(book_dir):
                    os.makedirs(book_dir)
                    logger.info(f"Created book directory: {book_dir}")
            except OSError as e:
                logger.error(f"Error creating book directory {book_dir}: {e}")
                raise IOError(f"Could not create book directory: {e}")
            
            # Save the extracted text in the book directory
            output_filename = f"{base_filename}.txt"
            output_file_path = os.path.join(book_dir, output_filename)

            # Save the extracted text to the file
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            logger.info(f"Extracted text saved to: {output_file_path}")
            return output_file_path
        else:
            logger.warning(f"No text was extracted from {input_file_path}, or the extracted text is empty. No file will be saved.")
            return None
            
    except UnsupportedFileTypeError as e:
        logger.error(f"Unsupported file type for '{input_file_path}': {e}")
        raise
    except TextExtractionError as e:
        logger.error(f"Text extraction error for '{input_file_path}': {e}")
        raise
    except FileNotFoundError:
        logger.error(f"File not found during extraction process (should have been caught earlier): {input_file_path}")
        raise
    except IOError as e:
        logger.error(f"Error writing extracted text to file: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing '{input_file_path}': {e}", exc_info=True)
        raise

def main():
    """Entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Extracts text from a given file (PDF, EPUB, TXT) and saves it.")
    parser.add_argument("input_file", help="Path to the input file for text extraction.")
    
    args = parser.parse_args()
    input_file_path = args.input_file

    try:
        output_path = extract_text(input_file_path)
        if output_path:
            print(f"Extracted text saved to: {output_path}")
        else:
            print(f"No text extracted from {input_file_path}. Nothing to save.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 