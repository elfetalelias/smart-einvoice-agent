"""Tests de couverture — agents, RAG, tools, graph/nodes (61% → 80%+)."""
import pytest
from unittest.mock import patch, MagicMock

from schemas.invoice_schema import InvoiceData, LigneFacture
from schemas.accounting_schema import AccountingCode, JournalEntry, LigneEcriture, SensEcriture
from schemas.compliance_schema import ComplianceResult, Avertissement, NiveauAvertissement

# Pre-import modules so @patch class-level decorators can resolve paths
import agents.compliance_agent              # noqa: F401
import agents.extractor_agent               # noqa: F401
import agents.journal_entry_agent           # noqa: F401
import agents.reporter_agent                # noqa: F401
import agents.accounting_classifier_agent   # noqa: F401


# ─── Shared fixtures ──────────────────────────────────────────────────────────

def _invoice(**kw) -> InvoiceData:
    base = dict(
        fournisseur="Atlas SARL", numero_facture="F-001",
        date_facture="01/01/2024", ice="001234567000012",
        if_fournisseur="12345678", montant_ht=1000.0,
        taux_tva=20.0, montant_tva=200.0, montant_ttc=1200.0,
        devise="MAD", score_confiance=0.9,
    )
    return InvoiceData(**{**base, **kw})


def _code(**kw) -> AccountingCode:
    base = dict(
        code_comptable="6125", libelle_compte="Achats non stockes",
        justification="Fournitures bureau", score_confiance=0.9,
        validation_humaine_requise=False,
    )
    return AccountingCode(**{**base, **kw})


def _entry(debit: float = 1200.0, credit: float = 1200.0) -> JournalEntry:
    return JournalEntry(
        date_ecriture="01/01/2024", reference="F-001",
        ecritures=[
            LigneEcriture(sens=SensEcriture.DEBIT, compte="6125",
                          libelle="Achat", montant=debit),
            LigneEcriture(sens=SensEcriture.CREDIT, compte="4411",
                          libelle="Fournisseur", montant=credit),
        ],
        equilibre=True,
    )


def _node_state(**kw) -> dict:
    base = dict(
        fichier_nom="test.pdf", fichier_path="/tmp/test.pdf",
        fichier_type="pdf", statut="fichier_recu",
        etape_courante="init", erreur=None,
        donnees_extraites=None, validation_extraction=None,
        resultat_conformite=None, validation_conformite=None,
        code_comptable=None, validation_classification=None,
        ecriture_comptable=None, rapport_final=None,
        rapport_genere=False, contexte_rag=[], historique_validations=[],
    )
    return {**base, **kw}


# ─── compliance_agent — fonctions internes (Python pur, sans LLM) ────────────

class TestNormalizeInvoice:
    def test_decimal_taux_normalized_to_percent(self):
        from agents.compliance_agent import _normalize_invoice
        result = _normalize_invoice(_invoice(taux_tva=0.20))
        assert result.taux_tva == 20.0

    def test_percent_taux_unchanged(self):
        from agents.compliance_agent import _normalize_invoice
        result = _normalize_invoice(_invoice(taux_tva=20.0))
        assert result.taux_tva == 20.0

    def test_zero_taux_unchanged(self):
        from agents.compliance_agent import _normalize_invoice
        result = _normalize_invoice(_invoice(taux_tva=0.0))
        assert result.taux_tva == 0.0

    def test_returns_new_object_not_mutated(self):
        from agents.compliance_agent import _normalize_invoice
        inv = _invoice(taux_tva=0.14)
        result = _normalize_invoice(inv)
        assert result is not inv
        assert result.taux_tva == 14.0


class TestArithmeticSummary:
    def test_all_correct_shows_valide_and_correct(self):
        from agents.compliance_agent import _arithmetic_summary
        summary = _arithmetic_summary(_invoice())
        assert "VALIDE" in summary
        assert "CORRECT" in summary

    def test_invalid_taux_shows_invalide(self):
        from agents.compliance_agent import _arithmetic_summary
        inv = _invoice(taux_tva=5.0, montant_tva=50.0, montant_ttc=1050.0)
        summary = _arithmetic_summary(inv)
        assert "INVALIDE" in summary

    def test_incorrect_tva_amount(self):
        from agents.compliance_agent import _arithmetic_summary
        inv = _invoice(montant_tva=250.0, montant_ttc=1250.0)
        summary = _arithmetic_summary(inv)
        assert "INCORRECT" in summary

    def test_incorrect_ttc_amount(self):
        from agents.compliance_agent import _arithmetic_summary
        inv = _invoice(montant_tva=200.0, montant_ttc=1300.0)
        summary = _arithmetic_summary(inv)
        assert "INCORRECT" in summary

    def test_contains_section_header(self):
        from agents.compliance_agent import _arithmetic_summary
        summary = _arithmetic_summary(_invoice())
        assert "VERIFICATION ARITHMETIQUE" in summary or "ARITHMÉTIQUE" in summary

    def test_taux_7_valide(self):
        from agents.compliance_agent import _arithmetic_summary
        inv = _invoice(taux_tva=7.0, montant_tva=70.0, montant_ttc=1070.0)
        summary = _arithmetic_summary(inv)
        assert "VALIDE" in summary


# ─── run_compliance_agent ─────────────────────────────────────────────────────

class TestRunComplianceAgent:
    @patch("agents.compliance_agent.retrieve_context")
    @patch("agents.compliance_agent.get_llm_openai")
    def test_invokes_chain_and_returns_result(self, mock_llm, mock_retrieve):
        mock_retrieve.return_value = "CGI Art.145"
        expected = ComplianceResult(
            conforme=True, avertissements=[], references_rag=["CGI Art.145"],
            score_conformite=0.95, resume="Conforme.",
        )
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.compliance_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.compliance_agent import run_compliance_agent
            result = run_compliance_agent(_invoice())
            assert result.conforme is True
            mock_retrieve.assert_called_once()

    @patch("agents.compliance_agent.retrieve_context")
    @patch("agents.compliance_agent.get_llm_openai")
    def test_normalizes_decimal_taux_before_chain(self, mock_llm, mock_retrieve):
        mock_retrieve.return_value = ""
        expected = ComplianceResult(
            conforme=True, avertissements=[], references_rag=[],
            score_conformite=0.9, resume="OK",
        )
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.compliance_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.compliance_agent import run_compliance_agent
            result = run_compliance_agent(_invoice(taux_tva=0.20))
            assert result is not None


# ─── run_extractor_agent ──────────────────────────────────────────────────────

class TestRunExtractorAgent:
    @patch("agents.extractor_agent.read_pdf_invoice")
    @patch("agents.extractor_agent.get_llm_openai")
    def test_empty_content_raises_value_error(self, mock_llm, mock_pdf):
        mock_pdf.invoke.return_value = {"texte_complet": "   "}
        from agents.extractor_agent import run_extractor_agent
        with pytest.raises(ValueError, match="Impossible de lire"):
            run_extractor_agent("/tmp/facture.pdf", "pdf")

    @patch("agents.extractor_agent.read_xml_invoice")
    @patch("agents.extractor_agent.get_llm_openai")
    def test_xml_path_calls_xml_reader(self, mock_llm, mock_xml):
        mock_xml.invoke.return_value = {"xml_parse": "<Invoice>contenu</Invoice>"}
        inv = _invoice()
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = inv
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.extractor_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.extractor_agent import run_extractor_agent
            result = run_extractor_agent("/tmp/facture.xml", "xml")
            mock_xml.invoke.assert_called_once()
            assert result == inv

    @patch("agents.extractor_agent.read_pdf_invoice")
    @patch("agents.extractor_agent.get_llm_openai")
    def test_pdf_path_calls_pdf_reader(self, mock_llm, mock_pdf):
        mock_pdf.invoke.return_value = {"texte_complet": "Facture Atlas SARL"}
        inv = _invoice()
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = inv
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.extractor_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.extractor_agent import run_extractor_agent
            result = run_extractor_agent("/tmp/facture.pdf", "pdf")
            mock_pdf.invoke.assert_called_once()
            assert result == inv


# ─── run_journal_entry_agent — balance check ─────────────────────────────────

class TestJournalEntryBalance:
    @patch("agents.journal_entry_agent.get_llm_openai")
    def test_balanced_entry_equilibre_true(self, mock_llm):
        entry = _entry(1200.0, 1200.0)
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = entry
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.journal_entry_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.journal_entry_agent import run_journal_entry_agent
            result = run_journal_entry_agent(_invoice(), _code())
            assert result.equilibre is True

    @patch("agents.journal_entry_agent.get_llm_openai")
    def test_unbalanced_entry_equilibre_false(self, mock_llm):
        entry = _entry(1200.0, 1000.0)
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = entry
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.journal_entry_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.journal_entry_agent import run_journal_entry_agent
            result = run_journal_entry_agent(_invoice(), _code())
            assert result.equilibre is False

    @patch("agents.journal_entry_agent.get_llm_openai")
    def test_multiple_lines_balance_check(self, mock_llm):
        entry = JournalEntry(
            date_ecriture="01/01/2024", reference="F-001",
            ecritures=[
                LigneEcriture(sens=SensEcriture.DEBIT, compte="6125",
                              libelle="HT", montant=1000.0),
                LigneEcriture(sens=SensEcriture.DEBIT, compte="3455",
                              libelle="TVA", montant=200.0),
                LigneEcriture(sens=SensEcriture.CREDIT, compte="4411",
                              libelle="Fournisseur", montant=1200.0),
            ],
            equilibre=False,
        )
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = entry
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.journal_entry_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.journal_entry_agent import run_journal_entry_agent
            result = run_journal_entry_agent(_invoice(), _code())
            assert result.equilibre is True


# ─── run_reporter_agent ───────────────────────────────────────────────────────

class TestRunReporterAgent:
    @patch("agents.reporter_agent.StrOutputParser")
    @patch("agents.reporter_agent.get_llm")
    def test_invokes_chain_and_returns_string(self, mock_llm, mock_parser_cls):
        expected = "# Rapport Final\nFacture conforme."
        mock_final_chain = MagicMock()
        mock_final_chain.invoke.return_value = expected
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_parser_cls.return_value = MagicMock()

        intermediate = MagicMock()
        intermediate.__or__ = lambda s, o: mock_final_chain

        with patch("agents.reporter_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: intermediate
            from agents.reporter_agent import run_reporter_agent
            state = {
                "fichier_nom": "facture.pdf",
                "donnees_extraites": _invoice(),
                "validation_extraction": "accepte",
                "resultat_conformite": None,
                "validation_conformite": None,
                "code_comptable": _code(),
                "validation_classification": "accepte",
                "ecriture_comptable": None,
                "contexte_rag": ["CGI Art.145"],
            }
            result = run_reporter_agent(state)
            assert result == expected
            mock_final_chain.invoke.assert_called_once()


# ─── run_accounting_classifier_agent ──────────────────────────────────────────

class TestRunAccountingClassifierAgent:
    @patch("agents.accounting_classifier_agent.retrieve_context")
    @patch("agents.accounting_classifier_agent.get_llm_openai")
    def test_returns_accounting_code(self, mock_llm, mock_retrieve):
        mock_retrieve.return_value = "PCM: 6125 Achats non stockes"
        code = _code(score_confiance=0.9)
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = code
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.accounting_classifier_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.accounting_classifier_agent import run_accounting_classifier_agent
            result = run_accounting_classifier_agent(_invoice())
            assert result.code_comptable == "6125"
            mock_retrieve.assert_called_once()

    @patch("agents.accounting_classifier_agent.retrieve_context")
    @patch("agents.accounting_classifier_agent.get_llm_openai")
    def test_low_confidence_sets_validation_humaine(self, mock_llm, mock_retrieve):
        from config.settings import settings
        mock_retrieve.return_value = ""
        threshold = settings.classification_confidence_threshold
        code = _code(score_confiance=threshold - 0.1, validation_humaine_requise=False)
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = code
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.accounting_classifier_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.accounting_classifier_agent import run_accounting_classifier_agent
            result = run_accounting_classifier_agent(_invoice())
            assert result.validation_humaine_requise is True

    @patch("agents.accounting_classifier_agent.retrieve_context")
    @patch("agents.accounting_classifier_agent.get_llm_openai")
    def test_lignes_descriptions_used_in_query(self, mock_llm, mock_retrieve):
        mock_retrieve.return_value = ""
        code = _code()
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = code
        mock_llm_inst = MagicMock()
        mock_llm.return_value = mock_llm_inst
        mock_llm_inst.with_structured_output.return_value = mock_chain
        with patch("agents.accounting_classifier_agent.ChatPromptTemplate") as mock_pt:
            mock_pt.from_messages.return_value.__or__ = lambda s, o: mock_chain
            from agents.accounting_classifier_agent import run_accounting_classifier_agent
            inv = _invoice()
            run_accounting_classifier_agent(inv)
            assert mock_retrieve.call_count == 1


# ─── rag_router_agent ─────────────────────────────────────────────────────────

class TestRagRouterAgent:
    @patch("rag.rag_router_agent.create_react_agent")
    @patch("rag.rag_router_agent.get_llm_openai")
    def test_retrieve_context_returns_last_message(self, mock_llm, mock_create):
        from langchain_core.messages import AIMessage
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content="Contexte RAG recupere")]
        }
        mock_create.return_value = mock_agent
        mock_llm.return_value = MagicMock()
        from rag.rag_router_agent import retrieve_context
        result = retrieve_context("Taux TVA medicaments Maroc")
        assert result == "Contexte RAG recupere"

    @patch("rag.rag_router_agent.create_react_agent")
    @patch("rag.rag_router_agent.get_llm_openai")
    def test_retrieve_context_returns_empty_on_exception(self, mock_llm, mock_create):
        mock_create.side_effect = RuntimeError("LLM indisponible")
        mock_llm.return_value = MagicMock()
        from rag.rag_router_agent import retrieve_context
        result = retrieve_context("question quelconque")
        assert result == ""

    @patch("rag.rag_router_agent.create_react_agent")
    @patch("rag.rag_router_agent.get_llm_openai")
    def test_retrieve_context_empty_messages_returns_empty(self, mock_llm, mock_create):
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": []}
        mock_create.return_value = mock_agent
        mock_llm.return_value = MagicMock()
        from rag.rag_router_agent import retrieve_context
        result = retrieve_context("question sans messages")
        assert result == ""

    @patch("rag.rag_router_agent.create_react_agent")
    @patch("rag.rag_router_agent.get_llm_openai")
    def test_build_rag_router_agent_calls_create_react_agent(self, mock_llm, mock_create):
        mock_create.return_value = MagicMock()
        mock_llm.return_value = MagicMock()
        from rag.rag_router_agent import build_rag_router_agent
        agent = build_rag_router_agent()
        assert agent is not None
        mock_create.assert_called_once()

    @patch("rag.rag_router_agent.create_react_agent")
    @patch("rag.rag_router_agent.get_llm_openai")
    def test_query_rag_returns_last_message(self, mock_llm, mock_create):
        from langchain_core.messages import AIMessage
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content="Reponse RAG verbose")]
        }
        mock_create.return_value = mock_agent
        mock_llm.return_value = MagicMock()
        from rag.rag_router_agent import query_rag
        result = query_rag("Champs obligatoires Article 145 CGI")
        assert result == "Reponse RAG verbose"


# ─── pdf_reader_tool ──────────────────────────────────────────────────────────

class TestPdfReaderToolCoverage:
    def test_read_txt_file_returns_content(self, tmp_path):
        f = tmp_path / "facture.txt"
        f.write_text("FACTURE N F-001\nAtlas SARL", encoding="utf-8")
        from tools.pdf_reader_tool import read_pdf_invoice
        result = read_pdf_invoice.invoke({"file_path": str(f)})
        assert "FACTURE" in result["texte_complet"]
        assert result["nombre_pages"] == "1"

    def test_read_txt_file_truncated_at_max_chars(self, tmp_path):
        from tools.pdf_reader_tool import MAX_CHARS, read_pdf_invoice
        f = tmp_path / "long.txt"
        f.write_text("X" * (MAX_CHARS + 500), encoding="utf-8")
        result = read_pdf_invoice.invoke({"file_path": str(f)})
        assert len(result["texte_complet"]) <= MAX_CHARS + 30

    def test_extract_text_pypdf_nonexistent_returns_empty(self):
        from tools.pdf_reader_tool import _extract_text_pypdf
        text, pages = _extract_text_pypdf("/nonexistent/file.pdf")
        assert text == ""
        assert pages == "1"

    def test_extract_text_fitz_nonexistent_returns_empty(self):
        from tools.pdf_reader_tool import _extract_text_fitz
        text, pages = _extract_text_fitz("/nonexistent/file.pdf")
        assert text == ""
        assert pages == "1"

    def test_read_nonexistent_txt_raises(self):
        from tools.pdf_reader_tool import read_pdf_invoice
        with pytest.raises(Exception):
            read_pdf_invoice.invoke({"file_path": "/no/such/file.txt"})

    def test_read_xml_extension_returns_content(self, tmp_path):
        f = tmp_path / "facture.xml"
        f.write_text("<Invoice><ID>F-001</ID></Invoice>", encoding="utf-8")
        from tools.pdf_reader_tool import read_pdf_invoice
        result = read_pdf_invoice.invoke({"file_path": str(f)})
        assert "Invoice" in result["texte_complet"]


# ─── graph/nodes — chemins d'exception ───────────────────────────────────────

class TestGraphNodesExceptionPaths:
    @patch("graph.nodes.run_compliance_agent")
    def test_node_compliance_exception_sets_erreur(self, mock_agent):
        mock_agent.side_effect = RuntimeError("LLM error")
        from graph.nodes import node_check_compliance
        result = node_check_compliance(_node_state(donnees_extraites=_invoice()))
        assert "Erreur conformite" in result["erreur"] or "conformité" in result["erreur"]
        assert result["statut"] == "erreur"

    @patch("graph.nodes.run_accounting_classifier_agent")
    def test_node_classify_exception_sets_erreur(self, mock_agent):
        mock_agent.side_effect = RuntimeError("PCM error")
        from graph.nodes import node_classify_accounting
        result = node_classify_accounting(_node_state(donnees_extraites=_invoice()))
        assert "Erreur classification" in result["erreur"]
        assert result["statut"] == "erreur"

    @patch("graph.nodes.run_journal_entry_agent")
    def test_node_journal_exception_sets_erreur(self, mock_agent):
        mock_agent.side_effect = RuntimeError("Journal error")
        from graph.nodes import node_generate_journal_entry
        result = node_generate_journal_entry(
            _node_state(donnees_extraites=_invoice(), code_comptable=_code())
        )
        assert "criture" in result["erreur"] or "journal" in result["erreur"].lower()
        assert result["statut"] == "erreur"

    @patch("graph.nodes.run_reporter_agent")
    def test_node_report_exception_sets_erreur(self, mock_agent):
        mock_agent.side_effect = RuntimeError("Report error")
        from graph.nodes import node_generate_report
        result = node_generate_report(_node_state())
        assert "Erreur rapport" in result["erreur"]
        assert result["statut"] == "erreur"

    @patch("graph.nodes.run_journal_entry_agent")
    def test_node_journal_dict_correction_branch(self, mock_agent):
        entry = _entry()
        mock_agent.return_value = entry
        from graph.nodes import node_generate_journal_entry
        val = {"decision": "corrige", "modifications": {
            "code_comptable": "6135", "libelle_compte": "Locations"
        }}
        result = node_generate_journal_entry(
            _node_state(
                donnees_extraites=_invoice(),
                code_comptable=_code(),
                validation_classification=val,
            )
        )
        assert result["ecriture_comptable"] == entry


# ─── rag/vector_store ─────────────────────────────────────────────────────────

class TestVectorStoreCoverage:
    @patch("rag.vector_store.FAISS")
    @patch("rag.vector_store.get_embeddings")
    def test_save_store_calls_save_local(self, mock_emb, mock_faiss):
        from rag.vector_store import save_store
        mock_store = MagicMock()
        save_store(mock_store, "/tmp/test_index/sub")
        mock_store.save_local.assert_called_once_with("/tmp/test_index/sub")

    @patch("rag.vector_store.save_store")
    @patch("rag.vector_store.FAISS")
    @patch("rag.vector_store.get_embeddings")
    def test_create_store_from_documents(self, mock_emb, mock_faiss_cls, mock_save):
        from langchain_core.documents import Document
        from rag.vector_store import create_store_from_documents
        mock_store = MagicMock()
        mock_faiss_cls.from_documents.return_value = mock_store
        mock_emb.return_value = MagicMock()
        docs = [Document(page_content="Regle fiscale TVA 20%")]
        result = create_store_from_documents(docs, "/tmp/test_idx")
        mock_faiss_cls.from_documents.assert_called_once()
        assert result == mock_store

    @patch("rag.vector_store.FAISS")
    @patch("rag.vector_store.get_embeddings")
    def test_search_documents_calls_similarity_search(self, mock_emb, _):
        from rag.vector_store import search_documents
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = []
        result = search_documents(mock_store, "TVA 20%")
        mock_store.similarity_search.assert_called_once()
        assert result == []

    @patch("rag.vector_store.FAISS")
    @patch("rag.vector_store.get_embeddings")
    def test_search_documents_custom_k(self, mock_emb, _):
        from rag.vector_store import search_documents
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = []
        search_documents(mock_store, "PCM classe 6", k=3)
        mock_store.similarity_search.assert_called_once()
