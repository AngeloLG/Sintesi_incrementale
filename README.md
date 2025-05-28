# Tool di Sintesi Incrementale

## Descrizione

Il "Tool di Sintesi Incrementale" è un\'applicazione a riga di comando (CLI) progettata per elaborare documenti di testo (TXT, PDF, EPUB), estrarne il contenuto, suddividerlo in porzioni gestibili (chunk), generare riassunti di tali porzioni utilizzando un modello linguistico di grandi dimensioni (LLM) fornito da OpenAI, aggregare questi riassunti parziali e, infine, produrre una sintesi finale completa e coerente del documento originale, anch\'essa generata tramite LLM.

L\'obiettivo è fornire uno strumento automatizzato per ottenere una comprensione tematica approfondita di testi lunghi, specialmente libri o documenti estesi.

## Funzionalità Principali

- **Estrazione Testo Multi-Formato**: Supporta file `.txt`, `.pdf`, e `.epub`.
- **Suddivisione Intelligente**: Divide il testo estratto in chunk di circa 10.000 parole, cercando di rispettare i confini di paragrafi e frasi.
- **Sintesi Incrementale**:
  - Genera un riassunto per ogni chunk di testo utilizzando l\'API di OpenAI (default: `gpt-4.1-mini`).
  - Salva i chunk di testo e i loro rispettivi riassunti in file separati.
- **Aggregazione dei Riassunti**: Unisce tutti i riassunti dei chunk in un unico file di testo.
- **Sintesi Finale**: Utilizza l\'LLM per generare una sintesi finale completa (circa 1500 parole) basata sul testo dei riassunti aggregati, salvata in formato Markdown (`.md`).
- **Output Organizzato**: Salva tutti i file generati (testo estratto, chunk, riassunti dei chunk, riassunti aggregati, sintesi finale) in una struttura di directory chiara sotto la cartella `output/nome_file_originale/`.
- **Logging Avanzato**: Registra informazioni dettagliate sull\'esecuzione in console e in un file di log (`logs/app.log`) per il debug.
- **Interfaccia CLI Intuitiva**: Utilizza `click` per una facile interazione da riga di comando.
- **Configurazione API Key**: Permette di specificare la API key di OpenAI tramite opzione CLI o variabile d'ambiente.

## Prerequisiti

- Python 3.8 o superiore.
- Una API key valida di OpenAI.

## Installazione

1.  **Clonare il Repository (o scaricare i file del progetto)**
    Se il progetto è in un repository Git:

    ```bash
    git clone <url_del_repository>
    cd tool_sintesi_incrementale
    ```

    Altrimenti, assicurarsi di avere tutti i file del progetto in una directory locale.

2.  **Creare un Ambiente Virtuale**
    È fortemente raccomandato utilizzare un ambiente virtuale Python. Dalla directory principale del progetto (`tool_sintesi_incrementale`):

    ```bash
    python -m venv venv
    ```

3.  **Attivare l'Ambiente Virtuale**

    - Windows (PowerShell):
      ```powershell
      .\venv\Scripts\Activate.ps1
      ```
    - Windows (cmd.exe):
      ```bash
      .\venv\Scripts\activate.bat
      ```
    - Linux/macOS:
      ```bash
      source venv/bin/activate
      ```

4.  **Installare le Dipendenze**
    Con l'ambiente virtuale attivo, installare le librerie necessarie:
    ```bash
    pip install -r requirements.txt
    ```

## Configurazione

### API Key di OpenAI

Il tool richiede una API key di OpenAI per le funzionalità di sintesi. Puoi configurarla in due modi:

1.  **Variabile d'Ambiente (Raccomandato)**:
    Crea un file `.env` nella directory principale del progetto (`tool_sintesi_incrementale`) con il seguente contenuto:

    ```
    OPENAI_API_KEY="la_tua_vera_api_key"
    ```

    Sostituisci `"la_tua_vera_api_key"` con la tua API key effettiva.

2.  **Opzione CLI**:
    Puoi passare la API key direttamente come opzione al momento dell'esecuzione del comando:
    ```bash
    python -m src.main --api-key="la_tua_vera_api_key" process ...
    ```

Se entrambe sono specificate, l'opzione CLI ha la precedenza sulla variabile d'ambiente per quella specifica esecuzione.

## Utilizzo

Il tool si utilizza tramite la sua interfaccia a riga di comando. Assicurati che l'ambiente virtuale sia attivo e di essere nella directory principale del progetto (`tool_sintesi_incrementale`).

Il punto di ingresso principale è `src/main.py`.

### Comandi Disponibili

1.  **Visualizzare l'Aiuto Generale**:

    ```bash
    python -m src.main --help
    ```

    Questo mostrerà le opzioni globali (come `--api-key` e `--debug`) e i comandi disponibili.

2.  **Comando `process`**:
    Questo è il comando principale per elaborare un file.

    ```bash
    python -m src.main process [OPZIONI] INPUT_FILE
    ```

    - `INPUT_FILE`: Percorso al file di input da processare (es. `documenti/mio_libro.pdf`). Formati supportati: `.txt`, `.pdf`, `.epub`.

    **Aiuto per il comando `process`**:

    ```bash
    python -m src.main process --help
    ```

### Esempio di Esecuzione

```bash
# Esempio con API key da variabile d'ambiente e un file PDF
python -m src.main process percorso/del/tuo/libro.pdf

# Esempio specificando l'API key e abilitando il logging di debug
python -m src.main --api-key="sk-xxxxxxxxxxxxxxx" --debug process altro_documento.epub
```

L'elaborazione potrebbe richiedere tempo, specialmente per file lunghi e a causa delle chiamate all'API LLM.

## Struttura dell'Output

Tutti i file generati durante l'elaborazione vengono salvati nella directory `output/`. Per ogni file di input, viene creata una sottodirectory specifica.

Esempio, per un input `mio_libro.pdf`:

```
output/
└── mio_libro/                              # Directory specifica per il file "mio_libro"
    ├── mio_libro_chunk_001.txt             # Primo chunk di testo
    ├── mio_libro_chunk_002.txt             # Secondo chunk di testo
    │   ...
    ├── summaries/                          # Sottodirectory per i riassunti dei chunk
    │   ├── mio_libro_chunk_001_summary.txt # Riassunto del primo chunk
    │   ├── mio_libro_chunk_002_summary.txt # Riassunto del secondo chunk
    │   ...
    ├── mio_libro_aggregated_summaries.txt  # File con tutti i riassunti dei chunk aggregati
    └── mio_libro_final_summary.md          # Sintesi finale completa in formato Markdown
```

Inoltre, una copia del testo completo estratto dal file originale viene salvata direttamente in `output/mio_libro_extracted.txt`.

## Logging

Il tool utilizza un sistema di logging configurabile:

- **Console**: Messaggi di log a livello `INFO` (o `DEBUG` se si usa l'opzione `--debug`) vengono stampati sulla console durante l'esecuzione.
- **File**: Messaggi di log dettagliati (a livello `DEBUG`) vengono salvati nel file `tool_sintesi_incrementale/src/logs/app.log`. Questo file ruota automaticamente quando raggiunge una certa dimensione.

Il logging su file è particolarmente utile per il debug e per tracciare l'esecuzione in dettaglio.

## Gestione degli Errori

Il tool implementa una gestione degli errori per:

- File non trovati o formati non supportati.
- Errori durante l'estrazione del testo.
- Problemi di scrittura su disco.
- Errori comuni dell'API OpenAI (autenticazione, rate limit, timeout, ecc.).

Messaggi di errore chiari vengono forniti sia in console che nei file di log.

## Esecuzione dei Test

Il progetto include test unitari e di integrazione. Per eseguirli:

1.  Assicurati che l'ambiente virtuale sia attivo e le dipendenze (incluse quelle di test) siano installate.
2.  Dalla directory principale del progetto (`tool_sintesi_incrementale`), esegui:

    Per tutti i test:

    ```bash
    python -m unittest discover tests
    ```

    Per un file di test specifico (es. `test_text_extraction.py`):

    ```bash
    python -m unittest tests.test_text_extraction
    ```

Alcuni test di integrazione o test che interagiscono con API esterne potrebbero richiedere configurazioni specifiche (come API key fittizie o mock) o essere più lenti.
