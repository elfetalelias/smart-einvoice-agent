from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm_openai
from tools.pdf_reader_tool import read_pdf_invoice
from tools.xml_reader_tool import read_xml_invoice
from schemas.invoice_schema import InvoiceData

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extracteur.txt"


def run_extractor_agent(file_path: str, file_type: str) -> InvoiceData:
    """Extrait les données structurées d'une facture PDF ou XML."""
    # Étape 1 : lire le contenu brut du fichier
    if file_type == "xml":
        raw = read_xml_invoice.invoke({"file_path": file_path})
        content = raw.get("xml_parse", "")
    else:
        # handles pdf, txt, png, jpg, jpeg, webp — OCR via Vision if needed
        raw = read_pdf_invoice.invoke({"file_path": file_path})
        content = raw.get("texte_complet", "")

    if not content.strip():
        raise ValueError("Impossible de lire le contenu du fichier.")

    # Étape 2 : extraction structurée via with_structured_output
    llm = get_llm_openai(temperature=0.0)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Extraire toutes les données de cette facture :\n\n{content}"),
    ])

    chain = prompt | llm.with_structured_output(InvoiceData)
    return chain.invoke({"content": content})
