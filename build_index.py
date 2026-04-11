import os
import time
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
KNOWLEDGE_BASE_DIR = "knowledge_base/bosses"
CHROMA_DIR = "chroma_db"


def load_documents() -> list[Document]:
    """Load markdown documents from knowledge base."""
    docs = []
    base_path = Path(KNOWLEDGE_BASE_DIR)
    for md_file in base_path.glob("*.md"):
        try:
            loader = TextLoader(str(md_file), encoding="utf-8")
            doc = loader.load()[0]
            doc.metadata["title"] = md_file.stem.replace("_", " ")
            doc.metadata["source_file"] = md_file.name
            docs.append(doc)
        except Exception as e:
            print(f"Error loading file {md_file.name}: {e}")
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=lambda x: len(x.split())
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def create_embeddings():
    """Initialize embedding model."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )


def build_index(docs: list[Document], embeddings) -> Chroma:
    """Build vector index using ChromaDB."""
    print(f"Creating index with {len(docs)} chunks...")
    start_time = time.time()
    
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    elapsed = time.time() - start_time
    print(f"Index created in {elapsed:.2f} seconds")
    return vectorstore


def test_search(vectorstore: Chroma, query: str, k: int = 3):
    """Test search with a query."""
    print(f"\n--- Test query: '{query}' ---")
    results = vectorstore.similarity_search(query, k=k)
    for i, doc in enumerate(results, 1):
        title = doc.metadata.get("title", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "?")
        print(f"{i}. [{title}] (chunk {chunk_id})")
        print(f"   {doc.page_content[:200]}...")
    return results


def main():
    print("=" * 60)
    print("Task 3: Build Vector Index")
    print("=" * 60)
    
    print("\n1. Loading documents...")
    docs = load_documents()
    print(f"   Loaded {len(docs)} documents")
    
    print("\n2. Splitting into chunks...")
    chunks = split_documents(docs)
    print(f"   Created {len(chunks)} chunks")
    
    print("\n3. Loading embedding model...")
    print(f"   Model: {EMBEDDING_MODEL}")
    embeddings = create_embeddings()
    
    print("\n4. Building index...")
    vectorstore = build_index(chunks, embeddings)
    
    print("\n5. Testing search...")
    test_queries = [
        "How to defeat False Knight?",
        "What are Hornet's attacks?",
        "Describe Soul Master's abilities"
    ]
    for query in test_queries:
        test_search(vectorstore, query, k=2)
    
    print("\n" + "=" * 60)
    print("Index built successfully!")
    print(f"   Location: {CHROMA_DIR}")
    print(f"   Model: {EMBEDDING_MODEL}")
    print(f"   Total chunks: {len(chunks)}")
    print("=" * 60)


if __name__ == "__main__":
    main()