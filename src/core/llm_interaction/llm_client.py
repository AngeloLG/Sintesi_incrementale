import openai
import logging
import os

logger = logging.getLogger(__name__)

# Prompt instructions for chunk summarization (Passo 2.3)
CHUNK_SUMMARY_PROMPT_INSTRUCTIONS = """## Task

Summarize the following text excerpt (up to 10,000 words) into a **concise, information-rich summary of ~1,000 words**.  

## Instructions

- Analyze the text carefully.
- Ignore:
  - editorial information, copyright, digitisation project;
  - added documents not part of the text (e.g. licences, critical introductions).
- Summarise **main text only**.
- Structure the summary with these sections:
  1. **Topics Covered**
  2. **Key Characters** (with brief descriptions)
  3. **Main Themes**
  4. **Main Points & Events**
  
- Be precise and comprehensive: do **not** omit details relevant for understanding the full book.
- Use clear, concise language.
- For fiction: capture main plot and character dynamics.  
  For non-fiction: focus on arguments, evidence, conclusions.
- **Do not paraphrase superficially—synthesize and preserve all substantive content.**
- If unsure, favor inclusion of information at this stage.
- Write the entire summary in Italian.

## Input
<input-text>
 {testo}
</input-text>
## Output
1. **Topics Covered**  
2. **Key Characters**  
3. **Main Themes**  
4. **Main Points & Events**  
 
*(Total: ~1,000 words)*
Write the entire summary in Italian
"""

# Prompt instructions for final synthesis from aggregated chunk summaries (Passo 3.2)
FINAL_SUMMARY_PROMPT_INSTRUCTIONS = """## Task

You are given multiple Italian summaries, each covering a different portion of a book.  
Your goal is to synthesize these into a **single, comprehensive final summary** of approximately 1,500 words.

## Instructions

- Carefully read and analyze all provided summaries.
- Eliminate any redundant or repeated information, but do **not** omit any important topics, characters, themes, or insights.
- Integrate information to create a **cohesive and complete picture** of the entire book.
- Structure the output and write all content in Italian.
- Ensure the summary is **dense, precise, and comprehensive**, preserving all relevant details, context, and nuances.
- For fiction: reflect the entire narrative arc, character evolution, and key plot points.  
  For non-fiction: cover all main arguments, evidence, and conclusions.
- If unsure whether to include information, favor inclusion.
- Use clear and fluent Italian throughout.
- Ignore:
  - editorial information, copyright, digitisation project;
  - added documents not part of the text (e.g. licences, critical introductions).

## Input
<input-text>
 {testo}
</input-text>

## Output
1. **Topics Covered**  
2. **Key Characters**  
3. **Main Themes**  
4. **Main Points & Events**  
 
*(Total: ~1,500 words)*
Write the entire summary in Italian
"""

class OpenAIClient:
    """
    Un client per interagire con l'API di OpenAI, specificamente per la sintesi di testo.
    """
    def __init__(self, api_key: str):
        """
        Inizializza il client OpenAI.

        Args:
            api_key (str): La tua API key di OpenAI.

        Raises:
            ValueError: Se l'API key non è fornita.
        """
        if not api_key:
            logger.error("API Key di OpenAI non fornita all'inizializzazione del client.")
            raise ValueError("API Key di OpenAI richiesta.")
        
        # Configure the OpenAI library with the API key
        # Note: The new OpenAI library (v1.0.0+) uses a different way to set the API key.
        # It can be set as an environment variable OPENAI_API_KEY,
        # or passed directly to the client constructor.
        # For this client, we expect it to be passed explicitly.
        self.api_key = api_key
        # The actual OpenAI client instance will be created per-request or managed
        # if we want to customize http client settings etc. For now, setting the key is enough
        # as the openai.ChatCompletion.create will use it if set globally or if client is instantiated.
        # openai.api_key = self.api_key # Old way for < v1.0.0
        # For openai >= 1.0.0, you typically instantiate a client:
        # from openai import OpenAI
        # self.client = OpenAI(api_key=self.api_key)
        # And then use self.client.chat.completions.create(...)

    def summarize_text(self, text: str, prompt_instructions: str = CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, model: str = "gpt-4.1-mini", max_tokens_summary: int = 1000) -> str:
        """
        Invia un testo all'API di OpenAI per la sintesi.

        Args:
            text (str): Il testo da riassumere.
            prompt_instructions (str): Istruzioni specifiche per il prompt di sintesi.
                                       Default a CHUNK_SUMMARY_PROMPT_INSTRUCTIONS.
                                       Deve contenere il placeholder {testo}.
            model (str): Il modello LLM da utilizzare (es. "gpt-3.5-turbo").
            max_tokens_summary (int): Il numero massimo di token desiderato per il riassunto generato.

        Returns:
            str: Il testo del riassunto generato dall'LLM.

        Raises:
            Exception: In caso di errori durante la chiamata API.
        """
        # Check for mock environment variables for integration testing
        mock_chunk_summary = os.getenv('TEST_MOCK_LLM_CHUNK_SUMMARY')
        mock_final_summary = os.getenv('TEST_MOCK_LLM_FINAL_SUMMARY')

        if mock_chunk_summary and prompt_instructions == CHUNK_SUMMARY_PROMPT_INSTRUCTIONS:
            logger.info("Utilizzo del riassunto mockato per chunk da variabile d'ambiente.")
            return mock_chunk_summary
        
        if mock_final_summary and prompt_instructions == FINAL_SUMMARY_PROMPT_INSTRUCTIONS:
            logger.info("Utilizzo del riassunto mockato finale da variabile d'ambiente.")
            return mock_final_summary

        if not text.strip():
            logger.warning("Tentativo di riassumere un testo vuoto. Restituzione di una stringa vuota.")
            return ""

        if '{testo}' not in prompt_instructions:
            logger.error("Il placeholder '{testo}' non è presente in prompt_instructions.")
            raise ValueError("Errore di formattazione del prompt: 'prompt_instructions' deve contenere '{testo}'.")

        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            logger.debug(f"Invio testo (primi 100 caratteri: '{text[:100]}...') al modello {model} per la sintesi.")
            # logger.debug(f"Istruzioni prompt: {prompt_instructions}") # Prompt is long, log only if necessary at DEBUG
            logger.debug(f"Max tokens per il riassunto: {max_tokens_summary}")

            # Constructing the user message by formatting the prompt with the text
            user_content = prompt_instructions.format(testo=text)

            messages = [
                {"role": "system", "content": "Sei un assistente AI specializzato nel riassumere testi accademici e letterari in modo dettagliato e neutrale, seguendo attentamente le istruzioni fornite per la struttura e il contenuto dell'output."},
                {"role": "user", "content": user_content}
            ]
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.5, 
                max_tokens=max_tokens_summary, 
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Riassunto ricevuto da OpenAI. Lunghezza: {len(summary)} caratteri.")
            logger.debug(f"Riassunto (primi 100 caratteri: '{summary[:100]}...')")
            return summary

        except openai.AuthenticationError as e:
            logger.error(f"Errore di autenticazione OpenAI: {e}. Controlla la tua API key.")
            raise
        except openai.RateLimitError as e:
            logger.error(f"Superato il rate limit di OpenAI: {e}. Riprova più tardi.")
            raise
        except openai.APITimeoutError as e:
            logger.error(f"Timeout della richiesta OpenAI: {e}.")
            raise
        except openai.APIConnectionError as e:
            logger.error(f"Errore di connessione con OpenAI: {e}. Controlla la tua connessione di rete.")
            raise
        except openai.APIStatusError as e:
            logger.error(f"Errore API OpenAI (status {e.status_code}): {e.message}")
            raise
        except openai.APIError as e:
            logger.error(f"Errore API OpenAI (generico): {e}")
            raise
        except Exception as e:
            logger.error(f"Errore imprevisto durante la chiamata all'API OpenAI: {e}", exc_info=True)
            raise

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    api_key_env = os.getenv("OPENAI_API_KEY")
    if not api_key_env:
        logger.error("Per l'esempio, imposta la variabile d'ambiente OPENAI_API_KEY.")
    else:
        try:
            client = OpenAIClient(api_key=api_key_env)
            sample_text_chunk = (
                "Questo è il primo capitolo di un libro affascinante. Narra le avventure di Marco, un giovane esploratore, "
                "e del suo fedele cane, Leo. Insieme, scoprono una mappa antica che promette di guidarli verso un tesoro nascosto. "
                "Il capitolo descrive la loro partenza dal villaggio e le prime sfide incontrate nella foresta incantata. "
                "Un personaggio misterioso, un vecchio saggio di nome Elara, li avverte dei pericoli imminenti e dona a Marco "
                "un amuleto protettivo. Il tema principale è l'inizio di un viaggio e il coraggio di fronte all'ignoto."
            )
            
            logger.info("[Esempio Chunk Summary] Tentativo di riassumere un testo di esempio con il prompt per chunk...")
            # Using the default CHUNK_SUMMARY_PROMPT_INSTRUCTIONS which now contains {testo}
            chunk_summary_example = client.summarize_text(
                sample_text_chunk, 
                prompt_instructions=CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, # Explicitly passing for clarity
                max_tokens_summary=1000
            ) 
            
            if chunk_summary_example:
                logger.info(f"""[Esempio Chunk Summary] Riassunto dell'esempio:
{chunk_summary_example}""")
            else:
                logger.warning("[Esempio Chunk Summary] Il riassunto dell'esempio è vuoto.")

            # Example for final summary (concept, not run with actual aggregated text here)
            sample_aggregated_summaries = (
                "RIASSUNTO CHUNK 1: Marco e Leo trovano una mappa e iniziano un viaggio. Elara li aiuta.\n"
                "RIASSUNTO CHUNK 2: Marco e Leo superano la foresta e raggiungono le montagne. Trovano un indizio."
            )
            logger.info("[Esempio Final Summary] Concetto: riassumere riassunti aggregati.")
            # final_summary_example = client.summarize_text(
            #     sample_aggregated_summaries,
            #     prompt_instructions=FINAL_SUMMARY_PROMPT_INSTRUCTIONS,
            #     # model="gpt-4.1-mini", # No longer needed to specify if it's the new default
            #     max_tokens_summary=1500 # Higher token limit for final summary
            # )
            # if final_summary_example:
            #     logger.info(f"[Esempio Final Summary] Riassunto finale concettuale:\n{final_summary_example}")
            # else:
            #     logger.warning("[Esempio Final Summary] Il riassunto finale concettuale è vuoto.")

        except ValueError as ve:
            logger.error(f"Errore di inizializzazione client o formattazione prompt: {ve}")
        except Exception as ex:
            logger.error(f"Errore durante l'esecuzione dell'esempio: {ex}", exc_info=True) 