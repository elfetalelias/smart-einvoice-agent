"""Tests unitaires — Agent Extracteur"""
import pytest
from unittest.mock import patch, MagicMock
from schemas.invoice_schema import InvoiceData, LigneFacture


SAMPLE_INVOICE_DATA = {
    "fournisseur": "Papeterie Atlas SARL",
    "numero_facture": "FAC-2024-0047",
    "date_facture": "15/03/2024",
    "ice": "002456789000045",
    "if_fournisseur": "15234567",
    "montant_ht": 1060.00,
    "taux_tva": 20.0,
    "montant_tva": 212.00,
    "montant_ttc": 1272.00,
    "devise": "MAD",
    "lignes_facture": [
        {
            "description": "Ramettes A4 80g",
            "quantite": 20,
            "prix_unitaire": 25.00,
            "montant_ht": 500.00,
            "taux_tva": 20.0,
        }
    ],
    "score_confiance": 0.92,
    "champs_manquants": [],
}


class TestInvoiceDataSchema:
    def test_invoice_data_creation(self):
        invoice = InvoiceData(**SAMPLE_INVOICE_DATA)
        assert invoice.fournisseur == "Papeterie Atlas SARL"
        assert invoice.montant_ht == 1060.00
        assert invoice.score_confiance == 0.92

    def test_invoice_data_defaults(self):
        minimal_data = {
            "fournisseur": "Test SARL",
            "numero_facture": "F001",
            "date_facture": "01/01/2024",
            "montant_ht": 100.0,
            "taux_tva": 20.0,
            "montant_tva": 20.0,
            "montant_ttc": 120.0,
            "score_confiance": 0.8,
        }
        invoice = InvoiceData(**minimal_data)
        assert invoice.devise == "MAD"
        assert invoice.ice is None
        assert invoice.lignes_facture == []

    def test_score_confiance_validation(self):
        with pytest.raises(Exception):
            InvoiceData(**{**SAMPLE_INVOICE_DATA, "score_confiance": 1.5})

    def test_score_confiance_zero(self):
        invoice = InvoiceData(**{**SAMPLE_INVOICE_DATA, "score_confiance": 0.0})
        assert invoice.score_confiance == 0.0

    def test_ligne_facture_creation(self):
        ligne = LigneFacture(
            description="Fournitures",
            quantite=5,
            prix_unitaire=10.0,
            montant_ht=50.0,
            taux_tva=20.0,
        )
        assert ligne.montant_ht == 50.0


class TestExtractorAgent:
    @patch("agents.extractor_agent.AgentExecutor")
    @patch("agents.extractor_agent.get_llm")
    def test_run_extractor_returns_invoice_data(self, mock_llm, mock_executor_class):
        import json
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": json.dumps(SAMPLE_INVOICE_DATA)}
        mock_executor_class.return_value = mock_executor

        from agents.extractor_agent import run_extractor_agent
        result = run_extractor_agent("test.pdf", "pdf")

        assert isinstance(result, InvoiceData)
        assert result.fournisseur == "Papeterie Atlas SARL"

    @patch("agents.extractor_agent.AgentExecutor")
    @patch("agents.extractor_agent.get_llm")
    def test_extractor_handles_missing_fields(self, mock_llm, mock_executor_class):
        import json
        data_with_missing = {
            **SAMPLE_INVOICE_DATA,
            "ice": None,
            "if_fournisseur": None,
            "champs_manquants": ["ice", "if_fournisseur"],
            "score_confiance": 0.65,
        }
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": json.dumps(data_with_missing)}
        mock_executor_class.return_value = mock_executor

        from agents.extractor_agent import run_extractor_agent
        result = run_extractor_agent("test.xml", "xml")

        assert result.ice is None
        assert "ice" in result.champs_manquants
        assert result.score_confiance == 0.65
