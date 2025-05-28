# src/__init__.py

# This file makes 'src' a package.
# You can leave it empty or use it to make submodules/symbols available.

# For example, if you want to allow `from src import file_utils`
# and file_utils.py is in src/ , you might not need to do anything here.
# If file_utils contained a class MyUtil, to make it `from src import MyUtil`,
# you would do: from .file_utils import MyUtil

# For now, we will just ensure the package structure works and specific modules
# are imported where needed (e.g., `from .file_utils import ...` in main.py) 

from .logging_config import setup_logging
from .text_extraction import get_text_extractor, UnsupportedFileTypeError, TextExtractor
from .text_processing import chunk_text_by_word_limit, count_words
from .llm_interaction import OpenAIClient, CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, FINAL_SUMMARY_PROMPT_INSTRUCTIONS
from .file_utils import save_text_chunks, aggregate_summaries, save_final_summary

__all__ = [
    "setup_logging",
    "get_text_extractor",
    "UnsupportedFileTypeError",
    "TextExtractor",
    "chunk_text_by_word_limit",
    "count_words",
    "OpenAIClient",
    "CHUNK_SUMMARY_PROMPT_INSTRUCTIONS",
    "FINAL_SUMMARY_PROMPT_INSTRUCTIONS",
    "save_text_chunks",
    "aggregate_summaries",
    "save_final_summary"
] 