"""
CLI module for the text synthesis and extraction tools.
"""

from .main import cli
from .extract_text import extract_text

__all__ = ['cli', 'extract_text'] 