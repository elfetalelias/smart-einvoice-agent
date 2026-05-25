from langchain.tools import tool
from rag.vector_store import load_or_create_store, search_documents
from config.settings import settings
from typing import List

_store = None


def _get_store():
    global _store
    if _store is None:
        _store = load_or_create_store(settings.faiss_index_tax)
    return _store


@tool
def search_regles_fiscales(query: str) -> str:
    """
    Recherche dans le corpus des règles fiscales marocaines.
    Utiliser pour vérifier : TVA, ICE obligatoire, mentions légales, champs requis sur facture.
    Retourne les passages pertinents du Code Général des Impôts et des circulaires DGI.
    """
    docs = search_documents(_get_store(), query)
    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Source inconnue")
        results.append(f"[{i}] {source}\n{doc.page_content}")
    return "\n\n---\n\n".join(results) if results else "Aucun résultat trouvé."
