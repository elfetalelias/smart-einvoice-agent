from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm_openai
from rag.rag_router_agent import retrieve_context
from schemas.invoice_schema import InvoiceData
from schemas.accounting_schema import AccountingCode
from config.settings import settings

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classificateur_comptable.txt"


def run_accounting_classifier_agent(invoice_data: InvoiceData) -> AccountingCode:
    """Classifie la facture avec un code du Plan Comptable Marocain."""
    # Routing RAG implicite par LLM — l'agent choisit le corpus approprié (PCM + fiscal si besoin)
    descriptions = " ".join(
        l.description for l in invoice_data.lignes_facture
    ) or invoice_data.fournisseur
    rag_pcm = retrieve_context(
        f"Code comptable du Plan Comptable Marocain pour : {descriptions}. "
        f"Fournisseur : {invoice_data.fournisseur}. Montant HT : {invoice_data.montant_ht} MAD."
    )

    # Étape 2 : classification structurée
    llm = get_llm_openai(temperature=0.0)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", (
            "Facture à classifier :\n{invoice_json}\n\n"
            "Extraits du Plan Comptable Marocain :\n{rag_pcm}"
        )),
    ])

    chain = prompt | llm.with_structured_output(AccountingCode)
    result = chain.invoke({
        "invoice_json": invoice_data.model_dump_json(indent=2),
        "rag_pcm": rag_pcm,
    })

    # Forcer validation humaine si confiance insuffisante
    threshold = settings.classification_confidence_threshold
    if result.score_confiance < threshold:
        result = result.model_copy(update={"validation_humaine_requise": True})
    return result
