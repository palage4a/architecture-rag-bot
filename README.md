# architecture-rag-bot


## parse media wiki

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

Extracts boss pages from Hollow Knight wiki XML dump and converts wikitext to markdown.

Usage:
```bash
python extract_bosses.py [xml_file] [output_dir]
```

- Input: `knowledge_base/source/hollowknight_pages_current.xml`
- Output: `knowledge_base/bosses/` - 47 boss markdown files

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
