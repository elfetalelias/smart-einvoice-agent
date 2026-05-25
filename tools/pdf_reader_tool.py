import base64
from langchain.tools import tool
from typing import Dict
from config.settings import settings

MAX_CHARS = 6000

_OCR_PROMPT = (
    "Extrais tout le texte visible de cette image de facture. "
    "Retourne uniquement le texte brut tel qu'il apparaît, sans reformatage ni commentaire."
)


def _extract_text_pypdf(file_path: str) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text = "".join((page.extract_text() or "") + "\n" for page in reader.pages)
        return text, str(len(reader.pages))
    except Exception:
        return "", "1"


def _extract_text_fitz(file_path: str) -> tuple[str, str]:
    try:
        import fitz
        doc = fitz.open(file_path)
        text = "".join(page.get_text() for page in doc)
        pages = str(len(doc))
        doc.close()
        return text, pages
    except Exception:
        return "", "1"


def _openai_vision_ocr(b64: str, mime: str = "image/png") -> str:
    """Call OpenAI Vision (gpt-4o-mini) with a base64 image and return extracted text."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": _OCR_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
        max_tokens=2000,
    )
    return response.choices[0].message.content or ""


def _ocr_with_vision(file_path: str) -> str:
    """Render each PDF page as PNG and send to OpenAI Vision for OCR."""
    import fitz

    doc = fitz.open(file_path)
    all_text = []
    for page in doc:
        mat = fitz.Matrix(150 / 72, 150 / 72)
        pix = page.get_pixmap(matrix=mat)
        b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        all_text.append(_openai_vision_ocr(b64, "image/png"))
    doc.close()
    return "\n\n".join(all_text)


def _ocr_image_with_vision(file_path: str) -> str:
    """Send a standalone image file (PNG/JPG) to OpenAI Vision for OCR."""
    import mimetypes

    mime, _ = mimetypes.guess_type(file_path)
    mime = mime or "image/png"
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return _openai_vision_ocr(b64, mime)


@tool
def read_pdf_invoice(file_path: str) -> Dict[str, str]:
    """
    Lit une facture PDF, image ou texte et retourne le contenu extrait.
    Supporte : PDF natif, PDF scanné (OCR Vision), PNG, JPG, TXT.
    """
    lower = file_path.lower()
    nombre_pages = "1"

    # ── Image directe (PNG / JPG) ──────────────────────────────────────────
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        full_text = _ocr_image_with_vision(file_path)
        if full_text.strip():
            return {"texte_complet": full_text[:MAX_CHARS], "nombre_pages": "1"}
        raise ValueError("Impossible d'extraire le texte de cette image.")

    # ── Fichier texte brut ─────────────────────────────────────────────────
    if lower.endswith((".txt", ".xml")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                full_text = f.read()
            return {"texte_complet": full_text[:MAX_CHARS], "nombre_pages": "1"}
        except Exception as exc:
            raise ValueError(f"Impossible de lire le fichier texte : {exc}") from exc

    # ── PDF : Tier 1 — pypdf (texte natif) ────────────────────────────────
    full_text, nombre_pages = _extract_text_pypdf(file_path)

    # ── PDF : Tier 2 — pymupdf (meilleure extraction native) ──────────────
    if not full_text.strip():
        full_text, nombre_pages = _extract_text_fitz(file_path)

    # ── PDF : Tier 3 — OpenAI Vision OCR (PDF scanné / image) ────────────
    if not full_text.strip():
        full_text = _ocr_with_vision(file_path)
        if not full_text.strip():
            raise ValueError(
                "Impossible d'extraire le texte de ce fichier même avec l'OCR. "
                "Vérifiez la qualité du scan ou téléversez un fichier .txt ou .xml."
            )

    if len(full_text) > MAX_CHARS:
        full_text = full_text[:MAX_CHARS] + "\n[... contenu tronqué ...]"

    return {"texte_complet": full_text, "nombre_pages": nombre_pages}
