import unittest
import os
import sys

# Adjust the path to import from the src directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from text_processing.text_chunker import chunk_text_by_word_limit, count_words

class TestTextChunker(unittest.TestCase):

    def test_count_words(self):
        self.assertEqual(count_words("Ciao mondo"), 2)
        self.assertEqual(count_words("  Ciao   mondo  "), 2)
        self.assertEqual(count_words("Una frase con cinque parole."), 5)
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words("   "), 0)

    def test_empty_text_chunking(self):
        """Test chunking of empty or whitespace-only text."""
        self.assertEqual(chunk_text_by_word_limit(""), [])
        self.assertEqual(chunk_text_by_word_limit("   \n  "), []) # Corrected whitespace check

    def test_short_text_chunking(self):
        """Test chunking of text shorter than the word limit."""
        text = "Questo è un testo breve. Meno di dieci parole."
        chunks = chunk_text_by_word_limit(text, word_limit=10)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_chunking_at_word_limit(self):
        """Test basic chunking at the word limit with simple paragraph structure."""
        paragraph1 = "Parola " * 8 + "FineP1." # 9 words
        paragraph2 = "InizioP2 " + "Altraparola " * 7 + "FineP2." # 9 words
        text = f"{paragraph1}\n\n{paragraph2}" # Total 18 words, separated by paragraph break
        
        chunks = chunk_text_by_word_limit(text, word_limit=10)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(paragraph1.strip() in chunks[0])
        self.assertTrue(paragraph2.strip() in chunks[1])
        self.assertLessEqual(count_words(chunks[0]), 10)
        self.assertLessEqual(count_words(chunks[1]), 10)

    def test_chunking_long_paragraph_by_sentences(self):
        """Test chunking a paragraph longer than limit, splitting by sentences."""
        # Sentence 1: 6 words. Sentence 2: 7 words. Sentence 3: 3 words. Total 16 words.
        long_paragraph = "Questa è la prima frase. Poi arriva la seconda frase più lunga. Infine la terza."
        chunks = chunk_text_by_word_limit(long_paragraph, word_limit=7)
        # Expected chunking based on sentence splitting when paragraph > limit:
        # Chunk 1: "Questa è la prima frase." (6 words)
        # Chunk 2: "Poi arriva la seconda frase più lunga." (7 words)
        # Chunk 3: "Infine la terza." (3 words)
        self.assertEqual(len(chunks), 3) 
        self.assertTrue("Questa è la prima frase." in chunks[0])
        self.assertTrue("Poi arriva la seconda frase più lunga." in chunks[1])
        self.assertTrue("Infine la terza." in chunks[2])
        self.assertLessEqual(count_words(chunks[0]), 7)
        self.assertLessEqual(count_words(chunks[1]), 7)
        self.assertLessEqual(count_words(chunks[2]), 7)

    def test_chunking_very_long_sentence(self):
        """Test chunking a single sentence longer than the word limit."""
        long_sentence = "Questa è una singola frase incredibilmente lunga che supera di gran lunga il limite di parole stabilito per un singolo chunk."
        # Word count of long_sentence is 20
        chunks = chunk_text_by_word_limit(long_sentence, word_limit=8)
        self.assertTrue(len(chunks) > 1)
        self.assertEqual(count_words(" ".join(chunks)), count_words(long_sentence)) # Check word preservation
        for chunk in chunks:
            self.assertLessEqual(count_words(chunk), 8)
        self.assertFalse(long_sentence == chunks[0])
        self.assertTrue(chunks[0].startswith("Questa è una singola frase incredibilmente lunga"))

    def test_respect_paragraph_boundaries(self):
        """Test that chunker respects paragraph boundaries when possible."""
        p1 = "Paragrafo uno con alcune parole."  # 5 words
        p2 = "Paragrafo due anche con un po' di testo."  # 8 words
        p3 = "Paragrafo tre è corto."  # 4 words
        text = f"{p1}\n\n{p2}\n\n{p3}" # Using f-string with explicit paragraph breaks

        chunks = chunk_text_by_word_limit(text, word_limit=10)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].strip(), p1)
        self.assertEqual(chunks[1].strip(), p2)
        self.assertEqual(chunks[2].strip(), p3)
    
    def test_respect_paragraph_boundaries_grouping(self):
        """Test that chunker groups paragraphs if they fit."""
        p1 = "Paragrafo uno corto."  # 3 words
        p2 = "Paragrafo due anche."  # 3 words
        # p3 is long and will be split by sentences
        p3_s1 = "Paragrafo tre, prima frase."
        p3_s2 = "Seconda frase di P3, un po' più lunga."
        p3_s3 = "Terza e ultima frase di P3."
        p3 = f"{p3_s1} {p3_s2} {p3_s3}" # ~17 words
        p4 = "Paragrafo quattro finale."  # 3 words
        text = f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"
        
        chunks = chunk_text_by_word_limit(text, word_limit=10)
        
        # Chunk 1: p1 + p2 (3+3=6 words)
        expected_chunk0 = f"{p1}\n\n{p2}"
        self.assertEqual(chunks[0].strip(), expected_chunk0.strip())
        self.assertLessEqual(count_words(chunks[0]), 10)

        # Check content of p3 is split and p4 is last
        # This part is complex because p3 itself is split into sentences then words
        # For simplicity, we'll check p3_s1, p3_s2, p3_s3 are in the subsequent chunks
        # and p4 is the last one.
        self.assertTrue(p3_s1 in chunks[1])
        self.assertTrue(p3_s2 in chunks[2])
        self.assertTrue(p3_s3 in chunks[3])
        self.assertTrue(p4 in chunks[4])
        self.assertEqual(len(chunks), 5)

    def test_retains_newlines_within_paragraphs(self):
        text_with_internal_newlines = "Questa è la prima riga.\nQuesta è la seconda riga dello stesso paragrafo.\n\nQuesto è un nuovo paragrafo."
        chunks = chunk_text_by_word_limit(text_with_internal_newlines, word_limit=50)
        self.assertEqual(len(chunks), 1)
        # Check that the structure of the first paragraph is maintained
        self.assertIn("Questa è la prima riga.\nQuesta è la seconda riga dello stesso paragrafo.", chunks[0])
        # Check that the paragraph separator and the next paragraph are also there
        self.assertIn("\n\nQuesto è un nuovo paragrafo.", chunks[0])

if __name__ == '__main__':
    unittest.main() 