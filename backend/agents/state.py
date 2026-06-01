from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    # Input
    user_query: str
    uploaded_data_summary: str
    retrieved_context: list

    # Parallel agent outputs (accumulated via operator.add)
    customer_insights: Annotated[list, operator.add]
    sales_analysis: Annotated[list, operator.add]
    competitor_swot: Annotated[list, operator.add]
    feature_priorities: Annotated[list, operator.add]
    opportunity_scores: Annotated[list, operator.add]
    strategic_recommendations: Annotated[list, operator.add]

    # Final outputs
    executive_summary: str
    report_sections: dict
    chat_response: str

    # Metadata
    agent_errors: Annotated[list, operator.add]
    processing_status: dict
