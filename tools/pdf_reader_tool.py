from langchain.tools import tool
from pypdf import PdfReader
from typing import Dict


@tool
def read_pdf_invoice(file_path: str) -> Dict[str, str]:
    """
    Lit un fichier PDF de facture et retourne le texte extrait page par page.
    Utiliser pour extraire le contenu brut d'une facture au format PDF.
    """
    reader = PdfReader(file_path)
    pages_text = {}
    full_text = ""
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text[f"page_{i+1}"] = text
        full_text += text + "\n"
    return {
        "texte_complet": full_text,
        "nombre_pages": str(len(reader.pages)),
        "pages": str(pages_text),
    }
