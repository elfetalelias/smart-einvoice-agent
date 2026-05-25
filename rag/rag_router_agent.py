"""
Agent RAG à routing implicite par LLM (create_react_agent).

Le LLM analyse la question, choisit le tool approprié parmi les 3 corpus,
récupère les documents, puis génère une réponse — sans routing codé en dur.

Architecture (selon cours Prof. RETAL) :
  - Une fonction retriever par corpus
  - Chaque retriever dans un @tool LangChain
  - L'agent LLM choisit le tool selon la question
"""
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from config.llm import get_llm_openai
from tools.tax_rules_retriever_tool import search_regles_fiscales
from tools.einvoice_standards_retriever_tool import search_normes_facturation
from tools.accounting_plan_retriever_tool import search_plan_comptable

_TOOLS = [search_regles_fiscales, search_normes_facturation, search_plan_comptable]

_PROMPT = PromptTemplate.from_template("""
Tu es un expert en fiscalité et comptabilité marocaine.
Tu as accès à trois bases de connaissances spécialisées :
- search_regles_fiscales : règles fiscales marocaines (TVA, ICE, IF, CGI)
- search_normes_facturation : normes de facturation électronique marocaines (Article 145 CGI)
- search_plan_comptable : Plan Comptable Marocain (codes, classes, écritures)

Utilise le ou les outils appropriés pour répondre à la question.

{tools}

Utilise ce format :
Question: la question posée
Thought: je dois chercher dans le corpus approprié
Action: le tool à utiliser ({tool_names})
Action Input: la requête de recherche
Observation: le résultat du tool
... (répète si nécessaire)
Thought: j'ai assez d'informations
Final Answer: la réponse complète en français

Question: {input}
{agent_scratchpad}
""")


def build_rag_router_agent() -> AgentExecutor:
    """Construit l'agent RAG avec routing implicite par LLM."""
    llm = get_llm_openai(temperature=0.0)
    agent = create_react_agent(llm=llm, tools=_TOOLS, prompt=_PROMPT)
    return AgentExecutor(agent=agent, tools=_TOOLS, verbose=True, max_iterations=5, handle_parsing_errors=True)


def query_rag(question: str) -> str:
    """Pose une question au système RAG multi-corpus avec routing LLM."""
    executor = build_rag_router_agent()
    result = executor.invoke({"input": question})
    return result.get("output", "")


if __name__ == "__main__":
    exemples = [
        "Quel est le taux de TVA applicable aux médicaments au Maroc ?",
        "Quels sont les champs obligatoires d'une facture selon l'Article 145 CGI ?",
        "Quel code comptable utiliser pour un achat de fournitures de bureau ?",
    ]
    for q in exemples:
        print(f"\n{'='*60}")
        print(f"Question : {q}")
        print(f"{'='*60}")
        print(query_rag(q))
