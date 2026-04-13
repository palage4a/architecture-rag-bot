import os
import sys
from pathlib import Path
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DIR = "chroma_db"

FEW_SHOT_EXAMPLES = [
    {
        "question": "What attacks does False Knight use?",
        "answer": """Шаг 1: Найду информацию о атаках False Knight в базе знаний.
Шаг 2: В документе указано, что False Knight использует следующие атаки: Leap (прыжок), Charge (заряд), Slam (удар об землю), Leaping Bludgeon (ныряющий удар), и Rage (ярость).
Шаг 3: Основываясь на найденной информации, False Knight имеет 5 основных типов атаки в разных фазах боя."""
    },
    {
        "question": "Where is False Knight located?",
        "answer": """Шаг 1: Найду информацию о местоположении False Knight.
Шаг 2: В документе указано, что False Knight находится в центре Forgotten Crossroads (Забытые Перекрёстки).
Шаг 3: Ответ: False Knight расположен в центре Forgotten Crossroads."""
    }
]

SYSTEM_PROMPT = """Ты - знаток базы знаний. Ты всегда сначала размышляешь, а потом отвечаешь.

Правила:
1. Всегда показывай свои шаги рассуждения (Chain-of-Thought)
2. Используй только информацию из предоставленного контекста
3. Если информации недостаточно, честно скажи "Я не знаю"
4. Отвечай на русском языке

Структура ответа:
Шаг 1: Проанализируй вопрос и найди релевантную информацию
Шаг 2: Извлеки ключевые факты из контекста
Шаг 3: Дай окончательный ответ"""


class RAGBot:
    def __init__(self):
        print("Initializing RAG Bot...")
        self.embeddings = self._load_embeddings()
        self.vectorstore = self._load_vectorstore()
        self.llm = self._init_llm()
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

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not set. Using mock responses for testing.")
            return None

        base_url = os.getenv("OPENAI_API_BASE_URL")
        if not base_url:
            print("WARNING: OPENAI_API_BASE_URL not set. Using mock responses for testing.")
            return None

        return ChatOpenAI(
            model="deepseek-chat",
            # stream_usage=True,
            # temperature=None,
            # max_tokens=None,
            # timeout=None,
            # reasoning_effort="low",
            # max_retries=2,
            api_key=api_key,
            base_url=base_url,
            # organization="...",
            # other params...
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
            return "Я не знаю. Недостаточно информации в базе знаний."

        titles = [doc.metadata.get('title', 'Unknown') for doc in context_docs]
        preview = context_docs[0].page_content[:200]

        return f"""Шаг 1: Найдены релевантные документы: {', '.join(titles)}
Шаг 2: Из контекста: {preview}...
Шаг 3: Для полного ответа нужен API ключ OpenAI. Установите OPENAI_API_KEY."""

    def answer(self, query: str, k: int = 3) -> str:
        """Main method to answer a question."""
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")

        context_docs = self.retrieve(query, k=k)

        if not context_docs:
            return "Я не знаю. Не удалось найти релевантную информацию в базе знаний."

        print(f"Found {len(context_docs)} relevant chunks:")
        for i, doc in enumerate(context_docs, 1):
            title = doc.metadata.get('title', 'Unknown')
            print(f"  {i}. {title}")

        if self.llm is None:
            query_lower = query.lower()

            generic_patterns = ['what is 2+', 'calculate', 'how much is', 'what time',
                              'what day', 'who is ', 'who are ', 'when was', 'where is',
                              'capital of', 'president of', 'weather in']

            for pattern in generic_patterns:
                if pattern in query_lower:
                    return "Я не знаю. Этот вопрос не относится к игре Hollow Knight. Я могу помочь только с информацией о боссах Hollow Knight."

            other_games = ['dark souls', 'elden ring', 'bloodborne', 'sekiro', 'monster hunter',
                          'god of war', ' Zelda', 'mario', 'pokemon', 'final fantasy', 'skyrim',
                          'witcher', ' Resident Evil', 'stardew valley', 'minecraft', 'terraria']

            for game in other_games:
                if game in query_lower:
                    return "Я не знаю. Этот вопрос не относится к игре Hollow Knight. Я могу помочь только с информацией о боссах Hollow Knight."

            hk_keywords = {'hollow knight', 'hollow_knight', 'hallownest', 'infection',
                          'crossroads', 'city of tears', 'greenpath', 'fog canyon',
                          'queens gardens', 'deepnest', 'resting grounds', 'howling cliffs'}

            query_has_hk = any(kw in query_lower for kw in hk_keywords)

        answer = self.generate(query, context_docs)
        return answer


def repl(bot: RAGBot):
    """REPL interface for the bot."""
    print("\n" + "="*60)
    print("Hollow Knight RAG Bot")
    print("Введите ваш вопрос или 'exit' для выхода")
    print("="*60)

    while True:
        try:
            query = input("\n> ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "выход"]:
                print("До свидания!")
                break

            answer = bot.answer(query)
            print(f"\n{answer}")

        except KeyboardInterrupt:
            print("\nДо свидания!")
            break
        except Exception as e:
            print(f"Ошибка: {e}")


def main():
    try:
        bot = RAGBot()
        repl(bot)
    except Exception as e:
        print(f"Error initializing bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
