from pathlib import Path
from datetime import datetime
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.llm import get_llm

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "rapporteur.txt"


def run_reporter_agent(state: dict) -> str:
    """Génère le rapport final en Markdown à partir de l'état complet du workflow."""
    llm = get_llm(temperature=0.1)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Générer le rapport final pour :\n{state_json}"),
    ])

    chain = prompt | llm | StrOutputParser()

    state_summary = {
        "fichier_nom": state.get("fichier_nom", ""),
        "date_rapport": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "donnees_extraites": state.get("donnees_extraites"),
        "validation_extraction": state.get("validation_extraction"),
        "resultat_conformite": state.get("resultat_conformite"),
        "validation_conformite": state.get("validation_conformite"),
        "code_comptable": state.get("code_comptable"),
        "validation_classification": state.get("validation_classification"),
        "ecriture_comptable": state.get("ecriture_comptable"),
        "contexte_rag": state.get("contexte_rag", []),
    }

    return chain.invoke({
        "state_json": json.dumps(state_summary, default=str, ensure_ascii=False, indent=2)
    })
