"""
Predictive Outage Intelligence: statistical risk scoring based on historical patterns.
Uses pandas to analyze 7,381 real Telstra incidents for proactive outage forecasting.
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

_df_cache: pd.DataFrame = None
SEVERITY_RANK = {"P1-Critical": 4, "P2-High": 3, "P3-Medium": 2, "P4-Low": 1}
SLA_THRESHOLD_MINUTES = 30


def _load_data() -> pd.DataFrame:
    global _df_cache
    if _df_cache is not None:
        return _df_cache
    try:
        df = pd.read_csv(settings.DATA_CSV_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["severity_rank"] = df["severity"].map(SEVERITY_RANK).fillna(1)
        df["outage_duration"] = pd.to_numeric(df["outage_duration"], errors="coerce").fillna(0)
        df["recurrence_count"] = pd.to_numeric(df["recurrence_count"], errors="coerce").fillna(0)
        df["affected_subscribers"] = pd.to_numeric(df["affected_subscribers"], errors="coerce").fillna(0)
        _df_cache = df
        return df
    except Exception as e:
        return pd.DataFrame()


def _risk_score(group: pd.DataFrame) -> float:
    """Compute 0-100 risk score from a subset of incidents."""
    if len(group) == 0:
        return 0.0
    sev_score = (group["severity_rank"].mean() - 1) / 3 * 40         # 0-40
    rec_score = min(group["recurrence_count"].mean() / 10 * 25, 25)  # 0-25
    vol_score = min(len(group) / 50 * 20, 20)                        # 0-20
    dur_score = min(group["outage_duration"].mean() / 120 * 15, 15)  # 0-15
    return round(sev_score + rec_score + vol_score + dur_score, 1)


def _risk_level(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 55:
        return "HIGH"
    if score >= 35:
        return "MEDIUM"
    return "LOW"


def _contributing_factors(group: pd.DataFrame) -> list:
    factors = []
    if group["severity_rank"].mean() >= 3:
        factors.append("High severity incident concentration")
    if group["recurrence_count"].mean() > 5:
        factors.append(f"High recurrence rate ({group['recurrence_count'].mean():.1f}x avg)")
    if group["outage_duration"].mean() > 60:
        factors.append(f"Extended outage durations ({group['outage_duration'].mean():.0f} min avg)")
    top_alarm_counts = group["alarm_type"].value_counts()
    if len(top_alarm_counts) > 0 and top_alarm_counts.iloc[0] / len(group) > 0.3:
        factors.append(f"Dominant fault: {top_alarm_counts.index[0]}")
    if not factors:
        factors.append("Standard incident frequency")
    return factors[:3]


def _recommendation(risk_score: float, top_alarm: str) -> str:
    if risk_score >= 75:
        return f"IMMEDIATE: Deploy preventive maintenance, escalate {top_alarm} monitoring to NOC"
    if risk_score >= 55:
        return f"URGENT: Schedule inspection for {top_alarm} within 48 hours"
    if risk_score >= 35:
        return f"MONITOR: Increase polling frequency for {top_alarm} patterns"
    return "ROUTINE: Continue standard monitoring procedures"


def predict_by_region() -> list:
    """Outage risk score per network region."""
    df = _load_data()
    if df.empty:
        return []
    results = []
    for region, group in df.groupby("network_region"):
        score = _risk_score(group)
        top_alarm = group["alarm_type"].value_counts().index[0] if len(group) > 0 else "Unknown"
        p1_pct = len(group[group["severity"] == "P1-Critical"]) / len(group) * 100
        results.append({
            "region": region,
            "risk_score": score,
            "risk_level": _risk_level(score),
            "incident_count": len(group),
            "top_alarm_type": top_alarm,
            "top_technology": group["technology_type"].value_counts().index[0] if len(group) > 0 else "Unknown",
            "avg_outage_minutes": round(float(group["outage_duration"].mean()), 1),
            "critical_incident_pct": round(p1_pct, 1),
            "avg_recurrence": round(float(group["recurrence_count"].mean()), 1),
            "contributing_factors": _contributing_factors(group),
            "recommended_action": _recommendation(score, top_alarm),
        })
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)


def predict_by_technology() -> list:
    """Outage risk score per technology type."""
    df = _load_data()
    if df.empty:
        return []
    results = []
    for tech, group in df.groupby("technology_type"):
        score = _risk_score(group)
        sev_dist = group["severity"].value_counts().to_dict()
        results.append({
            "technology": tech,
            "risk_score": score,
            "risk_level": _risk_level(score),
            "incident_count": len(group),
            "top_alarm_type": group["alarm_type"].value_counts().index[0] if len(group) > 0 else "Unknown",
            "avg_outage_minutes": round(float(group["outage_duration"].mean()), 1),
            "p1_count": int(sev_dist.get("P1-Critical", 0)),
            "avg_recurrence": round(float(group["recurrence_count"].mean()), 1),
            "contributing_factors": _contributing_factors(group),
        })
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)


def predict_hotspots(top_n: int = 10) -> list:
    """Highest-risk region + technology combinations."""
    df = _load_data()
    if df.empty:
        return []
    results = []
    for (region, tech), group in df.groupby(["network_region", "technology_type"]):
        score = _risk_score(group)
        if score > 15:
            results.append({
                "region": region,
                "technology": tech,
                "risk_score": score,
                "risk_level": _risk_level(score),
                "incident_count": len(group),
                "top_alarm": group["alarm_type"].value_counts().index[0] if len(group) > 0 else "Unknown",
                "avg_outage_minutes": round(float(group["outage_duration"].mean()), 1),
                "avg_subscribers_affected": round(float(group["affected_subscribers"].mean()), 0),
            })
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)[:top_n]


def get_sla_analysis() -> dict:
    """Full SLA health analysis with breach probabilities."""
    df = _load_data()
    if df.empty:
        return {}
    total = len(df)
    breached = df[df["outage_duration"] > SLA_THRESHOLD_MINUTES]
    at_risk = df[(df["outage_duration"] > 15) & (df["outage_duration"] <= SLA_THRESHOLD_MINUTES)]

    breach_by_region = breached.groupby("network_region").size().to_dict()
    breach_by_tech = breached.groupby("technology_type").size().to_dict()

    breach_prob = {}
    for sev, grp in df.groupby("severity"):
        b = len(grp[grp["outage_duration"] > SLA_THRESHOLD_MINUTES])
        breach_prob[sev] = round(b / len(grp) * 100, 1) if len(grp) > 0 else 0.0

    # Estimate next breach window per region (incidents per month proxy)
    next_breach_risk = {}
    for region, grp in df.groupby("network_region"):
        breach_rate = len(grp[grp["outage_duration"] > SLA_THRESHOLD_MINUTES]) / len(grp)
        p1_rate = len(grp[grp["severity"] == "P1-Critical"]) / len(grp)
        combined = (breach_rate * 0.6 + p1_rate * 0.4) * 100
        next_breach_risk[region] = round(combined, 1)

    return {
        "total_incidents": total,
        "sla_breaches": int(len(breached)),
        "sla_breach_rate_pct": round(len(breached) / total * 100, 1) if total > 0 else 0.0,
        "at_risk_incidents": int(len(at_risk)),
        "breach_by_region": {k: int(v) for k, v in breach_by_region.items()},
        "breach_by_technology": {k: int(v) for k, v in breach_by_tech.items()},
        "breach_probability_by_severity": breach_prob,
        "next_breach_risk_by_region": next_breach_risk,
        "avg_breach_duration_minutes": round(float(breached["outage_duration"].mean()), 1) if len(breached) > 0 else 0.0,
        "sla_threshold_minutes": SLA_THRESHOLD_MINUTES,
        "estimated_total_downtime_hours": round(float(df["outage_duration"].sum()) / 60, 1),
    }


def get_cross_region_correlation() -> dict:
    """Cross-region fault propagation patterns and correlation matrix."""
    df = _load_data()
    if df.empty:
        return {}
    regions = sorted(df["network_region"].unique().tolist())
    alarm_by_region = {r: set(df[df["network_region"] == r]["alarm_type"].unique()) for r in regions}

    matrix = {}
    for r1 in regions:
        matrix[r1] = {}
        for r2 in regions:
            if r1 == r2:
                count = len(df[df["network_region"] == r1])
                matrix[r1][r2] = round(count / len(df) * 100, 1)
            else:
                shared = len(alarm_by_region[r1] & alarm_by_region[r2])
                union = len(alarm_by_region[r1] | alarm_by_region[r2])
                matrix[r1][r2] = round(shared / union * 100, 1) if union > 0 else 0.0

    propagation = []
    for alarm_type, grp in df.groupby("alarm_type"):
        affected = grp["network_region"].unique().tolist()
        if len(affected) > 2:
            propagation.append({
                "alarm_type": alarm_type,
                "affected_regions": affected,
                "spread_count": len(affected),
                "avg_severity_rank": round(float(grp["severity_rank"].mean()), 2),
                "incident_count": int(len(grp)),
            })
    propagation.sort(key=lambda x: (-x["spread_count"], -x["avg_severity_rank"]))

    return {
        "regions": regions,
        "correlation_matrix": matrix,
        "propagation_patterns": propagation[:10],
    }


def get_alarm_frequency_trend() -> list:
    """Monthly alarm frequency trend with forecast direction."""
    df = _load_data()
    if df.empty:
        return []
    df_valid = df.dropna(subset=["timestamp"])
    if df_valid.empty:
        return []

    df_valid = df_valid.copy()
    df_valid["month"] = df_valid["timestamp"].dt.to_period("M").astype(str)
    monthly = df_valid.groupby("month").agg(
        incident_count=("alarm_id", "count"),
        p1_count=("severity", lambda x: (x == "P1-Critical").sum()),
        avg_duration=("outage_duration", "mean"),
        avg_subscribers=("affected_subscribers", "mean"),
    ).reset_index()
    monthly = monthly.sort_values("month").tail(12)
    monthly["avg_duration"] = monthly["avg_duration"].round(1)
    monthly["avg_subscribers"] = monthly["avg_subscribers"].round(0).astype(int)

    # Simple linear trend direction
    counts = monthly["incident_count"].tolist()
    if len(counts) >= 3:
        trend = "increasing" if counts[-1] > counts[-3] else "decreasing" if counts[-1] < counts[-3] else "stable"
    else:
        trend = "stable"

    result = monthly.to_dict(orient="records")
    for r in result:
        r["trend"] = trend
    return result
