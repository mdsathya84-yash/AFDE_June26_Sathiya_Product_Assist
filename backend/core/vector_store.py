import logging
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rank_bm25 import BM25Okapi

from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    document: str
    metadata: dict
    score: float
    id: str


def build_filter(
    categories: list[str] | None = None,
    regions: list[str] | None = None,
    source_types: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_rating: float | None = None,
) -> dict | None:
    """Build a ChromaDB $and/$or metadata filter dict from optional parameters."""
    clauses = []
    if categories:
        clauses.append({"category": {"$in": categories}})
    if regions:
        clauses.append({"region": {"$in": regions}})
    if source_types:
        clauses.append({"source_type": {"$in": source_types}})
    if date_from:
        clauses.append({"date": {"$gte": date_from}})
    if date_to:
        clauses.append({"date": {"$lte": date_to}})
    if min_rating is not None:
        clauses.append({"customer_rating": {"$gte": min_rating}})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


class HybridSearchRetriever:
    """
    Combines ChromaDB dense vector search with BM25 sparse keyword search.
    Uses Reciprocal Rank Fusion (RRF) to merge results (k=60).
    alpha=0.6 → 60% dense, 40% BM25.
    """

    def __init__(self, collection, all_documents: list[str], alpha: float = 0.6):
        self.collection = collection
        self.all_documents = all_documents
        self.alpha = alpha
        tokenized = [doc.split() for doc in all_documents]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None

    def _rrf_score(self, rank: int, k: int = 60) -> float:
        return 1.0 / (k + rank + 1)

    def search(
        self,
        query: str,
        n_results: int = 8,
        where: dict | None = None,
        where_document: dict | None = None,
    ) -> list[SearchResult]:
        if not self.all_documents or self.bm25 is None:
            return []

        # Dense search via ChromaDB
        dense_kwargs: dict = {"query_texts": [query], "n_results": min(n_results * 2, len(self.all_documents))}
        if where:
            dense_kwargs["where"] = where
        if where_document:
            dense_kwargs["where_document"] = where_document

        try:
            dense_results = self.collection.query(**dense_kwargs)
        except Exception as e:
            logger.warning("Dense search failed: %s", e)
            dense_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        dense_ids = dense_results["ids"][0]
        dense_docs = dense_results["documents"][0]
        dense_metas = dense_results["metadatas"][0]

        # BM25 sparse search over all documents
        bm25_scores = self.bm25.get_scores(query.split())
        bm25_ranked = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)

        # Build RRF score map keyed by document content
        rrf_map: dict[str, dict] = {}

        for rank, doc_id in enumerate(dense_ids):
            doc_content = dense_docs[rank]
            meta = dense_metas[rank]
            if doc_content not in rrf_map:
                rrf_map[doc_content] = {"meta": meta, "id": doc_id, "dense_rrf": 0.0, "sparse_rrf": 0.0}
            rrf_map[doc_content]["dense_rrf"] = self._rrf_score(rank)

        for rank, (doc_idx, _) in enumerate(bm25_ranked[: n_results * 3]):
            doc_content = self.all_documents[doc_idx]
            if doc_content not in rrf_map:
                # Only include if not already filtered out by metadata filter
                if where and dense_ids:
                    # Skip BM25-only results that wouldn't pass the metadata filter
                    continue
                rrf_map[doc_content] = {"meta": {}, "id": f"bm25_{doc_idx}", "dense_rrf": 0.0, "sparse_rrf": 0.0}
            rrf_map[doc_content]["sparse_rrf"] = self._rrf_score(rank)

        # Fuse scores
        results = []
        for doc_content, entry in rrf_map.items():
            fused = self.alpha * entry["dense_rrf"] + (1 - self.alpha) * entry["sparse_rrf"]
            results.append(
                SearchResult(
                    document=doc_content,
                    metadata=entry["meta"],
                    score=fused,
                    id=entry["id"],
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:n_results]


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._retriever: Optional[HybridSearchRetriever] = None

    def _rebuild_retriever(self):
        """Rebuild BM25 index after ingestion."""
        results = self.collection.get(include=["documents"])
        all_docs = results.get("documents") or []
        self._retriever = HybridSearchRetriever(self.collection, all_docs)

    def ingest_documents(
        self,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        # Clean None values — ChromaDB doesn't accept None in metadata
        clean_metas = []
        for m in metadatas:
            clean_metas.append({k: (v if v is not None else "") for k, v in m.items()})

        # Upsert in batches of 500
        batch_size = 500
        for i in range(0, len(documents), batch_size):
            self.collection.upsert(
                documents=documents[i : i + batch_size],
                metadatas=clean_metas[i : i + batch_size],
                ids=ids[i : i + batch_size],
            )
        self._rebuild_retriever()

    def search(
        self,
        query: str,
        n_results: int | None = None,
        where: dict | None = None,
        where_document: dict | None = None,
    ) -> list[SearchResult]:
        if self._retriever is None:
            self._rebuild_retriever()
        k = n_results or settings.TOP_K_RESULTS
        return self._retriever.search(query, n_results=k, where=where, where_document=where_document)

    def similarity_search_with_metadata(
        self,
        query: str,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        return self.search(query, where=filters)

    def get_collection_stats(self) -> dict:
        count = self.collection.count()
        try:
            sample = self.collection.get(limit=500, include=["metadatas"])
            metas = sample.get("metadatas") or []
            source_types: dict[str, int] = {}
            categories: dict[str, int] = {}
            regions: dict[str, int] = {}
            for m in metas:
                st = m.get("source_type", "unknown")
                source_types[st] = source_types.get(st, 0) + 1
                cat = m.get("category", "")
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1
                reg = m.get("region", "")
                if reg:
                    regions[reg] = regions.get(reg, 0) + 1
        except Exception:
            source_types = categories = regions = {}

        return {
            "total_chunks": count,
            "source_types": source_types,
            "categories": categories,
            "regions": regions,
        }

    def delete_collection(self) -> None:
        self.client.delete_collection(settings.COLLECTION_NAME)
        self._retriever = None


_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
