import json
from pathlib import Path
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from config.llm import get_llm
from tools.pdf_reader_tool import read_pdf_invoice
from tools.xml_reader_tool import read_xml_invoice
from schemas.invoice_schema import InvoiceData


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extracteur.txt"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def run_extractor_agent(file_path: str, file_type: str) -> InvoiceData:
    """Lance l'agent extracteur sur le fichier de facture fourni."""
    llm = get_llm(temperature=0.0)
    tools = [read_pdf_invoice, read_xml_invoice]

    system_prompt = _load_prompt()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Extraire les données de la facture : {file_path} (type: {file_type})"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    result = executor.invoke({
        "file_path": file_path,
        "file_type": file_type,
    })

    raw_output = result.get("output", "{}")
    if isinstance(raw_output, str):
        start = raw_output.find("{")
        end = raw_output.rfind("}") + 1
        json_str = raw_output[start:end] if start >= 0 else "{}"
        data = json.loads(json_str)
    else:
        data = raw_output

    return InvoiceData(**data)
