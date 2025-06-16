# This file makes src/text_processing a Python package

from .text_chunker import chunk_text_by_word_limit, count_words

__all__ = ['chunk_text_by_word_limit', 'count_words'] 