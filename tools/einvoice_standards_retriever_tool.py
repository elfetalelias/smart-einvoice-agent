from langchain.tools import tool
from rag.vector_store import load_or_create_store, search_documents
from config.settings import settings

_store = None


def _get_store():
    global _store
    if _store is None:
        _store = load_or_create_store(settings.faiss_index_standards)
    return _store


@tool
def search_normes_facturation(query: str) -> str:
    """
    Recherche dans le corpus des normes de facturation electronique marocaines.
    Source principale : cgi-2026.pdf (Article 145 CGI — mentions obligatoires,
    sanctions, e-facture DGI) et ubl_facturx.txt (formats d'echange).
    Utiliser pour verifier : mentions obligatoires Article 145, sanctions fiscales,
    obligations e-facture DGI, numero sequentiel, ICE, IF.
    """
    docs = search_documents(_get_store(), query)
    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Norme inconnue")
        results.append(f"[{i}] {source}\n{doc.page_content}")
    return "\n\n---\n\n".join(results) if results else "Aucun résultat trouvé."
