import json
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config.llm import get_llm
from schemas.invoice_schema import InvoiceData
from schemas.accounting_schema import AccountingCode, JournalEntry, LigneEcriture, SensEcriture


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "ecriture_comptable.txt"


def run_journal_entry_agent(
    invoice_data: InvoiceData,
    accounting_code: AccountingCode,
) -> JournalEntry:
    """Génère l'écriture comptable Débit/Crédit suggérée."""
    llm = get_llm(temperature=0.0)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", (
            "Données facture :\n{invoice_json}\n\n"
            "Code comptable validé : {code} — {libelle}\n"
            "Générer l'écriture comptable JSON."
        )),
    ])

    chain = prompt | llm | JsonOutputParser()
    data = chain.invoke({
        "invoice_json": invoice_data.model_dump_json(indent=2),
        "code": accounting_code.code_comptable,
        "libelle": accounting_code.libelle_compte,
    })

    entry = JournalEntry(**data)
    total_debit = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.DEBIT)
    total_credit = sum(l.montant for l in entry.ecritures if l.sens == SensEcriture.CREDIT)
    entry = entry.model_copy(update={"equilibre": abs(total_debit - total_credit) < 0.01})
    return entry
