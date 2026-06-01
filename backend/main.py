import ssl
import os

# Apply SSL patches FIRST — before any third-party imports.
# .env is not yet loaded by pydantic-settings here, so we read it manually via dotenv.
# The gateway uses an intermediate CA absent from Python's certifi bundle;
# httpx (OpenAI SDK transport) calls ssl.create_default_context(), so we patch both paths.
from dotenv import dotenv_values as _dotenv_values
_env = _dotenv_values(".env")
if _env.get("OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL"):
    ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[attr-defined]
    ssl.create_default_context = lambda *a, **kw: ssl._create_unverified_context(*a, **kw)  # type: ignore[assignment]
    os.environ["CURL_CA_BUNDLE"] = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["SSL_CERT_FILE"] = ""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core.config import settings
from backend.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Product Strategy Assistant...")

    from backend.core.vector_store import get_vector_store
    from backend.ingestion.ingestor import ingest_csv
    from backend.agents.graph import get_compiled_graph

    vs = get_vector_store()
    stats = vs.get_collection_stats()
    if stats.get("total_chunks", 0) < 10:
        csv_path = Path(__file__).parent.parent / "sample_data" / "Sample_Sales_Data.csv"
        if csv_path.exists():
            logger.info("Auto-ingesting sample data...")
            await ingest_csv(csv_path, vs)
            logger.info("Sample data ingested.")
        else:
            logger.warning("Sample data CSV not found at %s", csv_path)

    logger.info("Compiling LangGraph...")
    get_compiled_graph()
    logger.info("LangGraph ready.")

    logger.info("Application startup complete.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Product Strategy Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
