import json
from backend.agents.utils import extract_json
import logging
from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Strategic Business Analyst specializing in SWOT analysis.
Synthesize the provided data and agent insights into a comprehensive SWOT matrix.
Return ONLY valid JSON matching this exact schema:
{
  "strengths": [<string>, ...],
  "weaknesses": [<string>, ...],
  "opportunities": [<string>, ...],
  "threats": [<string>, ...],
  "swot_summary": <string>
}
Each array should have 3-5 items. swot_summary should be 2-3 sentences."""


async def swot_analysis_node(state: AgentState, llm: LLMRouter) -> dict:
    context = "\n".join(
        r.get("document", "") if isinstance(r, dict) else str(r)
        for r in (state.get("retrieved_context") or [])
    )
    # Pull in any available prior agent outputs for richer synthesis
    sales = state.get("sales_analysis") or []
    customers = state.get("customer_insights") or []
    prior_context = ""
    if sales:
        prior_context += f"\nSales Analysis: {json.dumps(sales[0]) if sales else ''}"
    if customers:
        prior_context += f"\nCustomer Insights: {json.dumps(customers[0]) if customers else ''}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Query: {state.get('user_query', 'Generate SWOT analysis')}\n\n"
                f"Data Context:\n{context[:4000]}"
                f"{prior_context[:2000]}"
            ),
        },
    ]
    try:
        raw = await llm.invoke(messages, json_mode=True)
        result = extract_json(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("swot_analysis_node error: %s", e)
        result = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "swot_summary": f"Analysis failed: {e}",
            "_error": str(e),
        }
    return {"competitor_swot": [result]}
