# architecture-rag-bot


## Task 1: Setup Knowledge Base

### parse media wiki

start python environment

```
python3 -m venv rag-env
source rag-env/bin/activate
```

get dependencies:

```
# mediawiki-utilities supports XML schema 0.11 in unmerged branches
pip install -qU git+https://github.com/mediawiki-utilities/python-mwtypes@updates_schema_0.11
# mediawiki-utilities mwxml has a bug, fix PR pending
pip install -qU git+https://github.com/gdedrouas/python-mwxml@xml_format_0.11
pip install -qU mwparserfromhell
pip install -qU langchain
pip install -qU langchain-community
```

---

## Task 2: Distill Knowledge Base

1) Extracts boss pages from Hollow Knight wiki XML dump and converts wikitext to markdown.

Usage:
```bash
usage: extract_bosses.py [-h] [xml_file] [output_dir]

Extract all boss pages from Hollow Knight wiki XML dump. Converts wikitext to clean markdown format.

positional arguments:
  xml_file    Path to the XML dump file (default: knowledge_base/source/hollowknight_pages_current.xml)
  output_dir  Output directory for extracted boss markdown files (default: knowledge_base/bosses)

options:
  -h, --help  show this help message and exit

Example: python extract_bosses.py input.xml output_dir
```

2) Generate boss name mappings by using `generate_mapping.py` script:

```bash
$ python generate_mapping.py -h
usage: generate_mapping.py [-h] [--input-dir INPUT_DIR] [--output OUTPUT]

Generate JSON mapping from markdown H1 headings to fake names

options:
  -h, --help            show this help message and exit
  --input-dir INPUT_DIR
                        Directory with markdown files
  --output OUTPUT       Output JSON file
```

---

## Task 3: Vector Index for Knowledge Base

### Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Repository**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **Embedding Size**: 384 dimensions
- **MTEB Score**: ~56.2

### Knowledge Base
- **Source**: `knowledge_base/bosses/` - 47 Hollow Knight boss pages

### Index Statistics
- **Total Documents**: 47
- **Total Chunks**: 112
- **Index Location**: `chroma_db/`
- **Index Size**: 2.4 MB

### Generation Time
- ~4.3 seconds (CPU-only)

### Test Results
The index was tested with 3 queries and returned relevant chunks.

#### Query 1: "How to defeat False Knight?"
- Returns chunks from False Knight page with attack patterns

#### Query 2: "What are Hornet's attacks?"
- Returns chunks from both Hornet Protector and Hornet Sentinel

#### Query 3: "Describe Soul Master's abilities"
- Returns chunks from Soul Master and Soul Tyrant pages

### Usage
```bash
python build_index.py
```

### Files
- `build_index.py` - Index building script
- `chroma_db/` - Persisted ChromaDB index
