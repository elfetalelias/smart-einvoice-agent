import json
from pathlib import Path
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm
from tools.tax_rules_retriever_tool import search_regles_fiscales
from tools.einvoice_standards_retriever_tool import search_normes_facturation
from schemas.invoice_schema import InvoiceData
from schemas.compliance_schema import ComplianceResult


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "conformite.txt"


def run_compliance_agent(invoice_data: InvoiceData) -> ComplianceResult:
    """Vérifie la conformité fiscale marocaine de la facture extraite."""
    llm = get_llm(temperature=0.0)
    tools = [search_regles_fiscales, search_normes_facturation]

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Vérifier la conformité de cette facture :\n{invoice_json}"),
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

    return ComplianceResult(**data)
