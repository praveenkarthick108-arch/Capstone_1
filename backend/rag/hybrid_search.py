"""
Hybrid search: RRF fusion of vector + BM25 results with metadata filtering.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.embeddings import embed_query
from rag.vector_store import vector_search, get_collection
from rag.bm25_search import bm25_search
from config import settings


def _fetch_metadata_for_ids(ids: list[str]) -> dict[str, dict]:
    """Fetch documents + metadata from ChromaDB for a list of IDs."""
    if not ids:
        return {}
    try:
        collection = get_collection()
        results = collection.get(ids=ids, include=["documents", "metadatas"])
        out = {}
        for i, doc_id in enumerate(results["ids"]):
            out[doc_id] = {
                "document": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
            }
        return out
    except Exception:
        return {}


def build_chroma_filter(
    network_region: str = None,
    technology_type: str = None,
    severity: str = None,
    device_vendor: str = None,
) -> dict | None:
    conditions = {}
    if network_region:
        conditions["network_region"] = network_region
    if technology_type:
        conditions["technology_type"] = technology_type
    if severity:
        conditions["severity"] = severity
    if device_vendor:
        conditions["device_vendor"] = device_vendor

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions
    return {"$and": [{k: v} for k, v in conditions.items()]}


def reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    k: int = None,
) -> list[dict]:
    k = k or settings.RRF_K
    scores: dict[str, float] = {}

    vector_ids = {r["id"]: r for r in vector_results}
    bm25_ids = {r["id"]: r for r in bm25_results}

    for rank, result in enumerate(vector_results):
        doc_id = result["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

    for rank, result in enumerate(bm25_results):
        doc_id = result["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    fused = []
    for doc_id, rrf_score in sorted_ids:
        entry = {"id": doc_id, "rrf_score": rrf_score}
        if doc_id in vector_ids:
            entry.update({
                "document": vector_ids[doc_id].get("document", ""),
                "metadata": vector_ids[doc_id].get("metadata", {}),
                "vector_similarity": vector_ids[doc_id].get("similarity", 0.0),
            })
        elif doc_id in bm25_ids:
            entry.update({"document": "", "metadata": {}, "vector_similarity": 0.0, "_needs_fetch": True})
        fused.append(entry)

    return fused


def hybrid_search(
    query: str,
    n_results: int = None,
    network_region: str = None,
    technology_type: str = None,
    severity: str = None,
    device_vendor: str = None,
) -> list[dict]:
    n_results = n_results or settings.MAX_RETRIEVED_DOCS
    chroma_filter = build_chroma_filter(network_region, technology_type, severity, device_vendor)

    query_embedding = embed_query(query)
    vector_results = vector_search(query_embedding, n_results=n_results, where=chroma_filter)
    bm25_results = bm25_search(query, n_results=n_results)

    if chroma_filter and bm25_results:
        vector_ids = {r["id"] for r in vector_results}
        bm25_results = [r for r in bm25_results if r["id"] in vector_ids]

    fused = reciprocal_rank_fusion(vector_results, bm25_results)

    # Fetch metadata for BM25-only results that weren't in vector results
    missing_ids = [r["id"] for r in fused if r.get("_needs_fetch")]
    if missing_ids:
        fetched = _fetch_metadata_for_ids(missing_ids)
        for r in fused:
            if r.get("_needs_fetch") and r["id"] in fetched:
                r["document"] = fetched[r["id"]]["document"]
                r["metadata"] = fetched[r["id"]]["metadata"]
            r.pop("_needs_fetch", None)

    return fused[: settings.TOP_K_RESULTS * 2]
