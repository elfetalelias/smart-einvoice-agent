"""
Agent RAG a routing implicite par LLM (create_react_agent — LangGraph).

Architecture (selon cours Prof. RETAL) :
  - Une fonction retriever par corpus
  - Chaque retriever dans un @tool LangChain
  - L'agent LLM choisit le tool selon la question
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from config.llm import get_llm_openai
from tools.tax_rules_retriever_tool import search_regles_fiscales
from tools.einvoice_standards_retriever_tool import search_normes_facturation
from tools.accounting_plan_retriever_tool import search_plan_comptable

_TOOLS = [search_regles_fiscales, search_normes_facturation, search_plan_comptable]

_SYSTEM_PROMPT = (
    "Tu es un expert en fiscalite et comptabilite marocaine. "
    "Tu as acces a trois bases de connaissances specialisees : "
    "search_regles_fiscales (regles fiscales, TVA, ICE, IF, CGI 2026), "
    "search_normes_facturation (normes facturation electronique, Article 145 CGI), "
    "search_plan_comptable (Plan Comptable Marocain, codes, classes, ecritures). "
    "Utilise le ou les outils appropries selon la question. "
    "Retourne une reponse complete en francais avec les extraits pertinents."
)


def build_rag_router_agent():
    """Construit l'agent RAG avec routing implicite par LLM (LangGraph)."""
    llm = get_llm_openai(temperature=0.0)
    return create_react_agent(model=llm, tools=_TOOLS, prompt=_SYSTEM_PROMPT)


def retrieve_context(question: str) -> str:
    """
    Routing RAG implicite par LLM : l'agent choisit le(s) corpus pertinent(s)
    selon la question et retourne le contexte recupere.
    Utilise dans les agents de conformite et de classification.
    """
    try:
        agent = build_rag_router_agent()
        result = agent.invoke({"messages": [HumanMessage(content=question)]})
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return ""
    except Exception:
        return ""


def query_rag(question: str) -> str:
    """Pose une question au systeme RAG multi-corpus avec routing LLM."""
    agent = build_rag_router_agent()
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    messages = result.get("messages", [])
    return messages[-1].content if messages else ""


