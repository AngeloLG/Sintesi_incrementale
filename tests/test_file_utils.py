import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch

# Adjust path to import from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from file_utils import save_text_chunks, aggregate_summaries, save_final_summary

class TestFileUtils(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for file operations."""
        self.test_dir = tempfile.mkdtemp() # Main temporary directory for the test class
        self.base_output_dir = os.path.join(self.test_dir, "output") # General output within test_dir

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_save_text_chunks_success(self):
        """Test successful saving of text chunks."""
        chunks_content = ["Chunk 1 content.", "Chunk 2: second line."]
        original_filename = "test_document.pdf"
        
        saved_paths = save_text_chunks(chunks_content, self.base_output_dir, original_filename)
        
        self.assertEqual(len(saved_paths), 2)
        expected_chunk_dir = os.path.join(self.base_output_dir, "test_document")
        self.assertTrue(os.path.isdir(expected_chunk_dir))

        for i, content in enumerate(chunks_content):
            expected_file_path = os.path.join(expected_chunk_dir, f"test_document_chunk_{i+1:03d}.txt")
            self.assertIn(expected_file_path, saved_paths)
            self.assertTrue(os.path.exists(expected_file_path))
            with open(expected_file_path, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), content)

    def test_save_text_chunks_empty_input(self):
        """Test save_text_chunks with an empty list of chunks."""
        saved_paths = save_text_chunks([], self.base_output_dir, "empty.txt")
        self.assertEqual(saved_paths, [])
        # Ensure output directory for "empty" is not created if no chunks
        self.assertFalse(os.path.exists(os.path.join(self.base_output_dir, "empty")))

    @patch('os.makedirs')
    def test_save_text_chunks_os_error_on_mkdir(self, mock_makedirs):
        """Test OSError propagation when creating directories fails."""
        mock_makedirs.side_effect = OSError("Permission denied")
        with self.assertRaises(OSError):
            save_text_chunks(["chunk1"], self.base_output_dir, "file.txt")

    @patch('builtins.open') # Patch the built-in open function
    def test_save_text_chunks_io_error_on_write(self, mock_open):
        """Test IOError propagation when writing a chunk file fails."""
        mock_open.side_effect = IOError("Disk full")
        # Need to ensure the directory creation part passes if we are only testing write error
        # So, we can pre-create the directory or mock os.path.exists for it
        os.makedirs(os.path.join(self.base_output_dir, "io_error_test"), exist_ok=True)
        
        with self.assertRaises(IOError):
            save_text_chunks(["chunk1 data"], self.base_output_dir, "io_error_test.txt")

    def test_aggregate_summaries_success(self):
        """Test successful aggregation of summary files."""
        original_filename = "aggregated_doc.txt"
        summaries_dir = os.path.join(self.base_output_dir, "aggregated_doc", "summaries")
        os.makedirs(summaries_dir, exist_ok=True)
        aggregated_output_dir = os.path.join(self.base_output_dir, "aggregated_doc") # Dir for the aggregated file

        summary_contents = {
            "s1.txt": "Summary 1 content.",
            "s2.txt": "Content of summary 2."
        }
        summary_paths = []
        for name, content in summary_contents.items():
            p = os.path.join(summaries_dir, name)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(content)
            summary_paths.append(p)

        result_path = aggregate_summaries(summary_paths, aggregated_output_dir, original_filename)
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path))
        expected_filename = os.path.join(aggregated_output_dir, "aggregated_doc_aggregated_summaries.txt")
        self.assertEqual(result_path, expected_filename)

        with open(result_path, 'r', encoding='utf-8') as f_agg:
            aggregated_content = f_agg.read()
        self.assertIn("Summary 1 content.", aggregated_content)
        self.assertIn("Content of summary 2.", aggregated_content)
        self.assertIn("--- INIZIO RIASSUNTO CHUNK 1", aggregated_content)
        self.assertIn("--- FINE RIASSUNTO CHUNK 2", aggregated_content)

    def test_aggregate_summaries_empty_input(self):
        """Test aggregate_summaries with an empty list of paths."""
        result = aggregate_summaries([], self.base_output_dir, "empty_agg.txt")
        self.assertIsNone(result)

    def test_aggregate_summaries_file_not_found(self):
        """Test aggregation when a summary file is not found (should be skipped)."""
        original_filename = "partial_agg.txt"
        summaries_dir = os.path.join(self.base_output_dir, "partial_agg", "summaries")
        aggregated_output_dir = os.path.join(self.base_output_dir, "partial_agg")
        os.makedirs(summaries_dir, exist_ok=True)

        valid_summary_path = os.path.join(summaries_dir, "valid.txt")
        with open(valid_summary_path, 'w', encoding='utf-8') as f:
            f.write("Valid summary.")
        
        paths = [valid_summary_path, os.path.join(summaries_dir, "non_existent.txt")]
        result_path = aggregate_summaries(paths, aggregated_output_dir, original_filename)
        self.assertIsNotNone(result_path)
        with open(result_path, 'r', encoding='utf-8') as f_agg:
            content = f_agg.read()
        self.assertIn("Valid summary.", content)
        self.assertNotIn("non_existent", content.lower()) # Check based on expected separator format

    def test_aggregate_summaries_no_collectible_content(self):
        """Test aggregation when all summary files are empty or unreadable."""
        original_filename = "no_content_agg.txt"
        summaries_dir = os.path.join(self.base_output_dir, "no_content_agg", "summaries")
        aggregated_output_dir = os.path.join(self.base_output_dir, "no_content_agg")
        os.makedirs(summaries_dir, exist_ok=True)
        
        empty_summary_path = os.path.join(summaries_dir, "empty.txt")
        with open(empty_summary_path, 'w', encoding='utf-8') as f: # Create empty file
            f.write("")
        
        result = aggregate_summaries([empty_summary_path, "non_existent.txt"], aggregated_output_dir, original_filename)
        self.assertIsNone(result)

    def test_save_final_summary_success(self):
        """Test successful saving of the final summary."""
        summary_content = "# Sintesi Finale\nQuesto è il riassunto definitivo."
        original_filename = "final_doc.pdf"
        output_final_dir = os.path.join(self.base_output_dir, "final_doc") # e.g. output/final_doc/
        os.makedirs(output_final_dir, exist_ok=True)

        saved_path = save_final_summary(summary_content, output_final_dir, original_filename)
        self.assertIsNotNone(saved_path)
        expected_filepath = os.path.join(output_final_dir, "final_doc_final_summary.md")
        self.assertEqual(saved_path, expected_filepath)
        self.assertTrue(os.path.exists(saved_path))
        with open(saved_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), summary_content)

    def test_save_final_summary_empty_text(self):
        """Test save_final_summary with empty summary text."""
        saved_path = save_final_summary("  ", self.base_output_dir, "empty_final.txt")
        self.assertIsNone(saved_path)

    @patch('builtins.open')
    def test_save_final_summary_io_error(self, mock_open):
        """Test save_final_summary when an IOError occurs."""
        mock_open.side_effect = IOError("Cannot write")
        # Ensure output_dir exists to isolate the open error
        os.makedirs(os.path.join(self.base_output_dir, "final_io_error"), exist_ok=True)
        saved_path = save_final_summary("some content", os.path.join(self.base_output_dir, "final_io_error"), "final_io_error.txt")
        self.assertIsNone(saved_path)

if __name__ == '__main__':
    unittest.main() 