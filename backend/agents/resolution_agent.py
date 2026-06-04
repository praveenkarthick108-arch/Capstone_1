import httpx
"""
Agent 4: Resolution Recommendation Agent
Generates vendor-specific, step-by-step troubleshooting guidance.
"""
import sys
import os
import json
from utils.json_extract import extract_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings
from utils.logger import get_logger

logger = get_logger("ResolutionAgent")

SYSTEM_PROMPT = """Senior telecom NOC engineer (Ericsson/Nokia/Huawei/Cisco/Juniper). Output ONLY compact JSON:
{"immediate_steps":[{"step":1,"action":"...","command":"...","expected_outcome":"...","priority":"CRITICAL|HIGH|MEDIUM"}],"escalation_path":"L1→L2→Vendor TAC","prevention_measures":["p1","p2"],"estimated_resolution_time":"X-Y min","vendor_specific_commands":[{"vendor":"Cisco","command":"sh ip ospf","purpose":"verify"}]}
Max 3 immediate steps. Keep each field under 20 words. No extra text outside JSON."""


def run(query: str, retrieval_result: dict, rca_result: dict, impact_result: dict) -> dict:
    logger.info("Resolution Agent: generating troubleshooting guidance...")

    incidents = retrieval_result.get("retrieved_incidents", [])
    resolution_notes = [
        inc.get("resolution_notes", "")
        for inc in incidents if inc.get("resolution_notes")
    ]

    vendors = list({inc.get("device_vendor", "") for inc in incidents if inc.get("device_vendor")})
    techs = list({inc.get("technology_type", "") for inc in incidents if inc.get("technology_type")})

    historical_resolutions = "\n".join([
        f"  - [{incidents[i]['alarm_id']}] {notes[:250]}"
        for i, notes in enumerate(resolution_notes[:3])
    ])

    first_cause = ""
    causes = rca_result.get('probable_causes', [])
    if causes and isinstance(causes[0], dict):
        first_cause = causes[0].get('cause', '')[:60]

    prompt = f"""FAULT: {query[:120]}
CAUSE: {first_cause or rca_result.get('root_cause_chain','N/A')[:80]}
IMPACT: {impact_result.get('affected_subscribers',0):,} subs, {impact_result.get('sla_breach_risk','?')} SLA risk
VENDORS: {', '.join(vendors[:2]) if vendors else 'Mixed'}
RESOLUTIONS FROM HISTORY: {historical_resolutions[:200] if historical_resolutions else 'None'}
Output troubleshooting JSON only."""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL,
                        http_client=httpx.Client(verify=False, timeout=8.0), max_retries=0)
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=490,
        )
        result = extract_json(response.choices[0].message.content)
        if not result or "immediate_steps" not in result:
            raise ValueError("Invalid JSON response")
    except Exception as e:
        logger.error(f"Resolution LLM call failed: {e}")
        result = {
            "immediate_steps": [
                {"step": 1, "action": "Check alarm logs and identify affected NEs", "command": "show alarm active", "expected_outcome": "List of active alarms", "priority": "CRITICAL"},
                {"step": 2, "action": "Verify redundancy path and activate failover if available", "command": "show interface status", "expected_outcome": "Redundant path active", "priority": "CRITICAL"},
                {"step": 3, "action": "Notify NOC and create P1 incident ticket", "command": "", "expected_outcome": "Ticket created, teams mobilized", "priority": "HIGH"},
            ],
            "escalation_path": "L1 NOC (immediate) → L2 Network Engineer (5min) → L3/Vendor TAC (30min)",
            "prevention_measures": ["Implement automated health checks", "Review change management process"],
            "estimated_resolution_time": "30-90 minutes",
            "vendor_specific_commands": [],
            "verification_steps": ["Confirm alarm cleared", "Verify KPIs returned to baseline", "Check subscriber complaints resolved"],
            "knowledge_base_refs": ["3GPP TS 32.111 Fault Management", "ITU-T G.7710 OAM"],
        }

    return result
