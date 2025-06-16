# Tool di Sintesi Incrementale e Estrazione Testo

## Descrizione

Questo repository contiene due tool distinti:

1. **Tool di Sintesi Incrementale**: Un'applicazione CLI che elabora documenti di testo (TXT, PDF, EPUB), estrae il contenuto, lo suddivide in porzioni gestibili, genera riassunti utilizzando un LLM di OpenAI, e produce una sintesi finale completa.

2. **Tool di Estrazione Testo**: Un'applicazione CLI standalone che si concentra solo sull'estrazione del testo da documenti (TXT, PDF, EPUB), utile quando non è necessaria la sintesi.

## Tool di Estrazione Testo

### Descrizione

Il tool di estrazione testo è un'applicazione CLI standalone che permette di estrarre il contenuto testuale da file in vari formati (TXT, PDF, EPUB) senza procedere con la sintesi.

### Funzionalità Principali

- **Estrazione Testo Multi-Formato**: Supporta file `.txt`, `.pdf`, e `.epub`
- **Output Configurabile**: Permette di specificare la directory di output
- **Gestione Errori**: Fornisce messaggi di errore chiari per vari scenari

### Prerequisiti

- Python 3.8 o superiore
- Le dipendenze elencate in `requirements.txt`

### Installazione

1. **Clonare il Repository**

   ```bash
   git clone <url_del_repository>
   cd tool_sintesi_incrementale
   ```

2. **Creare e Attivare l'Ambiente Virtuale**

   ```bash
   python -m venv venv
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # Windows (cmd.exe)
   .\venv\Scripts\activate.bat
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Installare le Dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

### Utilizzo

Il tool si utilizza tramite la sua interfaccia a riga di comando. Assicurati che l'ambiente virtuale sia attivo e di essere nella directory principale del progetto.

#### Comandi Disponibili

```bash
python -m src.cli.extract_text [OPZIONI] INPUT_FILE
```

**Opzioni:**

- `--output-dir TEXT`: Directory dove salvare il testo estratto (default: `extracted_texts_output/`)
- `--help`: Mostra il messaggio di aiuto

#### Esempi di Utilizzo

```bash
# Estrazione con directory di output predefinita
python -m src.cli.extract_text mio_libro.pdf

# Estrazione specificando una directory di output
python -m src.cli.extract_text --output-dir="miei_testi" mio_libro.epub
```

### Struttura dell'Output

Il testo estratto viene salvato nella directory specificata (o in `extracted_texts_output/` se non specificata) con il seguente formato:

```
extracted_texts_output/
└── nome_file_originale_extracted.txt
```

### Gestione degli Errori

Il tool gestisce i seguenti casi:

- File non trovato
- Formato file non supportato
- Errori durante l'estrazione del testo
- Problemi di scrittura su disco

Messaggi di errore chiari vengono mostrati in console per aiutare l'utente a risolvere eventuali problemi.

### Test

Per eseguire i test del tool di estrazione:

```bash
# Test con file TXT
python -m src.cli.extract_text test.txt

# Test con file PDF
python -m src.cli.extract_text test.pdf

# Test con file EPUB
python -m src.cli.extract_text test.epub
```

## Tool di Sintesi Incrementale

### Descrizione

Il tool di sintesi incrementale è un'applicazione CLI che elabora documenti di testo, estrae il contenuto, lo suddivide in porzioni gestibili, genera riassunti utilizzando un LLM di OpenAI, e produce una sintesi finale completa.

### Funzionalità Principali

- **Estrazione Testo Multi-Formato**: Supporta file `.txt`, `.pdf`, e `.epub`
- **Suddivisione Intelligente**: Divide il testo in chunk di circa 10.000 parole
- **Sintesi Incrementale**: Genera riassunti per ogni chunk usando l'API di OpenAI
- **Aggregazione dei Riassunti**: Unisce tutti i riassunti in un unico file
- **Sintesi Finale**: Produce una sintesi finale completa in formato Markdown

### Prerequisiti

- Python 3.8 o superiore
- Una API key valida di OpenAI
- Le dipendenze elencate in `requirements.txt`

### Installazione

1. **Clonare il Repository**

   ```bash
   git clone <url_del_repository>
   cd tool_sintesi_incrementale
   ```

2. **Creare e Attivare l'Ambiente Virtuale**

   ```bash
   python -m venv venv
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # Windows (cmd.exe)
   .\venv\Scripts\activate.bat
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Installare le Dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

### Configurazione

#### API Key di OpenAI

Il tool richiede una API key di OpenAI. Puoi configurarla in due modi:

1. **Variabile d'Ambiente (Raccomandato)**:
   Crea un file `.env` nella directory principale del progetto con:

   ```
   OPENAI_API_KEY="la_tua_vera_api_key"
   ```

2. **Opzione CLI**:
   Passa la API key direttamente come opzione:
   ```bash
   python -m src.cli.main --api-key="la_tua_vera_api_key" process ...
   ```

### Utilizzo

#### Comandi Disponibili

1. **Visualizzare l'Aiuto Generale**:

   ```bash
   python -m src.cli.main --help
   ```

2. **Comando `process`**:
   ```bash
   python -m src.cli.main process [OPZIONI] INPUT_FILE
   ```

### Struttura dell'Output

Tutti i file generati vengono salvati nella directory `output/`. Per ogni file di input, viene creata una sottodirectory specifica:

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

### Logging

Il tool utilizza un sistema di logging configurabile:

- **Console**: Messaggi di log a livello `INFO` (o `DEBUG` se si usa `--debug`)
- **File**: Messaggi di log dettagliati in `logs/app.log`

### Gestione degli Errori

Il tool gestisce:

- File non trovati o formati non supportati
- Errori durante l'estrazione del testo
- Problemi di scrittura su disco
- Errori dell'API OpenAI

### Test

Per eseguire i test:

```bash
# Tutti i test
python -m unittest discover tests

# Test specifici
python -m unittest tests.test_text_extraction
```

```

```
