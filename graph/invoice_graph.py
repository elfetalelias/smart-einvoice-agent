from langgraph.graph import StateGraph, END
from graph.invoice_state import InvoiceState
from graph.nodes import (
    node_extract_invoice,
    node_check_compliance,
    node_classify_accounting,
    node_generate_journal_entry,
    node_generate_report,
    node_human_validation_1,
    node_human_validation_2,
    node_human_validation_3,
)
from agents.supervisor_agent import decide_next_node


def build_invoice_graph() -> StateGraph:
    """Construit et compile le graphe LangGraph pour le traitement des factures."""
    workflow = StateGraph(InvoiceState)

    # Enregistrement des nœuds
    workflow.add_node("extract_invoice", node_extract_invoice)
    workflow.add_node("human_validation_1", node_human_validation_1)
    workflow.add_node("check_compliance", node_check_compliance)
    workflow.add_node("human_validation_2", node_human_validation_2)
    workflow.add_node("classify_accounting", node_classify_accounting)
    workflow.add_node("human_validation_3", node_human_validation_3)
    workflow.add_node("generate_journal_entry", node_generate_journal_entry)
    workflow.add_node("generate_report", node_generate_report)

    # Point d'entrée
    workflow.set_entry_point("extract_invoice")

    # Transitions séquentielles avec supervision
    workflow.add_edge("extract_invoice", "human_validation_1")
    workflow.add_conditional_edges(
        "human_validation_1",
        lambda s: decide_next_node(s),
        {
            "check_compliance": "check_compliance",
            "END": END,
        },
    )
    workflow.add_edge("check_compliance", "human_validation_2")
    workflow.add_conditional_edges(
        "human_validation_2",
        lambda s: decide_next_node(s),
        {
            "classify_accounting": "classify_accounting",
            "END": END,
        },
    )
    workflow.add_edge("classify_accounting", "human_validation_3")
    workflow.add_conditional_edges(
        "human_validation_3",
        lambda s: decide_next_node(s),
        {
            "generate_journal_entry": "generate_journal_entry",
            "END": END,
        },
    )
    workflow.add_edge("generate_journal_entry", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


# Instance compilée — importable directement
invoice_graph = build_invoice_graph()
