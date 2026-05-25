"""Tests d'intégration — RAG Retrievers"""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


MOCK_DOCS = [
    Document(
        page_content="Article 145 CGI : mentions obligatoires ICE et IF",
        metadata={"source": "CGI_Art145.txt"},
    ),
    Document(
        page_content="TVA Maroc taux normal 20%",
        metadata={"source": "CGI_TVA.txt"},
    ),
]


class TestRagRetrievers:
    @patch("tools.tax_rules_retriever_tool._get_store")
    def test_search_regles_fiscales_returns_text(self, mock_store):
        mock_faiss = MagicMock()
        mock_faiss.similarity_search.return_value = MOCK_DOCS
        mock_store.return_value = mock_faiss

        from tools.tax_rules_retriever_tool import search_regles_fiscales
        result = search_regles_fiscales.invoke({"query": "ICE obligatoire facture"})
        assert "Article 145 CGI" in result
        assert "20%" in result

    @patch("tools.accounting_plan_retriever_tool._get_store")
    def test_search_plan_comptable_returns_text(self, mock_store):
        pcm_docs = [
            Document(
                page_content="Compte 6125 — Achats non stockés de matières et fournitures",
                metadata={"source": "PCM_Classe6.txt"},
            )
        ]
        mock_faiss = MagicMock()
        mock_faiss.similarity_search.return_value = pcm_docs
        mock_store.return_value = mock_faiss

        from tools.accounting_plan_retriever_tool import search_plan_comptable
        result = search_plan_comptable.invoke({"query": "fournitures de bureau"})
        assert "6125" in result

    @patch("tools.einvoice_standards_retriever_tool._get_store")
    def test_search_normes_facturation(self, mock_store):
        norm_docs = [
            Document(
                page_content="BT-1 Identifiant facture UBL obligatoire",
                metadata={"source": "EN16931.txt"},
            )
        ]
        mock_faiss = MagicMock()
        mock_faiss.similarity_search.return_value = norm_docs
        mock_store.return_value = mock_faiss

        from tools.einvoice_standards_retriever_tool import search_normes_facturation
        result = search_normes_facturation.invoke({"query": "champs obligatoires UBL"})
        assert "BT-1" in result

    @patch("tools.tax_rules_retriever_tool._get_store")
    def test_search_returns_no_result(self, mock_store):
        mock_faiss = MagicMock()
        mock_faiss.similarity_search.return_value = []
        mock_store.return_value = mock_faiss

        from tools.tax_rules_retriever_tool import search_regles_fiscales
        result = search_regles_fiscales.invoke({"query": "query inconnue xyz"})
        assert "Aucun résultat" in result
