"""
Core functionality for text processing and synthesis.
"""

from .text_extraction import get_text_extractor
from .text_processing import chunk_text_by_word_limit, count_words
from .llm_interaction import OpenAIClient

__all__ = [
    'get_text_extractor',
    'chunk_text_by_word_limit',
    'count_words',
    'OpenAIClient'
] 