from backend.agents.utils import extract_json
import logging
from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Product Manager specializing in feature prioritization using RICE scoring.
RICE = (Reach × Impact × Confidence%) / Effort_weeks
Analyze customer reviews and feedback to identify and prioritize product improvements.
Return ONLY valid JSON matching this exact schema:
{
  "prioritized_features": [
    {
      "feature": <string>,
      "category": <string>,
      "reach_score": <int 1-10>,
      "impact_score": <int 1-10>,
      "confidence_pct": <int 0-100>,
      "effort_weeks": <int>,
      "rice_score": <float>,
      "rationale": <string>
    }
  ],
  "quick_wins": [<string>, ...],
  "key_insight": <string>
}
Include at least 5 features. Quick wins are high-impact, low-effort items."""


async def feature_prioritization_node(state: AgentState, llm: LLMRouter) -> dict:
    context = "\n".join(
        r.get("document", "") if isinstance(r, dict) else str(r)
        for r in (state.get("retrieved_context") or [])
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Query: {state.get('user_query', 'Prioritize product features')}\n\n"
                f"Data Context:\n{context[:6000]}"
            ),
        },
    ]
    try:
        raw = await llm.invoke(messages, json_mode=True)
        result = extract_json(raw)
        # Compute RICE scores if not already computed
        for feat in result.get("prioritized_features", []):
            if "rice_score" not in feat or feat["rice_score"] == 0:
                effort = feat.get("effort_weeks", 1) or 1
                feat["rice_score"] = round(
                    (feat.get("reach_score", 1) * feat.get("impact_score", 1) * feat.get("confidence_pct", 50)) / effort,
                    2,
                )
    except (json.JSONDecodeError, Exception) as e:
        logger.error("feature_prioritization_node error: %s", e)
        result = {
            "prioritized_features": [],
            "quick_wins": [],
            "key_insight": f"Analysis failed: {e}",
            "_error": str(e),
        }
    return {"feature_priorities": [result]}
