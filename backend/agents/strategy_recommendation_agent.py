import json
from backend.agents.utils import extract_json
import logging
from backend.agents.state import AgentState
from backend.core.llm_router import LLMRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Chief Strategy Officer. Synthesize all agent analyses into a comprehensive
strategic plan. Return ONLY valid JSON matching this exact schema:
{
  "executive_summary": <string 250-300 words>,
  "action_plan": {
    "90_days": [{"action": <string>, "owner": <string>, "kpi": <string>}, ...],
    "6_months": [{"action": <string>, "owner": <string>, "kpi": <string>}, ...],
    "12_months": [{"action": <string>, "owner": <string>, "kpi": <string>}, ...]
  },
  "product_roadmap": [
    {"quarter": <string>, "initiative": <string>, "priority": "P0|P1|P2", "product": <string>}
  ],
  "strategic_narrative": <string>
}
Each time horizon should have 3-5 actions. Product roadmap should cover 4 quarters."""


async def strategy_recommendation_node(state: AgentState, llm: LLMRouter) -> dict:
    # Collect all prior agent outputs for synthesis
    customer = (state.get("customer_insights") or [{}])[0]
    sales = (state.get("sales_analysis") or [{}])[0]
    swot = (state.get("competitor_swot") or [{}])[0]
    features = (state.get("feature_priorities") or [{}])[0]
    opportunities = (state.get("opportunity_scores") or [{}])[0]

    synthesis_context = f"""
Customer Insights: {json.dumps(customer)[:1500]}
Sales Analysis: {json.dumps(sales)[:1500]}
SWOT Analysis: {json.dumps(swot)[:1500]}
Feature Priorities: {json.dumps(features)[:1000]}
Opportunities: {json.dumps(opportunities)[:1000]}
"""

    context_docs = "\n".join(
        r.get("document", "") if isinstance(r, dict) else str(r)
        for r in (state.get("retrieved_context") or [])[:5]
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Query: {state.get('user_query', 'Generate strategic recommendations')}\n\n"
                f"Agent Synthesis:\n{synthesis_context}\n\n"
                f"Additional Context:\n{context_docs[:2000]}"
            ),
        },
    ]
    try:
        raw = await llm.invoke(messages, json_mode=True)
        result = extract_json(raw)
        if result.get("_error"):
            logger.warning("Strategy agent returned with error flag")
    except (json.JSONDecodeError, Exception) as e:
        logger.error("strategy_recommendation_node error: %s", e)
        result = {
            "executive_summary": f"Strategic analysis could not be completed: {e}",
            "action_plan": {"90_days": [], "6_months": [], "12_months": []},
            "product_roadmap": [],
            "strategic_narrative": "",
            "_error": str(e),
        }

    executive_summary = result.get("executive_summary", "")
    return {
        "strategic_recommendations": [result],
        "executive_summary": executive_summary,
        "report_sections": {
            "customer_insights": customer,
            "sales_analysis": sales,
            "swot": swot,
            "feature_priorities": features,
            "opportunities": opportunities,
            "strategy": result,
        },
        "chat_response": _format_chat_response(state, result, customer, sales),
    }


def _format_chat_response(
    state: AgentState,
    strategy: dict,
    customer: dict,
    sales: dict,
) -> str:
    summary = strategy.get("executive_summary", "")
    top_actions = strategy.get("action_plan", {}).get("90_days", [])
    action_text = "\n".join(
        f"- **{a.get('action', '')}** (KPI: {a.get('kpi', 'TBD')})"
        for a in top_actions[:3]
    )
    key_insight = customer.get("key_insight", "") or sales.get("key_insight", "")

    response = f"## Strategic Analysis Results\n\n{summary}"
    if action_text:
        response += f"\n\n### Immediate Actions (90-Day Plan)\n{action_text}"
    if key_insight:
        response += f"\n\n> **Key Insight:** {key_insight}"
    return response
