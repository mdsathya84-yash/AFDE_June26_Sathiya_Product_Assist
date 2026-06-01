from backend.agents.utils import extract_json
import logging
from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Customer Insights Analyst. Analyze the provided sales and review data.
Return ONLY valid JSON matching this exact schema:
{
  "overall_sentiment": "positive|neutral|negative",
  "nps_score": <float 0-100>,
  "top_complaints": [<string>, ...],
  "top_praise_points": [<string>, ...],
  "at_risk_products": [{"product": <string>, "reason": <string>}, ...],
  "satisfaction_by_category": {<category>: <float>, ...},
  "key_insight": <string>
}"""


async def customer_insights_node(state: AgentState, llm: LLMRouter) -> dict:
    context = "\n".join(
        r.get("document", "") if isinstance(r, dict) else str(r)
        for r in (state.get("retrieved_context") or [])
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Query: {state.get('user_query', 'Analyze customer insights')}\n\n"
                f"Data Context:\n{context[:6000]}"
            ),
        },
    ]
    try:
        raw = await llm.invoke(messages, json_mode=True)
        result = extract_json(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("customer_insights_node error: %s", e)
        result = {
            "overall_sentiment": "neutral",
            "nps_score": 0.0,
            "top_complaints": [],
            "top_praise_points": [],
            "at_risk_products": [],
            "satisfaction_by_category": {},
            "key_insight": f"Analysis failed: {e}",
            "_error": str(e),
        }
    return {"customer_insights": [result]}
