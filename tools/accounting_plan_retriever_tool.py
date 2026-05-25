from langchain.tools import tool
from rag.vector_store import load_or_create_store, search_documents
from config.settings import settings

_store = None


def _get_store():
    global _store
    if _store is None:
        _store = load_or_create_store(settings.faiss_index_accounting)
    return _store


@tool
def search_plan_comptable(query: str) -> str:
    """
    Recherche dans le Plan Comptable Marocain (PCM).
    Utiliser pour : trouver le code comptable approprié, identifier la classe de charges,
    vérifier les comptes TVA récupérable (3455), comptes fournisseurs (4411).
    Retourne les codes et libellés du PCM avec des exemples d'écritures.
    """
    docs = search_documents(_get_store(), query)
    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "PCM")
        results.append(f"[{i}] {source}\n{doc.page_content}")
    return "\n\n---\n\n".join(results) if results else "Aucun résultat trouvé."
