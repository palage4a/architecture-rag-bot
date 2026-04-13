# architecture-rag-bot

## TL;DR

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python extract_bosses.py

python generate_mapping.py

python rename_bosses.py

python indexing.py build

python indexing.py query "Who the main boss?"

# Set OPENAI_API_KEY and OPENAI_API_BASE_URL.
# Optionally, RAG_BOT_MODEL could be set.
source .env

python rag_bot.py
```

## Project setup

```
python3 -m venv .venv
source .venv/bin/activate

# Instrall dependencies manually
pip install -U langchain \
    langchain-community \
    langchain-huggingface \
    langchain-chroma \
    langchain-openai \
    faker \
    sentence-transformers

# Or use requirements.txt
pip install -r requirements.txt
```

## Task 1: Setup Knowledge Base



---

## Task 2: Distill Knowledge Base

1) Extracts boss pages from Hollow Knight wiki XML dump and converts wikitext to markdown.


```bash
python extract_bosses.py
```

2) Generate boss name mappings:

```bash
python generate_mapping.py
```

3) Rename bosses in all files from knowledge base:


```bash
python rename_bosses.py
```

---

## Task 3: Vector Index for Knowledge Base

1) Build index

```bash
python indexing.py build
```

2) Ask index
```bash
python indexing.py query "Who the main boss?"
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
