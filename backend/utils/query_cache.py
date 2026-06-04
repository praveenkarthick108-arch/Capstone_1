"""
Semantic Query Cache — avoid re-running the full pipeline for similar queries.
Uses cosine similarity on embeddings; falls back to text similarity if embedding unavailable.
"""
import difflib
import time
from typing import Optional

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    _NUMPY = False


class SemanticQueryCache:
    def __init__(self, max_size: int = 50, threshold: float = 0.88):
        self._entries: list[dict] = []  # [{query, embedding, result_dict, ts, hits}]
        self.max_size = max_size
        self.threshold = threshold
        self.total_hits = 0
        self.total_lookups = 0

    # ── Similarity helpers ──────────────────────────────────────────────────
    @staticmethod
    def _cosine(a, b) -> float:
        if not _NUMPY:
            return 0.0
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    @staticmethod
    def _text_sim(q1: str, q2: str) -> float:
        return difflib.SequenceMatcher(None, q1.lower(), q2.lower()).ratio()

    # ── Public API ───────────────────────────────────────────────────────────
    def lookup(
        self, query: str, embedding: Optional[list] = None
    ) -> Optional[dict]:
        """Return cache entry if a sufficiently similar query was already processed."""
        self.total_lookups += 1
        best_sim = 0.0
        best_entry = None

        for entry in self._entries:
            if embedding and entry.get("embedding"):
                sim = self._cosine(embedding, entry["embedding"])
            else:
                # fallback: text similarity
                sim = self._text_sim(query, entry["query"])

            if sim > best_sim:
                best_sim = sim
                best_entry = entry

        if best_sim >= self.threshold and best_entry:
            best_entry["hits"] += 1
            self.total_hits += 1
            return {
                "result": best_entry["result"],
                "similarity": round(best_sim, 4),
                "cached_query": best_entry["query"],
                "cached_at": best_entry["ts"],
                "hit_number": best_entry["hits"],
            }
        return None

    def store(self, query: str, result_dict: dict, embedding: Optional[list] = None):
        """Add a processed result to the cache."""
        if len(self._entries) >= self.max_size:
            self._entries.pop(0)  # evict oldest
        self._entries.append({
            "query": query,
            "embedding": embedding,
            "result": result_dict,
            "ts": time.time(),
            "hits": 0,
        })

    def stats(self) -> dict:
        return {
            "cached_queries": len(self._entries),
            "max_size": self.max_size,
            "threshold": self.threshold,
            "total_lookups": self.total_lookups,
            "total_hits": self.total_hits,
            "hit_rate_pct": round(self.total_hits / max(1, self.total_lookups) * 100, 1),
        }

    def clear(self):
        self._entries.clear()
        self.total_hits = 0
        self.total_lookups = 0


# ── Module-level singleton ────────────────────────────────────────────────────
query_cache = SemanticQueryCache(max_size=50, threshold=0.88)


# ── Token efficiency helpers ──────────────────────────────────────────────────
# Rough estimate: 1 token ≈ 4 characters for English text
def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def compute_token_efficiency(
    original_query: str,
    retrieved_incidents: list[dict],
    rca_explanation: str,
    resolution_steps: list[str],
    num_agents: int = 4,
) -> dict:
    """
    Compares actual RAG token usage against the hypothetical baseline of sending
    the full knowledge base (7,400 incidents) directly to the LLM.
    """
    # Actual tokens: query + top-5 incident descriptions + LLM outputs
    context_text = " ".join(
        inc.get("incident_description", "") for inc in retrieved_incidents[:5]
    )
    output_text = rca_explanation + " ".join(resolution_steps[:5])

    # Each of the 4 agents sees query + context (shared) + prior agent output
    estimated_input = _est_tokens(original_query + context_text) * num_agents
    estimated_output = _est_tokens(output_text)
    estimated_total = estimated_input + estimated_output

    # Baseline: sending ALL 7,400 incident descriptions (~110 tokens each avg) to a single LLM call
    baseline_tokens = 7400 * 110  # ~814,000 tokens

    savings_pct = round(max(0, (1 - estimated_total / baseline_tokens)) * 100, 1)

    # Carbon estimate: ~0.0004 gCO2e per token for typical cloud LLM inference
    GRAMS_CO2_PER_TOKEN = 0.0004
    co2_used_g = round(estimated_total * GRAMS_CO2_PER_TOKEN, 3)
    co2_baseline_g = round(baseline_tokens * GRAMS_CO2_PER_TOKEN, 1)
    co2_saved_g = round(co2_baseline_g - co2_used_g, 1)

    return {
        "estimated_tokens_used": estimated_total,
        "baseline_tokens": baseline_tokens,
        "retrieved_incidents_count": len(retrieved_incidents),
        "savings_pct": savings_pct,
        "co2_used_g": co2_used_g,
        "co2_saved_g": co2_saved_g,
        "co2_baseline_g": co2_baseline_g,
        "efficiency_label": (
            "Excellent" if savings_pct >= 95 else
            "Good" if savings_pct >= 85 else
            "Moderate"
        ),
    }
