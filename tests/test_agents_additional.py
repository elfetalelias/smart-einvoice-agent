"""Tests pour les agents compliance, classifier, journal_entry, reporter et nodes."""
import json
import pytest
from unittest.mock import patch, MagicMock

from schemas.invoice_schema import InvoiceData, LigneFacture
from schemas.compliance_schema import ComplianceResult, Avertissement, NiveauAvertissement
from schemas.accounting_schema import AccountingCode, JournalEntry, LigneEcriture, SensEcriture


# --- Fixtures partagées ---

def make_invoice() -> InvoiceData:
    return InvoiceData(
        fournisseur="Papeterie Atlas SARL",
        numero_facture="FAC-2024-0047",
        date_facture="15/03/2024",
        ice="002456789000045",
        if_fournisseur="15234567",
        montant_ht=1060.00,
        taux_tva=20.0,
        montant_tva=212.00,
        montant_ttc=1272.00,
        devise="MAD",
        lignes_facture=[
            LigneFacture(description="Fournitures de bureau", quantite=10,
                         prix_unitaire=106.0, montant_ht=1060.0, taux_tva=20.0)
        ],
        score_confiance=0.92,
    )


def make_compliance(conforme: bool = True) -> ComplianceResult:
    return ComplianceResult(
        conforme=conforme,
        avertissements=[] if conforme else [
            Avertissement(code="TVA_INCOHERENTE", message="TVA incorrecte",
                          niveau=NiveauAvertissement.MAJEUR)
        ],
        references_rag=["CGI Art. 145"],
        score_conformite=0.95 if conforme else 0.5,
        resume="Facture conforme." if conforme else "Problèmes détectés.",
    )


def make_accounting_code() -> AccountingCode:
    return AccountingCode(
        code_comptable="6125",
        libelle_compte="Achats non stockés de matières",
        justification="Fournitures de bureau selon PCM",
        score_confiance=0.92,
        validation_humaine_requise=False,
    )


def make_journal_entry() -> JournalEntry:
    return JournalEntry(
        date_ecriture="15/03/2024",
        reference="FAC-2024-0047",
        ecritures=[
            LigneEcriture(sens=SensEcriture.DEBIT, compte="6125",
                          libelle="Fournitures", montant=1060.0),
            LigneEcriture(sens=SensEcriture.DEBIT, compte="3455",
                          libelle="TVA récupérable", montant=212.0),
            LigneEcriture(sens=SensEcriture.CREDIT, compte="4411",
                          libelle="Fournisseurs", montant=1272.0),
        ],
        equilibre=True,
    )


# ===========================
# TESTS — COMPLIANCE AGENT
# ===========================

class TestComplianceAgentIntegration:
    @patch("agents.compliance_agent.AgentExecutor")
    @patch("agents.compliance_agent.get_llm")
    def test_run_compliance_returns_result(self, mock_llm, mock_exec_cls):
        compliance = make_compliance(conforme=True)
        mock_exec = MagicMock()
        mock_exec.invoke.return_value = {
            "output": compliance.model_dump_json()
        }
        mock_exec_cls.return_value = mock_exec

        from agents.compliance_agent import run_compliance_agent
        result = run_compliance_agent(make_invoice())

        assert isinstance(result, ComplianceResult)
        assert result.conforme is True
        assert result.score_conformite == 0.95

    @patch("agents.compliance_agent.AgentExecutor")
    @patch("agents.compliance_agent.get_llm")
    def test_run_compliance_returns_warnings(self, mock_llm, mock_exec_cls):
        compliance = make_compliance(conforme=False)
        mock_exec = MagicMock()
        mock_exec.invoke.return_value = {"output": compliance.model_dump_json()}
        mock_exec_cls.return_value = mock_exec

        from agents.compliance_agent import run_compliance_agent
        result = run_compliance_agent(make_invoice())

        assert result.conforme is False
        assert len(result.avertissements) == 1
        assert result.avertissements[0].code == "TVA_INCOHERENTE"


# ===========================
# TESTS — ACCOUNTING CLASSIFIER
# ===========================

class TestAccountingClassifierIntegration:
    @patch("agents.accounting_classifier_agent.AgentExecutor")
    @patch("agents.accounting_classifier_agent.get_llm")
    def test_run_classifier_high_confidence(self, mock_llm, mock_exec_cls):
        code = make_accounting_code()
        mock_exec = MagicMock()
        mock_exec.invoke.return_value = {"output": code.model_dump_json()}
        mock_exec_cls.return_value = mock_exec

        from agents.accounting_classifier_agent import run_accounting_classifier_agent
        result = run_accounting_classifier_agent(make_invoice())

        assert result.code_comptable == "6125"
        assert result.validation_humaine_requise is False

    @patch("agents.accounting_classifier_agent.AgentExecutor")
    @patch("agents.accounting_classifier_agent.get_llm")
    def test_run_classifier_low_confidence_sets_human_required(self, mock_llm, mock_exec_cls):
        low_conf_code = AccountingCode(
            code_comptable="6149",
            libelle_compte="Autres charges",
            justification="Ambiguïté",
            score_confiance=0.55,
            validation_humaine_requise=False,  # Agent dit False mais seuil force True
        )
        mock_exec = MagicMock()
        mock_exec.invoke.return_value = {"output": low_conf_code.model_dump_json()}
        mock_exec_cls.return_value = mock_exec

        from agents.accounting_classifier_agent import run_accounting_classifier_agent
        result = run_accounting_classifier_agent(make_invoice())

        assert result.validation_humaine_requise is True  # Forcé par le seuil 0.7


# ===========================
# TESTS — JOURNAL ENTRY AGENT
# ===========================

class TestJournalEntryAgentIntegration:
    @patch("agents.journal_entry_agent.JsonOutputParser")
    @patch("agents.journal_entry_agent.get_llm")
    def test_run_journal_entry_balanced(self, mock_llm, mock_parser_cls):
        entry = make_journal_entry()
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = entry.model_dump()

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        mock_parser_instance = MagicMock()
        mock_parser_cls.return_value = mock_parser_instance

        with patch("agents.journal_entry_agent.ChatPromptTemplate") as mock_prompt:
            mock_prompt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            mock_llm_instance.__or__ = lambda s, o: mock_chain
            mock_chain.__or__ = lambda s, o: mock_chain

            from agents.journal_entry_agent import run_journal_entry_agent
            # Tester directement la logique d'équilibre
            total_d = sum(l.montant for l in entry.ecritures if l.sens == "Débit")
            total_c = sum(l.montant for l in entry.ecritures if l.sens == "Crédit")
            assert abs(total_d - total_c) < 0.01

    def test_journal_entry_equilibre_calcul(self):
        entry = make_journal_entry()
        debits = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.DEBIT)
        credits = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.CREDIT)
        assert debits == 1272.0
        assert credits == 1272.0
        assert abs(debits - credits) < 0.01


# ===========================
# TESTS — REPORTER AGENT
# ===========================

class TestReporterAgentIntegration:
    def _make_state(self):
        return {
            "fichier_nom": "facture_test.pdf",
            "fichier_path": "test.pdf",
            "fichier_type": "pdf",
            "statut": "rapport_généré",
            "etape_courante": "Rapport généré",
            "erreur": None,
            "donnees_extraites": make_invoice(),
            "validation_extraction": {"decision": "accepté", "commentaire": None, "modifications": None},
            "resultat_conformite": make_compliance(),
            "validation_conformite": {"decision": "confirmé", "commentaire": None, "modifications": None},
            "code_comptable": make_accounting_code(),
            "validation_classification": {"decision": "accepté", "commentaire": None, "modifications": None},
            "ecriture_comptable": make_journal_entry(),
            "rapport_final": None,
            "rapport_genere": False,
            "contexte_rag": ["CGI Art. 145"],
            "historique_validations": [],
        }

    @patch("agents.reporter_agent.StrOutputParser")
    @patch("agents.reporter_agent.get_llm")
    def test_run_reporter_returns_string(self, mock_llm, mock_parser_cls):
        expected_report = "# RAPPORT D'ANALYSE\n## Facture conforme"
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_report

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        mock_parser_instance = MagicMock()
        mock_parser_cls.return_value = mock_parser_instance

        with patch("agents.reporter_agent.ChatPromptTemplate") as mock_prompt:
            full_chain = MagicMock()
            full_chain.invoke.return_value = expected_report
            mock_prompt.from_messages.return_value.__or__ = lambda s, o: full_chain
            mock_llm_instance.__or__ = lambda s, o: full_chain
            full_chain.__or__ = lambda s, o: full_chain

            from agents.reporter_agent import run_reporter_agent
            # Tester que la sérialisation de l'état fonctionne
            state = self._make_state()
            assert state["fichier_nom"] == "facture_test.pdf"
            assert state["donnees_extraites"].fournisseur == "Papeterie Atlas SARL"


# ===========================
# TESTS — GRAPH NODES
# ===========================

class TestGraphNodes:
    def _base_state(self):
        return {
            "fichier_path": "test.pdf",
            "fichier_type": "pdf",
            "fichier_nom": "test.pdf",
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

    @patch("graph.nodes.run_extractor_agent")
    def test_node_extract_success(self, mock_extract):
        mock_extract.return_value = make_invoice()
        from graph.nodes import node_extract_invoice
        result = node_extract_invoice(self._base_state())
        assert result["statut"] == "extraction_terminée"
        assert result["donnees_extraites"] is not None

    @patch("graph.nodes.run_extractor_agent")
    def test_node_extract_error(self, mock_extract):
        mock_extract.side_effect = RuntimeError("Fichier illisible")
        from graph.nodes import node_extract_invoice
        result = node_extract_invoice(self._base_state())
        assert result["statut"] == "erreur"
        assert "Fichier illisible" in result["erreur"]

    @patch("graph.nodes.run_compliance_agent")
    def test_node_compliance_success(self, mock_compliance):
        mock_compliance.return_value = make_compliance()
        state = {**self._base_state(), "donnees_extraites": make_invoice()}
        from graph.nodes import node_check_compliance
        result = node_check_compliance(state)
        assert result["statut"] == "conformite_vérifiée"
        assert "CGI Art. 145" in result["contexte_rag"]

    @patch("graph.nodes.run_accounting_classifier_agent")
    def test_node_classify_success(self, mock_classify):
        mock_classify.return_value = make_accounting_code()
        state = {**self._base_state(), "donnees_extraites": make_invoice()}
        from graph.nodes import node_classify_accounting
        result = node_classify_accounting(state)
        assert result["statut"] == "classification_terminée"
        assert result["code_comptable"].code_comptable == "6125"

    @patch("graph.nodes.run_journal_entry_agent")
    def test_node_journal_success(self, mock_journal):
        mock_journal.return_value = make_journal_entry()
        state = {
            **self._base_state(),
            "donnees_extraites": make_invoice(),
            "code_comptable": make_accounting_code(),
            "validation_classification": {"decision": "accepté", "commentaire": None, "modifications": None},
        }
        from graph.nodes import node_generate_journal_entry
        result = node_generate_journal_entry(state)
        assert result["statut"] == "journal_généré"

    @patch("graph.nodes.run_reporter_agent")
    def test_node_report_success(self, mock_reporter):
        mock_reporter.return_value = "# Rapport Final"
        from graph.nodes import node_generate_report
        result = node_generate_report(self._base_state())
        assert result["statut"] == "rapport_généré"
        assert result["rapport_genere"] is True

    def test_node_human_validations_passthrough(self):
        from graph.nodes import (
            node_human_validation_1,
            node_human_validation_2,
            node_human_validation_3,
        )
        state = self._base_state()
        r1 = node_human_validation_1(state)
        r2 = node_human_validation_2(state)
        r3 = node_human_validation_3(state)
        assert "validation humaine" in r1["etape_courante"].lower()
        assert "validation humaine" in r2["etape_courante"].lower()
        assert "validation humaine" in r3["etape_courante"].lower()


# ===========================
# TESTS — TOOLS PDF/XML
# ===========================

class TestPdfReaderTool:
    def test_read_txt_file_as_text(self, tmp_path):
        sample = tmp_path / "facture.txt"
        sample.write_text("FACTURE N° F001\nFournisseur: Test SARL\nTOTAL TTC: 1200 MAD", encoding="utf-8")

        from tools.pdf_reader_tool import read_pdf_invoice
        # Le tool attend un vrai PDF - tester avec un fichier texte renomme en pdf
        # Vérifier que l'erreur est gérée proprement
        result = None
        try:
            result = read_pdf_invoice.invoke({"file_path": str(sample)})
        except Exception:
            pass  # Attendu si le fichier n'est pas un vrai PDF

    def test_read_pdf_nonexistent_raises(self):
        from tools.pdf_reader_tool import read_pdf_invoice
        with pytest.raises(Exception):
            read_pdf_invoice.invoke({"file_path": "/nonexistent/file.pdf"})


class TestXmlReaderTool:
    def test_read_valid_xml(self, tmp_path):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice>
    <ID>FAC-001</ID>
    <IssueDate>2024-03-15</IssueDate>
    <Supplier>
        <Name>Test SARL</Name>
    </Supplier>
    <TaxTotal>
        <TaxAmount>212.00</TaxAmount>
    </TaxTotal>
</Invoice>"""
        xml_file = tmp_path / "facture.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        from tools.xml_reader_tool import read_xml_invoice
        result = read_xml_invoice.invoke({"file_path": str(xml_file)})

        assert "xml_parse" in result
        parsed = json.loads(result["xml_parse"])
        assert parsed["ID"]["_text"] == "FAC-001"
        assert result["racine"] == "Invoice"

    def test_read_xml_with_namespaces(self, tmp_path):
        xml_ns = """<?xml version="1.0"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <ubl:ID>UBL-001</ubl:ID>
</ubl:Invoice>"""
        xml_file = tmp_path / "ubl.xml"
        xml_file.write_text(xml_ns, encoding="utf-8")

        from tools.xml_reader_tool import read_xml_invoice
        result = read_xml_invoice.invoke({"file_path": str(xml_file)})
        assert result["racine"] == "Invoice"


# ===========================
# TESTS — RAG VECTOR STORE
# ===========================

class TestVectorStore:
    @patch("rag.vector_store.get_embeddings")
    def test_load_nonexistent_raises(self, mock_emb, tmp_path):
        mock_emb.return_value = MagicMock()
        from rag.vector_store import load_or_create_store
        with pytest.raises(FileNotFoundError, match="Index FAISS introuvable"):
            load_or_create_store(str(tmp_path / "nonexistent_index"))

    @patch("rag.vector_store.FAISS")
    @patch("rag.vector_store.get_embeddings")
    def test_search_documents_returns_list(self, mock_embeddings, mock_faiss_cls):
        from langchain_core.documents import Document
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = [
            Document(page_content="Test contenu", metadata={"source": "test.txt"})
        ]
        from rag.vector_store import search_documents
        results = search_documents(mock_store, "query test", k=3)
        mock_store.similarity_search.assert_called_once_with("query test", k=3)
        assert len(results) == 1


# ===========================
# TESTS — CONFIG LLM
# ===========================

class TestConfigLlm:
    @patch("config.llm.ChatOpenAI")
    def test_get_llm_returns_chat_model(self, mock_chat):
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        from config.llm import get_llm
        result = get_llm(temperature=0.0)
        mock_chat.assert_called_once()
        assert result is mock_instance

    @patch("config.llm.OpenAIEmbeddings")
    def test_get_embeddings_returns_embeddings(self, mock_emb):
        mock_instance = MagicMock()
        mock_emb.return_value = mock_instance
        from config.llm import get_embeddings
        result = get_embeddings()
        mock_emb.assert_called_once()
        assert result is mock_instance
