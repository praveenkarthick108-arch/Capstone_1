"""Input validation and guardrails for query safety."""
import re

TELECOM_KEYWORDS = {
    # Technical telecom terms
    "network", "alarm", "outage", "failure", "degradation", "latency", "packet",
    "5g", "4g", "lte", "nr", "enodeb", "gnb", "mme", "amf", "upf", "smf",
    "fiber", "mpls", "router", "switch", "tower", "bts", "bsc", "msc",
    "signal", "connectivity", "handover", "synchronization", "bandwidth",
    "interference", "drop", "timeout", "link", "down", "error", "fault",
    "incident", "troubleshoot", "resolve", "cause", "impact", "subscriber",
    "ericsson", "nokia", "huawei", "cisco", "juniper", "region", "vendor",
    "loss", "congestion", "overload", "reset", "reboot", "degraded", "restore",
    "port", "interface", "throughput", "jitter", "ping", "trace", "route",
    "core", "radio", "transport", "access", "backhaul", "fronthaul", "midhaul",
    # Casual / end-user vocabulary
    "internet", "wifi", "mobile", "phone", "call", "calls", "data", "speed",
    "slow", "working", "not", "disconnected", "connection", "service", "issue",
    "problem", "broken", "dead", "weak", "poor", "bad", "no", "cut", "off",
    "dropping", "dropped", "lost", "coverage", "bars", "reception",
    # Indian city names (map to regions via query enhancer)
    "chennai", "bangalore", "bengaluru", "hyderabad", "mumbai", "delhi",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow", "nagpur", "surat",
    "indore", "bhopal", "patna", "kochi", "chandigarh", "guwahati",
    # Generic location words
    "city", "region", "area", "zone", "sector", "location", "site",
}

PII_PATTERNS = [
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    r"\b(?:\d{4}[- ]?){4}\b",
]

INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"you\s+are\s+now\s+a",
    r"forget\s+your\s+(instructions|guidelines|rules)",
    r"(drop|delete|truncate|alter|insert|update)\s+(table|database|from)",
    r"<script[^>]*>",
    r"(system\s*prompt|override\s*instructions)",
]


def validate_query(query: str) -> tuple[bool, str]:
    if not query or not query.strip():
        return False, "Query cannot be empty."

    if len(query.strip()) < 5:
        return False, "Query too short. Please describe the network issue in more detail."

    if len(query) > 500:
        return False, "Query too long. Please limit to 500 characters."

    for pattern in PII_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains sensitive information (IP addresses, phone numbers, or emails). Please remove them."

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains disallowed content."

    query_words = set(re.findall(r"\b\w+\b", query.lower()))
    if not query_words.intersection(TELECOM_KEYWORDS):
        return False, "Query does not appear to be telecom-related. Please describe a network fault or incident."

    return True, ""


def sanitize_query(query: str) -> str:
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    return query
