from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm_openai
from schemas.invoice_schema import InvoiceData
from schemas.accounting_schema import AccountingCode, JournalEntry, SensEcriture

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "ecriture_comptable.txt"


def run_journal_entry_agent(invoice_data: InvoiceData, accounting_code: AccountingCode) -> JournalEntry:
    """Génère l'écriture comptable Débit/Crédit suggérée."""
    llm = get_llm_openai(temperature=0.0)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", (
            "Générer l'écriture comptable pour :\n"
            "Facture : {invoice_json}\n"
            "Code comptable validé : {code} — {libelle}"
        )),
    ])

    chain = prompt | llm.with_structured_output(JournalEntry)
    entry = chain.invoke({
        "invoice_json": invoice_data.model_dump_json(indent=2),
        "code": accounting_code.code_comptable,
        "libelle": accounting_code.libelle_compte,
    })

    # Vérifier l'équilibre Débit = Crédit
    total_d = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.DEBIT)
    total_c = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.CREDIT)
    return entry.model_copy(update={"equilibre": abs(total_d - total_c) < 0.02})
