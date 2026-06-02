import httpx
"""LLM-based reranker: scores retrieved documents for relevance to the query."""
import sys
import os
import json
from utils.json_extract import extract_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, http_client=httpx.Client(verify=False))
    return _client


def rerank(query: str, candidates: list[dict], top_k: int = None) -> list[dict]:
    top_k = top_k or settings.TOP_K_RESULTS
    if not candidates:
        return []
    if len(candidates) <= top_k:
        for i, c in enumerate(candidates):
            c["rerank_score"] = c.get("rrf_score", 1.0 - i * 0.05)
        return candidates

    docs_summary = []
    for i, c in enumerate(candidates[:10]):
        meta = c.get("metadata", {})
        snippet = c.get("document", "")[:300]
        docs_summary.append(
            f"[{i}] Alarm: {meta.get('alarm_id','?')} | Region: {meta.get('network_region','?')} | "
            f"Tech: {meta.get('technology_type','?')} | Severity: {meta.get('severity','?')} | "
            f"Snippet: {snippet}"
        )

    prompt = f"""You are a telecom network fault analysis expert.
Rank the following retrieved incidents by their relevance to this query:
QUERY: {query}

CANDIDATES:
{chr(10).join(docs_summary)}

Return a JSON array of indices sorted from MOST to LEAST relevant, e.g. [2,0,4,1,3].
Return ONLY the JSON array, nothing else."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            ranked_indices = list(parsed.values())[0] if parsed else list(range(len(candidates)))
        else:
            ranked_indices = parsed
    except Exception:
        ranked_indices = list(range(len(candidates)))

    reranked = []
    for new_rank, orig_idx in enumerate(ranked_indices[:top_k]):
        if 0 <= orig_idx < len(candidates):
            c = candidates[orig_idx].copy()
            c["rerank_score"] = 1.0 - new_rank * (1.0 / top_k)
            reranked.append(c)

    return reranked[:top_k]
