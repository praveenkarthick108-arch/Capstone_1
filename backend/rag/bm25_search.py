"""BM25 keyword search using pre-built index."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import pickle
from rank_bm25 import BM25Okapi
from config import settings

_bm25 = None
_alarm_ids = None


def _load_index():
    global _bm25, _alarm_ids
    if _bm25 is None:
        if not os.path.exists(settings.BM25_INDEX_PATH):
            raise FileNotFoundError(
                f"BM25 index not found at {settings.BM25_INDEX_PATH}. Run ingestion first."
            )
        with open(settings.BM25_INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        _bm25 = data["bm25"]
        _alarm_ids = data["alarm_ids"]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def bm25_search(query: str, n_results: int = 20) -> list[dict]:
    _load_index()
    tokens = tokenize(query)
    scores = _bm25.get_scores(tokens)

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for rank, (idx, score) in enumerate(ranked[:n_results]):
        if score > 0:
            results.append({
                "id": _alarm_ids[idx],
                "bm25_score": float(score),
                "rank": rank,
            })
    return results


def bm25_get_doc_idx(alarm_id: str) -> int:
    """Return the list index of an alarm_id in the BM25 index, or -1 if not found."""
    _load_index()
    try:
        return _alarm_ids.index(alarm_id)
    except ValueError:
        return -1


def bm25_explain_result(query: str, doc_idx: int, top_n: int = 4) -> list[str]:
    """Return the query tokens that contributed most to the BM25 score for a document."""
    if doc_idx < 0:
        return []
    _load_index()
    tokens = list(set(tokenize(query)))
    term_scores: dict[str, float] = {}
    for token in tokens:
        scores = _bm25.get_scores([token])
        if doc_idx < len(scores) and scores[doc_idx] > 0:
            term_scores[token] = float(scores[doc_idx])
    return sorted(term_scores, key=lambda t: term_scores[t], reverse=True)[:top_n]


def is_index_ready() -> bool:
    return os.path.exists(settings.BM25_INDEX_PATH)
