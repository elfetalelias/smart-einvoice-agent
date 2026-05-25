"""
Script d'ingestion des corpus RAG.
Exécuter une seule fois (ou après mise à jour des corpus) :
    python rag/ingest.py
"""
import os
import sys
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag.vector_store import create_store_from_documents
from config.settings import settings

CORPORA = {
    "regles_fiscales_marocaines": settings.faiss_index_tax,
    "normes_facturation_electronique": settings.faiss_index_standards,
    "plan_comptable_marocain": settings.faiss_index_accounting,
}

CORPORA_BASE_PATH = Path(__file__).parent / "corpora"


def ingest_corpus(corpus_name: str, index_path: str) -> None:
    corpus_path = CORPORA_BASE_PATH / corpus_name
    if not corpus_path.exists():
        print(f"[AVERTISSEMENT] Corpus introuvable : {corpus_path}")
        return

    print(f"[INGESTION] {corpus_name} -> {index_path}")
    loader = DirectoryLoader(
        str(corpus_path),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    if not docs:
        print(f"  [INFO] Aucun document .txt trouvé dans {corpus_path}")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " "],
    )
    chunks = splitter.split_documents(docs)
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
