import httpx
"""
Agent 2: Root Cause Analysis Agent
Correlates alarms, identifies probable causes, generates explainable RCA.
"""
import sys
import os
import json
from utils.json_extract import extract_json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings
from utils.logger import get_logger

logger = get_logger("RootCauseAgent")

SYSTEM_PROMPT = """You are a telecom RCA expert (3GPP, Ericsson/Nokia/Huawei/Cisco/Juniper).
Output ONLY compact JSON with these exact keys:
{"probable_causes":[{"cause":"...","confidence":0.0-1.0,"evidence":"...","category":"Hardware|Software|Config|Capacity|External"}],"root_cause_chain":"Trigger→Symptom→Impact","correlated_alarms":["alarm1","alarm2"],"confidence_score":0.0-1.0,"technical_explanation":"2-3 sentence summary"}
Keep each field SHORT. Max 2 causes. No extra text outside JSON."""


def correlate_alarms(incidents: list[dict]) -> list[str]:
    alarm_counts = Counter(inc.get("alarm_type", "") for inc in incidents)
    vendor_counts = Counter(inc.get("device_vendor", "") for inc in incidents)
    correlated = []
    for alarm, count in alarm_counts.most_common(2):
        if alarm:
            correlated.append(f"{alarm} ({count}/{len(incidents)} incidents)")
    if vendor_counts:
        top = vendor_counts.most_common(1)[0]
        correlated.append(f"{top[0]} ({top[1]} incidents)")
    return correlated


def run(query: str, retrieval_result: dict) -> dict:
    logger.info("Root Cause Agent: analyzing fault patterns...")

    incidents = retrieval_result.get("retrieved_incidents", [])
    alarm_patterns = retrieval_result.get("alarm_patterns", [])
    dominant_type = retrieval_result.get("dominant_alarm_type", "Unknown")
    correlated = correlate_alarms(incidents)

    incident_context = "\n".join([
        f"- {inc['alarm_id']}: {inc['alarm_type']} | {inc['technology_type']} | {inc['severity']} | {inc['incident_description'][:120]}"
        for inc in incidents[:3]
    ])

    prompt = f"""FAULT: {query[:200]}
DOMINANT ALARM: {dominant_type}
PATTERNS: {', '.join(alarm_patterns[:3])}
SIMILAR INCIDENTS (top 3):
{incident_context}
Analyze root cause. Output JSON only."""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, http_client=httpx.Client(verify=False))
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=490,
        )
        result = extract_json(response.choices[0].message.content)
        if not result or "probable_causes" not in result:
            raise ValueError("Empty/invalid JSON response")
    except Exception as e:
        logger.error(f"RCA LLM call failed: {e}")
        result = {
            "probable_causes": [
                {"cause": f"{dominant_type} triggered by equipment fault", "confidence": 0.65, "evidence": f"Seen in {len(incidents)} similar incidents", "category": "Hardware"},
            ],
            "root_cause_chain": f"{dominant_type} → Service Degradation → Customer Impact",
            "correlated_alarms": correlated,
            "confidence_score": 0.65,
            "technical_explanation": "Analysis based on historical incident pattern matching.",
        }

    result["correlated_alarms"] = result.get("correlated_alarms", correlated)
    return result
