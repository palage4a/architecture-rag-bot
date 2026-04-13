import os
import sys
from pathlib import Path
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI


DEFAULT_RAG_BOT_MODEL = 'gpt-4o-mini'
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DIR = "chroma_db"

FEW_SHOT_EXAMPLES = [
    {
        "question": "What attacks does False Knight use?",
        "answer": """Step 1: Find information about False Knight attacks in the knowledge base.
Step 2: The document shows False Knight uses: Leap, Charge, Slam, Leaping Bludgeon, and Rage.
Step 3: Based on the information, False Knight has 5 main attack types in different phases."""
    },
    {
        "question": "Where is False Knight located?",
        "answer": """Step 1: Find information about False Knight location.
Step 2: The document shows False Knight is located in the center of Forgotten Crossroads.
Step 3: Answer: False Knight is located in the center of Forgotten Crossroads."""
    }
]

SYSTEM_PROMPT = """You are a knowledge base assistant. Always think step by step before answering.

Rules:
1. Always show your reasoning steps (Chain-of-Thought)
2. Use only information from the provided context
3. If information is insufficient, honestly say "I don't know"

Response structure:
Step 1: Analyze the question and find relevant information
Step 2: Extract key facts from the context
Step 3: Give the final answer"""


class RAGBot:
    def __init__(self, model):
        print("Initializing RAG Bot...")
        self.embeddings = self._load_embeddings()
        self.vectorstore = self._load_vectorstore()
        self.llm = self._init_llm(model)
        self.prompt = self._create_prompt()

    def _load_embeddings(self):
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"}
        )

    def _load_vectorstore(self):
        print(f"Loading vector store from: {CHROMA_DIR}")
        if not Path(CHROMA_DIR).exists():
            raise ValueError(f"Vector store not found at {CHROMA_DIR}. Run build_index.py first.")
        return Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=self.embeddings
        )

    def _init_llm(self, model):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not set. Using mock responses for testing.")
            return None

        base_url = os.getenv("OPENAI_API_BASE_URL")
        if not base_url:
            print("WARNING: OPENAI_API_BASE_URL not set. Using mock responses for testing.")
            return None

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    def _create_prompt(self):
        example_prompt = ChatPromptTemplate.from_messages([
            ("human", "Q: {question}"),
            ("ai", "{answer}")
        ])

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=FEW_SHOT_EXAMPLES
        )

        final_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            few_shot_prompt,
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])

        return final_prompt

    def retrieve(self, query: str, k: int = 3) -> list:
        """Retrieve relevant chunks from vector store."""
        docs = self.vectorstore.similarity_search(query, k=k)
        return docs

    def generate(self, query: str, context_docs: list) -> str:
        """Generate answer using LLM with context."""
        if self.llm is None:
            return self._mock_response(query, context_docs)

        context = "\n\n".join([
            f"[{doc.metadata.get('title', 'Unknown')}]\n{doc.page_content}"
            for doc in context_docs
        ])

        chain = self.prompt | self.llm
        response = chain.invoke({
            "context": context,
            "question": query
        })

        return response.content

    def _mock_response(self, query: str, context_docs: list) -> str:
        """Mock response when no LLM is available."""
        if not context_docs:
            return "I don't know. Not enough information in the knowledge base."

        titles = [doc.metadata.get('title', 'Unknown') for doc in context_docs]
        preview = context_docs[0].page_content[:200]

        return f"""Step 1: Found relevant documents: {', '.join(titles)}
Step 2: From context: {preview}...
Step 3: For full answer, an OpenAI API key is required. Set OPENAI_API_KEY."""

    def answer(self, query: str, k: int = 3) -> str:
        """Main method to answer a question."""
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")

        context_docs = self.retrieve(query, k=k)

        if not context_docs:
            return "I don't know. Could not find relevant information in the knowledge base."

        print(f"Found {len(context_docs)} relevant chunks:")
        for i, doc in enumerate(context_docs, 1):
            title = doc.metadata.get('title', 'Unknown')
            print(f"  {i}. {title}")

        answer = self.generate(query, context_docs)
        return answer


def repl(bot: RAGBot):
    """REPL interface for the bot."""
    print("\n" + "="*60)
    print("Knowledge base RAG Bot")
    print("Enter your question or 'exit' to quit")
    print("="*60)

    while True:
        try:
            query = input("\n> ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            answer = bot.answer(query)
            print(f"\n{answer}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    try:
        model = os.getenv("RAG_BOT_MODEL", DEFAULT_RAG_BOT_MODEL)
        bot = RAGBot(model)
        repl(bot)
    except Exception as e:
        print(f"Error initializing bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
