# src/llm_interaction/__init__.py

from .llm_client import OpenAIClient, CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, FINAL_SUMMARY_PROMPT_INSTRUCTIONS

__all__ = [
    "OpenAIClient",
    "CHUNK_SUMMARY_PROMPT_INSTRUCTIONS",
    "FINAL_SUMMARY_PROMPT_INSTRUCTIONS"
] 