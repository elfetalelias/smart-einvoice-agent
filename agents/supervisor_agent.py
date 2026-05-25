from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.llm import get_llm
from graph.invoice_state import InvoiceState

VALID_NODES = {
    "extract_invoice",
    "human_validation_1",
    "check_compliance",
    "human_validation_2",
    "classify_accounting",
    "human_validation_3",
    "generate_journal_entry",
    "generate_report",
    "END",
}

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "superviseur.txt"


def decide_next_node(state: InvoiceState) -> str:
    """Détermine le prochain nœud à activer en fonction de l'état courant."""
    statut = state.get("statut", "")
    erreur = state.get("erreur")

    if erreur:
        return "END"

    routing_table = {
        "fichier_reçu": "extract_invoice",
        "extraction_terminée": "human_validation_1",
        "conformite_vérifiée": "human_validation_2",
        "classification_terminée": "human_validation_3",
        "journal_généré": "generate_report",
        "rapport_généré": "END",
    }

    val_extraction = state.get("validation_extraction")
    if statut == "validation_1_faite":
        if val_extraction and val_extraction.get("decision") in ("accepté", "modifié"):
            return "check_compliance"
        return "END"

    val_conformite = state.get("validation_conformite")
    if statut == "validation_2_faite":
        return "classify_accounting"

    val_classification = state.get("validation_classification")
    if statut == "validation_3_faite":
        if val_classification and val_classification.get("decision") in ("accepté", "corrigé"):
            return "generate_journal_entry"
        return "END"

    return routing_table.get(statut, "END")
