"""
Script d'ingestion des corpus RAG.
Exécuter une seule fois (ou après mise à jour des corpus) :
    python rag/ingest.py

Formats supportés : .txt, .pdf
"""
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.vector_store import create_store_from_documents
from config.settings import settings

CORPORA = {
    "regles_fiscales_marocaines": settings.faiss_index_tax,
    "normes_facturation_electronique": settings.faiss_index_standards,
    "plan_comptable_marocain": settings.faiss_index_accounting,
}

CORPORA_BASE_PATH = Path(__file__).parent / "corpora"

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", " "],
)


def _load_txt(corpus_path: Path) -> list:
    loader = DirectoryLoader(
        str(corpus_path),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        silent_errors=True,
    )
    return loader.load()


def _load_pdfs(corpus_path: Path) -> list:
    docs = []
    for pdf_file in corpus_path.glob("**/*.pdf"):
        print(f"  [PDF] {pdf_file.name}")
        try:
            loader = PyPDFLoader(str(pdf_file))
            docs.extend(loader.load())
        except Exception as exc:
            print(f"  [ERREUR] Impossible de lire {pdf_file.name} : {exc}")
    return docs


def ingest_corpus(corpus_name: str, index_path: str) -> None:
    corpus_path = CORPORA_BASE_PATH / corpus_name
    if not corpus_path.exists():
        print(f"[AVERTISSEMENT] Corpus introuvable : {corpus_path}")
        return

    print(f"[INGESTION] {corpus_name} -> {index_path}")

    docs = _load_txt(corpus_path) + _load_pdfs(corpus_path)

    if not docs:
        print(f"  [INFO] Aucun document (.txt / .pdf) trouvé dans {corpus_path}")
        return

    chunks = SPLITTER.split_documents(docs)
    print(f"  [INFO] {len(docs)} documents -> {len(chunks)} chunks")

    create_store_from_documents(chunks, index_path)
    print(f"  [OK] Index sauvegardé : {index_path}")


def main() -> None:
    print("=== INGESTION DES CORPUS RAG ===\n")
    for corpus_name, index_path in CORPORA.items():
        ingest_corpus(corpus_name, index_path)
    print("\n=== INGESTION TERMINÉE ===")


if __name__ == "__main__":
    main()
