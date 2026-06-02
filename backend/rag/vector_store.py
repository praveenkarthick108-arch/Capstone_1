"""ChromaDB vector store operations."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from config import settings

_collection = None


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def vector_search(
    query_embedding: list[float],
    n_results: int = 20,
    where: dict = None,
) -> list[dict]:
    collection = get_collection()
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    documents = []
    for i, doc_id in enumerate(results["ids"][0]):
        documents.append({
            "id": doc_id,
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
            "similarity": 1.0 - results["distances"][0][i],
        })
    return documents


def get_collection_count() -> int:
    try:
        return get_collection().count()
    except Exception:
        return 0


def get_all_metadatas(limit: int = 500) -> list[dict]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []
    results = collection.get(limit=min(limit, count), include=["metadatas"])
    return results["metadatas"]
