from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings


def get_llm_openai(temperature: float = 0.0) -> ChatOpenAI:
    """GPT-4o-mini — extraction (vision) et fallback général."""
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=temperature,
        openai_api_key=settings.openai_api_key,
    )


def get_llm_gemini(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Gemini 2.0 Flash — conformité, classification, écriture comptable."""
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=temperature,
        google_api_key=settings.gemini_api_key,
    )


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """Alias OpenAI — conservé pour compatibilité (outils RAG, tests)."""
    return get_llm_openai(temperature)


def get_embeddings() -> OpenAIEmbeddings:
    """Embeddings OpenAI pour les index FAISS."""
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )
