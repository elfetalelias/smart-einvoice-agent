"""
Application Streamlit — Système Intelligent de Traitement des Factures
Interface en français avec validation humaine à 3 étapes.
"""
import streamlit as st
import tempfile
import os
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="Système de Traitement des Factures",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS personnalisé ---
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1a5276;
        border-bottom: 3px solid #2e86c1;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2e86c1;
        margin-top: 1.5rem;
    }
    .status-ok { color: #27ae60; font-weight: bold; }
    .status-warn { color: #e67e22; font-weight: bold; }
    .status-error { color: #e74c3c; font-weight: bold; }
    .confidence-high { color: #27ae60; }
    .confidence-med { color: #e67e22; }
    .confidence-low { color: #e74c3c; }
    .avertissement-critique { background: #fdecea; border-left: 4px solid #e74c3c; padding: 0.5rem; }
    .avertissement-majeur { background: #fef9e7; border-left: 4px solid #f39c12; padding: 0.5rem; }
    .avertissement-mineur { background: #eaf4fb; border-left: 4px solid #3498db; padding: 0.5rem; }
</style>
""", unsafe_allow_html=True)


def init_session() -> None:
    """Initialise l'état de session Streamlit."""
    defaults = {
        "etape": 1,
        "fichier_temp": None,
        "fichier_type": None,
        "fichier_nom": None,
        "invoice_state": None,
        "analyse_lancee": False,
        "validation_1_faite": False,
        "validation_2_faite": False,
        "validation_3_faite": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def afficher_score_confiance(score: float) -> str:
    if score >= 0.8:
        return f"🟢 Élevé ({score:.0%})"
    elif score >= 0.6:
        return f"🟡 Moyen ({score:.0%})"
    return f"🔴 Faible ({score:.0%})"


def etape_1_telechargement() -> None:
    st.markdown('<div class="main-header">🧾 Système Intelligent de Traitement des Factures</div>',
                unsafe_allow_html=True)
    st.markdown("**Assistant IA pour la vérification de conformité et la classification comptable**")
    st.info("ℹ️ Ce système est un assistant. Toutes les décisions comptables doivent être "
            "validées par un expert-comptable qualifié.")

    st.markdown('<div class="section-header">📁 Étape 1 — Téléversement de la Facture</div>',
                unsafe_allow_html=True)

    fichier = st.file_uploader(
        "Téléverser une facture",
        type=["pdf", "xml"],
        help="Formats acceptés : PDF (texte natif) ou XML (UBL / Factur-X)",
    )

    if fichier:
        ext = Path(fichier.name).suffix.lower().lstrip(".")
        st.session_state.fichier_type = ext
        st.session_state.fichier_nom = fichier.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(fichier.read())
            st.session_state.fichier_temp = tmp.name

        st.success(f"✅ Fichier téléversé : **{fichier.name}** ({ext.upper()})")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True):
                with st.spinner("Analyse en cours... Veuillez patienter."):
                    _lancer_analyse()

    if st.session_state.analyse_lancee:
        etape_2_donnees_extraites()


def _lancer_analyse() -> None:
    """Lance l'extraction via LangGraph."""
    from graph.invoice_state import InvoiceState
    from agents.extractor_agent import run_extractor_agent

    try:
        invoice_data = run_extractor_agent(
            file_path=st.session_state.fichier_temp,
            file_type=st.session_state.fichier_type,
        )
        state: InvoiceState = {
            "fichier_path": st.session_state.fichier_temp,
            "fichier_type": st.session_state.fichier_type,
            "fichier_nom": st.session_state.fichier_nom,
            "statut": "extraction_terminée",
            "etape_courante": "Extraction terminée",
            "erreur": None,
            "donnees_extraites": invoice_data,
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
        st.session_state.invoice_state = state
        st.session_state.analyse_lancee = True
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse : {e}")


def etape_2_donnees_extraites() -> None:
    state = st.session_state.invoice_state
    if not state:
        return

    st.markdown('<div class="section-header">📋 Étape 2 — Données Extraites</div>',
                unsafe_allow_html=True)

    invoice = state.get("donnees_extraites")
    if not invoice:
        st.error("Aucune donnée extraite.")
        return

    score = invoice.score_confiance
    st.markdown(f"**Niveau de confiance de l'extraction :** {afficher_score_confiance(score)}")

    if invoice.champs_manquants:
        st.warning(f"⚠️ Champs non détectés : {', '.join(invoice.champs_manquants)}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Informations Fournisseur**")
        data_table = {
            "Champ": ["Fournisseur", "N° Facture", "Date", "ICE", "IF", "Devise"],
            "Valeur": [
                invoice.fournisseur,
                invoice.numero_facture,
                invoice.date_facture,
                invoice.ice or "Non renseigné",
                invoice.if_fournisseur or "Non renseigné",
                invoice.devise,
            ],
        }
        st.table(data_table)

    with col2:
        st.markdown("**Montants**")
        montants = {
            "Champ": ["Montant HT", "Taux TVA", "Montant TVA", "Montant TTC"],
            "Valeur": [
                f"{invoice.montant_ht:,.2f} {invoice.devise}",
                f"{invoice.taux_tva}%",
                f"{invoice.montant_tva:,.2f} {invoice.devise}",
                f"{invoice.montant_ttc:,.2f} {invoice.devise}",
            ],
        }
        st.table(montants)

    if invoice.lignes_facture:
        st.markdown("**Lignes de Facture**")
        lignes_data = [
            {
                "Description": l.description,
                "Quantité": l.quantite,
                "PU HT": f"{l.prix_unitaire:,.2f}",
                "Montant HT": f"{l.montant_ht:,.2f}",
                "TVA %": f"{l.taux_tva}%",
            }
            for l in invoice.lignes_facture
        ]
        st.dataframe(lignes_data, use_container_width=True)

    # --- VALIDATION HUMAINE #1 ---
    if not st.session_state.validation_1_faite:
        st.markdown("---")
        st.markdown("### ✅ Validation Humaine — Données Extraites")
        st.warning("Veuillez vérifier les données extraites avant de continuer.")

        col_ok, col_mod, col_rej = st.columns(3)
        with col_ok:
            if st.button("✅ Accepter", type="primary", use_container_width=True):
                _valider_extraction("accepté", None)

        with col_mod:
            with st.expander("✏️ Modifier"):
                fournisseur_mod = st.text_input("Fournisseur", value=invoice.fournisseur)
                numero_mod = st.text_input("N° Facture", value=invoice.numero_facture)
                ht_mod = st.number_input("Montant HT", value=invoice.montant_ht, format="%.2f")
                tva_mod = st.number_input("Montant TVA", value=invoice.montant_tva, format="%.2f")
                ttc_mod = st.number_input("Montant TTC", value=invoice.montant_ttc, format="%.2f")
                if st.button("💾 Sauvegarder les modifications", use_container_width=True):
                    mods = {
                        "fournisseur": fournisseur_mod,
                        "numero_facture": numero_mod,
                        "montant_ht": ht_mod,
                        "montant_tva": tva_mod,
                        "montant_ttc": ttc_mod,
                    }
                    _valider_extraction("modifié", mods)

        with col_rej:
            if st.button("❌ Rejeter", use_container_width=True):
                _valider_extraction("rejeté", None)

    if st.session_state.validation_1_faite:
        decision = state.get("validation_extraction", {}).get("decision", "")
        if decision in ("accepté", "modifié"):
            etape_3_conformite()
        elif decision == "rejeté":
            st.error("❌ Extraction rejetée. Le traitement est arrêté.")


def _valider_extraction(decision: str, modifications) -> None:
    state = st.session_state.invoice_state
    state["validation_extraction"] = {
        "decision": decision,
        "commentaire": f"Décision : {decision}",
        "modifications": modifications,
    }
    state["statut"] = "validation_1_faite"
    st.session_state.validation_1_faite = True

    if decision == "modifié" and modifications:
        invoice = state["donnees_extraites"]
        updated = invoice.model_copy(update=modifications)
        state["donnees_extraites"] = updated

    if decision in ("accepté", "modifié"):
        with st.spinner("Vérification de conformité en cours..."):
            from agents.compliance_agent import run_compliance_agent
            try:
                compliance = run_compliance_agent(state["donnees_extraites"])
                state["resultat_conformite"] = compliance
                state["statut"] = "conformite_vérifiée"
            except Exception as e:
                state["erreur"] = str(e)
    st.rerun()


def etape_3_conformite() -> None:
    state = st.session_state.invoice_state
    compliance = state.get("resultat_conformite")
    if not compliance:
        return

    st.markdown('<div class="section-header">🔍 Étape 3 — Vérification de Conformité</div>',
                unsafe_allow_html=True)

    status_icon = "✅" if compliance.conforme else "⚠️"
    status_text = "CONFORME" if compliance.conforme else "NON CONFORME"
    st.markdown(f"**Statut :** {status_icon} {status_text} | "
                f"**Score :** {afficher_score_confiance(compliance.score_conformite)}")

    if compliance.avertissements:
        st.markdown("**Avertissements détectés :**")
        for avert in compliance.avertissements:
            niveau_map = {
                "critique": ("🔴", "avertissement-critique"),
                "majeur": ("🟡", "avertissement-majeur"),
                "mineur": ("🔵", "avertissement-mineur"),
            }
            icon, css_class = niveau_map.get(avert.niveau, ("⚪", ""))
            ref = f" — *{avert.reference_legale}*" if avert.reference_legale else ""
            st.markdown(
                f'<div class="{css_class}">{icon} <b>[{avert.niveau.upper()}]</b> '
                f'{avert.message}{ref}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ Aucun avertissement — Facture conforme.")

    if compliance.references_rag:
        with st.expander("📚 Références réglementaires consultées"):
            for ref in compliance.references_rag:
                st.markdown(f"- {ref}")

    if not st.session_state.validation_2_faite:
        st.markdown("---")
        st.markdown("### ✅ Validation Humaine — Conformité")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmer et continuer", type="primary", use_container_width=True):
                _valider_conformite("confirmé")
        with col2:
            if st.button("⚠️ Ignorer et continuer", use_container_width=True):
                _valider_conformite("ignoré")

    if st.session_state.validation_2_faite:
        etape_4_classification()


def _valider_conformite(decision: str) -> None:
    state = st.session_state.invoice_state
    state["validation_conformite"] = {"decision": decision, "commentaire": None, "modifications": None}
    state["statut"] = "validation_2_faite"
    st.session_state.validation_2_faite = True

    with st.spinner("Classification comptable en cours..."):
        from agents.accounting_classifier_agent import run_accounting_classifier_agent
        try:
            code = run_accounting_classifier_agent(state["donnees_extraites"])
            state["code_comptable"] = code
            state["statut"] = "classification_terminée"
        except Exception as e:
            state["erreur"] = str(e)
    st.rerun()


def etape_4_classification() -> None:
    state = st.session_state.invoice_state
    code = state.get("code_comptable")
    if not code:
        return

    st.markdown('<div class="section-header">📂 Étape 4 — Classification Comptable</div>',
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Code Comptable Suggéré", code.code_comptable)
        st.markdown(f"**Libellé :** {code.libelle_compte}")
    with col2:
        st.metric("Niveau de Confiance", afficher_score_confiance(code.score_confiance))
        if code.validation_humaine_requise:
            st.warning("⚠️ Validation humaine recommandée (confiance faible)")

    st.markdown(f"**Justification :** {code.justification}")

    if code.alternatives:
        with st.expander("📋 Codes alternatifs proposés"):
            for alt in code.alternatives:
                st.markdown(f"- `{alt.code}` — {alt.libelle} (score: {alt.score:.0%})")

    if not st.session_state.validation_3_faite:
        st.markdown("---")
        st.markdown("### ✅ Validation Humaine — Classification Comptable")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Accepter le code proposé", type="primary", use_container_width=True):
                _valider_classification("accepté", None)
        with col2:
            with st.expander("✏️ Corriger le code"):
                code_corrige = st.text_input("Nouveau code PCM", value=code.code_comptable)
                libelle_corrige = st.text_input("Libellé", value=code.libelle_compte)
                if st.button("💾 Appliquer la correction", use_container_width=True):
                    _valider_classification("corrigé", {
                        "code_comptable": code_corrige,
                        "libelle_compte": libelle_corrige,
                    })

    if st.session_state.validation_3_faite:
        etape_5_ecriture()


def _valider_classification(decision: str, modifications) -> None:
    state = st.session_state.invoice_state
    state["validation_classification"] = {
        "decision": decision,
        "commentaire": None,
        "modifications": modifications,
    }
    state["statut"] = "validation_3_faite"
    st.session_state.validation_3_faite = True

    with st.spinner("Génération de l'écriture comptable..."):
        from agents.journal_entry_agent import run_journal_entry_agent
        try:
            entry = run_journal_entry_agent(
                state["donnees_extraites"],
                state["code_comptable"],
            )
            state["ecriture_comptable"] = entry
            state["statut"] = "journal_généré"
        except Exception as e:
            state["erreur"] = str(e)
    st.rerun()


def etape_5_ecriture() -> None:
    state = st.session_state.invoice_state
    entry = state.get("ecriture_comptable")
    if not entry:
        return

    st.markdown('<div class="section-header">📝 Étape 5 — Écriture Comptable Suggérée</div>',
                unsafe_allow_html=True)
    st.warning("⚠️ Cette écriture est une SUGGESTION. Elle doit être validée par un comptable qualifié.")

    equilibre_icon = "✅" if entry.equilibre else "❌"
    st.markdown(f"**Référence :** {entry.reference} | **Équilibre :** {equilibre_icon}")

    ecritures_data = [
        {
            "Sens": l.sens,
            "Compte": l.compte,
            "Libellé": l.libelle,
            "Montant (MAD)": f"{l.montant:,.2f}",
        }
        for l in entry.ecritures
    ]
    st.dataframe(ecritures_data, use_container_width=True)

    if entry.avertissement:
        st.warning(f"⚠️ {entry.avertissement}")

    st.markdown("---")
    if st.button("📄 Générer le Rapport Final", type="primary", use_container_width=False):
        with st.spinner("Génération du rapport en cours..."):
            _generer_rapport()


def _generer_rapport() -> None:
    state = st.session_state.invoice_state
    from agents.reporter_agent import run_reporter_agent
    try:
        rapport = run_reporter_agent(state)
        state["rapport_final"] = rapport
        state["rapport_genere"] = True
        state["statut"] = "rapport_généré"
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erreur rapport : {e}")


def etape_6_rapport() -> None:
    state = st.session_state.invoice_state
    if not state or not state.get("rapport_genere"):
        return

    st.markdown('<div class="section-header">📊 Rapport Final</div>', unsafe_allow_html=True)
    rapport = state.get("rapport_final", "")
    st.markdown(rapport)

    os.makedirs("data/outputs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"data/outputs/rapport_{ts}.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rapport)

    st.download_button(
        label="⬇️ Télécharger le Rapport",
        data=rapport.encode("utf-8"),
        file_name=f"rapport_facture_{ts}.md",
        mime="text/markdown",
    )
    st.success(f"✅ Rapport sauvegardé : {output_path}")


def barre_progression() -> None:
    etapes = [
        ("📁 Téléversement", st.session_state.analyse_lancee),
        ("📋 Données Extraites", st.session_state.validation_1_faite),
        ("🔍 Conformité", st.session_state.validation_2_faite),
        ("📂 Classification", st.session_state.validation_3_faite),
        ("📝 Écriture", bool(
            st.session_state.invoice_state
            and st.session_state.invoice_state.get("ecriture_comptable")
        )),
        ("📊 Rapport", bool(
            st.session_state.invoice_state
            and st.session_state.invoice_state.get("rapport_genere")
        )),
    ]
    st.sidebar.markdown("### 📊 Progression")
    for nom, fait in etapes:
        icon = "✅" if fait else "⏳"
        st.sidebar.markdown(f"{icon} {nom}")

    if st.sidebar.button("🔄 Nouvelle Analyse", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main() -> None:
    init_session()
    barre_progression()

    etape_1_telechargement()

    state = st.session_state.invoice_state
    if state and state.get("rapport_genere"):
        etape_6_rapport()


if __name__ == "__main__":
    main()
