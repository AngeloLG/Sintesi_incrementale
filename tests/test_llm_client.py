import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Adjust path to import from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from llm_interaction.llm_client import OpenAIClient, CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, FINAL_SUMMARY_PROMPT_INSTRUCTIONS
import openai # Import for openai error types

# A dummy API key for testing initialization
DUMMY_API_KEY = "test_api_key_123"

class TestOpenAIClient(unittest.TestCase):

    def test_client_initialization_success(self):
        """Test successful client initialization with an API key."""
        client = OpenAIClient(api_key=DUMMY_API_KEY)
        self.assertEqual(client.api_key, DUMMY_API_KEY)

    def test_client_initialization_no_api_key(self):
        """Test client initialization failure if API key is missing."""
        with self.assertRaises(ValueError) as context:
            OpenAIClient(api_key="")
        self.assertIn("API Key di OpenAI richiesta.", str(context.exception))

        with self.assertRaises(ValueError) as context:
            OpenAIClient(api_key=None)
        self.assertIn("API Key di OpenAI richiesta.", str(context.exception))

    def test_summarize_text_empty_input(self):
        """Test summarize_text with empty or whitespace-only input."""
        client = OpenAIClient(api_key=DUMMY_API_KEY)
        self.assertEqual(client.summarize_text(""), "")
        self.assertEqual(client.summarize_text("   \n  "), "")

    @patch('openai.OpenAI') # Patch the OpenAI class constructor
    def test_summarize_text_success(self, mock_openai_constructor):
        """Test a successful call to summarize_text."""
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock(message=MagicMock(content="Questo è un riassunto fittizio."))]
        
        mock_openai_instance = MagicMock()
        mock_openai_instance.chat.completions.create.return_value = mock_chat_completion
        mock_openai_constructor.return_value = mock_openai_instance

        client = OpenAIClient(api_key=DUMMY_API_KEY)
        summary = client.summarize_text("Testo di esempio.", prompt_instructions="Riassumi: {testo}")
        
        self.assertEqual(summary, "Questo è un riassunto fittizio.")
        mock_openai_constructor.assert_called_once_with(api_key=DUMMY_API_KEY)
        mock_openai_instance.chat.completions.create.assert_called_once()
        
        args, kwargs = mock_openai_instance.chat.completions.create.call_args
        self.assertEqual(kwargs['model'], "gpt-4.1-mini")
        self.assertIn({"role": "user", "content": "Riassumi: Testo di esempio."}, kwargs['messages'])

    @patch('openai.OpenAI')
    def test_summarize_text_key_error_in_prompt(self, mock_openai_constructor):
        """Test summarize_text with prompt_instructions missing {testo} placeholder."""
        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(ValueError) as context:
            client.summarize_text("Testo.", prompt_instructions="Istruzioni senza placeholder.")
        self.assertIn("Errore di formattazione del prompt", str(context.exception))
        self.assertIn("'prompt_instructions' deve contenere '{testo}'.", str(context.exception))
        # OpenAI client might be constructed, but .create shouldn't be called if formatting fails early.
        # Depending on exact implementation, mock_openai_constructor might or might not have been called.
        # For now, let's assume the client is created, but the actual API call isn't made.
        if mock_openai_constructor.called:
            mock_openai_constructor.return_value.chat.completions.create.assert_not_called()


    @patch('openai.OpenAI')
    def test_summarize_text_authentication_error(self, mock_openai_constructor): # Renamed for clarity
        mock_openai_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_openai_instance.chat.completions.create.side_effect = openai.AuthenticationError(message="Auth error", response=mock_response, body=None)
        mock_openai_constructor.return_value = mock_openai_instance
        
        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(openai.AuthenticationError):
            client.summarize_text("Testo.", prompt_instructions="{testo}")

    @patch('openai.OpenAI')
    def test_summarize_text_rate_limit_error(self, mock_openai_constructor):
        mock_openai_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_openai_instance.chat.completions.create.side_effect = openai.RateLimitError(message="Rate limit", response=mock_response, body=None)
        mock_openai_constructor.return_value = mock_openai_instance

        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(openai.RateLimitError):
            client.summarize_text("Testo.", prompt_instructions="{testo}")

    @patch('openai.OpenAI')
    def test_summarize_text_api_timeout_error(self, mock_openai_constructor):
        mock_openai_instance = MagicMock()
        mock_openai_instance.chat.completions.create.side_effect = openai.APITimeoutError(request=MagicMock())
        mock_openai_constructor.return_value = mock_openai_instance

        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(openai.APITimeoutError):
            client.summarize_text("Testo.", prompt_instructions="{testo}")
            
    @patch('openai.OpenAI')
    def test_summarize_text_api_connection_error(self, mock_openai_constructor):
        mock_openai_instance = MagicMock()
        mock_openai_instance.chat.completions.create.side_effect = openai.APIConnectionError(message="Connection error", request=MagicMock())
        mock_openai_constructor.return_value = mock_openai_instance

        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(openai.APIConnectionError):
            client.summarize_text("Testo.", prompt_instructions="{testo}")

    @patch('openai.OpenAI')
    def test_summarize_text_generic_api_status_error(self, mock_openai_constructor): # Renamed to reflect APIStatusError
        mock_openai_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500 # Example of a generic server error
        mock_openai_instance.chat.completions.create.side_effect = openai.APIStatusError(message="Generic API status error", response=mock_response, body=None)
        mock_openai_constructor.return_value = mock_openai_instance

        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(openai.APIStatusError):
            client.summarize_text("Testo.", prompt_instructions="{testo}")
            
    @patch('openai.OpenAI')
    def test_summarize_text_unexpected_error(self, mock_openai_constructor):
        mock_openai_instance = MagicMock()
        mock_openai_instance.chat.completions.create.side_effect = Exception("Unexpected error")
        mock_openai_constructor.return_value = mock_openai_instance

        client = OpenAIClient(api_key=DUMMY_API_KEY)
        with self.assertRaises(Exception) as context:
            client.summarize_text("Testo.", prompt_instructions="{testo}")
        # Check it's not one of the specific OpenAI errors we handle, but a more generic Exception
        self.assertNotIn(type(context.exception), [
            openai.AuthenticationError, openai.RateLimitError, 
            openai.APITimeoutError, openai.APIConnectionError, openai.APIStatusError, openai.APIError
        ])
        self.assertIn("Unexpected error", str(context.exception))

if __name__ == '__main__':
    unittest.main() 