"""
Query Enhancement Layer: rewrites casual/vague queries into technical telecom
NOC terminology and extracts filter parameters automatically.

Strategy: rule-based extraction (instant) + short LLM call for text rewriting.
"""
import sys
import os
import re
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openai import OpenAI
from config import settings
from utils.logger import get_logger

logger = get_logger("QueryEnhancer")

# ── Rule-based lookups ────────────────────────────────────────────────────────

CITY_TO_REGION = {
    # India – South
    "chennai": "South", "bangalore": "South", "bengaluru": "South",
    "hyderabad": "South", "coimbatore": "South", "madurai": "South",
    "kochi": "South", "trivandrum": "South", "mysore": "South",
    "mangalore": "South", "vijayawada": "South", "visakhapatnam": "South",
    # India – North
    "delhi": "North", "new delhi": "North", "jaipur": "North",
    "lucknow": "North", "chandigarh": "North", "amritsar": "North",
    "shimla": "North", "dehradun": "North", "agra": "North",
    "varanasi": "North", "kanpur": "North", "meerut": "North",
    # India – West
    "mumbai": "West", "pune": "West", "ahmedabad": "West",
    "surat": "West", "vadodara": "West", "goa": "West",
    "nashik": "West", "kolhapur": "West",
    # India – East
    "kolkata": "East", "bhubaneswar": "East", "guwahati": "East",
    "patna": "East", "ranchi": "East", "imphal": "East",
    "bhopal": "Central",
    # India – Central
    "nagpur": "Central", "indore": "Central", "raipur": "Central",
    "jabalpur": "Central",
    # International
    "london": "West", "manchester": "North", "glasgow": "North",
    "sydney": "South", "melbourne": "South", "perth": "West",
    "new york": "East", "boston": "East", "washington": "East",
    "chicago": "North", "dallas": "Central", "denver": "Central",
    "los angeles": "West", "san francisco": "West", "seattle": "North",
    "toronto": "North", "dubai": "West", "singapore": "East",
    "tokyo": "East", "seoul": "East", "frankfurt": "Central",
}

TECH_KEYWORDS = {
    "5G-NR":   ["5g", "5 g", "five g", "gnb", "g-nb", "nr ", "new radio", "5gnr", "ngran"],
    "4G-LTE":  ["4g", "4 g", "four g", "lte", "enodeb", "enb", "e-nodeb", "volte"],
    "3G-UMTS": ["3g", "3 g", "three g", "umts", "wcdma", "nodeb", "hspa"],
    "Fiber":   ["fiber", "fibre", "optical", "dwdm", "ofc", "optical fiber", "fttp"],
    "MPLS":    ["mpls", "backbone", "core network", "pe router", "label switching"],
    "SD-WAN":  ["sd-wan", "sdwan", "sd wan", "wan "],
}

SEVERITY_KEYWORDS = {
    "P1-Critical": ["outage", "down", "not working", "dead", "complete failure",
                    "emergency", "critical", "blackout", "total loss", "offline",
                    "no service", "completely failed", "no signal", "no network"],
    "P2-High":     ["major", "widespread", "serious", "high priority", "significant",
                    "large scale", "multiple sites", "many users"],
    "P3-Medium":   ["slow", "sluggish", "intermittent", "degraded", "partial",
                    "occasional", "unstable", "dropping", "fluctuating", "poor"],
    "P4-Low":      ["minor", "slight", "small", "barely", "low priority", "marginal"],
}

REWRITE_SYSTEM = """You are a telecom NOC engineer. Rewrite the user's query as a technical incident description (1-2 sentences). Use proper telecom terms: alarm types, network elements, symptoms. Be concise. Return ONLY the rewritten query text, nothing else."""


def _extract_region(text: str) -> str | None:
    text_lower = text.lower()
    for city, region in CITY_TO_REGION.items():
        if city in text_lower:
            return region
    return None


def _extract_technology(text: str) -> str | None:
    text_lower = text.lower()
    for tech, keywords in TECH_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return tech
    return None


def _extract_severity(text: str) -> str | None:
    text_lower = text.lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return severity
    return None


def _is_already_technical(query: str) -> bool:
    technical_markers = [
        "interface", "gnb", "enodeb", "handover", "rrc", "s1", "x2", "n2", "n3",
        "alarm", "failure", "degradation", "latency", "packet loss", "rsrp",
        "sync", "ptp", "dwdm", "mpls", "bgp", "ospf", "lsp", "bfd",
    ]
    q = query.lower()
    return sum(1 for m in technical_markers if m in q) >= 2


def _rewrite_with_llm(raw_query: str, region: str, technology: str) -> str:
    """Short LLM call to rewrite query into technical language."""
    context = ""
    if region:
        context += f" (region: {region})"
    if technology:
        context += f" (technology: {technology})"

    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            http_client=httpx.Client(verify=False, timeout=20.0),
        max_retries=0,
        )
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM},
                {"role": "user", "content": f"Query: {raw_query}{context}"},
            ],
            temperature=0,
            max_tokens=120,
        )
        return response.choices[0].message.content.strip().strip('"')
    except Exception as e:
        logger.warning(f"LLM rewrite failed ({e}), using rule-based fallback")
        return None


def _rule_based_rewrite(raw_query: str, technology: str, severity: str) -> str:
    """Fallback: inject telecom terminology without LLM."""
    q = raw_query.lower()

    # Map common consumer phrases to technical equivalents
    replacements = {
        "not working": "service outage and connectivity failure",
        "broken": "equipment failure",
        "slow": "high latency and throughput degradation",
        "bad internet": "data bearer degradation and packet loss",
        "no signal": "radio coverage loss and RSRP degradation",
        "dropping calls": "call drop due to handover failure",
        "keeps disconnecting": "intermittent link flap and session drop",
        "towers are down": "base station outage — eNodeB/gNB offline",
        "tower down": "base station outage",
        "internet down": "data service outage",
        "network down": "network element failure causing service disruption",
        "5g not working": "5G-NR radio interface failure",
        "4g not working": "4G-LTE data service failure",
        "fiber cut": "optical fiber link break causing L1 loss-of-signal",
    }

    result = raw_query
    for phrase, replacement in replacements.items():
        if phrase in q:
            result = re.sub(re.escape(phrase), replacement, result, flags=re.IGNORECASE)

    tech_prefix = f"{technology} " if technology else ""
    if not any(t in result.lower() for t in ["failure", "outage", "degradation", "loss", "fault", "error"]):
        result = f"{tech_prefix}network fault detected: {result}"

    return result


def enhance_query(raw_query: str) -> dict:
    """
    Rewrite a raw user query into technical telecom language and extract filters.
    Uses rule-based extraction (instant) + short LLM rewrite.
    Falls back gracefully if LLM is unavailable.
    """
    # Step 1: Rule-based extraction (always fast, no LLM)
    region = _extract_region(raw_query)
    technology = _extract_technology(raw_query)
    severity = _extract_severity(raw_query)
    already_technical = _is_already_technical(raw_query)

    # Step 2: Decide if rewriting is needed
    needs_rewrite = not already_technical and len(raw_query.split()) < 30

    if needs_rewrite:
        # Step 3a: Try LLM rewrite (short prompt, 25s timeout)
        technical_query = _rewrite_with_llm(raw_query, region, technology)

        if not technical_query:
            # Step 3b: Rule-based fallback
            technical_query = _rule_based_rewrite(raw_query, technology, severity)

        was_enhanced = technical_query.lower().strip() != raw_query.lower().strip()
    else:
        technical_query = raw_query
        was_enhanced = False

    # Build enhancement notes
    notes_parts = []
    if region:
        notes_parts.append(f"location mapped to {region} region")
    if technology:
        notes_parts.append(f"technology identified as {technology}")
    if severity:
        notes_parts.append(f"severity inferred as {severity}")
    if needs_rewrite and was_enhanced:
        notes_parts.append("query expanded to telecom terminology")

    enhancement_notes = "; ".join(notes_parts) if notes_parts else "query used as-is"

    logger.info(
        f"Enhanced: '{raw_query[:50]}' -> '{technical_query[:60]}' "
        f"[region={region}, tech={technology}, sev={severity}]"
    )

    return {
        "technical_query": technical_query or raw_query,
        "network_region": region,
        "technology_type": technology,
        "severity": severity,
        "was_enhanced": was_enhanced or bool(region or technology or severity),
        "enhancement_notes": enhancement_notes,
        "original_query": raw_query,
    }
