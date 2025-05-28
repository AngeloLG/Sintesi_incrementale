import click
import logging
import os
from dotenv import load_dotenv
import openai
from typing import Optional, List, Tuple # Added Optional, List, Tuple

from .logging_config import setup_logging # Relative import
from .text_extraction import get_text_extractor, UnsupportedFileTypeError, PdfExtractionError, EpubExtractionError # Added EpubExtractionError
from .text_processing import chunk_text_by_word_limit # New import
from .file_utils import save_text_chunks, aggregate_summaries, save_final_summary # Updated import
from .llm_interaction import OpenAIClient, CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, FINAL_SUMMARY_PROMPT_INSTRUCTIONS # Updated import

# --- Constants ---
BASE_OUTPUT_DIR = "output"
SUMMARIES_SUBDIR = "summaries"
DEFAULT_CHUNK_MODEL = "gpt-4.1-mini"
DEFAULT_FINAL_MODEL = "gpt-4.1-mini"
DEFAULT_CHUNK_MAX_TOKENS = 1000
DEFAULT_FINAL_MAX_TOKENS = 4000 # Changed from 3000 to 4000
DEFAULT_WORD_LIMIT_PER_CHUNK = 10000

# Load environment variables from .env file if it exists
load_dotenv()

# Setup basic logging configuration
# The level can be made configurable later if needed (e.g., via a CLI option)
setup_logging()

# Get a logger for this module
logger = logging.getLogger(__name__)

# --- Helper function to resolve output directory for aggregated summaries ---
# This could also be in file_utils.py if it becomes more complex or widely used
def get_aggregated_summaries_output_dir(input_file: str, base_output_dir: str = "output") -> str:
    """
    Determina la directory per salvare il file dei riassunti aggregati.
    Solitamente è la directory che contiene le sottodirectory dei chunk e dei loro riassunti.
    Es: output/nome_file_originale/
    """
    filename_stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(base_output_dir, filename_stem)

# --- Helper function for output directory ---
def get_per_file_output_dir(input_file: str) -> str:
    """Determina la directory di output specifica per il file di input (es. output/nome_file_originale/)."""
    filename_stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(BASE_OUTPUT_DIR, filename_stem)

# --- Private Helper Functions for process() ---
def _initialize_openai_client(api_key: Optional[str]) -> Optional[OpenAIClient]:
    if not api_key:
        logger.warning("OpenAI API key not provided. LLM-dependent operations will fail.")
        click.echo(click.style("API Key non fornita. Le operazioni LLM verranno saltate.", fg='yellow'))
        return None
    try:
        client = OpenAIClient(api_key=api_key)
        logger.info("Client OpenAI inizializzato con successo.")
        click.echo(f"API Key caricata.")
        return client
    except ValueError as e:
        logger.error(f"Errore durante l'inizializzazione del client OpenAI: {e}")
        click.echo(click.style(f"Errore client OpenAI: {e}. Le operazioni LLM non saranno eseguite.", fg='red'))
        return None

def _extract_and_chunk_text(input_file: str) -> Tuple[str, List[str]]:
    logger.info(f"Tentativo di estrazione del testo da: {input_file}")
    extractor = get_text_extractor(input_file)
    extracted_text = extractor.extract(input_file)
    
    if not extracted_text.strip():
        logger.warning(f"Nessun testo è stato estratto da {input_file} o il testo è vuoto.")
        click.echo(click.style(f"Attenzione: Nessun testo estratto da {input_file}.", fg='yellow'))
        return extracted_text, [] # Return empty list of chunks
    
    logger.info(f"Testo estratto con successo. Lunghezza originale: {len(extracted_text)} caratteri.")
    
    # --- SEZIONE PER LA PULIZIA GUTENBERG ---
    cleanup_phrase = "*** END OF THE PROJECT GUTENBERG EBOOK"
    phrase_index = extracted_text.find(cleanup_phrase)

    if phrase_index != -1:
        logger.info(f"Trovata la dicitura di fine progetto Gutenberg alla posizione {phrase_index}.")
        original_length_before_cleanup = len(extracted_text)
        extracted_text = extracted_text[:phrase_index]
        logger.info(f"Testo troncato. Nuova lunghezza: {len(extracted_text)} caratteri (rimossi {original_length_before_cleanup - len(extracted_text)} caratteri).")
        click.echo(click.style("Rilevata e rimossa sezione finale del Progetto Gutenberg.", fg='blue'))
    else:
        logger.info("Dicitura di fine progetto Gutenberg non trovata. Il testo non è stato troncato.")
    # --- FINE SEZIONE PULIZIA ---
        
    # Log e echo dopo la potenziale pulizia
    if extracted_text.strip():
        logger.info(f"Testo (dopo pulizia) pronto per chunking. Lunghezza: {len(extracted_text)} caratteri.")
        click.echo(click.style(f"Testo (dopo pulizia) pronto per chunking. Primi 200 chars: {extracted_text[:200]}...", fg='green'))
    else:
        logger.warning(f"Il testo estratto da {input_file} è diventato vuoto dopo la pulizia.")
        click.echo(click.style(f"Attenzione: Testo vuoto dopo la pulizia da {input_file}.", fg='yellow'))

    logger.info("Inizio suddivisione del testo in chunk.")
    text_chunks = chunk_text_by_word_limit(extracted_text, word_limit=DEFAULT_WORD_LIMIT_PER_CHUNK)
    logger.info(f"Testo suddiviso in {len(text_chunks)} chunk(s).")
    click.echo(f"Testo suddiviso in {len(text_chunks)} chunk(s) di circa {DEFAULT_WORD_LIMIT_PER_CHUNK} parole.")
    if logger.level == logging.DEBUG:
        for i, chunk in enumerate(text_chunks):
            logger.debug(f"Chunk {i+1}: {len(chunk.split())} parole, {len(chunk)} caratteri. Anteprima: {chunk[:100]}...")
    return extracted_text, text_chunks

def _save_text_chunks_to_files(text_chunks: List[str], input_file: str, ctx: click.Context) -> List[str]:
    if not text_chunks:
        logger.info("Nessun chunk testuale da salvare.")
        return []
    try:
        per_file_output_dir = get_per_file_output_dir(input_file) # Chunks go into the per-file subdir
        saved_chunk_files = save_text_chunks(text_chunks, per_file_output_dir, input_file) # save_text_chunks creates its own subdir based on original_filename within the passed base_output_dir
                                                                                      # So we pass the specific per-file dir here
        
        # The save_text_chunks now creates output/original_filename/original_filename_chunk_NNN.txt
        # This logic needs to be aligned. save_text_chunks in file_utils creates a subdir itself.
        # Let's adjust the call to save_text_chunks to pass BASE_OUTPUT_DIR,
        # and it will create output/filename_stem/ for the chunks.
        
        saved_chunk_files = save_text_chunks(text_chunks, BASE_OUTPUT_DIR, input_file)

        click.echo(click.style(f"{len(saved_chunk_files)} chunk(s) salvati in sottodirectory in '{get_per_file_output_dir(input_file)}'.", fg='cyan'))
        ctx.obj['chunk_file_paths'] = saved_chunk_files
        return saved_chunk_files
    except OSError as e:
        logger.error(f"Errore critico durante il salvataggio dei chunk: {e}. Elaborazione interrotta.", exc_info=True)
        click.echo(click.style(f"Errore critico salvando i chunk: {e}. Interruzione.", fg='red'), err=True)
        ctx.abort()
    except Exception as e: # Catch any other exception from save_text_chunks
        logger.error(f"Errore imprevisto durante il salvataggio dei chunk: {e}. Elaborazione interrotta.", exc_info=True)
        click.echo(click.style(f"Errore imprevisto salvando i chunk: {e}. Interruzione.", fg='red'), err=True)
        ctx.abort()
    return []

def _summarize_all_chunks(
    openai_client: OpenAIClient, 
    saved_chunk_files: List[str], 
    input_file: str, 
    ctx: click.Context
) -> List[str]:
    logger.info(f"Inizio sintesi dei {len(saved_chunk_files)} chunk(s) con LLM.")
    click.echo(f"Inizio sintesi dei chunk con LLM (modello: {DEFAULT_CHUNK_MODEL})... " +
               "Questo potrebbe richiedere tempo.")
    
    chunk_summaries_paths = []
    filename_stem = os.path.splitext(os.path.basename(input_file))[0]
    
    # Determine base directory for summaries (e.g., output/filename_stem/summaries)
    summaries_output_dir = ""
    if saved_chunk_files:
        # Assuming saved_chunk_files are like: output/filename_stem/filename_stem_chunk_001.txt
        # The parent dir of the first chunk file is output/filename_stem/
        base_chunk_dir = os.path.dirname(saved_chunk_files[0]) 
        summaries_output_dir = os.path.join(base_chunk_dir, SUMMARIES_SUBDIR)
    
    if not summaries_output_dir:
        logger.warning("Impossibile determinare la directory per i riassunti dei chunk. Salto sintesi.")
        return []

    try:
        if not os.path.exists(summaries_output_dir):
            os.makedirs(summaries_output_dir)
            logger.info(f"Creata directory per i riassunti dei chunk: {summaries_output_dir}")
    except OSError as e:
        logger.error(f"Errore creazione directory riassunti {summaries_output_dir}: {e}. Salto sintesi LLM.", exc_info=True)
        click.echo(click.style(f"Errore creazione directory riassunti: {e}. Sintesi LLM saltata.", fg='red'))
        return [] # Cannot proceed without summary directory

    for i, chunk_file_path in enumerate(saved_chunk_files):
        try:
            logger.info(f"Lettura del chunk {i+1}/{len(saved_chunk_files)}: {chunk_file_path}")
            with open(chunk_file_path, 'r', encoding='utf-8') as f_chunk:
                chunk_text = f_chunk.read()
            
            if not chunk_text.strip():
                logger.warning(f"Il chunk {chunk_file_path} è vuoto. Salto la sintesi.")
                click.echo(click.style(f"Chunk {i+1} è vuoto. Sintesi saltata.", fg='yellow'))
                continue

            click.echo(f"Invio del chunk {i+1}/{len(saved_chunk_files)} all'LLM...")
            summary = openai_client.summarize_text(
                chunk_text,
                prompt_instructions=CHUNK_SUMMARY_PROMPT_INSTRUCTIONS,
                model=DEFAULT_CHUNK_MODEL,
                max_tokens_summary=DEFAULT_CHUNK_MAX_TOKENS
            )

            summary_filename = f"{filename_stem}_chunk_{i+1:03d}_summary.txt"
            summary_filepath = os.path.join(summaries_output_dir, summary_filename)
            
            try:
                with open(summary_filepath, 'w', encoding='utf-8') as f_summary:
                    f_summary.write(summary)
                chunk_summaries_paths.append(summary_filepath)
                logger.info(f"Riassunto del chunk {i+1} salvato in: {summary_filepath}")
                click.echo(click.style(f"Riassunto del chunk {i+1} salvato.", fg='green'))
            except IOError as e:
                logger.error(f"Errore I/O salvataggio riassunto chunk {summary_filepath}: {e}", exc_info=True)
                click.echo(click.style(f"Errore salvataggio riassunto chunk {i+1}: {e}. Continuo.", fg='yellow'))
        except FileNotFoundError:
            logger.error(f"File chunk non trovato: {chunk_file_path}. Salto sintesi.", exc_info=True)
            click.echo(click.style(f"File chunk {chunk_file_path} non trovato. Sintesi saltata.", fg='yellow'))
        except openai.AuthenticationError as e:
            logger.error(f"Errore di autenticazione OpenAI per chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Errore Autenticazione OpenAI per chunk {i+1}: {e}. Verifica la API key. Interrompo sintesi chunk.", fg='red'))
            break 
        except openai.RateLimitError as e:
            logger.error(f"Rate limit OpenAI per chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Rate Limit OpenAI per chunk {i+1}: {e}. Riprova più tardi. Interrompo sintesi chunk.", fg='red'))
            break 
        except openai.APIConnectionError as e:
            logger.error(f"Errore di connessione OpenAI per chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Errore Connessione OpenAI per chunk {i+1}: {e}. Controlla la rete. Provo con il prossimo chunk.", fg='yellow'))
        except openai.APITimeoutError as e:
            logger.error(f"Timeout OpenAI per chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Timeout OpenAI per chunk {i+1}: {e}. Provo con il prossimo chunk.", fg='yellow'))
        except openai.APIError as e:
            logger.error(f"Errore API OpenAI per chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Errore API OpenAI per chunk {i+1}: {e}. Provo con il prossimo chunk.", fg='red'))
        except ValueError as e: 
            logger.error(f"Errore di valore/configurazione per sintesi chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Errore Configurazione Sintesi chunk: {e}. Interrompo sintesi.", fg='red'))
            break
        except Exception as e:
            logger.error(f"Errore imprevisto sintesi chunk {chunk_file_path}: {e}", exc_info=True)
            click.echo(click.style(f"Errore imprevisto sintesi chunk {i+1}: {e}. Provo con il prossimo.", fg='red'))
            
    if chunk_summaries_paths:
        logger.info(f"{len(chunk_summaries_paths)} riassunti dei chunk salvati in {summaries_output_dir}")
        click.echo(click.style(f"Completata sintesi dei chunk. {len(chunk_summaries_paths)} riassunti salvati.", fg='cyan'))
        ctx.obj['chunk_summaries_paths'] = chunk_summaries_paths
    else:
        logger.warning("Nessun riassunto dei chunk è stato salvato.")
        click.echo(click.style("Nessun riassunto dei chunk è stato salvato.", fg='yellow'))
    return chunk_summaries_paths

def _perform_final_summary(
    openai_client: OpenAIClient, 
    aggregated_summaries_file_path: Optional[str], 
    ctx: click.Context
) -> Optional[str]:
    if not aggregated_summaries_file_path:
        logger.info("File dei riassunti aggregati non disponibile, sintesi finale LLM saltata.")
        click.echo(click.style("Sintesi finale saltata: file riassunti aggregati non disponibile.", fg='yellow'))
        return None

    logger.info(f"Inizio sintesi finale LLM da: {aggregated_summaries_file_path}")
    click.echo(f"Inizio sintesi finale con LLM (modello: {DEFAULT_FINAL_MODEL})... " +
               "Questo potrebbe richiedere tempo.")
    try:
        with open(aggregated_summaries_file_path, 'r', encoding='utf-8') as f_agg:
            aggregated_text = f_agg.read()
        
        if not aggregated_text.strip():
            logger.warning(f"File riassunti aggregati {aggregated_summaries_file_path} è vuoto. Salto sintesi finale.")
            click.echo(click.style("File riassunti aggregati vuoto. Sintesi finale saltata.", fg='yellow'))
            return None

        click.echo(f"Invio del testo aggregato all'LLM per la sintesi finale...")
        final_summary = openai_client.summarize_text(
            aggregated_text,
            prompt_instructions=FINAL_SUMMARY_PROMPT_INSTRUCTIONS,
            model=DEFAULT_FINAL_MODEL,
            max_tokens_summary=DEFAULT_FINAL_MAX_TOKENS
        )
        ctx.obj['final_summary_text'] = final_summary # Store in context for saving
        if final_summary:
            logger.info("Sintesi finale ricevuta dall'LLM.")
            click.echo(click.style("Sintesi finale generata.", fg='green'))
        else:
            logger.warning("La sintesi finale dall'LLM è vuota.")
            click.echo(click.style("La sintesi finale generata è vuota.", fg='yellow'))
        return final_summary

    except openai.AuthenticationError as e:
        logger.error(f"Errore di autenticazione OpenAI per sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Errore Autenticazione OpenAI per sintesi finale: {e}. Verifica la API key.", fg='red'))
    except openai.RateLimitError as e:
        logger.error(f"Rate limit OpenAI per sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Rate Limit OpenAI per sintesi finale: {e}. Riprova più tardi.", fg='red'))
    except openai.APIConnectionError as e:
        logger.error(f"Errore di connessione OpenAI per sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Errore Connessione OpenAI per sintesi finale: {e}. Controlla la rete.", fg='red'))
    except openai.APITimeoutError as e:
        logger.error(f"Timeout OpenAI per sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Timeout OpenAI per sintesi finale: {e}. Riprova.", fg='red'))
    except openai.APIError as e:
        logger.error(f"Errore API OpenAI per sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Errore API OpenAI per sintesi finale: {e}.", fg='red'))
    except ValueError as e: 
        logger.error(f"Errore di valore/configurazione per sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Errore Configurazione Sintesi finale: {e}.", fg='red'))
    except Exception as e:
        logger.error(f"Errore imprevisto durante la sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Errore imprevisto durante la sintesi finale: {e}", fg='red'))
    return None

def _save_final_summary_to_file(final_summary_text: Optional[str], input_file: str) -> Optional[str]:
    if not final_summary_text: # Also handles empty string from LLM
        logger.info("Nessuna sintesi finale disponibile da salvare.")
        return None
        
    logger.info("Inizio salvataggio della sintesi finale.")
    output_dir_for_final_summary = get_per_file_output_dir(input_file)
    saved_final_summary_path = save_final_summary(
        final_summary_text,
        output_dir_for_final_summary, # save_final_summary will place it inside this dir
        input_file
    )
    if saved_final_summary_path:
        logger.info(f"Sintesi finale salvata con successo in: {saved_final_summary_path}")
        click.echo(click.style(f"Sintesi finale salvata in: {saved_final_summary_path}", fg='bright_green'))
    else:
        logger.error("Fallimento nel salvare la sintesi finale.")
        click.echo(click.style("Errore durante il salvataggio della sintesi finale. Controllare i log.", fg='red'))
    return saved_final_summary_path

@click.group() # Main command group
@click.option('--api-key', envvar='OPENAI_API_KEY', help="Your OpenAI API key. Can also be set via OPENAI_API_KEY environment variable.")
@click.option('--debug', is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx, api_key, debug):
    """
    Tool di Sintesi Incrementale

    Questo strumento permette di generare una sintesi tematica coerente di un libro
    partendo da file PDF, EPUB o TXT.
    """
    ctx.ensure_object(dict)
    ctx.obj['API_KEY'] = api_key

    if debug:
        setup_logging(logging.DEBUG)
        logger.debug("Debug mode enabled.")
    
    if not api_key:
        logger.warning("OpenAI API key not provided. LLM-dependent operations will fail. Set it via --api-key or OPENAI_API_KEY env var.")
    else:
        logger.debug("OpenAI API key loaded.") # Be careful not to log the key itself

@cli.command() # Example subcommand
@click.argument('input_file', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.pass_context
def process(ctx, input_file):
    """
    Processa un file di input (PDF, EPUB, TXT) per la sintesi.
    """
    logger.info(f"Ricevuto comando 'process' per il file: {input_file}")
    api_key = ctx.obj.get('API_KEY') # Get API key from context
    # logger.info(f"API Key disponibile nel contesto: {'Sì' if api_key_present else 'No'}")

    click.echo(f"Inizio elaborazione del file: {input_file}")
    if api_key:
        click.echo(f"API Key caricata.") # Simplified message
        # click.echo(f"API Key: {'*'*len(ctx.obj['API_KEY'])}")
    else:
        click.echo(click.style("API Key non fornita. Le operazioni LLM verranno saltate.", fg='yellow'))

    openai_client = None
    if api_key:
        try:
            openai_client = OpenAIClient(api_key=api_key)
            logger.info("Client OpenAI inizializzato con successo.")
        except ValueError as e:
            logger.error(f"Errore durante l'inizializzazione del client OpenAI: {e}")
            click.echo(click.style(f"Errore client OpenAI: {e}. Le operazioni LLM non saranno eseguite.", fg='red'))
            # Non abortiamo qui, potremmo voler continuare con altre operazioni non-LLM
            # o lasciare che l'utente decida. Per ora, continuiamo e saltiamo i passaggi LLM.

    extracted_text = ""
    text_chunks = []
    saved_chunk_files = []
    
    try:
        # 1. Text Extraction
        logger.info(f"Tentativo di estrazione del testo da: {input_file}")
        extractor = get_text_extractor(input_file)
        extracted_text = extractor.extract(input_file)
        
        if not extracted_text.strip():
            logger.warning(f"Nessun testo è stato estratto da {input_file} o il testo è vuoto.")
            click.echo(click.style(f"Attenzione: Nessun testo estratto da {input_file}.", fg='yellow'))
            # text_chunks = [] # Sarà gestito più avanti
        else:
            logger.info(f"Testo estratto con successo. Lunghezza originale: {len(extracted_text)} caratteri.")

            # --- SEZIONE PER LA PULIZIA GUTENBERG ---
            cleanup_phrase = "*** END OF THE PROJECT GUTENBERG EBOOK"
            phrase_index = extracted_text.find(cleanup_phrase)

            if phrase_index != -1:
                logger.info(f"Trovata la dicitura di fine progetto Gutenberg alla posizione {phrase_index}.")
                original_length_before_cleanup = len(extracted_text)
                extracted_text = extracted_text[:phrase_index]
                logger.info(f"Testo troncato. Nuova lunghezza: {len(extracted_text)} caratteri (rimossi {original_length_before_cleanup - len(extracted_text)} caratteri).")
                click.echo(click.style("Rilevata e rimossa sezione finale del Progetto Gutenberg.", fg='blue'))
            else:
                logger.info("Dicitura di fine progetto Gutenberg non trovata. Il testo non è stato troncato.")
            # --- FINE SEZIONE PULIZIA ---

            # Log e echo dopo la potenziale pulizia
            if extracted_text.strip():
                logger.info(f"Testo (dopo pulizia) pronto per chunking. Lunghezza: {len(extracted_text)} caratteri.")
                click.echo(click.style(f"Testo (dopo pulizia) pronto per chunking. Primi 200 chars: {extracted_text[:200]}...", fg='green'))
            else:
                logger.warning(f"Il testo estratto da {input_file} è diventato vuoto dopo la pulizia.")
                click.echo(click.style(f"Attenzione: Testo vuoto dopo la pulizia da {input_file}.", fg='yellow'))

        # 2. Text Chunking
        if not extracted_text.strip(): # Check again if text is empty after cleanup or initial extraction
            logger.warning("Il testo è vuoto, la fase di chunking verrà saltata.")
            text_chunks = []
        else:
            logger.info("Inizio suddivisione del testo in chunk.")
            word_limit_per_chunk = 10000 
            text_chunks = chunk_text_by_word_limit(extracted_text, word_limit=word_limit_per_chunk)
            logger.info(f"Testo suddiviso in {len(text_chunks)} chunk(s).")
            click.echo(f"Testo suddiviso in {len(text_chunks)} chunk(s) di circa {word_limit_per_chunk} parole.")
            if logger.level == logging.DEBUG:
                for i, chunk in enumerate(text_chunks):
                    logger.debug(f"Chunk {i+1}: {len(chunk.split())} parole, {len(chunk)} caratteri. Anteprima: {chunk[:100]}...")

        # 3. Save Chunks
        if text_chunks:
            chunk_output_base_dir = "output"
            try:
                saved_chunk_files = save_text_chunks(text_chunks, chunk_output_base_dir, input_file)
                click.echo(click.style(f"{len(saved_chunk_files)} chunk(s) salvati in sottodirectory in '{os.path.join(chunk_output_base_dir, os.path.splitext(os.path.basename(input_file))[0])}'.", fg='cyan'))
                ctx.obj['chunk_file_paths'] = saved_chunk_files 
            except OSError as e:
                logger.error(f"Errore critico durante il salvataggio dei chunk: {e}. Elaborazione interrotta.", exc_info=True)
                click.echo(click.style(f"Errore critico salvando i chunk: {e}. Interruzione.", fg='red'), err=True)
                ctx.abort()
            except Exception as e:
                logger.error(f"Errore imprevisto durante il salvataggio dei chunk: {e}. Elaborazione interrotta.", exc_info=True)
                click.echo(click.style(f"Errore imprevisto salvando i chunk: {e}. Interruzione.", fg='red'), err=True)
                ctx.abort()
        else:
            logger.info("Nessun chunk testuale da salvare.")

        # 4. LLM Summarization of Chunks (Passo 2.3)
        if openai_client and saved_chunk_files:
            logger.info(f"Inizio sintesi dei {len(saved_chunk_files)} chunk(s) con LLM.")
            click.echo(f"Inizio sintesi dei chunk con LLM (modello: {DEFAULT_CHUNK_MODEL})... " +
                       "Questo potrebbe richiedere tempo.")
            
            chunk_summaries_content = []
            chunk_summaries_paths = []
            filename_stem = os.path.splitext(os.path.basename(input_file))[0]
            summaries_dir = ""
            if saved_chunk_files:
                base_chunk_dir = os.path.dirname(saved_chunk_files[0])
                summaries_dir = os.path.join(base_chunk_dir, "summaries")
            
            if summaries_dir:
                try:
                    if not os.path.exists(summaries_dir):
                        os.makedirs(summaries_dir)
                        logger.info(f"Creata directory per i riassunti dei chunk: {summaries_dir}")
                except OSError as e:
                    logger.error(f"Errore creazione directory riassunti {summaries_dir}: {e}. Salto sintesi LLM.", exc_info=True)
                    click.echo(click.style(f"Errore creazione directory riassunti: {e}. Sintesi LLM saltata.", fg='red'))
                    summaries_dir = "" # Invalidate to skip saving summaries
            
            if summaries_dir: # Proceed only if summaries_dir is valid and created
                for i, chunk_file_path in enumerate(saved_chunk_files):
                    try:
                        logger.info(f"Lettura del chunk {i+1}/{len(saved_chunk_files)}: {chunk_file_path}")
                        with open(chunk_file_path, 'r', encoding='utf-8') as f_chunk:
                            chunk_text = f_chunk.read()
                        
                        if not chunk_text.strip():
                            logger.warning(f"Il chunk {chunk_file_path} è vuoto. Salto la sintesi.")
                            click.echo(click.style(f"Chunk {i+1} è vuoto. Sintesi saltata.", fg='yellow'))
                            continue

                        click.echo(f"Invio del chunk {i+1}/{len(saved_chunk_files)} all'LLM...")
                        summary = openai_client.summarize_text(
                            chunk_text,
                            prompt_instructions=CHUNK_SUMMARY_PROMPT_INSTRUCTIONS,
                            model=DEFAULT_CHUNK_MODEL,
                            max_tokens_summary=DEFAULT_CHUNK_MAX_TOKENS
                        )
                        # chunk_summaries_content.append(summary) # Contenuto non più usato direttamente

                        summary_filename = f"{filename_stem}_chunk_{i+1:03d}_summary.txt"
                        summary_filepath = os.path.join(summaries_dir, summary_filename)
                        
                        try:
                            with open(summary_filepath, 'w', encoding='utf-8') as f_summary:
                                f_summary.write(summary)
                            chunk_summaries_paths.append(summary_filepath)
                            logger.info(f"Riassunto del chunk {i+1} salvato in: {summary_filepath}")
                            click.echo(click.style(f"Riassunto del chunk {i+1} salvato.", fg='green'))
                        except IOError as e:
                            logger.error(f"Errore I/O salvataggio riassunto chunk {summary_filepath}: {e}", exc_info=True)
                            click.echo(click.style(f"Errore salvataggio riassunto chunk {i+1}: {e}. Continuo con il prossimo chunk.", fg='yellow'))
                            # Non aggiungiamo a chunk_summaries_paths se il salvataggio fallisce

                    except FileNotFoundError:
                        logger.error(f"File chunk non trovato: {chunk_file_path}. Salto sintesi.", exc_info=True)
                        click.echo(click.style(f"File chunk {chunk_file_path} non trovato. Sintesi saltata.", fg='yellow'))
                    # Specific OpenAI client errors
                    except openai.AuthenticationError as e:
                        logger.error(f"Errore di autenticazione OpenAI per chunk {i+1}: {e}", exc_info=True)
                        click.echo(click.style(f"Errore Autenticazione OpenAI per chunk {i+1}: {e}. Verifica la API key. Interrompo sintesi chunk.", fg='red'))
                        break # Stop processing further chunks if auth fails
                    except openai.RateLimitError as e:
                        logger.error(f"Rate limit OpenAI per chunk {i+1}: {e}", exc_info=True)
                        click.echo(click.style(f"Rate Limit OpenAI per chunk {i+1}: {e}. Riprova più tardi. Interrompo sintesi chunk.", fg='red'))
                        break # Stop processing further chunks
                    except openai.APIConnectionError as e:
                        logger.error(f"Errore di connessione OpenAI per chunk {i+1}: {e}", exc_info=True)
                        click.echo(click.style(f"Errore Connessione OpenAI per chunk {i+1}: {e}. Controlla la rete. Provo con il prossimo chunk.", fg='yellow'))
                        # Potremmo voler continuare o interrompere, per ora continuo
                    except openai.APITimeoutError as e:
                        logger.error(f"Timeout OpenAI per chunk {i+1}: {e}", exc_info=True)
                        click.echo(click.style(f"Timeout OpenAI per chunk {i+1}: {e}. Provo con il prossimo chunk.", fg='yellow'))
                    except openai.APIError as e: # Catch other OpenAI specific API errors
                        logger.error(f"Errore API OpenAI per chunk {i+1}: {e}", exc_info=True)
                        click.echo(click.style(f"Errore API OpenAI per chunk {i+1}: {e}. Provo con il prossimo chunk.", fg='red'))
                    except ValueError as e: # E.g. prompt formatting error from within summarize_text
                        logger.error(f"Errore di configurazione/valore per la sintesi del chunk {i+1}: {e}", exc_info=True)
                        click.echo(click.style(f"Errore Configurazione Sintesi chunk {i+1}: {e}. Interrompo sintesi chunk.", fg='red'))
                        break
                    except Exception as e:
                        logger.error(f"Errore imprevisto sintesi chunk {chunk_file_path}: {e}", exc_info=True)
                        click.echo(click.style(f"Errore imprevisto sintesi chunk {i+1}: {e}. Provo con il prossimo chunk.", fg='red'))
                
                if chunk_summaries_paths:
                    logger.info(f"{len(chunk_summaries_paths)} riassunti dei chunk salvati in {summaries_dir}")
                    click.echo(click.style(f"Tutti i riassunti dei chunk ({len(chunk_summaries_paths)}) generati e salvati.", fg='cyan'))
                    ctx.obj['chunk_summaries_paths'] = chunk_summaries_paths
                    ctx.obj['chunk_summaries_content'] = chunk_summaries_content
                else:
                    logger.warning("Nessun riassunto dei chunk è stato salvato.")
                    click.echo(click.style("Nessun riassunto dei chunk è stato salvato.", fg='yellow'))
        
        elif not openai_client:
            logger.info("OpenAI client non disponibile, sintesi LLM dei chunk saltata.")
        elif not saved_chunk_files:
            logger.info("Nessun chunk salvato, sintesi LLM dei chunk saltata.")

        # 5. Aggregate Chunk Summaries (Passo 3.1)
        if ctx.obj.get('chunk_summaries_paths'):
            logger.info("Inizio aggregazione dei riassunti dei chunk.")
            click.echo("Aggregazione dei riassunti dei chunk...")
            aggregated_dir = get_aggregated_summaries_output_dir(input_file)
            aggregated_summaries_file = aggregate_summaries(
                ctx.obj['chunk_summaries_paths'],
                aggregated_dir,
                input_file
            )
            if aggregated_summaries_file:
                logger.info(f"Riassunti dei chunk aggregati con successo in: {aggregated_summaries_file}")
                click.echo(click.style(f"Riassunti aggregati salvati in: {aggregated_summaries_file}", fg='cyan'))
                ctx.obj['aggregated_summaries_file_path'] = aggregated_summaries_file
            else:
                logger.error("Fallimento nell'aggregare i riassunti dei chunk.")
                click.echo(click.style("Errore aggregazione. Controllare i log.", fg='red'))
        else:
            logger.info("Nessun riassunto di chunk disponibile da aggregare.")

        # 6. LLM Final Summarization (Passo 3.2)
        if openai_client and ctx.obj.get('aggregated_summaries_file_path'):
            aggregated_file_path = ctx.obj['aggregated_summaries_file_path']
            logger.info(f"Inizio sintesi finale LLM da: {aggregated_file_path}")
            click.echo(f"Inizio sintesi finale con LLM... " +
                       "Questo potrebbe richiedere tempo.")
            try:
                with open(aggregated_file_path, 'r', encoding='utf-8') as f_agg:
                    aggregated_text = f_agg.read()
                
                if not aggregated_text.strip():
                    logger.warning(f"File riassunti aggregati {aggregated_file_path} è vuoto. Salto sintesi finale.")
                    click.echo(click.style("File riassunti aggregati vuoto. Sintesi finale saltata.", fg='yellow'))
                else:
                    click.echo(f"Invio del testo aggregato all'LLM per la sintesi finale...")
                    final_summary = openai_client.summarize_text(
                        aggregated_text,
                        prompt_instructions=FINAL_SUMMARY_PROMPT_INSTRUCTIONS,
                        model=DEFAULT_FINAL_MODEL,
                        max_tokens_summary=DEFAULT_FINAL_MAX_TOKENS
                    )
                    ctx.obj['final_summary_text'] = final_summary
                    if final_summary:
                        logger.info("Sintesi finale ricevuta dall'LLM.")
                        click.echo(click.style("Sintesi finale generata.", fg='green'))
                    else:
                        logger.warning("La sintesi finale dall'LLM è vuota.")
                        click.echo(click.style("La sintesi finale generata è vuota.", fg='yellow'))

            except openai.AuthenticationError as e:
                logger.error(f"Errore di autenticazione OpenAI per sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Errore Autenticazione OpenAI per sintesi finale: {e}. Verifica la API key.", fg='red'))
            except openai.RateLimitError as e:
                logger.error(f"Rate limit OpenAI per sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Rate Limit OpenAI per sintesi finale: {e}. Riprova più tardi.", fg='red'))
            except openai.APIConnectionError as e:
                logger.error(f"Errore di connessione OpenAI per sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Errore Connessione OpenAI per sintesi finale: {e}. Controlla la rete.", fg='red'))
            except openai.APITimeoutError as e:
                logger.error(f"Timeout OpenAI per sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Timeout OpenAI per sintesi finale: {e}. Riprova.", fg='red'))
            except openai.APIError as e:
                logger.error(f"Errore API OpenAI per sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Errore API OpenAI per sintesi finale: {e}.", fg='red'))
            except ValueError as e: # E.g. prompt formatting error
                logger.error(f"Errore di configurazione/valore per la sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Errore Configurazione Sintesi finale: {e}.", fg='red'))
            except Exception as e:
                logger.error(f"Errore imprevisto durante la sintesi finale: {e}", exc_info=True)
                click.echo(click.style(f"Errore imprevisto durante la sintesi finale: {e}", fg='red'))
        
        elif not openai_client:
            logger.info("OpenAI client non disponibile, sintesi finale LLM saltata.")
            click.echo(click.style("Sintesi finale saltata: client OpenAI non disponibile.", fg='yellow'))
        elif not ctx.obj.get('aggregated_summaries_file_path'):
            logger.info("File dei riassunti aggregati non disponibile, sintesi finale LLM saltata.")
            click.echo(click.style("Sintesi finale saltata: file riassunti aggregati non disponibile.", fg='yellow'))

        # 7. Save Final Summary (Passo 3.3)
        if ctx.obj.get('final_summary_text'):
            logger.info("Inizio salvataggio della sintesi finale.")
            final_output_dir = get_aggregated_summaries_output_dir(input_file) # Save in the same per-file output dir
            saved_final_summary_path = save_final_summary(
                ctx.obj['final_summary_text'],
                final_output_dir,
                input_file
            )
            if saved_final_summary_path:
                logger.info(f"Sintesi finale salvata con successo in: {saved_final_summary_path}")
                click.echo(click.style(f"Sintesi finale salvata in: {saved_final_summary_path}", fg='bright_green'))
                click.echo(click.style("Elaborazione completata con successo!", fg='bright_blue'))
            else:
                logger.error("Fallimento nel salvare la sintesi finale.")
                click.echo(click.style("Errore durante il salvataggio della sintesi finale. Controllare i log.", fg='red'))
        else:
            logger.info("Nessuna sintesi finale disponibile da salvare.")
            # Check if it was because of no API key or other skipped steps
            if not openai_client:
                 click.echo(click.style("Elaborazione terminata. Sintesi finale non generata (API key mancante o client non inizializzato).", fg='yellow'))
            elif not ctx.obj.get('aggregated_summaries_file_path'):
                 click.echo(click.style("Elaborazione terminata. Sintesi finale non generata (nessun riassunto aggregato disponibile).", fg='yellow'))
            else: # Should imply final_summary_text was empty from LLM
                 click.echo(click.style("Elaborazione terminata. La sintesi finale generata era vuota e non è stata salvata.", fg='yellow'))

        # Save full extracted text (optional, consider making it a flag)
        output_dir = "output"
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e:
                logger.warning(f"Impossibile creare la directory di output principale {output_dir}: {e}. Il salvataggio del testo estratto potrebbe fallire.")
        
        if extracted_text.strip(): # Only save if there's content
            base_filename = os.path.splitext(os.path.basename(input_file))[0]
            extracted_text_file = os.path.join(output_dir, f"{base_filename}_extracted.txt")
            try:
                with open(extracted_text_file, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                logger.info(f"Testo estratto completo salvato in: {extracted_text_file}")
                click.echo(f"Testo estratto completo salvato in: {extracted_text_file}")
            except IOError as e:
                logger.error(f"Errore I/O durante il salvataggio del testo estratto completo {extracted_text_file}: {e}", exc_info=True)
                click.echo(click.style(f"Errore salvataggio testo estratto: {e}", fg='yellow'))

    except FileNotFoundError as e:
        logger.error(f"File di input non trovato: {input_file}. Dettagli: {e}", exc_info=True)
        click.echo(click.style(f"Errore: File di input non trovato - {input_file}. Dettagli: {e}", fg='red'), err=True)
        ctx.abort()
    except UnsupportedFileTypeError as e:
        logger.error(f"Tipo di file non supportato per: {input_file}. Dettagli: {e}", exc_info=True)
        click.echo(click.style(f"Errore: Tipo di file non supportato per {input_file}. Dettagli: {e}", fg='red'), err=True)
        ctx.abort()
    except PdfExtractionError as e: 
        logger.error(f"Errore durante l'estrazione del testo dal PDF: {input_file}. Dettagli: {e}", exc_info=True)
        click.echo(click.style(f"Errore estrazione PDF per {input_file}: {e}. Controllare i log.", fg='red'), err=True)
        ctx.abort()
    except EpubExtractionError as e: # Added this block
        logger.error(f"Errore durante l'estrazione del testo da EPUB: {input_file}. Dettagli: {e}", exc_info=True)
        click.echo(click.style(f"Errore estrazione EPUB per {input_file}: {e}. Controllare i log.", fg='red'), err=True)
        ctx.abort()
    except OSError as e:
        # This catches OS errors not caught more specifically by file_utils (which should raise them)
        # or other OS-level issues during main processing stages if any.
        logger.error(f"Errore del sistema operativo durante l'elaborazione di {input_file}: {e}", exc_info=True)
        click.echo(click.style(f"Errore del sistema operativo durante l'elaborazione: {e}. Controllare i log.", fg='red'), err=True)
        ctx.abort()
    except ValueError as e: # Catch other ValueErrors that might propagate (e.g. API key not set and client init was skipped, then used)
        logger.error(f"Errore di valore/configurazione durante l'elaborazione di {input_file}: {e}", exc_info=True)
        click.echo(click.style(f"Errore di configurazione o valore non valido: {e}. Controllare i log.", fg='red'), err=True)
        ctx.abort()
    except Exception as e:
        logger.critical(f"Errore imprevisto e non gestito durante l'elaborazione del file {input_file}: {e}", exc_info=True)
        click.echo(click.style(f"Errore imprevisto e fatale durante l'elaborazione: {e}. Controllare i log per i dettagli.", fg='red'), err=True)
        ctx.abort()

    logger.info(f"Elaborazione del file {input_file} terminata.")

if __name__ == '__main__':
    # This allows running the CLI directly, e.g., python -m src.main process my_book.pdf
    # For a proper package installation, you'd set up an entry point in pyproject.toml or setup.py
    cli() 