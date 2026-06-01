from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class FilterOptions(BaseModel):
    categories: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    source_types: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_rating: Optional[float] = None


class ChatRequest(BaseModel):
    message: str
    filters: Optional[FilterOptions] = None


class AnalyzeRequest(BaseModel):
    query: str
    filters: Optional[FilterOptions] = None


class IngestResponse(BaseModel):
    status: str
    chunks_ingested: int
    collection_stats: Dict[str, Any]


class ChatResponse(BaseModel):
    response: str
    agent_outputs: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, Any]]] = None


class DashboardData(BaseModel):
    total_revenue: float
    total_profit: float
    avg_customer_rating: float
    total_units_sold: int
    revenue_by_product: List[Dict[str, Any]]
    revenue_by_category: List[Dict[str, Any]]
    revenue_by_region: List[Dict[str, Any]]
    monthly_trend: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    collection_stats: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    collection_count: int
    llm_health: Dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
