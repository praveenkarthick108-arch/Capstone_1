"""
Feedback loop storage: persists user ratings on query responses to JSON.
"""
import os
import json
from datetime import datetime

FEEDBACK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/feedback.json")


def _load() -> list:
    if not os.path.exists(FEEDBACK_PATH):
        return []
    try:
        with open(FEEDBACK_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save(records: list) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(FEEDBACK_PATH)), exist_ok=True)
    with open(FEEDBACK_PATH, "w") as f:
        json.dump(records, f, indent=2)


def save_feedback(query_id: str, query: str, rating: int, helpful: bool, comment: str = "") -> dict:
    records = _load()
    entry = {
        "id": f"fb-{len(records) + 1:04d}",
        "query_id": query_id,
        "query": query[:200],
        "rating": rating,
        "helpful": helpful,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    records.append(entry)
    _save(records)
    return entry


def get_feedback_stats() -> dict:
    records = _load()
    if not records:
        return {
            "total_feedback": 0, "avg_rating": 0.0,
            "helpful_pct": 0.0, "recent_feedback": [],
        }
    ratings = [r["rating"] for r in records if r.get("rating")]
    helpful = [r for r in records if r.get("helpful") is True]
    return {
        "total_feedback": len(records),
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0.0,
        "helpful_pct": round(len(helpful) / len(records) * 100, 1),
        "rating_distribution": {
            str(i): sum(1 for r in records if r.get("rating") == i) for i in range(1, 6)
        },
        "recent_feedback": records[-5:][::-1],
    }


def get_all_feedback() -> list:
    return _load()
