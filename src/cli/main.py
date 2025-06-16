import click
import logging
import os
from dotenv import load_dotenv
import openai
from typing import Optional, List, Tuple

from ..utils.logging_config import setup_logging
from ..core.text_extraction import get_text_extractor, UnsupportedFileTypeError, PdfExtractionError, EpubExtractionError
from ..core.text_processing import chunk_text_by_word_limit
from ..utils.file_utils import save_text_chunks, aggregate_summaries, save_final_summary
from ..core.llm_interaction import OpenAIClient, CHUNK_SUMMARY_PROMPT_INSTRUCTIONS, FINAL_SUMMARY_PROMPT_INSTRUCTIONS

# --- Constants ---
BASE_OUTPUT_DIR = "output"
SUMMARIES_SUBDIR = "summaries"
CHUNKS_SUBDIR = "chunks"
DEFAULT_CHUNK_MODEL = "gpt-4.1-mini"
DEFAULT_FINAL_MODEL = "gpt-4.1-mini"
DEFAULT_CHUNK_MAX_TOKENS = 1000
DEFAULT_FINAL_MAX_TOKENS = 4000
DEFAULT_WORD_LIMIT_PER_CHUNK = 10000

# Load environment variables from .env file if it exists
load_dotenv()

# Setup basic logging configuration
# The level can be made configurable later if needed (e.g., via a CLI option)
setup_logging()

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_book_output_dir(input_file: str) -> str:
    """
    Determina la directory principale per il libro.
    Es: output/nome_libro/
    """
    filename_stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(BASE_OUTPUT_DIR, filename_stem)

def get_chunks_dir(input_file: str) -> str:
    """
    Determina la directory per i chunk.
    Es: output/nome_libro/chunks/
    """
    return os.path.join(get_book_output_dir(input_file), CHUNKS_SUBDIR)

def get_summaries_dir(input_file: str) -> str:
    """
    Determina la directory per i riassunti.
    Es: output/nome_libro/summaries/
    """
    return os.path.join(get_book_output_dir(input_file), SUMMARIES_SUBDIR)

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
        book_dir = get_book_output_dir(input_file)
        chunks_dir = get_chunks_dir(input_file)
        
        # Crea la directory principale del libro se non esiste
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)
            logger.info(f"Creata directory principale per il libro: {book_dir}")
        
        saved_chunk_files = save_text_chunks(text_chunks, chunks_dir, input_file)
        
        click.echo(click.style(f"{len(saved_chunk_files)} chunk(s) salvati in '{chunks_dir}'.", fg='cyan'))
        ctx.obj['chunk_file_paths'] = saved_chunk_files
        return saved_chunk_files
    except OSError as e:
        logger.error(f"Errore critico durante il salvataggio dei chunk: {e}. Elaborazione interrotta.", exc_info=True)
        click.echo(click.style(f"Errore critico salvando i chunk: {e}. Interruzione.", fg='red'), err=True)
        ctx.abort()
    except Exception as e:
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
    summaries_dir = get_summaries_dir(input_file)
    
    try:
        if not os.path.exists(summaries_dir):
            os.makedirs(summaries_dir)
            logger.info(f"Creata directory per i riassunti: {summaries_dir}")
    except OSError as e:
        logger.error(f"Errore creazione directory riassunti {summaries_dir}: {e}. Salto sintesi LLM.", exc_info=True)
        click.echo(click.style(f"Errore creazione directory riassunti: {e}. Sintesi LLM saltata.", fg='red'))
        return []

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

            summary_filename = f"chunk_{i+1:03d}_summary.txt"
            summary_filepath = os.path.join(summaries_dir, summary_filename)
            
            try:
                with open(summary_filepath, 'w', encoding='utf-8') as f_summary:
                    f_summary.write(summary)
                chunk_summaries_paths.append(summary_filepath)
                logger.info(f"Riassunto del chunk {i+1} salvato in: {summary_filepath}")
                click.echo(click.style(f"Riassunto del chunk {i+1} salvato.", fg='green'))
            except IOError as e:
                logger.error(f"Errore I/O durante il salvataggio del riassunto del chunk {i+1}: {e}", exc_info=True)
                click.echo(click.style(f"Errore salvataggio riassunto chunk {i+1}: {e}", fg='red'))
                continue
        except Exception as e:
            logger.error(f"Errore durante la sintesi del chunk {i+1}: {e}", exc_info=True)
            click.echo(click.style(f"Errore sintesi chunk {i+1}: {e}", fg='red'))
            continue

    return chunk_summaries_paths

def _perform_final_summary(
    openai_client: OpenAIClient, 
    aggregated_summaries_file_path: Optional[str], 
    input_file: str,
    ctx: click.Context
) -> Optional[str]:
    """
    Genera una sintesi finale a partire dai riassunti aggregati.
    """
    if not aggregated_summaries_file_path or not os.path.exists(aggregated_summaries_file_path):
        logger.warning("Nessun file di riassunti aggregati disponibile per la sintesi finale.")
        return None

    try:
        logger.info("Lettura dei riassunti aggregati per la sintesi finale...")
        with open(aggregated_summaries_file_path, 'r', encoding='utf-8') as f:
            aggregated_text = f.read()

        if not aggregated_text.strip():
            logger.warning("Il file dei riassunti aggregati è vuoto. Sintesi finale non generata.")
            return None

        logger.info("Generazione sintesi finale con LLM...")
        final_summary = openai_client.summarize_text(
            aggregated_text,
            prompt_instructions=FINAL_SUMMARY_PROMPT_INSTRUCTIONS,
            model=DEFAULT_FINAL_MODEL,
            max_tokens_summary=DEFAULT_FINAL_MAX_TOKENS
        )

        if not final_summary or not final_summary.strip():
            logger.warning("La sintesi finale generata è vuota.")
            return None

        # Salva la sintesi finale
        summaries_dir = get_summaries_dir(input_file)
        final_summary_path = save_final_summary(final_summary, summaries_dir, input_file)
        
        if final_summary_path:
            logger.info(f"Sintesi finale salvata in: {final_summary_path}")
            click.echo(click.style("Sintesi finale generata e salvata con successo.", fg='green'))
            return final_summary_path
        else:
            logger.error("Errore durante il salvataggio della sintesi finale.")
            return None

    except Exception as e:
        logger.error(f"Errore durante la generazione della sintesi finale: {e}", exc_info=True)
        click.echo(click.style(f"Errore durante la generazione della sintesi finale: {e}", fg='red'))
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

def _process_single_file(input_file_path: str, ctx: click.Context, openai_client: Optional[OpenAIClient]):
    """
    Processa un singolo file attraverso l'intero flusso di lavoro.
    """
    logger.info(f"--- Elaborazione per: {input_file_path} ---")
    click.echo(f"\n--- Elaborazione per: {input_file_path} ---")

    # Estrai e dividi il testo
    extracted_text, text_chunks = _extract_and_chunk_text(input_file_path)
    
    # Salva il testo estratto completo
    _save_full_extracted_text(extracted_text, input_file_path)
    
    # Salva i chunk in file separati
    saved_chunk_files = _save_text_chunks_to_files(text_chunks, input_file_path, ctx)
    
    if not saved_chunk_files:
        logger.warning("Nessun chunk salvato. Elaborazione interrotta.")
        click.echo(click.style("Nessun chunk salvato. Elaborazione interrotta.", fg='yellow'))
        return

    # Se non c'è un client OpenAI, interrompi qui
    if not openai_client:
        logger.warning("Nessun client OpenAI disponibile. Sintesi LLM saltata.")
        click.echo(click.style("Nessun client OpenAI disponibile. Sintesi LLM saltata.", fg='yellow'))
        return

    # Genera riassunti per ogni chunk
    chunk_summaries_paths = _summarize_all_chunks(openai_client, saved_chunk_files, input_file_path, ctx)
    
    if not chunk_summaries_paths:
        logger.warning("Nessun riassunto di chunk generato. Elaborazione interrotta.")
        click.echo(click.style("Nessun riassunto di chunk generato. Elaborazione interrotta.", fg='yellow'))
        return

    # Aggrega i riassunti
    summaries_dir = get_summaries_dir(input_file_path)
    aggregated_summaries_file = aggregate_summaries(chunk_summaries_paths, summaries_dir, input_file_path)
    
    if not aggregated_summaries_file:
        logger.warning("Nessun file di riassunti aggregati generato. Elaborazione interrotta.")
        click.echo(click.style("Nessun file di riassunti aggregati generato. Elaborazione interrotta.", fg='yellow'))
        return

    # Genera la sintesi finale
    final_summary_file = _perform_final_summary(openai_client, aggregated_summaries_file, input_file_path, ctx)
    
    if not final_summary_file:
        logger.warning("Nessuna sintesi finale generata.")
        click.echo(click.style("Nessuna sintesi finale generata.", fg='yellow'))
    else:
        logger.info(f"Sintesi finale salvata in: {final_summary_file}")
        click.echo(click.style(f"Sintesi finale salvata in: {final_summary_file}", fg='green'))

    logger.info(f"--- Elaborazione per: {input_file_path} completata ---")
    click.echo(f"--- Elaborazione per: {input_file_path} completata ---")

def _save_full_extracted_text(text_content: str, original_input_file_path: str):
    """
    Salva il testo estratto completo in un file nella directory principale del libro.
    """
    if not text_content or not text_content.strip():
        logger.warning("Nessun contenuto testuale da salvare.")
        return None

    try:
        book_dir = get_book_output_dir(original_input_file_path)
        filename_stem = os.path.splitext(os.path.basename(original_input_file_path))[0]
        output_filepath = os.path.join(book_dir, f"{filename_stem}.txt")
        
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)
            logger.info(f"Creata directory principale per il libro: {book_dir}")
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        logger.info(f"Testo estratto completo salvato in: {output_filepath}")
        return output_filepath
    except (OSError, IOError) as e:
        logger.error(f"Errore durante il salvataggio del testo estratto completo {output_filepath}: {e}", exc_info=True)
        return None

def _cleanup_extra_chunks_dir():
    """
    Rimuove la directory chunks extra nella root di output se esiste.
    """
    extra_chunks_dir = os.path.join(BASE_OUTPUT_DIR, "chunks")
    if os.path.exists(extra_chunks_dir):
        try:
            import shutil
            shutil.rmtree(extra_chunks_dir)
            logger.info(f"Rimossa directory chunks extra: {extra_chunks_dir}")
        except OSError as e:
            logger.warning(f"Impossibile rimuovere la directory chunks extra {extra_chunks_dir}: {e}")

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

@cli.command()
@click.argument('input_path', type=click.Path(exists=True, readable=True, dir_okay=True))
@click.pass_context
def process(ctx, input_path):
    """
    Process a single file or all supported files in a directory.
    """
    # Initialize context object if it doesn't exist
    if ctx.obj is None:
        ctx.obj = {}
    
    # Get OpenAI API key from context or environment
    api_key = ctx.obj.get('api_key') or os.getenv('OPENAI_API_KEY')
    
    # Initialize OpenAI client
    openai_client = _initialize_openai_client(api_key)
    
    try:
        if os.path.isfile(input_path):
            _process_single_file(input_path, ctx, openai_client)
        else:
            # Process all supported files in the directory
            for filename in os.listdir(input_path):
                file_path = os.path.join(input_path, filename)
                if os.path.isfile(file_path):
                    try:
                        _process_single_file(file_path, ctx, openai_client)
                    except Exception as e:
                        logger.error(f"Errore durante l'elaborazione di {file_path}: {e}", exc_info=True)
                        click.echo(click.style(f"Errore elaborazione {file_path}: {e}", fg='red'))
                        continue
    finally:
        # Pulizia finale della directory chunks extra
        _cleanup_extra_chunks_dir()

if __name__ == '__main__':
    # This allows running the CLI directly, e.g., python -m src.main process my_book.pdf
    # For a proper package installation, you'd set up an entry point in pyproject.toml or setup.py
    cli() 