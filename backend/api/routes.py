import io
import json
import logging
import traceback
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response, StreamingResponse

async def _init():
    from backend.main import ensure_initialized
    await ensure_initialized()

from backend.agents.graph import run_analysis
from backend.core.vector_store import build_filter, get_vector_store
from backend.ingestion.ingestor import ingest_csv, ingest_text
from backend.models.schemas import (
    AnalyzeRequest,
    ChatRequest,
    ChatResponse,
    DashboardData,
    ErrorResponse,
    HealthResponse,
    IngestResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# Cache the last analysis result for report download
_last_analysis: dict = {}


@router.post("/ingest", response_model=IngestResponse)
async def ingest_files(files: list[UploadFile] = File(...)):
    await _init()
    vs = get_vector_store()
    total_chunks = 0
    stats = {}
    for upload in files:
        content = await upload.read()
        filename = upload.filename or "upload"
        ext = Path(filename).suffix.lower()
        try:
            if ext == ".csv":
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                result = await ingest_csv(tmp_path, vs)
                os.unlink(tmp_path)
            else:
                # TXT, MD, or PDF (basic text extraction)
                if ext == ".pdf":
                    try:
                        import pdfminer.high_level as pdfminer
                        text = pdfminer.extract_text(io.BytesIO(content))
                    except Exception:
                        text = content.decode("utf-8", errors="replace")
                else:
                    text = content.decode("utf-8", errors="replace")
                result = await ingest_text(text, filename, vs)

            total_chunks += result.get("chunks_ingested", 0)
            stats = result.get("collection_stats", vs.get_collection_stats())
        except Exception as e:
            logger.error("Ingest failed for %s: %s", filename, traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")

    return IngestResponse(
        status="success",
        chunks_ingested=total_chunks,
        collection_stats=stats,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    await _init()
    global _last_analysis
    try:
        filters = None
        if request.filters:
            f = request.filters
            filters = build_filter(
                categories=f.categories,
                regions=f.regions,
                source_types=f.source_types,
                date_from=f.date_from,
                date_to=f.date_to,
                min_rating=f.min_rating,
            )
        result = await run_analysis(request.message, filters=filters)
        _last_analysis = dict(result)

        sources = [
            {"document": c.get("document", "")[:200], "metadata": c.get("metadata", {})}
            for c in (result.get("retrieved_context") or [])[:5]
        ]
        agent_outputs = {
            "customer_insights": (result.get("customer_insights") or [{}])[0],
            "sales_analysis": (result.get("sales_analysis") or [{}])[0],
            "swot": (result.get("competitor_swot") or [{}])[0],
            "feature_priorities": (result.get("feature_priorities") or [{}])[0],
            "opportunities": (result.get("opportunity_scores") or [{}])[0],
            "strategy": (result.get("strategic_recommendations") or [{}])[0],
        }
        return ChatResponse(
            response=result.get("chat_response", "Analysis complete."),
            agent_outputs=agent_outputs,
            sources=sources,
        )
    except Exception as e:
        logger.error("Chat failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    await _init()
    global _last_analysis
    try:
        filters = None
        if request.filters:
            f = request.filters
            filters = build_filter(
                categories=f.categories,
                regions=f.regions,
                source_types=f.source_types,
                date_from=f.date_from,
                date_to=f.date_to,
                min_rating=f.min_rating,
            )
        result = await run_analysis(request.query, filters=filters)
        _last_analysis = dict(result)
        # Return serializable subset
        return {
            "executive_summary": result.get("executive_summary", ""),
            "report_sections": result.get("report_sections", {}),
            "customer_insights": (result.get("customer_insights") or [{}])[0],
            "sales_analysis": (result.get("sales_analysis") or [{}])[0],
            "swot": (result.get("competitor_swot") or [{}])[0],
            "feature_priorities": (result.get("feature_priorities") or [{}])[0],
            "opportunities": (result.get("opportunity_scores") or [{}])[0],
            "strategy": (result.get("strategic_recommendations") or [{}])[0],
            "processing_status": result.get("processing_status", {}),
        }
    except Exception as e:
        logger.error("Analyze failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_report(format: str = "pdf"):
    from backend.core.report_generator import ReportGenerator

    if not _last_analysis:
        raise HTTPException(status_code=404, detail="No analysis available. Run /api/analyze first.")

    gen = ReportGenerator()
    if format == "json":
        data = gen.generate_json(_last_analysis)
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=strategy_report.json"},
        )
    else:
        pdf_bytes = gen.generate_pdf(_last_analysis)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=strategy_report.pdf"},
        )


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard():
    await _init()
    try:
        csv_path = Path(__file__).parent.parent.parent / "sample_data" / "Sample_Sales_Data.csv"
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Sample data not found")

        df = pd.read_csv(csv_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.strftime("%Y-%m")

        total_revenue = float(df["Revenue_USD"].sum())
        total_profit = float(df["Profit_USD"].sum())
        avg_rating = float(df["Customer_Rating"].mean())
        total_units = int(df["Units_Sold"].sum())

        rev_by_product = (
            df.groupby("Product_Name")["Revenue_USD"]
            .sum()
            .reset_index()
            .rename(columns={"Product_Name": "name", "Revenue_USD": "revenue"})
            .sort_values("revenue", ascending=False)
            .to_dict(orient="records")
        )

        rev_by_category = (
            df.groupby("Category")["Revenue_USD"]
            .sum()
            .reset_index()
            .rename(columns={"Category": "category", "Revenue_USD": "revenue"})
            .to_dict(orient="records")
        )

        rev_by_region = (
            df.groupby("Region")["Revenue_USD"]
            .sum()
            .reset_index()
            .rename(columns={"Region": "region", "Revenue_USD": "revenue"})
            .to_dict(orient="records")
        )

        monthly = (
            df.groupby("Month")
            .agg(revenue=("Revenue_USD", "sum"), profit=("Profit_USD", "sum"))
            .reset_index()
            .rename(columns={"Month": "month"})
            .sort_values("month")
            .to_dict(orient="records")
        )

        top_products = (
            df.groupby("Product_Name")
            .agg(
                units=("Units_Sold", "sum"),
                revenue=("Revenue_USD", "sum"),
                profit=("Profit_USD", "sum"),
                rating=("Customer_Rating", "mean"),
                returns=("Returns", "sum"),
                category=("Category", "first"),
            )
            .reset_index()
            .rename(columns={"Product_Name": "name"})
            .sort_values("revenue", ascending=False)
        )
        top_products["margin_pct"] = (top_products["profit"] / top_products["revenue"] * 100).round(1)
        top_products_list = top_products.head(10).to_dict(orient="records")

        vs = get_vector_store()
        stats = vs.get_collection_stats()

        return DashboardData(
            total_revenue=total_revenue,
            total_profit=total_profit,
            avg_customer_rating=round(avg_rating, 2),
            total_units_sold=total_units,
            revenue_by_product=[{k: float(v) if hasattr(v, "item") else v for k, v in r.items()} for r in rev_by_product],
            revenue_by_category=[{k: float(v) if hasattr(v, "item") else v for k, v in r.items()} for r in rev_by_category],
            revenue_by_region=[{k: float(v) if hasattr(v, "item") else v for k, v in r.items()} for r in rev_by_region],
            monthly_trend=[{k: float(v) if hasattr(v, "item") else v for k, v in r.items()} for r in monthly],
            top_products=[{k: (float(v) if hasattr(v, "item") else v) for k, v in r.items()} for r in top_products_list],
            collection_stats=stats,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Dashboard failed: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health():
    from backend.core.llm_router import get_llm_router

    llm = get_llm_router()
    vs = get_vector_store()
    stats = vs.get_collection_stats()
    return HealthResponse(
        status="ok",
        llm_provider=llm.get_active_provider(),
        collection_count=stats.get("total_chunks", 0),
        llm_health=llm.get_health(),
    )
