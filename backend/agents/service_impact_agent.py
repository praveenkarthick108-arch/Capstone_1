import httpx
# Agent 3: Service Impact Agent — full SLA prediction + proactive breach alerting
import sys
import os
import json
from utils.json_extract import extract_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings
from utils.logger import get_logger

logger = get_logger("ServiceImpactAgent")

# Carrier SLA standard: 99.95% monthly uptime = 21.6 min downtime budget
SLA_MONTHLY_BUDGET_MINUTES = 21.6
SLA_THRESHOLD_SINGLE_INCIDENT = 30

SYSTEM_PROMPT = """Telecom SLA/service assurance expert with carrier-grade knowledge.
Output ONLY compact JSON:
{"affected_subscribers":N,"sla_breach_risk":"HIGH|MEDIUM|LOW","sla_breach_probability":0.0-1.0,"impacted_services":["s1","s2"],"business_impact_score":0.0-10.0,"revenue_impact_estimate":"$XK-YK per hour","affected_regions":["R1"],"cascading_risks":["r1"],"sla_details":"brief","proactive_alert":"alert message if HIGH risk","mttr_estimate_minutes":N}
HIGH: P1/P2+>15min+>10K subs or breach_prob>0.7. MEDIUM: P2/P3+5-15min or breach_prob 0.4-0.7. LOW: P3/P4+<5min. No extra text."""


def _sla_breach_probability(severity: str, avg_duration: float, recurrence: float) -> float:
    """Estimate SLA breach probability (0-1) from incident characteristics."""
    base = {"P1-Critical": 0.85, "P2-High": 0.60, "P3-Medium": 0.30, "P4-Low": 0.10}
    prob = base.get(severity, 0.30)
    if avg_duration > SLA_THRESHOLD_SINGLE_INCIDENT:
        prob = min(prob + 0.20, 0.99)
    if recurrence > 5:
        prob = min(prob + 0.10, 0.99)
    return round(prob, 2)


def _proactive_sla_alert(breach_risk: str, breach_prob: float, top_sev: str, avg_duration: float) -> str:
    if breach_risk == "HIGH" or breach_prob > 0.7:
        return (
            f"PROACTIVE SLA ALERT: {breach_prob*100:.0f}% breach probability detected. "
            f"Incident pattern ({top_sev}, avg {avg_duration:.0f}min) exceeds SLA budget of "
            f"{SLA_MONTHLY_BUDGET_MINUTES}min/month. Escalate to NOC and begin preventive actions immediately."
        )
    if breach_risk == "MEDIUM" or breach_prob > 0.4:
        return (
            f"SLA WATCH: {breach_prob*100:.0f}% breach probability. Monitor closely — "
            f"continued degradation will breach the {SLA_MONTHLY_BUDGET_MINUTES}min monthly SLA budget."
        )
    return ""


def run(query: str, retrieval_result: dict, rca_result: dict) -> dict:
    logger.info("Service Impact Agent: assessing business impact + SLA breach risk...")

    incidents = retrieval_result.get("retrieved_incidents", [])
    avg_subscribers = int(
        sum(inc.get("affected_subscribers", 0) for inc in incidents) / max(len(incidents), 1)
    )
    avg_duration = sum(inc.get("outage_duration", 0) for inc in incidents) / max(len(incidents), 1)
    avg_recurrence = sum(inc.get("recurrence_count", 0) for inc in incidents) / max(len(incidents), 1)
    severities = [inc.get("severity", "P4-Low") for inc in incidents]
    service_impacts = list({
        s.strip() for inc in incidents for s in inc.get("service_impact", "").split(",") if s.strip()
    })
    regions = list({inc.get("network_region", "") for inc in incidents if inc.get("network_region")})

    severity_score = {"P1-Critical": 9, "P2-High": 7, "P3-Medium": 4, "P4-Low": 2}
    top_sev = max(severities, key=lambda s: severity_score.get(s, 1)) if severities else "P3-Medium"
    breach_prob = _sla_breach_probability(top_sev, avg_duration, avg_recurrence)

    prompt = f"""FAULT: {query[:150]}
RCA: {rca_result.get('root_cause_chain','N/A')[:80]}
HISTORY: avg {avg_subscribers:,} subs, avg {avg_duration:.0f}min, recurrence {avg_recurrence:.1f}x, severities: {','.join(set(severities))}, services: {','.join(service_impacts[:3])}
SLA breach probability (pre-computed): {breach_prob:.2f}
Assess impact. Output JSON only."""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL,
                        http_client=httpx.Client(verify=False, timeout=8.0), max_retries=0)
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
        breach_risk = "HIGH" if "P1" in top_sev else "MEDIUM" if "P2" in top_sev else "LOW"
        result = {
            "affected_subscribers": avg_subscribers,
            "sla_breach_risk": breach_risk,
            "sla_breach_probability": breach_prob,
            "impacted_services": service_impacts or ["Data Sessions", "Voice Calls"],
            "business_impact_score": severity_score.get(top_sev, 5),
            "revenue_impact_estimate": f"${int(avg_duration * 5)}K-{int(avg_duration * 15)}K per hour",
            "affected_regions": regions,
            "cascading_risks": ["Traffic rerouting overload", "Core network congestion"],
            "sla_details": f"Carrier SLA: 99.95% monthly ({SLA_MONTHLY_BUDGET_MINUTES}min budget). Breach prob: {breach_prob:.0%}",
            "mttr_estimate_minutes": max(int(avg_duration * 1.5), 15),
        }

    # Always inject computed proactive alert
    result["sla_breach_probability"] = result.get("sla_breach_probability", breach_prob)
    result["proactive_alert"] = _proactive_sla_alert(
        result.get("sla_breach_risk", "LOW"),
        float(result.get("sla_breach_probability", breach_prob)),
        top_sev,
        avg_duration,
    )
    return result
