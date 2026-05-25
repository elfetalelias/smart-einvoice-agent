import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List
from config.llm import get_embeddings
from config.settings import settings


def load_or_create_store(index_path: str) -> FAISS:
    embeddings = get_embeddings()
    if os.path.exists(f"{index_path}.faiss"):
        return FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    raise FileNotFoundError(
        f"Index FAISS introuvable : {index_path}. Exécuter rag/ingest.py d'abord."
    )


def save_store(store: FAISS, index_path: str) -> None:
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    store.save_local(index_path)


def create_store_from_documents(documents: List[Document], index_path: str) -> FAISS:
    embeddings = get_embeddings()
    store = FAISS.from_documents(documents, embeddings)
    save_store(store, index_path)
    return store


def search_documents(store: FAISS, query: str, k: int = None) -> List[Document]:
    k = k or settings.rag_top_k
    return store.similarity_search(query, k=k)
