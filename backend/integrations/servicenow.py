"""
ServiceNow OSS/BSS Integration — TelecomIQ Fault Intelligence Platform
Creates structured NOC incident tickets via the ServiceNow Table REST API.
"""
import sys
import os
import requests
from datetime import datetime, timezone
from requests.auth import HTTPBasicAuth

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

SERVICENOW_BASE = settings.SERVICENOW_INSTANCE.rstrip("/")
INCIDENT_API = f"{SERVICENOW_BASE}/api/now/table/incident"

# Maps project severity to ServiceNow urgency/impact/priority
SEVERITY_MAP = {
    "P1-Critical": {"urgency": "1", "impact": "1", "priority": "1"},
    "P2-High":     {"urgency": "1", "impact": "2", "priority": "2"},
    "P3-Medium":   {"urgency": "2", "impact": "2", "priority": "3"},
    "P4-Low":      {"urgency": "3", "impact": "3", "priority": "4"},
}

# Technology → ServiceNow subcategory
TECH_SUBCATEGORY = {
    "5G-NR":    "5g_nr",
    "4G-LTE":   "4g_lte",
    "3G-UMTS":  "3g_umts",
    "Fiber":    "fiber_optic",
    "MPLS":     "mpls",
    "SD-WAN":   "sd_wan",
}

# SLA risk → human readable
SLA_LABELS = {
    "HIGH":   "■■■ HIGH  — Immediate action required",
    "MEDIUM": "■■□ MEDIUM — Monitor closely",
    "LOW":    "■□□ LOW    — Standard resolution",
}

DIVIDER = "─" * 62


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(settings.SERVICENOW_USER, settings.SERVICENOW_PASSWORD)


def _headers() -> dict:
    return {"Content-Type": "application/json", "Accept": "application/json"}


def _fmt_description(
    query: str,
    query_id: str,
    alarm_type: str,
    region: str,
    technology: str,
    severity: str,
    sla_breach_risk: str,
    affected_subscribers: int,
    revenue_impact: str,
    business_impact_score: float,
    impacted_services: list[str],
    root_cause_chain: str,
    confidence_score: float,
    probable_causes: list[dict],
    technical_explanation: str,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sla_label = SLA_LABELS.get(sla_breach_risk, sla_breach_risk)
    causes_text = "\n".join(
        f"    {i+1}. {c.get('cause','?'):<42} ({int(c.get('confidence',0)*100)}% confidence) [{c.get('category','?')}]"
        for i, c in enumerate(probable_causes[:4])
    )

    return f"""╔══════════════════════════════════════════════════════════════╗
  TELECOM FAULT INTELLIGENCE REPORT — AI GENERATED
  TelecomIQ  |  Network Operations Center Automation Platform
╚══════════════════════════════════════════════════════════════╝

■ INCIDENT IDENTIFICATION
{DIVIDER}
  Report ID      : TIQ-{query_id.upper()}
  Generated      : {now}
  Source         : TelecomIQ AI Fault Intelligence Platform v2.0
  Detection Mode : Automated AI Analysis (RAG + Multi-Agent Pipeline)

■ FAULT CLASSIFICATION
{DIVIDER}
  Alarm Type     : {alarm_type}
  Technology     : {technology}
  Affected Region: {region}
  Severity       : {severity}
  SLA Risk       : {sla_label}

■ BUSINESS IMPACT ASSESSMENT
{DIVIDER}
  Subscribers Affected : {affected_subscribers:,}
  Revenue Impact       : {revenue_impact}
  Business Impact Score: {business_impact_score:.1f} / 10.0
  Impacted Services    : {', '.join(impacted_services) if impacted_services else 'N/A'}

■ AI ROOT CAUSE ANALYSIS  (Confidence: {int(confidence_score*100)}%)
{DIVIDER}
  Fault Chain:
    {root_cause_chain}

  Probable Causes:
{causes_text if causes_text else "    Analysis in progress"}

  Technical Explanation:
  {technical_explanation or 'See work notes for details.'}

■ ORIGINAL FAULT QUERY
{DIVIDER}
  "{query}"

{DIVIDER}
* This incident was automatically raised by TelecomIQ AI Platform.
* All findings are AI-generated and should be verified by an engineer.
"""


def _fmt_work_notes(
    resolution_steps: list[str],
    escalation_path: str,
    estimated_resolution_time: str,
    vendor_commands: list[dict] | None = None,
    prevention_measures: list[str] | None = None,
) -> str:
    steps_text = "\n".join(
        f"  Step {i+1}: {step}" for i, step in enumerate(resolution_steps[:6])
    )

    vendor_text = ""
    if vendor_commands:
        vendor_text = "\n■ VENDOR-SPECIFIC COMMANDS\n" + DIVIDER + "\n"
        for vc in vendor_commands[:4]:
            vendor_text += f"  [{vc.get('vendor','?')}]  {vc.get('command','?')}\n"
            vendor_text += f"         → {vc.get('purpose','')}\n"

    prevention_text = ""
    if prevention_measures:
        prevention_text = "\n■ PREVENTION MEASURES\n" + DIVIDER + "\n"
        prevention_text += "\n".join(f"  • {m}" for m in prevention_measures[:4])

    return f"""■ AI-GENERATED RESOLUTION PLAYBOOK
{DIVIDER}

{steps_text}

■ ESCALATION PATH
{DIVIDER}
  {escalation_path or 'L1 NOC → L2 Network Engineer → L3/Vendor TAC'}

■ ESTIMATED RESOLUTION TIME
{DIVIDER}
  {estimated_resolution_time or 'See escalation path'}
{vendor_text}{prevention_text}
{DIVIDER}
Updated by TelecomIQ AI Platform — verify steps before execution.
"""


def create_incident(
    query: str,
    alarm_type: str,
    region: str,
    technology: str,
    severity: str,
    root_cause_chain: str,
    technical_explanation: str,
    resolution_steps: list[str],
    affected_subscribers: int,
    sla_breach_risk: str,
    query_id: str,
    # Optional enrichment fields
    confidence_score: float = 0.0,
    probable_causes: list[dict] | None = None,
    revenue_impact: str = "Unknown",
    business_impact_score: float = 0.0,
    impacted_services: list[str] | None = None,
    escalation_path: str = "",
    estimated_resolution_time: str = "",
    vendor_commands: list[dict] | None = None,
    prevention_measures: list[str] | None = None,
) -> dict:
    """Create a structured ServiceNow NOC incident from a TelecomIQ fault analysis result."""
    sev = SEVERITY_MAP.get(severity, SEVERITY_MAP["P3-Medium"])

    short_desc = (
        f"[TelecomIQ] {severity} | {alarm_type} | {region} Region | "
        f"{affected_subscribers:,} subscribers | SLA: {sla_breach_risk}"
    )

    description = _fmt_description(
        query=query, query_id=query_id, alarm_type=alarm_type,
        region=region, technology=technology, severity=severity,
        sla_breach_risk=sla_breach_risk, affected_subscribers=affected_subscribers,
        revenue_impact=revenue_impact, business_impact_score=business_impact_score,
        impacted_services=impacted_services or [],
        root_cause_chain=root_cause_chain, confidence_score=confidence_score,
        probable_causes=probable_causes or [], technical_explanation=technical_explanation,
    )

    work_notes = _fmt_work_notes(
        resolution_steps=resolution_steps,
        escalation_path=escalation_path,
        estimated_resolution_time=estimated_resolution_time,
        vendor_commands=vendor_commands,
        prevention_measures=prevention_measures,
    )

    payload = {
        "short_description": short_desc,
        "description": description,
        "work_notes": work_notes,
        "urgency": sev["urgency"],
        "impact": sev["impact"],
        "category": "network",
        "subcategory": TECH_SUBCATEGORY.get(technology, "network_other"),
        "contact_type": "monitoring",          # automated detection
        "caller_id": settings.SERVICENOW_USER,
        "assignment_group": "Network Operations",
        "comments": (
            f"Automated incident raised by TelecomIQ AI Platform. "
            f"Query ID: TIQ-{query_id.upper()}. "
            f"AI RCA confidence: {int(confidence_score*100)}%. "
            f"Please review and assign to appropriate NOC engineer."
        ),
    }

    resp = requests.post(
        INCIDENT_API,
        json=payload,
        auth=_auth(),
        headers=_headers(),
        timeout=15,
        verify=False,
    )
    resp.raise_for_status()
    result = resp.json().get("result", {})

    sys_id = result.get("sys_id", "")
    number = result.get("number", "")
    ticket_url = f"{SERVICENOW_BASE}/nav_to.do?uri=incident.do?sys_id={sys_id}" if sys_id else ""

    return {
        "sys_id": sys_id,
        "ticket_number": number,
        "ticket_url": ticket_url,
        "state": result.get("state", "1"),
        "priority": result.get("priority", sev["priority"]),
        "short_description": short_desc,
        "created_at": result.get("sys_created_on", ""),
    }


def get_incident(sys_id: str) -> dict:
    resp = requests.get(
        f"{INCIDENT_API}/{sys_id}",
        auth=_auth(), headers=_headers(), timeout=15, verify=False,
    )
    resp.raise_for_status()
    return resp.json().get("result", {})


def list_recent_incidents(limit: int = 10) -> list:
    params = {
        "sysparm_query": "short_descriptionSTARTSWITH[TelecomIQ]^ORDERBYDESCsys_created_on",
        "sysparm_limit": str(limit),
        "sysparm_fields": "sys_id,number,short_description,state,priority,sys_created_on,urgency,impact,category,subcategory,contact_type",
    }
    resp = requests.get(
        INCIDENT_API, params=params,
        auth=_auth(), headers=_headers(), timeout=15, verify=False,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])
