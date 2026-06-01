import logging
from functools import partial
from typing import Optional

from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter, get_llm_router
from backend.core.vector_store import VectorStore, get_vector_store
from backend.agents.customer_insights_agent import customer_insights_node
from backend.agents.sales_analysis_agent import sales_analysis_node
from backend.agents.swot_agent import swot_analysis_node
from backend.agents.feature_prioritization_agent import feature_prioritization_node
from backend.agents.opportunity_scoring_agent import opportunity_scoring_node
from backend.agents.strategy_recommendation_agent import strategy_recommendation_node

logger = logging.getLogger(__name__)


async def retrieve_context_node(state: AgentState, vector_store: VectorStore) -> dict:
    """Hybrid search to fetch relevant context chunks for the query."""
    query = state.get("user_query", "")
    filters = state.get("_filters")  # optional pre-built ChromaDB where filter

    try:
        results = vector_store.search(query, where=filters)
        context = [
            {"document": r.document, "metadata": r.metadata, "score": r.score}
            for r in results
        ]
    except Exception as e:
        logger.error("retrieve_context_node error: %s", e)
        context = []

    return {
        "retrieved_context": context,
        "processing_status": {"retrieval": "complete", "chunks_found": len(context)},
    }


async def assemble_report_node(state: AgentState) -> dict:
    """Finalize report_sections. chat_response is already set by strategy node."""
    return {
        "processing_status": {
            **state.get("processing_status", {}),
            "report": "complete",
        }
    }


def build_graph() -> StateGraph:
    llm = get_llm_router()
    vs = get_vector_store()

    graph = StateGraph(AgentState)

    # Retrieval node
    graph.add_node("retrieve_context", partial(retrieve_context_node, vector_store=vs))

    # Parallel analysis nodes
    graph.add_node("customer_insights", partial(customer_insights_node, llm=llm))
    graph.add_node("sales_analysis", partial(sales_analysis_node, llm=llm))
    graph.add_node("swot_analysis", partial(swot_analysis_node, llm=llm))
    graph.add_node("feature_prioritization", partial(feature_prioritization_node, llm=llm))
    graph.add_node("opportunity_scoring", partial(opportunity_scoring_node, llm=llm))

    # Synthesis and assembly
    graph.add_node("strategy_recommendation", partial(strategy_recommendation_node, llm=llm))
    graph.add_node("assemble_report", assemble_report_node)

    # Edges: retrieve → fan-out to 5 parallel agents
    graph.set_entry_point("retrieve_context")
    parallel_nodes = [
        "customer_insights",
        "sales_analysis",
        "swot_analysis",
        "feature_prioritization",
        "opportunity_scoring",
    ]
    for node in parallel_nodes:
        graph.add_edge("retrieve_context", node)
        graph.add_edge(node, "strategy_recommendation")

    graph.add_edge("strategy_recommendation", "assemble_report")
    graph.add_edge("assemble_report", END)

    return graph.compile()


_compiled_graph: Optional[object] = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_analysis(
    query: str,
    filters: dict | None = None,
    uploaded_data_summary: str = "",
) -> AgentState:
    """Entry point for running the full multi-agent pipeline."""
    graph = get_compiled_graph()
    initial_state: AgentState = {
        "user_query": query,
        "uploaded_data_summary": uploaded_data_summary,
        "retrieved_context": [],
        "customer_insights": [],
        "sales_analysis": [],
        "competitor_swot": [],
        "feature_priorities": [],
        "opportunity_scores": [],
        "strategic_recommendations": [],
        "executive_summary": "",
        "report_sections": {},
        "chat_response": "",
        "agent_errors": [],
        "processing_status": {},
        "_filters": filters,
    }
    result = await graph.ainvoke(initial_state)
    return result
