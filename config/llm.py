from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=temperature,
        openai_api_key=settings.openai_api_key,
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )
