"""Tests d'intégration — Graphe LangGraph"""
import pytest
from graph.invoice_state import InvoiceState


def make_initial_state(fichier_path: str = "test.pdf") -> InvoiceState:
    return {
        "fichier_path": fichier_path,
        "fichier_type": "pdf",
        "fichier_nom": "test_facture.pdf",
        "statut": "fichier_reçu",
        "etape_courante": "Démarrage",
        "erreur": None,
        "donnees_extraites": None,
        "validation_extraction": None,
        "resultat_conformite": None,
        "validation_conformite": None,
        "code_comptable": None,
        "validation_classification": None,
        "ecriture_comptable": None,
        "rapport_final": None,
        "rapport_genere": False,
        "contexte_rag": [],
        "historique_validations": [],
    }


class TestSupervisorAgent:
    def test_decide_next_node_fichier_recu(self):
        from agents.supervisor_agent import decide_next_node
        state = make_initial_state()
        assert decide_next_node(state) == "extract_invoice"

    def test_decide_next_node_erreur(self):
        from agents.supervisor_agent import decide_next_node
        state = {**make_initial_state(), "erreur": "Erreur de lecture"}
        assert decide_next_node(state) == "END"

    def test_decide_next_node_extraction_terminee(self):
        from agents.supervisor_agent import decide_next_node
        state = {**make_initial_state(), "statut": "extraction_terminée"}
        assert decide_next_node(state) == "human_validation_1"

    def test_decide_next_node_rapport_genere(self):
        from agents.supervisor_agent import decide_next_node
        state = {**make_initial_state(), "statut": "rapport_généré"}
        assert decide_next_node(state) == "END"

    def test_decide_validation_1_acceptee(self):
        from agents.supervisor_agent import decide_next_node
        state = {
            **make_initial_state(),
            "statut": "validation_1_faite",
            "validation_extraction": {"decision": "accepté", "commentaire": None, "modifications": None},
        }
        assert decide_next_node(state) == "check_compliance"

    def test_decide_validation_1_rejetee(self):
        from agents.supervisor_agent import decide_next_node
        state = {
            **make_initial_state(),
            "statut": "validation_1_faite",
            "validation_extraction": {"decision": "rejeté", "commentaire": None, "modifications": None},
        }
        assert decide_next_node(state) == "END"


class TestInvoiceState:
    def test_state_initialisation(self):
        state = make_initial_state()
        assert state["statut"] == "fichier_reçu"
        assert state["rapport_genere"] is False
        assert state["contexte_rag"] == []

    def test_state_update_immutable_pattern(self):
        state = make_initial_state()
        new_state = {**state, "statut": "extraction_terminée"}
        assert state["statut"] == "fichier_reçu"
        assert new_state["statut"] == "extraction_terminée"
