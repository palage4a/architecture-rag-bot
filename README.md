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
pip install -qU langchain-huggingface
pip install -qU langchain-chroma
```

---

## Task 2: Distill Knowledge Base

1) Extracts boss pages from Hollow Knight wiki XML dump and converts wikitext to markdown.


Get help:

```bash
python extract_bosses.py -h
```

Usage:

```bash
python extract_bosses.py
```

2) Generate boss name mappings by using `generate_mapping.py` script:

Get help:

```bash
python generate_mapping.py -h
```

Usage:

```bash
python generate_mapping.py
```

---

## Task 3: Vector Index for Knowledge Base

Get help:

```bash
python indexing.py -h
python indexing.py build -h
python indexing.py query -h
```

### Build Index
```bash
python indexing.py build --input-dir knowledge_base/bosses --output-dir chroma_db
```

### Query Index
```bash
python indexing.py query "How to defeat John Snow?" --top-k 5
```

### Interactive Python Inspection
```python
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

# Search
results = db.similarity_search("How to defeat Hornet?", k=3)
for doc in results:
    print(doc.metadata["title"])
    print(doc.page_content[:200])
```
