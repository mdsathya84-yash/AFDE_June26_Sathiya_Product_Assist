import logging
from pathlib import Path

from backend.ingestion.csv_parser import parse_csv
from backend.ingestion.text_splitter import split_documents

logger = logging.getLogger(__name__)


async def ingest_csv(csv_path: str | Path, vector_store) -> dict:
    """Parse CSV, split into chunks, upsert into ChromaDB. Returns ingestion stats."""
    logger.info("Ingesting CSV: %s", csv_path)
    documents, metadatas, ids = parse_csv(csv_path)
    chunks, chunk_metas, chunk_ids = split_documents(documents, metadatas, ids)
    vector_store.ingest_documents(chunks, chunk_metas, chunk_ids)
    stats = vector_store.get_collection_stats()
    logger.info("Ingested %d chunks from %s", len(chunks), csv_path)
    return {"chunks_ingested": len(chunks), "collection_stats": stats}


async def ingest_text(
    text: str,
    filename: str,
    vector_store,
) -> dict:
    """Ingest plain-text content (from uploaded TXT/MD/PDF) into ChromaDB."""
    import hashlib

    doc_id = hashlib.sha256(text.encode()).hexdigest()[:32]
    meta = {
        "source_type": "uploaded_doc",
        "product_id": None,
        "product_name": None,
        "category": None,
        "region": None,
        "date": None,
        "month": None,
        "revenue_usd": None,
        "profit_usd": None,
        "customer_rating": None,
        "chunk_index": 0,
        "doc_id": doc_id,
        "filename": filename,
    }
    chunks, chunk_metas, chunk_ids = split_documents([text], [meta], [doc_id])
    vector_store.ingest_documents(chunks, chunk_metas, chunk_ids)
    return {"chunks_ingested": len(chunks)}
