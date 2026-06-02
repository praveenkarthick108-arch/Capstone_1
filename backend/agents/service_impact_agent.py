import httpx
# Agent 3: Service Impact Agent
import sys
import os
import json
from utils.json_extract import extract_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings
from utils.logger import get_logger

logger = get_logger("ServiceImpactAgent")

SYSTEM_PROMPT = """Telecom SLA/service assurance expert. Output ONLY compact JSON:
{"affected_subscribers":N,"sla_breach_risk":"HIGH|MEDIUM|LOW","impacted_services":["s1","s2"],"business_impact_score":0.0-10.0,"revenue_impact_estimate":"$XK-YK per hour","affected_regions":["R1"],"cascading_risks":["r1"],"sla_details":"brief"}
HIGH: P1/P2+>15min+>10K subs. MEDIUM: P2/P3+5-15min. LOW: P3/P4+<5min. No extra text."""


def run(query: str, retrieval_result: dict, rca_result: dict) -> dict:
    logger.info("Service Impact Agent: assessing business impact...")

    incidents = retrieval_result.get("retrieved_incidents", [])
    avg_subscribers = int(
        sum(inc.get("affected_subscribers", 0) for inc in incidents) / max(len(incidents), 1)
    )
    avg_duration = int(
        sum(inc.get("outage_duration", 0) for inc in incidents) / max(len(incidents), 1)
    )
    severities = [inc.get("severity", "P4-Low") for inc in incidents]
    service_impacts = list({
        s.strip() for inc in incidents for s in inc.get("service_impact", "").split(",") if s.strip()
    })
    regions = list({inc.get("network_region", "") for inc in incidents if inc.get("network_region")})

    prompt = f"""FAULT: {query[:150]}
RCA: {rca_result.get('root_cause_chain','N/A')[:80]}
HISTORY: avg {avg_subscribers:,} subs, avg {avg_duration}min, {','.join(set(severities))}, services: {','.join(service_impacts[:3])}
Assess impact. Output JSON only."""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, http_client=httpx.Client(verify=False))
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=490,
        )
        result = extract_json(response.choices[0].message.content)
        if not result or "affected_subscribers" not in result:
            raise ValueError("Invalid JSON response")
    except Exception as e:
        logger.error(f"Service impact LLM call failed: {e}")
        severity_score = {"P1-Critical": 9, "P2-High": 7, "P3-Medium": 4, "P4-Low": 2}
        top_sev = max(severities, key=lambda s: severity_score.get(s, 1)) if severities else "P3-Medium"
        result = {
            "affected_subscribers": avg_subscribers,
            "sla_breach_risk": "HIGH" if "P1" in top_sev else "MEDIUM" if "P2" in top_sev else "LOW",
            "impacted_services": service_impacts or ["Data Sessions", "Voice Calls"],
            "business_impact_score": severity_score.get(top_sev, 5),
            "revenue_impact_estimate": f"${avg_duration * 5}K-{avg_duration * 15}K per hour",
            "affected_regions": regions,
            "customer_segments": {"residential": avg_subscribers * 7 // 10, "enterprise": avg_subscribers * 2 // 10, "iot": avg_subscribers // 10},
            "cascading_risks": ["Traffic rerouting overload", "Core network congestion"],
            "sla_details": "Carrier SLA: 99.95% monthly availability (21.6 min budget)",
        }

    return result
