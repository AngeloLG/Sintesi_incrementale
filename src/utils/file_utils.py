import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def save_text_chunks(chunks: List[str], chunks_dir: str, original_filename: str) -> List[str]:
    """
    Saves a list of text chunks to individual .txt files in the chunks directory.

    Args:
        chunks (list[str]): A list of strings, where each string is a text chunk.
        chunks_dir (str): The directory where to save the chunks (e.g., "output/nome_libro/chunks").
        original_filename (str): The name of the original input file (e.g., "my_book.pdf").

    Returns:
        list[str]: A list of paths to the saved chunk files.
                   Returns an empty list if the input chunks list is empty.
    
    Raises:
        OSError: If there are issues creating directories or writing files.
    """
    if not chunks:
        logger.info("Nessun chunk fornito, nessun file verrà salvato.")
        return []

    try:
        if not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)
            logger.info(f"Creata directory per i chunk: {chunks_dir}")
    except OSError as e:
        logger.error(f"Errore durante la creazione della directory {chunks_dir}: {e}", exc_info=True)
        raise

    saved_paths = []
    for i, chunk_text in enumerate(chunks):
        chunk_filename = f"chunk_{i+1:03d}.txt"
        chunk_filepath = os.path.join(chunks_dir, chunk_filename)
        try:
            with open(chunk_filepath, 'w', encoding='utf-8') as f:
                f.write(chunk_text)
            saved_paths.append(chunk_filepath)
        except IOError as e:
            logger.error(f"Errore I/O durante il salvataggio del chunk {chunk_filepath}: {e}", exc_info=True)
            raise
    
    logger.info(f"{len(saved_paths)} chunks salvati in {chunks_dir}")
    return saved_paths

def aggregate_summaries(summary_file_paths: List[str], summaries_dir: str, original_filename: str) -> Optional[str]:
    """
    Aggrega il contenuto di più file di riassunto di chunk in un unico file di testo.

    Args:
        summary_file_paths (list[str]): Una lista di percorsi ai file di riassunto dei chunk.
        summaries_dir (str): La directory dove salvare il file aggregato dei riassunti.
                           (solitamente output/nome_libro/summaries/)
        original_filename (str): Il nome del file originale.

    Returns:
        str | None: Il percorso al file di testo aggregato se l'operazione ha successo,
                    None altrimenti o in caso di errore.
    """
    if not summary_file_paths:
        logger.info("Nessun percorso di file di riassunto fornito per l'aggregazione.")
        return None

    all_summaries_content = []

    for i, summary_path in enumerate(summary_file_paths):
        try:
            with open(summary_path, 'r', encoding='utf-8') as f_summary:
                content = f_summary.read().strip()
                if content:
                    summary_filename_only = os.path.basename(summary_path)
                    header = f"--- INIZIO RIASSUNTO CHUNK {i+1} ({summary_filename_only}) ---"
                    footer = f"--- FINE RIASSUNTO CHUNK {i+1} ---"
                    all_summaries_content.append(f"{header}\n{content}\n{footer}\n\n")
                else:
                    logger.warning(f"File di riassunto vuoto: {summary_path}. Sarà saltato.")
        except FileNotFoundError:
            logger.warning(f"File di riassunto non trovato: {summary_path}. Sarà saltato.")
        except IOError as e:
            logger.error(f"Errore I/O durante la lettura del file di riassunto {summary_path}: {e}. Sarà saltato.", exc_info=True)

    if not all_summaries_content:
        logger.warning("Nessun contenuto valido trovato nei file di riassunto forniti. File aggregato non creato.")
        return None

    aggregated_text = "".join(all_summaries_content).strip()
    
    if not aggregated_text:
        logger.warning("Il testo aggregato finale è vuoto. File aggregato non creato.")
        return None

    aggregated_filename = "aggregated_summaries.txt"
    aggregated_filepath = os.path.join(summaries_dir, aggregated_filename)

    try:
        if not os.path.exists(summaries_dir):
            os.makedirs(summaries_dir)
            logger.info(f"Creata directory per il file aggregato: {summaries_dir}")
            
        with open(aggregated_filepath, 'w', encoding='utf-8') as f_agg:
            f_agg.write(aggregated_text)
        logger.info(f"Riassunti aggregati salvati in: {aggregated_filepath}")
        return aggregated_filepath
    except (OSError, IOError) as e:
        logger.error(f"Errore durante il salvataggio del file dei riassunti aggregati {aggregated_filepath}: {e}", exc_info=True)
        return None

def save_final_summary(summary_text: str, summaries_dir: str, original_filename: str) -> Optional[str]:
    """
    Salva il testo della sintesi finale in un file Markdown.

    Args:
        summary_text (str): Il testo della sintesi finale.
        summaries_dir (str): La directory dove salvare il file di sintesi finale.
                           (Solitamente output/nome_libro/summaries/)
        original_filename (str): Il nome del file originale.

    Returns:
        str | None: Il percorso al file Markdown della sintesi finale se l'operazione ha successo,
                    None altrimenti o in caso di errore.
    """
    if not summary_text or not summary_text.strip():
        logger.warning("Il testo della sintesi finale è vuoto. Nessun file verrà salvato.")
        return None

    filename_stem = os.path.splitext(os.path.basename(original_filename))[0]
    summary_filename = f"{filename_stem}.md"
    summary_filepath = os.path.join(summaries_dir, summary_filename)

    try:
        if not os.path.exists(summaries_dir):
            os.makedirs(summaries_dir)
            logger.info(f"Creata directory per la sintesi finale: {summaries_dir}")

        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        logger.info(f"Sintesi finale salvata in: {summary_filepath}")
        return summary_filepath
    except (OSError, IOError) as e:
        logger.error(f"Errore durante il salvataggio della sintesi finale {summary_filepath}: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    # Example usage (requires manual creation of a logger if run directly like this)
    if not logging.getLogger().hasHandlers(): # Basic setup for example
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Esecuzione esempio di salvataggio chunks...")
    dummy_chunks = [
        "Questo è il contenuto del primo chunk.\nCon più righe.",
        "Secondo chunk, un po' più corto.",
        "Terzo ed ultimo chunk di testo.\nHa anche questo più righe."
    ]
    original_file_for_example = "libro_esempio.epub"
    output_directory_for_example = "output_example_chunks"

    # Clean up previous example run if it exists
    import shutil
    if os.path.exists(output_directory_for_example):
        shutil.rmtree(output_directory_for_example)
        logger.debug(f"Rimossa directory di esempio precedente: {output_directory_for_example}")

    try:
        saved_files = save_text_chunks(dummy_chunks, output_directory_for_example, original_file_for_example)
        if saved_files:
            logger.info("File salvati con successo:")
            for f_path in saved_files:
                logger.info(f" - {f_path}")
            # Verify content of one file
            with open(saved_files[0], 'r', encoding='utf-8') as f_check:
                logger.info(f"Contenuto verificato di {saved_files[0]}:\n{f_check.read()}")
        else:
            logger.warning("Nessun file è stato salvato dall'esempio.")
    except Exception as e:
        logger.error(f"Errore nell'esecuzione dell'esempio di salvataggio chunks: {e}", exc_info=True)
    finally:
        # Optional: clean up created example directory after run
        # if os.path.exists(output_directory_for_example):
        #     shutil.rmtree(output_directory_for_example)
        #     logger.debug(f"Pulita directory di esempio: {output_directory_for_example}")
        pass
    logger.info("Esempio di salvataggio chunks completato.") 