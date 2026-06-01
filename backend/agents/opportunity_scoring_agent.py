from backend.agents.utils import extract_json
import logging
from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Market Opportunity Analyst. Score product opportunities using:
opportunity_score = (revenue_growth_potential×0.3) + (customer_satisfaction_gap×0.25) +
                    (market_penetration_gap×0.25) + (strategic_fit×0.2)
All sub-scores are 0-100. Final score is 0-100.
Return ONLY valid JSON matching this exact schema:
{
  "top_opportunities": [
    {
      "opportunity": <string>,
      "score": <float 0-100>,
      "category": <string>,
      "region": <string>,
      "rationale": <string>,
      "investment_required": "low|medium|high",
      "expected_return": "low|medium|high"
    }
  ],
  "whitespace_areas": [<string>, ...],
  "key_insight": <string>
}
Include top 5 opportunities and at least 3 whitespace areas."""


async def opportunity_scoring_node(state: AgentState, llm: LLMRouter) -> dict:
    context = "\n".join(
        r.get("document", "") if isinstance(r, dict) else str(r)
        for r in (state.get("retrieved_context") or [])
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Query: {state.get('user_query', 'Identify growth opportunities')}\n\n"
                f"Data Context:\n{context[:6000]}"
            ),
        },
    ]
    try:
        raw = await llm.invoke(messages, json_mode=True)
        result = extract_json(raw)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("opportunity_scoring_node error: %s", e)
        result = {
            "top_opportunities": [],
            "whitespace_areas": [],
            "key_insight": f"Analysis failed: {e}",
            "_error": str(e),
        }
    return {"opportunity_scores": [result]}
