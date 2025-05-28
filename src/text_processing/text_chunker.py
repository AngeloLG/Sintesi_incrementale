import logging
import re
from typing import List

logger = logging.getLogger(__name__)

def count_words(text: str) -> int:
    """Counts words in a text. A word is defined as a sequence of non-whitespace characters."""
    if not text:
        return 0
    return len(text.split())

def _split_long_paragraph(paragraph_text: str, word_limit: int) -> List[str]:
    """Splits a paragraph that exceeds the word limit, first by sentences, then by words."""
    sub_chunks = []
    logger.debug(f"Tentativo di divisione per frasi del paragrafo lungo.")
    # A simple regex for sentence splitting (can be improved for more complex cases)
    # Handles periods, question marks, and exclamation marks as sentence terminators,
    # followed by whitespace. Avoids splitting on e.g. Mr. Smith.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=[\.\?\!])\s+', paragraph_text)
    
    current_sentence_sub_chunk_parts = []
    current_sentence_sub_chunk_words = 0

    for sentence in sentences:
        if not sentence.strip(): # Skip empty sentences that might result from splitting
            continue
        sentence_word_count = count_words(sentence)

        if current_sentence_sub_chunk_words + sentence_word_count > word_limit and current_sentence_sub_chunk_parts:
            sub_chunks.append(" ".join(current_sentence_sub_chunk_parts).strip())
            current_sentence_sub_chunk_parts = [sentence.strip()] # Start new sub-chunk with current sentence
            current_sentence_sub_chunk_words = sentence_word_count
        elif sentence_word_count > word_limit: # Single sentence is too long, needs hard split
            if current_sentence_sub_chunk_parts: # Finalize previous sentence sub-chunk
                sub_chunks.append(" ".join(current_sentence_sub_chunk_parts).strip())
                current_sentence_sub_chunk_parts = []
                current_sentence_sub_chunk_words = 0
            
            logger.debug(f"Forzatura divisione per parole di una frase di {sentence_word_count} parole.")
            words_in_long_sentence = sentence.split()
            hard_split_sub_chunk_parts = []
            hard_split_sub_chunk_words = 0
            for word in words_in_long_sentence:
                if hard_split_sub_chunk_words + 1 > word_limit and hard_split_sub_chunk_parts:
                    sub_chunks.append(" ".join(hard_split_sub_chunk_parts).strip())
                    hard_split_sub_chunk_parts = [word]
                    hard_split_sub_chunk_words = 1
                else:
                    hard_split_sub_chunk_parts.append(word)
                    hard_split_sub_chunk_words += 1
            if hard_split_sub_chunk_parts: # Add the remainder of the hard-split sentence
                sub_chunks.append(" ".join(hard_split_sub_chunk_parts).strip())
        else: # Add sentence to current sentence sub-chunk
            current_sentence_sub_chunk_parts.append(sentence.strip())
            current_sentence_sub_chunk_words += sentence_word_count
    
    if current_sentence_sub_chunk_parts: # Add the last sentence sub-chunk
        sub_chunks.append(" ".join(current_sentence_sub_chunk_parts).strip())
    
    return [sc for sc in sub_chunks if sc] # Filter out any empty strings from splits

def chunk_text_by_word_limit(text: str, word_limit: int = 10000) -> List[str]:
    """
    Splits a large text into smaller chunks, each not exceeding a specified word limit.
    Tries to split along paragraph boundaries (defined by double newlines) first,
    then falls back to sentence boundaries if a paragraph is too long using _split_long_paragraph.
    If a single sentence is too long, it will be split harshly at the word limit by _split_long_paragraph.

    Args:
        text (str): The input text to be chunked.
        word_limit (int, optional): The approximate maximum number of words per chunk.
                                    Defaults to 10000.

    Returns:
        list[str]: A list of text chunks.
    """
    if not text.strip():
        logger.warning("Tentativo di dividere in chunk un testo vuoto o composto da soli spazi.")
        return []

    all_resulting_chunks = []
    current_chunk_word_count = 0
    current_chunk_paragraph_parts = [] # Stores paragraphs (strings) for the current chunk being built

    # Split by paragraphs, preserving the delimiters to maintain paragraph structure.
    # A paragraph is typically separated by one or more blank lines (i.e., two or more newlines).
    raw_paragraphs = re.split(r'(\n\s*\n)', text)
    
    # Reconstruct paragraphs with their delimiters to preserve original formatting as much as possible
    processed_paragraphs = []
    i = 0
    while i < len(raw_paragraphs):
        paragraph_part = raw_paragraphs[i]
        if i + 1 < len(raw_paragraphs) and raw_paragraphs[i+1].strip() == "": # This is a delimiter part
            # Append paragraph content and its delimiter (e.g., "text\n\n")
            processed_paragraphs.append(paragraph_part + raw_paragraphs[i+1])
            i += 2
        else:
            # This part is either a paragraph without a following captured delimiter, or the last part
            if paragraph_part.strip(): # Avoid adding empty strings if any resulted from split
                 processed_paragraphs.append(paragraph_part)
            i += 1

    for paragraph_text_with_ending in processed_paragraphs:
        if not paragraph_text_with_ending.strip():
            continue

        paragraph_word_count = count_words(paragraph_text_with_ending)

        if paragraph_word_count > word_limit:
            logger.warning(
                f"Un paragrafo di {paragraph_word_count} parole supera il limite di {word_limit} parole. "
                f"Verrà suddiviso internamente."
            )
            # Finalize and add the current_chunk being built (if any) before processing the long paragraph
            if current_chunk_paragraph_parts:
                all_resulting_chunks.append("".join(current_chunk_paragraph_parts).strip())
                current_chunk_paragraph_parts = []
                current_chunk_word_count = 0
            
            # Split the long paragraph and add its sub-chunks directly to the main list
            paragraph_sub_chunks = _split_long_paragraph(paragraph_text_with_ending, word_limit)
            all_resulting_chunks.extend(paragraph_sub_chunks)
        
        elif current_chunk_word_count + paragraph_word_count > word_limit:
            # Current chunk would exceed limit with this new paragraph.
            # Finalize and add the current_chunk.
            if current_chunk_paragraph_parts:
                all_resulting_chunks.append("".join(current_chunk_paragraph_parts).strip())
            
            # Start a new chunk with the current paragraph.
            current_chunk_paragraph_parts = [paragraph_text_with_ending]
            current_chunk_word_count = paragraph_word_count
        else:
            # Add paragraph to the current chunk being built.
            current_chunk_paragraph_parts.append(paragraph_text_with_ending)
            current_chunk_word_count += paragraph_word_count

    # Add the last remaining chunk if any content is present.
    if current_chunk_paragraph_parts:
        all_resulting_chunks.append("".join(current_chunk_paragraph_parts).strip())
    
    # Filter out any empty chunks that might have been created during processing.
    final_cleaned_chunks = [chunk for chunk in all_resulting_chunks if chunk]
    logger.info(f"Testo diviso in {len(final_cleaned_chunks)} chunk(s) con un limite di circa {word_limit} parole per chunk.")
    return final_cleaned_chunks 