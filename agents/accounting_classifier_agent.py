import json
from pathlib import Path
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm
from tools.accounting_plan_retriever_tool import search_plan_comptable
from schemas.invoice_schema import InvoiceData
from schemas.accounting_schema import AccountingCode
from config.settings import settings


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "classificateur_comptable.txt"


def run_accounting_classifier_agent(invoice_data: InvoiceData) -> AccountingCode:
    """Classifie la facture avec un code du Plan Comptable Marocain."""
    llm = get_llm(temperature=0.0)
    tools = [search_plan_comptable]

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Classifier cette facture selon le PCM :\n{invoice_json}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    result = executor.invoke({
        "invoice_json": invoice_data.model_dump_json(indent=2),
    })

    raw_output = result.get("output", "{}")
    if isinstance(raw_output, str):
        start = raw_output.find("{")
        end = raw_output.rfind("}") + 1
        json_str = raw_output[start:end] if start >= 0 else "{}"
        data = json.loads(json_str)
    else:
        data = raw_output

    result_obj = AccountingCode(**data)
    threshold = settings.classification_confidence_threshold
    if result_obj.score_confiance < threshold:
        result_obj = result_obj.model_copy(update={"validation_humaine_requise": True})
    return result_obj
