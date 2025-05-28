import unittest
import os
import sys
import tempfile
import shutil
import subprocess

# Adjust path to import from src (for direct imports if needed, though CLI is preferred)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

# For potential direct imports (though CLI testing is primary here)
# from main import cli # This might be tricky due to click context

# Path to the main script entry point (as a module)
MAIN_MODULE_PATH = "src.main" # Changed from MAIN_SCRIPT_PATH

class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.input_files_dir = os.path.join(self.test_dir, "input_files")
        self.output_dir = os.path.join(project_root, "output") # App default output dir
        os.makedirs(self.input_files_dir, exist_ok=True)

        # Clean up output directory from previous runs if it exists to ensure clean state
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        # os.makedirs(self.output_dir) # main.py should create this if needed

        # Create a sample TXT file
        self.sample_txt_filename = "sample_book.txt"
        self.sample_txt_path = os.path.join(self.input_files_dir, self.sample_txt_filename)
        with open(self.sample_txt_path, "w", encoding="utf-8") as f:
            f.write("Questo è il primo paragrafo del libro di esempio.\n\n")
            f.write("Questo è il secondo paragrafo, un po' più lungo per poter essere, forse, un chunk a sé stante.\n\n")
            f.write("Terzo e ultimo paragrafo.")
        
        self.mock_api_key = "fake_integration_test_key"

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        # Optionally, clean up the main output directory again if tests are independent
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_full_flow_txt_file_mocked_llm(self):
        """Test the full processing flow with a TXT file and mocked LLM responses via ENV VARS."""
        
        single_chunk_summary = "Riassunto dell'intero testo come un unico chunk."
        final_summary_from_single = "Sintesi finale basata sull'unico chunk."

        cmd = [
            sys.executable, # Path to python interpreter
            "-m",           # Run as module
            MAIN_MODULE_PATH,
            "--api-key", self.mock_api_key,
            "process",
            self.sample_txt_path
        ]
        
        current_env = os.environ.copy()
        current_env['PYTHONUTF8'] = '1'
        # Set environment variables for mocking LLM in the subprocess
        current_env['TEST_MOCK_LLM_CHUNK_SUMMARY'] = single_chunk_summary
        current_env['TEST_MOCK_LLM_FINAL_SUMMARY'] = final_summary_from_single
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=current_env)

        # Print stdout/stderr for debugging if the test fails
        if result.returncode != 0:
            print("Integration Test Failed. Subprocess stdout:")
            print(result.stdout)
            print("Subprocess stderr:")
            print(result.stderr)
        
        self.assertEqual(result.returncode, 0, "CLI script execution failed.")

        # Verify outputs
        filename_stem = "sample_book"
        expected_output_subdir = os.path.join(self.output_dir, filename_stem)
        self.assertTrue(os.path.isdir(expected_output_subdir), f"Output subdirectory {expected_output_subdir} not found.")

        # 1. Check chunk file (assuming 1 chunk with default settings)
        expected_chunk_file = os.path.join(expected_output_subdir, f"{filename_stem}_chunk_001.txt")
        self.assertTrue(os.path.exists(expected_chunk_file), f"Chunk file {expected_chunk_file} not found.")
        with open(self.sample_txt_path, 'r', encoding='utf-8') as f_orig:
             original_content = f_orig.read()
        with open(expected_chunk_file, 'r', encoding='utf-8') as f_chunk:
            self.assertEqual(f_chunk.read(), original_content, "Chunk content mismatch")

        # 2. Check chunk summary file
        summaries_dir = os.path.join(expected_output_subdir, "summaries")
        self.assertTrue(os.path.isdir(summaries_dir), "Summaries directory not found.")
        expected_chunk_summary_file = os.path.join(summaries_dir, f"{filename_stem}_chunk_001_summary.txt")
        self.assertTrue(os.path.exists(expected_chunk_summary_file), f"Chunk summary file {expected_chunk_summary_file} not found.")
        with open(expected_chunk_summary_file, 'r', encoding='utf-8') as f_sum:
            self.assertEqual(f_sum.read(), single_chunk_summary, "Chunk summary content mismatch")

        # 3. Check aggregated summaries file
        expected_aggregated_file = os.path.join(expected_output_subdir, f"{filename_stem}_aggregated_summaries.txt")
        self.assertTrue(os.path.exists(expected_aggregated_file), f"Aggregated summaries file {expected_aggregated_file} not found.")
        with open(expected_aggregated_file, 'r', encoding='utf-8') as f_agg:
            aggregated_content = f_agg.read()
            self.assertIn(single_chunk_summary, aggregated_content, "Aggregated summary content error")
            # The header for aggregated summaries might need to be adapted if it includes full path
            self.assertIn(f"--- INIZIO RIASSUNTO CHUNK 1", aggregated_content) # Simplified check for header

        # 4. Check final summary markdown file
        expected_final_summary_file = os.path.join(expected_output_subdir, f"{filename_stem}_final_summary.md")
        self.assertTrue(os.path.exists(expected_final_summary_file), f"Final summary file {expected_final_summary_file} not found.")
        with open(expected_final_summary_file, 'r', encoding='utf-8') as f_final:
            self.assertEqual(f_final.read(), final_summary_from_single, "Final summary content mismatch")
        
        # We can no longer easily check mock_summarize_text.call_count this way
        # self.assertEqual(mock_summarize_text.call_count, 2, "summarize_text was not called the expected number of times.")

if __name__ == '__main__':
    unittest.main() 