import argparse
import time
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_KNOWLEDGE_BASE_DIR = "knowledge_base"
DEFAULT_CHROMA_DIR = "chroma_db"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_TOP_K = 3


def load_documents(knowledge_base_dir: str) -> list[Document]:
    """Load markdown documents from knowledge base."""
    docs = []
    base_path = Path(knowledge_base_dir)
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


def split_documents(docs: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda x: len(x.split())
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def create_embeddings(model_name: str, device: str = "cpu"):
    """Initialize embedding model."""
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device}
    )


def build_index(docs: list[Document], embeddings, chroma_dir: str) -> Chroma:
    """Build vector index using ChromaDB."""
    print(f"Creating index with {len(docs)} chunks...")
    start_time = time.time()

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=chroma_dir
    )

    elapsed = time.time() - start_time
    print(f"Index created in {elapsed:.2f} seconds")
    return vectorstore


def load_index(embeddings, chroma_dir: str) -> Chroma:
    """Load existing vector index from ChromaDB."""
    return Chroma(
        persist_directory=chroma_dir,
        embedding_function=embeddings
    )


def search_index(vectorstore: Chroma, query: str, k: int = 3):
    """Search index with a query."""
    print(f"\n--- Query: '{query}' ---")
    results = vectorstore.similarity_search(query, k=k)
    for i, doc in enumerate(results, 1):
        title = doc.metadata.get("title", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "?")
        print(f"{i}. [{title}] (chunk {chunk_id})")
        print(f"   {doc.page_content[:200]}...")
    return results


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Build and query vector index for knowledge base"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    build_parser = subparsers.add_parser("build", help="Build vector index")
    build_parser.add_argument(
        "--input-dir", "-i",
        default=DEFAULT_KNOWLEDGE_BASE_DIR,
        help=f"Input directory with markdown files (default: {DEFAULT_KNOWLEDGE_BASE_DIR})"
    )
    build_parser.add_argument(
        "--output-dir", "-o",
        default=DEFAULT_CHROMA_DIR,
        help=f"Output directory for ChromaDB index (default: {DEFAULT_CHROMA_DIR})"
    )
    build_parser.add_argument(
        "--model", "-m",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Embedding model name (default: {DEFAULT_EMBEDDING_MODEL})"
    )
    build_parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size in words (default: {DEFAULT_CHUNK_SIZE})"
    )
    build_parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Chunk overlap in words (default: {DEFAULT_CHUNK_OVERLAP})"
    )
    build_parser.add_argument(
        "--device",
        default="cpu",
        help="Device for embeddings (default: cpu)"
    )

    query_parser = subparsers.add_parser("query", help="Query existing index")
    query_parser.add_argument(
        "query",
        help="Search query string"
    )
    query_parser.add_argument(
        "--index-dir", "-i",
        default=DEFAULT_CHROMA_DIR,
        help=f"ChromaDB index directory (default: {DEFAULT_CHROMA_DIR})"
    )
    query_parser.add_argument(
        "--model", "-m",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Embedding model name (default: {DEFAULT_EMBEDDING_MODEL})"
    )
    query_parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Number of results (default: {DEFAULT_TOP_K})"
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "build":
        docs = load_documents(args.input_dir)
        if not docs:
            print(f"No documents found in {args.input_dir}")
            return

        chunks = split_documents(docs, args.chunk_size, args.chunk_overlap)
        embeddings = create_embeddings(args.model, args.device)
        vectorstore = build_index(chunks, embeddings, args.output_dir)

        print("\n" + "=" * 60)
        print("Index built successfully!")
        print(f"   Location: {args.output_dir}")
        print(f"   Model: {args.model}")
        print(f"   Total chunks: {len(chunks)}")
        print("=" * 60)

    elif args.command == "query":
        embeddings = create_embeddings(args.model)
        vectorstore = load_index(embeddings, args.index_dir)
        search_index(vectorstore, args.query, args.top_k)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()