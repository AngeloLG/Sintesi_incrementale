# Descrizione Tecnica del Progetto: Tool di Sintesi Incrementale

## Stato Attuale: Setup Iniziale del Progetto

Data: 23 Maggio 2024 (Assumendo la data odierna, da aggiornare se necessario)

### Moduli Implementati

Oltre alla struttura di base del progetto (Passo 1.1), sono stati implementati i seguenti componenti per l'interfaccia CLI e il logging (Passo 1.2):

- **`tool_sintesi_incrementale/src/logging_config.py`**: Un modulo per configurare il sistema di logging standard di Python. Fornisce una funzione `setup_logging()` per inizializzare un logger che scrive su stdout con un formato predefinito (timestamp, nome logger, livello, messaggio).
- **`tool_sintesi_incrementale/src/main.py`**: Il punto di ingresso principale per l'applicazione CLI. Utilizza la libreria `click` per definire:
  - Un gruppo di comandi principale (`cli`).
  - Opzioni globali per `--api-key` (leggibile anche dalla variabile d'ambiente `OPENAI_API_KEY`) e `--debug` (per abilitare il logging a livello DEBUG).
  - Un comando di esempio `process` che accetta un `input_file` come argomento. Al momento, questo comando stampa solo informazioni sull'input ricevuto e sull'API key, ma servirà come base per le funzionalità di elaborazione future.
  - Inizializzazione del logging all'avvio, utilizzando `logging_config.py`.
  - Caricamento di variabili d'ambiente da un file `.env` (se presente) utilizzando `python-dotenv`.

La struttura delle directory e i file di configurazione (`.gitignore`, `requirements.txt`, `__init__.py`) rimangono come definiti nel Passo 1.1.

Oltre ai componenti per CLI e logging (Passo 1.2) e alla struttura di base (Passo 1.1), è stato implementato il **Modulo di Estrazione Testo** (Passo 1.3). Questo modulo è responsabile di leggere il contenuto testuale da diversi tipi di file.

Componenti chiave del modulo di estrazione testo (situati in `tool_sintesi_incrementale/src/text_extraction/`):

- **`base_extractor.py`**: Definisce la classe astratta `TextExtractor` con un metodo `extract(file_path)` che le classi concrete devono implementare.
- **`txt_extractor.py`**: Contiene `TxtExtractor`, una sottoclasse di `TextExtractor` per leggere file di testo semplice (`.txt`).
- **`pdf_extractor.py`**: Contiene `PdfExtractor`, una sottoclasse di `TextExtractor` che utilizza la libreria `PyPDF2` per estrarre testo da file PDF (`.pdf`). Gestisce l'iterazione sulle pagine e la concatenazione del testo. Include logging per pagine senza testo o errori durante l'estrazione da singole pagine.
- **`epub_extractor.py`**: Contiene `EpubExtractor`, una sottoclasse di `TextExtractor` che usa `EbookLib` per leggere la struttura dei file EPUB (`.epub`) e `BeautifulSoup4` per parsare il contenuto HTML degli item del libro ed estrarne il testo.
- **`__init__.py`** (nel package `text_extraction`):
  - Definisce un'eccezione custom: `UnsupportedFileTypeError`.
  - Fornisce una factory function `get_text_extractor(file_path)` che, dato un percorso file, restituisce l'istanza dell'estrattore appropriato in base all'estensione del file (.txt, .pdf, .epub). Solleva `UnsupportedFileTypeError` se il formato non è supportato o `FileNotFoundError` se il file non esiste.

**Aggiornamenti a `requirements.txt`:**

- È stata aggiunta la dipendenza `beautifulsoup4` per il parsing HTML negli EPUB.

**Integrazione in `main.py`:**

- Il comando `process` in `tool_sintesi_incrementale/src/main.py` è stato aggiornato per utilizzare il `get_text_extractor`.
- Ora tenta di estrarre il testo dal file di input fornito.
- Logga l'esito dell'estrazione e mostra i primi 200 caratteri del testo estratto sulla console.
- Salva il testo estratto completo in un file `.txt` nella directory `output/` (es. `nomefileoriginale_extracted.txt`).
- È stata migliorata la gestione degli errori per catturare `FileNotFoundError`, `UnsupportedFileTypeError` ed eccezioni generiche durante l'estrazione.

### Come Funziona

1.  **Selezione Estrattore**: Quando il comando `process` viene invocato con un file di input, chiama `get_text_extractor(input_file)`. Questa funzione analizza l'estensione del file e restituisce un'istanza del parser corretto (`TxtExtractor`, `PdfExtractor`, o `EpubExtractor`).
2.  **Estrazione Testo**: Viene chiamato il metodo `extract()` sull'istanza dell'estrattore ottenuto. Ogni estrattore implementa la logica specifica per il suo formato:
    - `TxtExtractor`: Legge direttamente il contenuto del file.
    - `PdfExtractor`: Usa `PdfReader` di `PyPDF2` per leggere ogni pagina, estrarre il testo e concatenarlo.
    - `EpubExtractor`: Usa `epub.read_epub()` di `EbookLib` per aprire l'EPUB, itera sugli item nello `spine` (contenuti principali), e per ogni item HTML usa `BeautifulSoup` per estrarre il testo pulito.
3.  **Output e Salvataggio**: Il testo estratto viene loggato, una parte viene mostrata a schermo, e l'intero testo viene salvato in un nuovo file `.txt` nella cartella `output/`.
4.  **Gestione Errori**: Se il file non viene trovato, il tipo di file non è supportato, o si verifica un altro errore durante l'estrazione, vengono loggati errori appropriati e messaggi vengono mostrati all'utente.

### Come si Testa o si Esegue

**Prerequisiti:**

1.  Assicurati di avere Python installato.
2.  Crea un ambiente virtuale nella directory `tool_sintesi_incrementale`:
    ```bash
    python -m venv venv
    ```
3.  Attiva l'ambiente virtuale:
    - Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
    - Windows (cmd.exe): `.\venv\Scripts\activate.bat`
    - Linux/macOS: `source venv/bin/activate`
4.  Installa le dipendenze dalla directory principale del progetto (`tool_sintesi_incrementale`):
    ```bash
    pip install -r requirements.txt
    ```

**Esecuzione (dalla directory principale `tool_sintesi_incrementale`):**

Per eseguire il modulo `main.py` direttamente:

1.  **Mostrare l'aiuto:**

    ```bash
    python -m src.main --help
    ```

    Output atteso:

    ```
    Usage: main.py [OPTIONS] COMMAND [ARGS]...

      Tool di Sintesi Incrementale

      Questo strumento permette di generare una sintesi tematica coerente di un
      libro partendo da file PDF, EPUB o TXT.

    Options:
      --api-key TEXT  Your OpenAI API key. Can also be set via OPENAI_API_KEY
                      environment variable.
      --debug         Enable debug logging.
      --help          Show this message and exit.

    Commands:
      process  Processa un file di input (PDF, EPUB, TXT) per la sintesi....
    ```

2.  **Mostrare l'aiuto per il comando `process`:**

    ```bash
    python -m src.main process --help
    ```

    Output atteso:

    ```
    Usage: main.py process [OPTIONS] INPUT_FILE

      Processa un file di input (PDF, EPUB, TXT) per la sintesi. (Funzionalità
      di base, verrà estesa nei prossimi passi)

    Options:
      --help  Show this message and exit.
    ```

3.  **Eseguire il comando `process` (richiede un file fittizio esistente):**

    - Crea un file fittizio, ad esempio `dummy.txt` nella directory `tool_sintesi_incrementale`.
    - Esegui:
      ```bash
      python -m src.main process dummy.txt
      ```
      Output atteso (esempio, il timestamp varierà):
      ```
      2024-05-23 10:30:00 - src.main - INFO - Ricevuto comando 'process' per il file: dummy.txt
      2024-05-23 10:30:00 - src.main - INFO - API Key disponibile nel contesto: No
      Inizio elaborazione del file: dummy.txt
      API Key: Non fornita
      2024-05-23 10:30:00 - src.main - INFO - Elaborazione (placeholder) del file dummy.txt completata.
      ```

4.  **Eseguire con API key e debug:**
    - Puoi creare un file `.env` nella directory `tool_sintesi_incrementale` con il contenuto:
      `OPENAI_API_KEY="la_tua_vera_api_key"`
    - Oppure passare la chiave tramite l'opzione `--api-key`.
    - Esegui (con file fittizio `dummy.txt`):
      ```bash
      python -m src.main --api-key="test_key_123" --debug process dummy.txt
      ```
      Output atteso (esempio):
      ```
      2024-05-23 10:32:00 - src.main - DEBUG - Debug mode enabled.
      2024-05-23 10:32:00 - src.main - DEBUG - OpenAI API key loaded.
      2024-05-23 10:32:00 - src.main - INFO - Ricevuto comando 'process' per il file: dummy.txt
      2024-05-23 10:32:00 - src.main - INFO - API Key disponibile nel contesto: Sì
      Inizio elaborazione del file: dummy.txt
      API Key: ***********
      2024-05-23 10:32:00 - src.main - INFO - Elaborazione (placeholder) del file dummy.txt completata.
      ```

**Test Specifici per i Moduli:**

- **`logging_config.py`**: Si può testare eseguendolo direttamente (`python src/logging_config.py` dalla directory principale del progetto, dopo aver attivato l'ambiente virtuale). Questo stamperà messaggi di log di esempio a vari livelli.

Questo setup fornisce la base per aggiungere comandi più complessi e integrare la logica di business nei passi successivi.

**Esecuzione del Comando `process` (dalla directory principale `tool_sintesi_incrementale`):**

Puoi testare il comando `process` con file di tipo `.txt`, `.pdf`, o `.epub`.

1.  **Crea file di test (o usa i tuoi):**

    - `test.txt`: "Questo è il contenuto di un file di testo di prova."
    - `test.pdf`: Un semplice PDF con testo estraibile.
    - `test.epub`: Un semplice EPUB con testo estraibile.
      Mettili nella directory principale del progetto o fornisci il percorso completo.

2.  **Esegui il comando `process`:**

    ```bash
    # Per un file TXT
    python -m src.main process test.txt

    # Per un file PDF
    python -m src.main process test.pdf

    # Per un file EPUB
    python -m src.main process test.epub

    # Per un file non supportato (es. test.docx, se lo crei)
    # python -m src.main process test.docx
    ```

    L'output mostrerà i log, i primi caratteri del testo estratto (se riuscito), e il percorso del file `.txt` salvato nella cartella `output/`.
    Per i file non supportati o non trovati, verranno mostrati messaggi di errore.

**Esecuzione dei Test Unitari:**

È stato creato un file di test preliminare: `tool_sintesi_incrementale/tests/test_text_extraction.py`.
Questo file include test per la factory `get_text_extractor` e per l'estrazione da file TXT.

Per eseguire i test (dalla directory principale del progetto `tool_sintesi_incrementale`, con ambiente virtuale attivato):

```bash
python -m unittest tests.test_text_extraction
```

I test per PDF ed EPUB in questo file verificano principalmente la corretta selezione dell'estrattore da parte della factory, poiché la creazione programmatica di file PDF/EPUB validi e non banali per i test è complessa. Per testare a fondo l'estrazione da PDF ed EPUB, si dovrebbero usare file di esempio reali e piccoli, inclusi negli asset di test (non implementato in questo script di test base).

La funzione `run_extraction_example()` dentro `test_text_extraction.py` può essere decommentata ed eseguita per vedere un output di esempio (crea un file TXT temporaneo).

Questo modulo ora fornisce la capacità fondamentale di ottenere testo da diverse fonti, preparandolo per le successive fasi di elaborazione.

Oltre ai moduli precedenti (Setup, CLI, Logging, Estrazione Testo - Passi 1.1, 1.2, 1.3), è stato implementato il **Modulo di Suddivisione del Testo (Chunking)** (Passo 2.1).

Componenti chiave del modulo di suddivisione testo (situati in `tool_sintesi_incrementale/src/text_processing/`):

- **`text_chunker.py`**: Contiene la logica per suddividere un testo lungo in porzioni (chunk) più piccole.
  - `count_words(text: str) -> int`: Funzione di utilità per contare le parole in una stringa.
  - `chunk_text_by_word_limit(text: str, word_limit: int = 10000) -> list[str]`: La funzione principale che prende un testo e un limite di parole. Suddivide il testo in una lista di stringhe (i chunk). La strategia cerca di:
    1.  Mantenere interi i paragrafi (delimitati da doppie interruzioni di riga `\n\n`).
    2.  Se un paragrafo supera `word_limit`, tenta di suddividerlo per frasi (basandosi su punteggiatura come `.`, `?`, `!`).
    3.  Se una singola frase supera `word_limit`, la frase viene suddivisa forzatamente al limite di parole.
    4.  Raggruppa paragrafi/frasi successive nello stesso chunk finché il `word_limit` non viene raggiunto.
- **`__init__.py`** (nel package `text_processing`): Esporta la funzione `chunk_text_by_word_limit`.

**Integrazione in `main.py`:**

- Il comando `process` in `tool_sintesi_incrementale/src/main.py` è stato aggiornato per utilizzare la funzione `chunk_text_by_word_limit` dopo l'estrazione del testo.
- Se il testo estratto non è vuoto, viene suddiviso in chunk.
- Il numero di chunk generati e il limite di parole target vengono loggati e mostrati all'utente.
- In modalità debug (`--debug`), vengono loggati anche il numero di parole, il numero di caratteri e un'anteprima di ciascun chunk.
- Il salvataggio effettivo dei chunk in file separati è previsto per il Passo 2.2.

### Come Funziona

1.  **Estrazione Testo**: Come nel Passo 1.3, il testo viene prima estratto dal file di input.
2.  **Controllo Testo Vuoto**: Se il testo estratto è vuoto, la fase di chunking viene saltata.
3.  **Suddivisione in Chunk**: La funzione `chunk_text_by_word_limit` prende il testo estratto.
    - Il testo viene prima diviso in paragrafi.
    - I paragrafi vengono accumulati in un chunk corrente finché l'aggiunta del paragrafo successivo non supererebbe il `word_limit`.
    - Se un paragrafo da solo è più lungo del `word_limit`, viene ulteriormente suddiviso per frasi.
    - Se una frase da sola è più lunga del `word_limit`, viene divisa forzatamente.
    - Questo processo continua finché tutto il testo non è stato assegnato a un chunk.
4.  **Output Informativo**: Il comando `process` della CLI informa l'utente sul numero di chunk creati. In modalità debug, fornisce dettagli su ciascun chunk.

### Come si Testa o si Esegue

**Prerequisiti:**

- Ambiente virtuale attivato e dipendenze installate (come descritto nei passi precedenti).

**Esecuzione del Comando `process` (dalla directory principale `tool_sintesi_incrementale`):**

Usa il comando `process` come prima, con un file di input (`.txt`, `.pdf`, `.epub`).

```bash
python -m src.main process nome_del_tuo_file.pdf
# Oppure con debug per vedere i dettagli dei chunk:
python -m src.main --debug process nome_del_tuo_file.pdf
```

L'output includerà ora informazioni sul numero di chunk generati. Se usi l'opzione `--debug`, vedrai anche dettagli su ogni chunk (conteggio parole, caratteri, anteprima).
Il testo estratto completo continuerà ad essere salvato in `output/nome_del_tuo_file_extracted.txt`.

**Esecuzione dei Test Unitari:**

È stato creato un file di test per il modulo di chunking: `tool_sintesi_incrementale/tests/test_text_chunker.py`.
_(Nota: la creazione di questo file di test ha riscontrato problemi di formattazione con le interruzioni di riga durante i tentativi precedenti. Se i test non dovessero eseguirsi correttamente a causa di ciò, il file potrebbe richiedere una correzione manuale delle interruzioni di riga)._

Per eseguire i test (dalla directory principale del progetto `tool_sintesi_incrementale`, con ambiente virtuale attivato):

```bash
python -m unittest tests.test_text_chunker
```

Questi test verificano la funzione `count_words` e vari scenari della funzione `chunk_text_by_word_limit`, inclusi testi vuoti, testi brevi, suddivisione per limite di parole, gestione di paragrafi lunghi tramite suddivisione per frasi, gestione di frasi molto lunghe, e il rispetto dei confini dei paragrafi.

Con questo passo, l'applicazione è ora in grado di prendere un testo lungo, estrarlo e suddividerlo in porzioni più maneggevoli, pronte per le fasi successive di elaborazione da parte di un LLM.

Oltre ai moduli precedenti (Setup, CLI, Logging, Estrazione Testo, Suddivisione Testo - Passi 1.1, 1.2, 1.3, 2.1), è stato implementato il **Modulo di Gestione delle Porzioni** (Passo 2.2).

Componenti chiave del modulo di gestione porzioni:

- **`tool_sintesi_incrementale/src/file_utils.py`**: Creato questo nuovo modulo per utilità relative ai file.
  - `save_text_chunks(chunks: list[str], base_output_dir: str, original_filename: str) -> list[str]`: Questa funzione è responsabile di salvare una lista di chunk di testo in file `.txt` individuali. Crea una sottodirectory all'interno di `base_output_dir` (generalmente `output/`) nominandola con il nome base del file originale (es. `output/nome_file_originale/`). Ogni chunk viene salvato come `nome_file_originale_chunk_NNN.txt` (es. `output/nome_file_originale/nome_file_originale_chunk_001.txt`). La funzione restituisce una lista dei percorsi ai file dei chunk salvati e gestisce la creazione delle directory necessarie. Solleva `OSError` o altre eccezioni specifiche in caso di problemi di scrittura o creazione directory.

**Integrazione in `main.py`:**

- Il comando `process` in `tool_sintesi_incrementale/src/main.py` è stato aggiornato per utilizzare la funzione `save_text_chunks` dopo la fase di suddivisione del testo (chunking).
- Se sono stati generati dei chunk, `save_text_chunks` viene chiamata per salvarli.
- L'utente viene informato del numero di chunk salvati e della directory in cui sono stati creati.
- I percorsi dei file dei chunk salvati vengono memorizzati nel contesto `ctx.obj['chunk_file_paths']` per un potenziale uso futuro (anche se non ancora utilizzati attivamente).
- Una gestione degli errori più robusta è stata aggiunta per questa fase: se `save_text_chunks` solleva un'eccezione (es. `OSError` per problemi di permessi), l'esecuzione della CLI viene interrotta con `ctx.abort()` per prevenire ulteriori elaborazioni con dati parziali o mancanti.
- Il salvataggio del file di testo estratto completo (es. `output/nome_file_originale_extracted.txt`) è stato mantenuto per ora, ma potrebbe diventare opzionale in futuro.

### Come Funziona

1.  **Estrazione e Chunking**: Come nei passi precedenti. I percorsi dei file dei riassunti dei chunk vengono salvati in `ctx.obj['chunk_summaries_paths']`.
2.  **Controllo Preliminare**: Se non ci sono riassunti di chunk da aggregare, questa fase viene saltata.
3.  **Aggregazione**: La funzione `aggregate_summaries` legge ogni file di riassunto specificato.
4.  **Formattazione**: I contenuti dei riassunti vengono uniti con separatori che indicano l'inizio e la fine di ogni riassunto di chunk, includendo anche il nome del file del chunk per riferimento.
5.  **Salvataggio File Aggregato**: Il testo risultante viene salvato in un unico file `.txt`.
6.  **Output Informativo**: La CLI informa l'utente sulla creazione del file aggregato o su eventuali problemi.

### Come si Testa o si Esegue

**Prerequisiti:**

- Ambiente virtuale attivato e dipendenze installate.

**Esecuzione del Comando `process` (dalla directory principale `tool_sintesi_incrementale`):**

Usa il comando `process` come prima, con un file di input (`.txt`, `.pdf`, `.epub`).

```bash
python -m src.main process nome_del_tuo_file.pdf
# Oppure con debug:
python -m src.main --debug process nome_del_tuo_file.pdf
```

L'output includerà ora un messaggio che conferma il salvataggio dei chunk e la directory in cui si trovano. Controlla la directory `output/` nel tuo progetto. Dovresti trovare una nuova sottodirectory con il nome del tuo file di input (senza estensione), e al suo interno i file `.txt` dei chunk.

**Esempio di Struttura Output:**
Se esegui `python -m src.main process libro_interessante.epub`, potresti trovare:

```
tool_sintesi_incrementale/
├── output/
│   ├── libro_interessante_extracted.txt  (testo completo estratto)
│   └── libro_interessante/
│       ├── libro_interessante_chunk_001.txt
│       │   └── ...
│       ├── summaries/
│       │   ├── libro_interessante_chunk_001_summary.txt
│       │   └── ...
│       ├── libro_interessante_aggregated_summaries.txt
│       └── libro_interessante_final_summary.md  <-- NUOVO FILE MARKDOWN
└── src/
    └── ... (altri file sorgente)
```

**Test Unitari:**

- Il file `tool_sintesi_incrementale/src/file_utils.py` include una sezione `if __name__ == '__main__':` che può essere eseguita direttamente (es. `python src/file_utils.py` dalla root del progetto, con ambiente virtuale attivo) per un semplice test di esempio della funzione `save_text_chunks`. Questo esempio crea una directory `output_example_chunks/` e la popola.
- Per test più formali, si potrebbero aggiungere test unitari specifici per `file_utils.py` in un nuovo file nella directory `tests/` (es. `tests/test_file_utils.py`), mockando le operazioni su file system o usando `tempfile` per creare directory e file temporanei.

Questo passo completa la preparazione dei dati di input per la prima fase di sintesi con LLM, poiché ora abbiamo il testo originale suddiviso e salvato in porzioni gestibili.

Successivamente ai moduli precedenti (Setup, CLI, Logging, Estrazione Testo, Suddivisione Testo, Gestione Porzioni - Passi 1.1, 1.2, 1.3, 2.1, 2.2), è stata implementata l'**Integrazione con LLM (Fase 1 - Sintesi Porzioni)** (Passo 2.3).

Componenti chiave di questa integrazione:

- **`tool_sintesi_incrementale/src/llm_interaction/llm_client.py`**: Creato questo nuovo modulo che contiene la classe `OpenAIClient`.
  - `OpenAIClient(api_key: str)`: Inizializza il client con la API key di OpenAI. Solleva `ValueError` se la chiave non è fornita.
  - `summarize_text(text: str, prompt_instructions: str, model: str, max_tokens_summary: int) -> str`: Invia il testo fornito all'API di OpenAI (modello ChatCompletion) per la sintesi, utilizzando le istruzioni di prompt specificate. Gestisce vari tipi di eccezioni dell'API OpenAI (autenticazione, rate limit, timeout, errori generici) e le solleva nuovamente. Restituisce il testo del riassunto.
  - `CHUNK_SUMMARY_PROMPT_INSTRUCTIONS`: Una costante stringa definita in `llm_client.py` che contiene il prompt di default per la sintesi di un singolo chunk.
- **`tool_sintesi_incrementale/src/llm_interaction/__init__.py`**: Rende `OpenAIClient` e `CHUNK_SUMMARY_PROMPT_INSTRUCTIONS` facilmente importabili.

**Integrazione in `main.py`:**

- Il comando `process` in `tool_sintesi_incrementale/src/main.py` è stato esteso significativamente:
  - **Inizializzazione Client**: All'inizio del comando, se una API key è disponibile (tramite opzione CLI o variabile d'ambiente), viene istanziato `OpenAIClient`. Se l'inizializzazione fallisce (es. API key non valida a priori, anche se `OpenAIClient` attualmente la accetta e l'errore avverrebbe alla prima chiamata), viene loggato un errore, ma il programma cerca di continuare per le operazioni che non richiedono LLM.
  - **Iterazione e Sintesi dei Chunk**: Dopo che i chunk di testo sono stati salvati su file (Passo 2.2):
    - Se il client OpenAI è disponibile e ci sono chunk salvati, il programma procede alla sintesi.
    - Viene creata una nuova sottodirectory `summaries` all'interno della directory specifica del file originale (es. `output/nome_file_originale/summaries/`).
    - Per ogni file di chunk:
      - Il contenuto del chunk viene letto.
      - Se il chunk non è vuoto, viene chiamato `openai_client.summarize_text()` con il testo del chunk e le istruzioni di prompt `CHUNK_SUMMARY_PROMPT_INSTRUCTIONS`. Il modello LLM (ora `gpt-4.1-mini` come default) e il `max_tokens_summary` (impostato a 2000, con l'obiettivo di ottenere circa 1500 parole di output) sono specificati. I modelli GPT-4, come `gpt-4.1-mini`, generalmente offrono finestre di contesto più ampie rispetto a `gpt-3.5-turbo`, il che è vantaggioso per input lunghi come il testo aggregato. Tuttavia, è sempre buona norma verificare i limiti specifici del modello utilizzato e considerare strategie alternative (es. sintesi ricorsiva) per testi eccezionalmente lunghi.
      - Il riassunto restituito dall'LLM viene salvato in un nuovo file `.txt` nella sottodirectory `summaries` (es. `output/nome_file_originale/summaries/nome_file_originale_chunk_001_summary.txt`).
      - Vengono gestiti errori specifici come `FileNotFoundError` per i file dei chunk e eccezioni generiche durante la sintesi di un singolo chunk (incluse quelle sollevate da `OpenAIClient`). L'errore di un chunk non blocca la sintesi dei successivi.
  - **Salvataggio Percorsi e Contenuti**: I percorsi dei file dei riassunti dei chunk e il contenuto testuale dei riassunti vengono salvati in `ctx.obj['chunk_summaries_paths']` e `ctx.obj['chunk_summaries_content']` rispettivamente, per un potenziale uso in fasi successive (come l'aggregazione).
  - **Feedback Utente**: L'utente riceve messaggi informativi sullo stato della sintesi dei chunk, inclusi eventuali errori.

### Come Funziona

1.  **Estrazione, Chunking, Sintesi Chunks**: Come nei passi precedenti. I percorsi dei file dei riassunti dei chunk vengono salvati in `ctx.obj['chunk_summaries_paths']`.
2.  **Controllo Preliminare**: Se non ci sono riassunti di chunk da aggregare, questa fase viene saltata.
3.  **Aggregazione**: La funzione `aggregate_summaries` legge ogni file di riassunto specificato.
4.  **Formattazione**: I contenuti dei riassunti vengono uniti con separatori che indicano l'inizio e la fine di ogni riassunto di chunk, includendo anche il nome del file del chunk per riferimento.
5.  **Salvataggio File Aggregato**: Il testo risultante viene salvato in un unico file `.txt`.
6.  **Output Informativo**: La CLI informa l'utente sulla creazione del file aggregato o su eventuali problemi.

### Come si Testa o si Esegue

**Prerequisiti:**

- Come per il Passo 2.3, è necessario un ambiente configurato con API key OpenAI valida.

**Esecuzione del Comando `process` (dalla directory principale `tool_sintesi_incrementale`):**

L'esecuzione è la stessa del Passo 2.3. Se la sintesi dei chunk ha successo, la fase di aggregazione seguirà automaticamente.

```bash
python -m src.main --api-key="sk-tua_vera_api_key" process nome_del_tuo_file.pdf
```

L'output includerà ora un messaggio che conferma il salvataggio del file dei riassunti aggregati. Controlla la directory `output/nome_file_originale/`. Dovresti trovare un nuovo file chiamato `nome_file_originale_aggregated_summaries.txt`.

**Esempio di Struttura Output Aggiornata (con file aggregato):**
Se esegui `python -m src.main process libro_interessante.epub` (con API key valida), la struttura dell'output sarà:

```
tool_sintesi_incrementale/
├── output/
│   ├── libro_interessante_extracted.txt
│   └── libro_interessante/
│       ├── libro_interessante_chunk_001.txt
│       │   └── ...
│       ├── summaries/
│       │   ├── libro_interessante_chunk_001_summary.txt
│       │   └── ...
│       ├── libro_interessante_aggregated_summaries.txt
│       └── libro_interessante_final_summary.md  <-- NUOVO FILE MARKDOWN
└── src/
    └── ...
```

**Test Specifici per i Moduli:**

- La funzione `aggregate_summaries` in `file_utils.py` può essere testata creando manualmente alcuni file di riassunto fittizi e poi chiamando la funzione in uno script di test separato o nella sezione `if __name__ == '__main__':` del modulo stesso. (Nota: la sezione `if __name__ == '__main__':` di `file_utils.py` non è stata aggiornata per testare specificamente `aggregate_summaries` in questo passaggio, ma potrebbe essere estesa).
- Per test unitari formali, si dovrebbero creare test in `tests/test_file_utils.py` che mockano la lettura dei file o usano `tempfile` per creare file di riassunto temporanei da aggregare.

Questo passo prepara il testo combinato che sarà utilizzato nella successiva fase di sintesi finale da parte dell'LLM.

Dopo l'aggregazione dei riassunti dei chunk (Passo 3.1), è stata implementata l'**Integrazione con LLM per la Sintesi Finale** (Passo 3.2).

Componenti chiave e integrazione:

- **`tool_sintesi_incrementale/src/llm_interaction/llm_client.py`**:
  - È stata aggiunta una nuova costante `FINAL_SUMMARY_PROMPT_INSTRUCTIONS`. Questo prompt è specificamente progettato per guidare l'LLM a sintetizzare un output finale coerente e completo partendo da una collezione di riassunti di chunk. Include istruzioni sulla struttura desiderata (Topics Covered, Key Characters, etc.) e sull'obiettivo di produrre un riassunto di circa 1500 parole in italiano.
- **`tool_sintesi_incrementale/src/llm_interaction/__init__.py`**:
  - La nuova costante `FINAL_SUMMARY_PROMPT_INSTRUCTIONS` è stata esportata per l'utilizzo in altri moduli.
- **`tool_sintesi_incrementale/src/main.py`** (comando `process`):
  - **Lettura Testo Aggregato**: Dopo che il file contenente i riassunti aggregati dei chunk è stato creato (Passo 3.1) e il suo percorso è disponibile in `ctx.obj['aggregated_summaries_file_path']`, il contenuto di questo file viene letto.
  - **Chiamata LLM per Sintesi Finale**: Se il testo aggregato non è vuoto e il client OpenAI è disponibile:
    - Viene effettuata una chiamata a `openai_client.summarize_text()`, passando il testo aggregato e le `FINAL_SUMMARY_PROMPT_INSTRUCTIONS`.
    - Il modello LLM (ora `gpt-4.1-mini` come default) e il `max_tokens_summary` (impostato a 2000, con l'obiettivo di ottenere circa 1500 parole di output) sono specificati. I modelli GPT-4, come `gpt-4.1-mini`, generalmente offrono finestre di contesto più ampie rispetto a `gpt-3.5-turbo`, il che è vantaggioso per input lunghi come il testo aggregato. Tuttavia, è sempre buona norma verificare i limiti specifici del modello utilizzato e considerare strategie alternative (es. sintesi ricorsiva) per testi eccezionalmente lunghi.
  - **Gestione Risposta**: La risposta testuale della sintesi finale viene memorizzata in `ctx.obj['final_summary_text']`.
  - **Errori e Logging**: Vengono gestiti errori come il file dei riassunti aggregati non trovato o vuoto, e è stato aggiunto logging per tracciare questa fase e stimare i token di input.
  - **Struttura Codice**: Il file `main.py` è stato ulteriormente ristrutturato per migliorare la chiarezza e la gestione degli errori, con un blocco `try-except` principale che racchiude l'intero processo di elaborazione del file.

### Come Funziona

1.  **Fasi Precedenti Completate**: Estrazione testo, chunking, sintesi dei chunk, aggregazione, e generazione della sintesi finale da LLM.
2.  **Preparazione Input Finale**: Il contenuto del file `*_aggregated_summaries.txt` viene letto.
3.  **Invio a LLM**: Questo testo aggregato, insieme al `FINAL_SUMMARY_PROMPT_INSTRUCTIONS`, viene inviato all'LLM.
4.  **Generazione Sintesi Finale**: L'LLM elabora i riassunti parziali e genera una sintesi finale coesiva, seguendo le istruzioni del prompt (struttura, lunghezza, lingua).
5.  **Memorizzazione Risultato**: Il testo della sintesi finale viene temporaneamente salvato nel contesto del comando (`ctx.obj`) in attesa del salvataggio su file (Passo 3.3).

### Come si Testa o si Esegue

L'esecuzione è identica a quella del Passo 3.1. Se tutte le fasi precedenti, inclusa l'aggregazione dei riassunti, hanno successo e una API key OpenAI è fornita, il programma procederà automaticamente con la richiesta della sintesi finale.

```bash
python -m src.main --api-key="sk-tua_vera_api_key" process nome_del_tuo_file.pdf
```

L'output della console includerà ora messaggi relativi all'invio del testo aggregato all'LLM per la sintesi finale e una conferma se questa viene generata con successo. Il contenuto effettivo della sintesi finale non viene ancora salvato in un file `.md` dedicato (questo è per il Passo 3.3), ma viene loggato (parzialmente) e memorizzato internamente.

**Considerazioni sui Token:**
Come menzionato, una sfida chiave con questo approccio è il limite di token contestuali dei modelli LLM. Se il libro è molto lungo, il testo aggregato dei riassunti dei chunk potrebbe superare il limite di input del modello scelto. Il passaggio a `gpt-4.1-mini` (o altri modelli GPT-4) aiuta ad alleviare questo problema grazie a finestre di contesto generalmente più grandi (es. 8k, 32k, 128k tokens) rispetto a `gpt-3.5-turbo` (es. 4k, 16k tokens). Tuttavia, per testi estremamente lunghi, anche i limiti dei modelli GPT-4 potrebbero essere raggiunti. In tali casi, tecniche di sintesi gerarchica/ricorsiva o un'ulteriore suddivisione del testo aggregato potrebbero essere necessarie.

Questo passo porta l'applicazione molto vicina al completamento del flusso principale, con la generazione della sintesi finale. Il prossimo passo sarà salvarla correttamente.

Dopo la generazione della sintesi finale (Passo 3.2), è stato implementato il **Modulo di Salvataggio Output Finale** (Passo 3.3).

Componenti chiave e integrazione:

- **`tool_sintesi_incrementale/src/file_utils.py`**:
  - È stata aggiunta una nuova funzione `save_final_summary(summary_text: str, output_dir: str, original_filename: str) -> str | None`.
  - Questa funzione prende il testo della sintesi finale, la directory di output desiderata (tipicamente `output/<nome_file_originale>/`), e il nome del file originale.
  - Crea un nome file per la sintesi finale (es. `<nome_file_originale>_final_summary.md`).
  - Salva il testo della sintesi in questo file Markdown.
  - Restituisce il percorso al file salvato o `None` in caso di errore.
- **`tool_sintesi_incrementale/src/__init__.py`**:
  - La nuova funzione `save_final_summary` è stata esportata per renderla disponibile globalmente all'interno del package `src`.
- **`tool_sintesi_incrementale/src/main.py`** (comando `process`):
  - Dopo aver ottenuto `final_summary_text` da `ctx.obj`, se questo testo esiste e non è vuoto, viene chiamata `save_final_summary`.
  - La directory di output per la sintesi finale è la stessa utilizzata per i riassunti aggregati (determinata da `get_aggregated_summaries_output_dir`).
  - Il salvataggio viene loggato e l'utente viene informato tramite `click.echo` del percorso del file `.md` finale.
  - Il percorso del file della sintesi finale viene memorizzato in `ctx.obj['final_summary_file_path']`.
  - Vengono gestiti eventuali errori durante il salvataggio.

### Come Funziona (Aggiornamento per il Salvataggio Finale)

1.  **Fasi Precedenti Completate**: Estrazione, chunking, sintesi dei chunk, aggregazione, e generazione della sintesi finale da LLM.
2.  **Controllo Sintesi Finale**: Il sistema verifica se `ctx.obj['final_summary_text']` contiene del testo.
3.  **Salvataggio File Markdown**: Se presente, il testo della sintesi finale viene passato a `save_final_summary`.
    - La funzione determina il percorso corretto (es. `output/nome_libro/nome_libro_final_summary.md`).
    - Il testo viene scritto nel file `.md`.
4.  **Feedback Utente**: L'utente viene informato della posizione del file Markdown generato.

### Come si Testa o si Esegue (Aggiornamento per Output Finale)

L'esecuzione del comando `process` rimane la stessa:

```bash
python -m src.main --api-key="sk-tua_vera_api_key" process nome_del_tuo_file.pdf
```

Se tutte le fasi precedenti hanno successo, l'output della console includerà ora un messaggio che indica il percorso del file `.md` contenente la sintesi finale. Controlla la directory `output/nome_file_originale/`. Dovresti trovare un nuovo file chiamato `nome_file_originale_final_summary.md`.

**Esempio di Struttura Output Finale (con file .md):**

```
tool_sintesi_incrementale/
├── output/
│   ├── libro_interessante_extracted.txt
│   └── libro_interessante/
│       ├── libro_interessante_chunk_001.txt
│       │   └── ...
│       ├── summaries/
│       │   ├── libro_interessante_chunk_001_summary.txt
│       │   └── ...
│       ├── libro_interessante_aggregated_summaries.txt
│       └── libro_interessante_final_summary.md  <-- NUOVO FILE MARKDOWN
└── src/
    └── ...
```

**Considerazioni sui Token:**
// ... existing code ...

Usa il comando `process` come prima, con un file di input (`.txt`, `.pdf`, `.epub`).

Oltre ai moduli precedenti (Setup, CLI, Logging iniziale, Estrazione Testo, Chunking del Testo, Salvataggio Chunk, Sintesi LLM dei Chunk, Aggregazione Riassunti, Sintesi LLM Finale, Salvataggio Output Finale - Passi 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3), è stato implementato il **Logging Avanzato** (Passo 4.1).

### Aggiornamento: Logging Avanzato (Passo 4.1)

Il sistema di logging è stato significativamente migliorato per fornire un tracciamento più dettagliato e persistente.

**Componenti Modificati:**

- **`tool_sintesi_incrementale/src/logging_config.py`**:

  - La funzione `setup_logging` ora configura due gestori di log (handler):
    1.  **Console Handler (`StreamHandler`)**: Continua a inviare log all'output standard (console). Il formato è stato reso più conciso per la leggibilità immediata (`%(asctime)s - %(levelname)s - %(name)s - %(message)s`, con `datefmt='%H:%M:%S'`). Il livello di default per la console è `INFO`.
    2.  **File Handler (`RotatingFileHandler`)**: Invia log a un file. Questo handler è configurato per:
        - Salvare i log in una directory `logs/` (creata automaticamente se non esiste) all'interno della directory principale del tool (`tool_sintesi_incrementale/src/logs/app.log`).
        - Ruotare i file di log quando raggiungono una dimensione massima (attualmente 5MB), conservando fino a 3 file di backup.
        - Utilizzare una codifica `utf-8`.
        - Avere un formato di log più dettagliato che include modulo e numero di riga, utile per il debug (`%(asctime)s - %(name)s:%(module)s:%(lineno)d - %(levelname)s - %(message)s`, con `datefmt='%Y-%m-%d %H:%M:%S'`). Il livello di default per il file è `DEBUG`, garantendo che vengano catturate informazioni dettagliate.
  - Il logger radice è impostato al livello `DEBUG` per assicurare che tutti i messaggi inviati ai gestori con livelli appropriati siano processati.
  - La funzione `setup_logging` accetta ora i parametri `console_level` e `file_level` per personalizzare i livelli al momento della chiamata.
  - Include una gestione base degli errori nel caso la directory dei log non possa essere creata, effettuando un fallback a `logging.basicConfig`.

- **`tool_sintesi_incrementale/src/main.py`**:
  - La chiamata iniziale a `setup_logging()` ora utilizza i nuovi livelli di default (INFO per console, DEBUG per file).
  - Quando viene usata l'opzione `--debug` dalla CLI, `setup_logging(logging.DEBUG)` viene chiamato, il che imposta efficacemente sia la console che il file handler al livello `DEBUG` (poiché `file_level` di default è già `DEBUG` e `console_level` viene sovrascritto). Questo comportamento è in linea con l'obiettivo di avere un output più verboso in modalità debug.

**Come Funziona Ora il Logging:**

1.  All'avvio dell'applicazione (`python -m src.main ...`), la funzione `setup_logging()` in `logging_config.py` viene chiamata da `main.py`.
2.  Questa configura il logger radice e aggiunge i due handler (console e file) con i loro rispettivi livelli e formati.
3.  Tutti i messaggi di log emessi dall'applicazione usando il modulo standard `logging` (es. `logger.info(...)`, `logger.debug(...)`) verranno ora processati da entrambi gli handler.
4.  La console mostrerà i log a partire dal livello `INFO` (o `DEBUG` se `--debug` è specificato).
5.  Il file `tool_sintesi_incrementale/src/logs/app.log` conterrà tutti i log a partire dal livello `DEBUG`, fornendo una traccia dettagliata dell'esecuzione per analisi post-mortem o debug approfondito.

**Come si Testa o si Esegue:**

- L'esecuzione del tool rimane invariata.
- Dopo aver eseguito un comando (es. `python -m src.main process mio_file.pdf`), si dovrebbe osservare:
  - L'output della console con i messaggi di log (a livello INFO o DEBUG).
  - La creazione (o aggiornamento) del file `tool_sintesi_incrementale/src/logs/app.log` con i log dettagliati.
- Eseguendo `python -m src.logging_config` direttamente (dalla directory `tool_sintesi_incrementale/src`), si possono vedere esempi di output dei log e verrà creato/aggiornato il file di log con i messaggi di test di quel modulo.

Questa configurazione avanzata del logging migliora la capacità di monitorare e diagnosticare il comportamento del tool.

### Aggiornamento: Gestione Errori Complessiva (Passo 4.2)

La gestione degli errori è stata rivista e migliorata in tutto il flusso applicativo per fornire maggiore robustezza e messaggi più chiari all'utente.

**Modifiche Chiave Apportate:**

- **`tool_sintesi_incrementale/src/main.py`**:

  - Migliorata la gestione delle eccezioni specifiche sollevate durante le interazioni con l'API OpenAI (es. `openai.APIAuthenticationError`, `openai.RateLimitError`, `openai.APIConnectionError`, `openai.APITimeoutError`, `openai.APIError`). Ora vengono forniti messaggi utente più specifici per ciascuno di questi errori, sia durante la sintesi dei singoli chunk che per la sintesi finale.
  - Per errori critici come `APIAuthenticationError` o `RateLimitError` durante la sintesi dei chunk, il ciclo di sintesi dei chunk viene interrotto per evitare tentativi ripetuti e costosi.
  - Rafforzati i messaggi utente e il logging nel blocco `try-except` principale che avvolge l'intero processo, per fornire maggiore contesto in caso di `FileNotFoundError`, `UnsupportedFileTypeError`, `OSError`, `ValueError`, e eccezioni generiche.
  - Aggiunti messaggi utente più chiari quando determinate fasi (es. sintesi LLM) vengono saltate a causa della mancanza della API key o di errori nelle fasi precedenti.

- **`tool_sintesi_incrementale/src/text_extraction/`**:

  - Introdotte eccezioni personalizzate più specifiche: `PdfExtractionError` e `EpubExtractionError`.
  - I moduli `pdf_extractor.py` e `epub_extractor.py` ora sollevano queste eccezioni specifiche invece di `Exception` generiche quando si verificano problemi durante l'elaborazione di file PDF o EPUB. Questo permette a `main.py` di intercettarle e fornire feedback utente più mirato.
  - Aggiunto `exc_info=True` a diverse chiamate `logger.error()` per includere lo stack trace completo nei log su file, facilitando il debug.

- **Altri Moduli (`text_processing`, `llm_interaction`, `file_utils`)**:
  - La revisione ha confermato che la gestione degli errori in questi moduli era già relativamente robusta. `llm_client.py` già sollevava eccezioni OpenAI specifiche. `file_utils.py` gestisce errori I/O sollevando `OSError` per problemi critici (che `main.py` intercetta) o restituendo `None` per errori non bloccanti (es. un singolo file di riassunto mancante durante l'aggregazione), permettendo a `main.py` di gestire il flusso di conseguenza.

**Strategia Generale Adottata:**

- **Errori Critici vs. Non Critici**: Viene fatta una distinzione tra errori che devono interrompere l'intero processo (es. file di input non trovato, API key non valida, impossibilità di scrivere file di output essenziali) e quelli che possono permettere una continuazione parziale o un graceful degradation (es. fallimento nella sintesi di un singolo chunk, un file di riassunto mancante durante l'aggregazione).
- **Feedback Utente Chiaro**: La CLI ora fornisce messaggi più specifici e colorati (tramite `click.style`) per distinguere successi, avvisi ed errori.
- **Logging Dettagliato**: Gli errori vengono loggati con dettagli sufficienti (spesso con `exc_info=True`) per facilitare il debug tramite i file di log (`logs/app.log`).

Questi miglioramenti contribuiscono a rendere il tool più resiliente e user-friendly.

### Aggiornamento: Revisione Codice e Aderenza Principi (Passo 4.4)

È stata effettuata una revisione complessiva del codice sorgente con l'obiettivo di migliorarne la struttura, la leggibilità, la manutenibilità e l'aderenza ai principi SOLID e Clean Code.

**Modifiche e Osservazioni Chiave per Modulo:**

- **`tool_sintesi_incrementale/src/main.py`**:

  - **Refactoring Significativo**: La funzione principale `process` è stata scomposta estraendo la logica per le diverse fasi (inizializzazione client, estrazione e chunking, salvataggio chunk, sintesi dei chunk, sintesi finale, salvataggio finale) in funzioni helper private (es. `_initialize_openai_client`, `_extract_and_chunk_text`, `_summarize_all_chunks`, etc.). Questo ha reso la funzione `process` un orchestratore più snello e leggibile.
  - **Costanti**: Introdotti costanti a livello di modulo per parametri di default dell'LLM (modelli, max token), percorsi di output (`BASE_OUTPUT_DIR`), e nomi di sottodirectory (`SUMMARIES_SUBDIR`), migliorando la configurabilità e riducendo stringhe/numeri magici.
  - **Logica dei Percorsi**: Centralizzata la determinazione dei percorsi di output specifici per file tramite la nuova funzione helper `get_per_file_output_dir`.
  - **Pulizia**: Rimosse variabili non utilizzate e codice commentato obsoleto.
  - **Aderenza SOLID**: Il refactoring migliora ulteriormente l'SRP della funzione `process` e delle sue helper. L'uso di factory per l'estrazione del testo e la configurazione chiara del client LLM supportano OCP e DIP.

- **`tool_sintesi_incrementale/src/text_processing/text_chunker.py`**:

  - **Refactoring**: La logica complessa per la suddivisione dei paragrafi troppo lunghi (prima per frasi, poi forzatamente per parole) è stata estratta dalla funzione principale `chunk_text_by_word_limit` nella nuova funzione helper privata `_split_long_paragraph`. Questo ha migliorato notevolmente la leggibilità della funzione principale.
  - **Regex Migliorata**: Affinata la regex per la suddivisione delle frasi per una maggiore precisione.
  - **Chiarezza**: Migliorata la gestione della ricostruzione dei paragrafi per preservare la formattazione.

- **`tool_sintesi_incrementale/src/llm_interaction/llm_client.py`**:

  - **Prompt**: Corretto un piccolo refuso nel conteggio delle parole dell'output di esempio nel `FINAL_SUMMARY_PROMPT_INSTRUCTIONS` per coerenza.
  - **Struttura**: Il codice è risultato ben strutturato, con chiare responsabilità per l'inizializzazione e il metodo `summarize_text`. Buona gestione degli errori specifici dell'API OpenAI.

- **`tool_sintesi_incrementale/src/file_utils.py`**:

  - **Chiarezza e Robustezza**: Le funzioni sono risultate ben definite, con docstring completi e una buona gestione degli errori (restituendo `None` o sollevando eccezioni appropriate che `main.py` può gestire).
  - **Logica dei Percorsi**: La logica di creazione delle directory è coerente con le aspettative di `main.py` dopo il suo refactoring.
  - Non sono state necessarie modifiche significative, confermando la buona qualità iniziale del modulo.

- **`tool_sintesi_incrementale/src/text_extraction/*`** (inclusi `__init__.py`, `base_extractor.py`, e i vari estrattori specifici):

  - Questi moduli erano già stati rivisti durante la fase di gestione errori (Passo 4.2) e trovati conformi ai principi di OCP (grazie all'architettura basata su `TextExtractor` e factory) e SRP (ogni estrattore fa una cosa).
  - Le eccezioni personalizzate (`PdfExtractionError`, `EpubExtractionError`) migliorano la gestione errori.

- **`tool_sintesi_incrementale/src/logging_config.py`**:
  - Revisionato durante il Passo 4.1, fornisce una configurazione flessibile e robusta per il logging su console e file.

**Commenti Inline:**

- I docstring sono stati verificati e sono generalmente completi e chiari in tutti i moduli.
- Commenti inline sono presenti dove spiegano logiche non immediatamente ovvie o decisioni di progettazione.

Questa revisione ha contribuito a consolidare la qualità del codice, rendendolo più facile da comprendere, testare e far evolvere in futuro.

### Aggiornamento: Documentazione Utente (Passo 4.5)

È stata creata una documentazione utente completa sotto forma di file `README.md` nella directory principale del progetto (`tool_sintesi_incrementale/README.md`).

Il `README.md` include le seguenti sezioni principali:

- **Descrizione**: Una panoramica generale del tool e dei suoi obiettivi.
- **Funzionalità Principali**: Un elenco delle capacità chiave del software.
- **Prerequisiti**: Software e requisiti necessari prima dell'installazione (Python, API key OpenAI).
- **Installazione**: Istruzioni passo-passo per configurare l'ambiente, inclusa la creazione di un ambiente virtuale e l'installazione delle dipendenze da `requirements.txt`.
- **Configurazione**: Come impostare l'API key di OpenAI (tramite file `.env` o opzione CLI).
- **Utilizzo**: Dettagli su come eseguire il tool dalla riga di comando, inclusi esempi dei comandi principali (`--help`, `process`) e opzioni (`--api-key`, `--debug`).
- **Struttura dell'Output**: Una descrizione di come i file generati sono organizzati nella directory `output/`.
- **Logging**: Spiegazione di come funziona il logging su console e su file.
- **Gestione degli Errori**: Breve menzione di come il tool gestisce gli errori comuni.
- **Esecuzione dei Test**: Istruzioni su come eseguire i test unitari e di integrazione inclusi nel progetto.

Questa documentazione serve come guida completa per gli utenti che desiderano installare, configurare ed eseguire il "Tool di Sintesi Incrementale".
