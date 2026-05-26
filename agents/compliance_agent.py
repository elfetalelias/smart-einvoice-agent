from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm_openai
from rag.rag_router_agent import retrieve_context
from schemas.invoice_schema import InvoiceData
from schemas.compliance_schema import ComplianceResult

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "conformite.txt"

VALID_TVA_RATES = {0.0, 7.0, 10.0, 14.0, 20.0}


def _normalize_invoice(invoice_data: InvoiceData) -> InvoiceData:
    taux = invoice_data.taux_tva
    if 0 < taux <= 1.0:
        taux = round(taux * 100, 2)
    return invoice_data.model_copy(update={"taux_tva": taux})


def _arithmetic_summary(invoice: InvoiceData) -> str:
    """Calcule en Python les vérifications arithmétiques et retourne un résumé factuel."""
    tva_calculee = round(invoice.montant_ht * invoice.taux_tva / 100, 2)
    ttc_calcule = round(invoice.montant_ht + invoice.montant_tva, 2)

    tva_ok = abs(invoice.montant_tva - tva_calculee) <= 0.02
    ttc_ok = abs(invoice.montant_ttc - ttc_calcule) <= 0.02
    taux_ok = invoice.taux_tva in VALID_TVA_RATES

    lines = [
        "=== VÉRIFICATION ARITHMÉTIQUE (calculée par le système Python — NE PAS recalculer) ===",
        f"taux_tva          = {invoice.taux_tva}% → {'VALIDE (Article 99 CGI)' if taux_ok else 'INVALIDE — taux non reconnu (Article 99 CGI)'}",
        f"tva_calculée      = {invoice.montant_ht} × {invoice.taux_tva} / 100 = {tva_calculee} MAD",
        f"montant_tva réel  = {invoice.montant_tva} MAD → {'CORRECT' if tva_ok else f'INCORRECT (écart = {abs(invoice.montant_tva - tva_calculee):.2f} MAD)'}",
        f"ttc_calculé       = {invoice.montant_ht} + {invoice.montant_tva} = {ttc_calcule} MAD",
        f"montant_ttc réel  = {invoice.montant_ttc} MAD → {'CORRECT' if ttc_ok else f'INCORRECT (écart = {abs(invoice.montant_ttc - ttc_calcule):.2f} MAD)'}",
        "=== FIN VÉRIFICATION ARITHMÉTIQUE ===",
    ]
    return "\n".join(lines)


def run_compliance_agent(invoice_data: InvoiceData) -> ComplianceResult:
    """Vérifie la conformité fiscale de la facture en consultant le RAG."""
    invoice_data = _normalize_invoice(invoice_data)

    # Routing RAG implicite par LLM — l'agent choisit les corpus pertinents
    query = (
        f"Règles de conformité fiscale marocaine pour une facture : "
        f"TVA {invoice_data.taux_tva}%, fournisseur '{invoice_data.fournisseur}'. "
        f"Champs obligatoires Article 145 CGI, taux TVA valides Article 99 CGI, "
        f"ICE et IF obligatoires, mentions légales."
    )
    rag_context = retrieve_context(query)

    llm = get_llm_openai(temperature=0.0)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", (
            "Facture à vérifier :\n{invoice_json}\n\n"
            "{arithmetic_summary}\n\n"
            "Contexte RAG (routing LLM multi-corpus) :\n{rag_context}"
        )),
    ])

    chain = prompt | llm.with_structured_output(ComplianceResult)
    return chain.invoke({
        "invoice_json": invoice_data.model_dump_json(indent=2),
        "arithmetic_summary": _arithmetic_summary(invoice_data),
        "rag_context": rag_context,
    })
