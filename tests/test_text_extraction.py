import unittest
import os
import tempfile
from unittest.mock import patch
import ebooklib

# Adjust the path to import from the src directory
import sys
# Get the absolute path to the project's root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) 
# Add the src directory to Python's path
sys.path.insert(0, os.path.join(project_root, 'src'))

from text_extraction import get_text_extractor
from text_extraction.exceptions import UnsupportedFileTypeError, PdfExtractionError, EpubExtractionError
from text_extraction.base_extractor import TextExtractor

# Mock an API key for tests if necessary, or ensure tests don't rely on it for this stage
# os.environ['OPENAI_API_KEY'] = 'test_key' 

class TestTextExtraction(unittest.TestCase):

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a dummy TXT file
        self.txt_file_path = os.path.join(self.temp_dir.name, "test.txt")
        with open(self.txt_file_path, "w", encoding="utf-8") as f:
            f.write("Questo è un semplice file di testo.")

        # Note: For PDF and EPUB, creating valid dummy files programmatically is complex.
        # These tests will primarily focus on the factory and TXT for now.
        # For full PDF/EPUB testing, you would typically use small, actual sample files
        # included in your test assets.
        self.pdf_file_path = os.path.join(self.temp_dir.name, "test.pdf")
        with open(self.pdf_file_path, "w") as f: # Create an empty pdf file for factory testing
            f.write("") 

        self.epub_file_path = os.path.join(self.temp_dir.name, "test.epub")
        with open(self.epub_file_path, "w") as f: # Create an empty epub file for factory testing
            f.write("")
        
        self.unsupported_file_path = os.path.join(self.temp_dir.name, "test.doc")
        with open(self.unsupported_file_path, "w") as f:
            f.write("Questo non è supportato.")

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_get_txt_extractor(self):
        """Test if the factory returns TxtExtractor for .txt files."""
        extractor = get_text_extractor(self.txt_file_path)
        self.assertIsInstance(extractor, TextExtractor) # Check against base class
        # More specifically, you might want to check the concrete type if not too rigid
        # from text_extraction.txt_extractor import TxtExtractor
        # self.assertIsInstance(extractor, TxtExtractor)
        extracted_text = extractor.extract(self.txt_file_path)
        self.assertEqual(extracted_text, "Questo è un semplice file di testo.")

    def test_get_pdf_extractor_factory(self):
        """Test if the factory returns PdfExtractor for .pdf files (factory part only)."""
        # This test only checks if the factory function dispatches correctly.
        # Actual PDF content extraction is harder to test without a real PDF library and file.
        from text_extraction.pdf_extractor import PdfExtractor
        extractor = get_text_extractor(self.pdf_file_path)
        self.assertIsInstance(extractor, PdfExtractor)

    def test_get_epub_extractor_factory(self):
        """Test if the factory returns EpubExtractor for .epub files (factory part only)."""
        from text_extraction.epub_extractor import EpubExtractor
        extractor = get_text_extractor(self.epub_file_path)
        self.assertIsInstance(extractor, EpubExtractor)

    def test_unsupported_file_type(self):
        """Test if UnsupportedFileTypeError is raised for unsupported file types."""
        with self.assertRaises(UnsupportedFileTypeError):
            get_text_extractor(self.unsupported_file_path)

    def test_file_not_found(self):
        """Test if FileNotFoundError is raised for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            get_text_extractor("non_existent_file.txt")

    def test_txt_extraction_content(self):
        """Test content extraction from a TXT file."""
        extractor = get_text_extractor(self.txt_file_path)
        content = extractor.extract(self.txt_file_path)
        self.assertEqual(content, "Questo è un semplice file di testo.")

    @patch('text_extraction.pdf_extractor.PdfReader')
    def test_pdf_extraction_error(self, mock_pdf_reader):
        """Test if PdfExtractionError is raised for PDF processing errors."""
        # Configure the mock PdfReader to raise an error when its methods are called
        # For instance, when trying to access reader.pages or page.extract_text()
        # A simple way is to make the instance itself raise an error or a problematic attribute.
        mock_pdf_reader.side_effect = Exception("Simulated PyPDF2 error")
        
        extractor = get_text_extractor(self.pdf_file_path) # This should give PdfExtractor
        with self.assertRaises(PdfExtractionError) as cm:
            extractor.extract(self.pdf_file_path)
        self.assertIn("Simulated PyPDF2 error", str(cm.exception))
        self.assertIn("Impossibile elaborare il file PDF", str(cm.exception))

    @patch('text_extraction.epub_extractor.epub.read_epub')
    def test_epub_extraction_error(self, mock_read_epub):
        """Test if EpubExtractionError is raised for EPUB processing errors."""
        # Configure the mock read_epub to raise an error
        mock_read_epub.side_effect = ebooklib.epub.EpubException("Simulated EbookLib error", msg="Simulated EbookLib error")
        
        extractor = get_text_extractor(self.epub_file_path) # This should give EpubExtractor
        with self.assertRaises(EpubExtractionError) as cm:
            extractor.extract(self.epub_file_path)
        self.assertIn("Simulated EbookLib error", str(cm.exception))
        self.assertIn("Errore durante l'elaborazione del file EPUB (EbookLib)", str(cm.exception))

    # Example of how you might structure a simple run script (not a formal test)
    # This would typically be in a separate `examples` or `scripts` directory

def run_extraction_example():
    print("Esecuzione esempio di estrazione testo...")
    # Create dummy files for the example
    temp_dir_for_example = tempfile.TemporaryDirectory()
    sample_txt_path = os.path.join(temp_dir_for_example.name, "esempio.txt")
    with open(sample_txt_path, "w", encoding="utf-8") as f:
        f.write("Ciao mondo! Questo è un file di testo di esempio.")
    
    print(f"Creato file TXT di esempio: {sample_txt_path}")

    # (Per PDF ed EPUB, avresti bisogno di veri file di esempio)
    # sample_pdf_path = "path/to/your/sample.pdf" 
    # sample_epub_path = "path/to/your/sample.epub"

    files_to_test = [sample_txt_path]
    # if os.path.exists(sample_pdf_path): files_to_test.append(sample_pdf_path)
    # if os.path.exists(sample_epub_path): files_to_test.append(sample_epub_path)

    for file_path in files_to_test:
        print(f"\n--- Elaborazione file: {file_path} ---")
        try:
            extractor = get_text_extractor(file_path)
            text = extractor.extract(file_path)
            print(f"Testo estratto (primi 100 caratteri):\n{text[:100]}...")
            print(f"Lunghezza totale del testo estratto: {len(text)} caratteri")
        except UnsupportedFileTypeError as e:
            print(f"Errore: {e}")
        except FileNotFoundError as e:
            print(f"Errore: {e}")
        except Exception as e:
            print(f"Errore imprevisto: {e}")
        finally:
            print("-------------------------------------")
    
    temp_dir_for_example.cleanup()
    print("Esempio di estrazione completato.")

if __name__ == '__main__':
    # Per eseguire i test unittest:
    # Naviga nella directory principale del progetto `tool_sintesi_incrementale`
    # Esegui: python -m unittest tests.test_text_extraction
    print("Per eseguire i test, naviga nella root del progetto e usa: python -m unittest tests.test_text_extraction")
    print("Per eseguire l'esempio, chiama la funzione run_extraction_example() da uno script o interprete Python.")
    
    # Puoi decommentare la linea seguente per eseguire l'esempio direttamente quando questo file è eseguito
    # run_extraction_example() 