"""
Démonstration du workflow LangGraph pour une seule facture.

Usage :
    uv run python demo_graph.py data/sample_invoices/facture_test_01.txt

Ce script exécute le graphe LangGraph complet (graph/invoice_graph.py) sur
une facture en mode automatique (validation humaine simulée = accepté).
"""
import sys
from pathlib import Path
from graph.invoice_graph import invoice_graph
from graph.invoice_state import InvoiceState


def run_demo(file_path: str) -> None:
    ext = Path(file_path).suffix.lower().lstrip(".")
    file_type = "xml" if ext == "xml" else "pdf"

    print(f"\n{'='*60}")
    print(f"  DEMO LangGraph — {Path(file_path).name}")
    print(f"{'='*60}\n")

    initial_state: InvoiceState = {
        "fichier_path": file_path,
        "fichier_type": file_type,
        "fichier_nom": Path(file_path).name,
        "statut": "fichier_reçu",
        "etape_courante": "Initialisation",
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

    # Étape 1 — Extraction
    print("[1/5] Extraction des données...")
    from graph.nodes import node_extract_invoice
    state = node_extract_invoice(initial_state)
    if state.get("erreur"):
        print(f"  ❌ Erreur : {state['erreur']}")
        return
    inv = state["donnees_extraites"]
    print(f"  ✅ Fournisseur  : {inv.fournisseur}")
    print(f"  ✅ N° Facture   : {inv.numero_facture}")
    print(f"  ✅ Montant TTC  : {inv.montant_ttc} MAD")
    print(f"  ✅ Confiance    : {inv.score_confiance:.0%}")

    # Validation humaine simulée #1
    state = {**state, "statut": "validation_1_faite", "validation_extraction": {"decision": "accepté", "commentaire": "OK (demo)"}}

    # Étape 2 — Conformité
    print("\n[2/5] Vérification de conformité fiscale...")
    from graph.nodes import node_check_compliance
    state = node_check_compliance(state)
    if state.get("erreur"):
        print(f"  ❌ Erreur : {state['erreur']}")
        return
    comp = state["resultat_conformite"]
    statut = "✅ CONFORME" if comp.conforme else "⚠️ NON CONFORME"
    print(f"  {statut} — Score : {comp.score_conformite:.0%}")
    for a in comp.avertissements:
        print(f"  [{a.niveau}] {a.message}")

    # Validation humaine simulée #2
    state = {**state, "statut": "validation_2_faite", "validation_conformite": {"decision": "confirmé", "commentaire": "OK (demo)"}}

    # Étape 3 — Classification
    print("\n[3/5] Classification comptable (PCM)...")
    from graph.nodes import node_classify_accounting
    state = node_classify_accounting(state)
    if state.get("erreur"):
        print(f"  ❌ Erreur : {state['erreur']}")
        return
    code = state["code_comptable"]
    print(f"  ✅ Code PCM    : {code.code_comptable} — {code.libelle_compte}")
    print(f"  ✅ Confiance   : {code.score_confiance:.0%}")

    # Validation humaine simulée #3
    state = {**state, "statut": "validation_3_faite", "validation_classification": {"decision": "accepté", "commentaire": "OK (demo)"}}

    # Étape 4 — Écriture comptable
    print("\n[4/5] Génération de l'écriture comptable...")
    from graph.nodes import node_generate_journal_entry
    state = node_generate_journal_entry(state)
    if state.get("erreur"):
        print(f"  ❌ Erreur : {state['erreur']}")
        return
    entry = state["ecriture_comptable"]
    for ligne in entry.ecritures:
        print(f"  {ligne.sens:<8} | {ligne.compte:<10} | {ligne.libelle:<40} | {ligne.montant:>12.2f} MAD")
    eq = "✅ Équilibrée" if entry.equilibre else "❌ Déséquilibrée"
    print(f"  → Écriture {eq}")

    # Étape 5 — Rapport
    print("\n[5/5] Génération du rapport final...")
    from graph.nodes import node_generate_report
    state = node_generate_report(state)
    if state.get("erreur"):
        print(f"  ❌ Erreur : {state['erreur']}")
        return
    print(f"  ✅ Rapport généré ({len(state['rapport_final'])} caractères)")

    print(f"\n{'='*60}")
    print("  WORKFLOW LANGGRAPH TERMINÉ AVEC SUCCÈS")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_invoices/facture_test_01.txt"
    run_demo(path)
