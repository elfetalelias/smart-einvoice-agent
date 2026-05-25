from graph.invoice_state import InvoiceState
from agents.extractor_agent import run_extractor_agent
from agents.compliance_agent import run_compliance_agent
from agents.accounting_classifier_agent import run_accounting_classifier_agent
from agents.journal_entry_agent import run_journal_entry_agent
from agents.reporter_agent import run_reporter_agent


def node_extract_invoice(state: InvoiceState) -> InvoiceState:
    """Nœud : extraction des données de la facture."""
    try:
        invoice_data = run_extractor_agent(
            file_path=state["fichier_path"],
            file_type=state["fichier_type"],
        )
        return {
            **state,
            "donnees_extraites": invoice_data,
            "statut": "extraction_terminée",
            "etape_courante": "Extraction terminée",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur extraction : {str(e)}", "statut": "erreur"}


def node_check_compliance(state: InvoiceState) -> InvoiceState:
    """Nœud : vérification de conformité fiscale."""
    try:
        invoice_data = state["donnees_extraites"]
        compliance = run_compliance_agent(invoice_data)
        return {
            **state,
            "resultat_conformite": compliance,
            "statut": "conformite_vérifiée",
            "etape_courante": "Conformité vérifiée",
            "contexte_rag": state.get("contexte_rag", []) + compliance.references_rag,
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur conformité : {str(e)}", "statut": "erreur"}


def node_classify_accounting(state: InvoiceState) -> InvoiceState:
    """Nœud : classification comptable PCM."""
    try:
        invoice_data = state["donnees_extraites"]
        code = run_accounting_classifier_agent(invoice_data)
        return {
            **state,
            "code_comptable": code,
            "statut": "classification_terminée",
            "etape_courante": "Classification comptable terminée",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur classification : {str(e)}", "statut": "erreur"}


def node_generate_journal_entry(state: InvoiceState) -> InvoiceState:
    """Nœud : génération de l'écriture comptable."""
    try:
        invoice_data = state["donnees_extraites"]
        code = state["code_comptable"]

        # Appliquer la correction humaine si présente
        val = state.get("validation_classification", {})
        if val and val.get("decision") == "corrigé" and val.get("modifications"):
            mods = val["modifications"]
            if "code_comptable" in mods:
                code = code.model_copy(update={
                    "code_comptable": mods["code_comptable"],
                    "libelle_compte": mods.get("libelle_compte", code.libelle_compte),
                })

        entry = run_journal_entry_agent(invoice_data, code)
        return {
            **state,
            "ecriture_comptable": entry,
            "statut": "journal_généré",
            "etape_courante": "Écriture comptable générée",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur écriture comptable : {str(e)}", "statut": "erreur"}


def node_generate_report(state: InvoiceState) -> InvoiceState:
    """Nœud : génération du rapport final."""
    try:
        rapport = run_reporter_agent(state)
        return {
            **state,
            "rapport_final": rapport,
            "rapport_genere": True,
            "statut": "rapport_généré",
            "etape_courante": "Rapport final généré",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur rapport : {str(e)}", "statut": "erreur"}


# Nœuds de validation humaine — retournent l'état tel quel
# La logique de validation est gérée dans l'interface Streamlit
def node_human_validation_1(state: InvoiceState) -> InvoiceState:
    """Nœud d'attente : validation humaine des données extraites."""
    return {**state, "etape_courante": "En attente de validation humaine (extraction)"}


def node_human_validation_2(state: InvoiceState) -> InvoiceState:
    """Nœud d'attente : validation humaine de la conformité."""
    return {**state, "etape_courante": "En attente de validation humaine (conformité)"}


def node_human_validation_3(state: InvoiceState) -> InvoiceState:
    """Nœud d'attente : validation humaine de la classification."""
    return {**state, "etape_courante": "En attente de validation humaine (classification)"}
