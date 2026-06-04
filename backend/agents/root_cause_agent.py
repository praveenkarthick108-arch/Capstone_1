import httpx
"""
Agent 2: Root Cause Analysis Agent
Correlates alarms, identifies probable causes, generates explainable RCA,
and performs cross-region fault pattern analysis.
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
{"probable_causes":[{"cause":"...","confidence":0.0-1.0,"evidence":"...","category":"Hardware|Software|Config|Capacity|External"}],"root_cause_chain":"Trigger→Symptom→Impact","correlated_alarms":["alarm1","alarm2"],"confidence_score":0.0-1.0,"technical_explanation":"2-3 sentence summary","cross_region_risk":"None|Low|Medium|High","propagation_risk":"brief note if alarm spreads across regions"}
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


def analyze_cross_region(incidents: list[dict]) -> dict:
    """Detect if alarm patterns span multiple regions (cross-region propagation risk)."""
    regions = [inc.get("network_region", "") for inc in incidents if inc.get("network_region")]
    unique_regions = list(set(r for r in regions if r))
    alarm_types = [inc.get("alarm_type", "") for inc in incidents if inc.get("alarm_type")]
    dominant = Counter(alarm_types).most_common(1)[0][0] if alarm_types else "Unknown"

    if len(unique_regions) >= 4:
        risk = "High"
        note = f"{dominant} detected across {len(unique_regions)} regions — likely backbone/core issue"
    elif len(unique_regions) >= 3:
        risk = "Medium"
        note = f"{dominant} spreading across {', '.join(unique_regions)} — potential cascading failure"
    elif len(unique_regions) == 2:
        risk = "Low"
        note = f"{dominant} in {' and '.join(unique_regions)} — monitor for spread"
    else:
        risk = "None"
        note = "Fault appears localized to single region"

    return {"risk": risk, "note": note, "affected_regions": unique_regions}


def run(query: str, retrieval_result: dict) -> dict:
    logger.info("Root Cause Agent: analyzing fault patterns + cross-region risk...")

    incidents = retrieval_result.get("retrieved_incidents", [])
    alarm_patterns = retrieval_result.get("alarm_patterns", [])
    dominant_type = retrieval_result.get("dominant_alarm_type", "Unknown")
    correlated = correlate_alarms(incidents)
    cross_region = analyze_cross_region(incidents)

    incident_context = "\n".join([
        f"- {inc['alarm_id']}: {inc['alarm_type']} | {inc['technology_type']} | {inc['severity']} | {inc.get('network_region','?')} | {inc['incident_description'][:100]}"
        for inc in incidents[:3]
    ])

    prompt = f"""FAULT: {query[:200]}
DOMINANT ALARM: {dominant_type}
PATTERNS: {', '.join(alarm_patterns[:3])}
CROSS-REGION: {cross_region['risk']} risk — {cross_region['note']}
SIMILAR INCIDENTS (top 3):
{incident_context}
Analyze root cause. Output JSON only."""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL,
                        http_client=httpx.Client(verify=False, timeout=8.0), max_retries=0)
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
                {
                    "cause": f"{dominant_type} triggered by equipment fault",
                    "confidence": 0.65,
                    "evidence": f"Seen in {len(incidents)} similar incidents",
                    "category": "Hardware",
                },
            ],
            "root_cause_chain": f"{dominant_type} → Service Degradation → Customer Impact",
            "correlated_alarms": correlated,
            "confidence_score": 0.65,
            "technical_explanation": "Analysis based on historical incident pattern matching.",
            "cross_region_risk": cross_region["risk"],
            "propagation_risk": cross_region["note"],
        }

    result["correlated_alarms"] = result.get("correlated_alarms", correlated)
    result["cross_region_risk"] = result.get("cross_region_risk", cross_region["risk"])
    result["propagation_risk"] = result.get("propagation_risk", cross_region["note"])
    result["affected_regions"] = cross_region["affected_regions"]
    return result
