"""
Agent 1: Alarm Retrieval Agent
Retrieves semantically similar historical incidents via hybrid search + reranking.
"""
import sys
import os
import json
from utils.json_extract import extract_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from openai import OpenAI
from config import settings
from rag.hybrid_search import hybrid_search
from rag.reranker import rerank
from utils.logger import get_logger

logger = get_logger("AlarmRetrievalAgent")

SYSTEM_PROMPT = """Telecom alarm retrieval specialist. Output ONLY compact JSON:
{"alarm_patterns":["p1","p2"],"dominant_alarm_type":"...","affected_components":["RAN","Core"],"fault_domain":"RAN|Core|Transport|OSS|Multi-domain","query_intent":"brief description"}
No extra text outside JSON."""


def run(
    query: str,
    network_region: str = None,
    technology_type: str = None,
    severity: str = None,
    device_vendor: str = None,
    top_k: int = 5,
) -> dict:
    logger.info(f"Alarm Retrieval Agent: processing query '{query[:80]}...'")

    candidates = hybrid_search(
        query=query,
        network_region=network_region,
        technology_type=technology_type,
        severity=severity,
        device_vendor=device_vendor,
    )

    reranked = rerank(query, candidates, top_k=top_k)

    incidents = []
    for r in reranked:
        meta = r.get("metadata", {})
        incidents.append({
            "alarm_id": meta.get("alarm_id", r["id"]),
            "incident_description": r.get("document", "").replace(f"Alarm: {meta.get('alarm_id','')} | ", "")[:500],
            "network_region": meta.get("network_region", ""),
            "technology_type": meta.get("technology_type", ""),
            "severity": meta.get("severity", ""),
            "outage_duration": meta.get("outage_duration", 0),
            "device_vendor": meta.get("device_vendor", ""),
            "resolution_notes": meta.get("resolution_notes", ""),
            "timestamp": meta.get("timestamp", ""),
            "service_impact": meta.get("service_impact", ""),
            "alarm_type": meta.get("alarm_type", ""),
            "affected_subscribers": meta.get("affected_subscribers", 0),
            "similarity_score": r.get("rerank_score", r.get("rrf_score", 0.0)),
        })

    incident_summary = "\n".join([
        f"[{i+1}] {inc['alarm_id']}: {inc['alarm_type']} | {inc['technology_type']} | "
        f"{inc['network_region']} | {inc['severity']} | {inc['incident_description'][:200]}"
        for i, inc in enumerate(incidents)
    ])

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, http_client=httpx.Client(verify=False))
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"QUERY: {query}\n\nRETRIEVED INCIDENTS:\n{incident_summary}"},
            ],
            temperature=0.1,
            max_tokens=490,
        )
        analysis = extract_json(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        alarm_types = [inc["alarm_type"] for inc in incidents]
        analysis = {
            "alarm_patterns": list(set(alarm_types)),
            "dominant_alarm_type": max(set(alarm_types), key=alarm_types.count) if alarm_types else "Unknown",
            "affected_components": [],
            "fault_domain": "Multi-domain",
            "query_intent": query[:100],
        }

    return {
        "retrieved_incidents": incidents,
        "alarm_patterns": analysis.get("alarm_patterns", []),
        "dominant_alarm_type": analysis.get("dominant_alarm_type", "Unknown"),
        "search_metadata": {
            "query": query,
            "filters_applied": {
                k: v for k, v in {
                    "network_region": network_region,
                    "technology_type": technology_type,
                    "severity": severity,
                    "device_vendor": device_vendor,
                }.items() if v
            },
            "total_candidates": len(candidates),
            "returned_count": len(incidents),
            "fault_domain": analysis.get("fault_domain", "Unknown"),
            "query_intent": analysis.get("query_intent", ""),
        },
    }
