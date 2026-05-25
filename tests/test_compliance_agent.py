"""Tests unitaires — Agent de Conformité"""
import pytest
from schemas.compliance_schema import ComplianceResult, Avertissement, NiveauAvertissement
from schemas.invoice_schema import InvoiceData


def make_invoice(**kwargs) -> InvoiceData:
    defaults = {
        "fournisseur": "Test SARL",
        "numero_facture": "F-001",
        "date_facture": "01/01/2024",
        "ice": "001234567000012",
        "if_fournisseur": "12345678",
        "montant_ht": 1000.00,
        "taux_tva": 20.0,
        "montant_tva": 200.00,
        "montant_ttc": 1200.00,
        "devise": "MAD",
        "score_confiance": 0.9,
    }
    return InvoiceData(**{**defaults, **kwargs})


class TestComplianceSchema:
    def test_conforme_result(self):
        result = ComplianceResult(
            conforme=True,
            avertissements=[],
            references_rag=[],
            score_conformite=1.0,
            resume="Facture conforme.",
        )
        assert result.conforme is True
        assert result.score_conformite == 1.0

    def test_non_conforme_with_warnings(self):
        avert = Avertissement(
            code="ICE_MANQUANT",
            message="ICE du fournisseur absent",
            niveau=NiveauAvertissement.MAJEUR,
            reference_legale="Article 145 CGI",
        )
        result = ComplianceResult(
            conforme=False,
            avertissements=[avert],
            references_rag=["CGI Art. 145"],
            score_conformite=0.6,
            resume="Champs obligatoires manquants.",
        )
        assert result.conforme is False
        assert len(result.avertissements) == 1
        assert result.avertissements[0].code == "ICE_MANQUANT"


class TestTVACoherence:
    def test_tva_correcte(self):
        invoice = make_invoice(montant_ht=1000.0, taux_tva=20.0, montant_tva=200.0, montant_ttc=1200.0)
        tva_calculee = invoice.montant_ht * invoice.taux_tva / 100
        assert abs(tva_calculee - invoice.montant_tva) < 0.02

    def test_tva_incoherente(self):
        invoice = make_invoice(montant_ht=1000.0, taux_tva=20.0, montant_tva=250.0, montant_ttc=1250.0)
        tva_calculee = invoice.montant_ht * invoice.taux_tva / 100
        assert abs(tva_calculee - invoice.montant_tva) > 0.02

    def test_taux_tva_valides_maroc(self):
        taux_valides = [0, 7, 10, 14, 20]
        for taux in taux_valides:
            invoice = make_invoice(taux_tva=float(taux))
            assert invoice.taux_tva in [0, 7, 10, 14, 20]
