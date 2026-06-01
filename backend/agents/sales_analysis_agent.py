from backend.agents.utils import extract_json
import logging
from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Sales Performance Analyst. Analyze the provided sales data.
Return ONLY valid JSON matching this exact schema:
{
  "top_revenue_products": [{"product": <string>, "revenue": <float>}, ...],
  "top_profit_margin_products": [{"product": <string>, "margin_pct": <float>}, ...],
  "best_region": <string>,
  "worst_region": <string>,
  "marketing_roi_by_product": [{"product": <string>, "roi": <float>}, ...],
  "growth_trend": "growing|stable|declining",
  "anomalies": [<string>, ...],
  "key_insight": <string>
}"""


async def sales_analysis_node(state: AgentState, llm: LLMRouter) -> dict:
    context = "\n".join(
        r.get("document", "") if isinstance(r, dict) else str(r)
        for r in (state.get("retrieved_context") or [])
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Query: {state.get('user_query', 'Analyze sales performance')}\n\n"
                f"Data Context:\n{context[:6000]}"
            ),
        },
    ]
    try:
        raw = await llm.invoke(messages, json_mode=True)
        result = extract_json(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("sales_analysis_node error: %s", e)
        result = {
            "top_revenue_products": [],
            "top_profit_margin_products": [],
            "best_region": "Unknown",
            "worst_region": "Unknown",
            "marketing_roi_by_product": [],
            "growth_trend": "stable",
            "anomalies": [],
            "key_insight": f"Analysis failed: {e}",
            "_error": str(e),
        }
    return {"sales_analysis": [result]}
