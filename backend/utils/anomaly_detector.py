"""Detect statistically anomalous incident rates for a region+technology combination."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config import settings


def detect_anomaly(region: str = None, technology: str = None) -> dict:
    """
    Compare recent 3-month incident rate vs all-time baseline for a combo.
    Returns anomaly details when rate >= 2x baseline, else {"is_anomaly": False}.
    """
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.DATA_CSV_PATH)
        df = pd.read_csv(csv_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])

        if df.empty:
            return {"is_anomaly": False}

        # Filter to this combination
        mask = pd.Series([True] * len(df), index=df.index)
        if region:
            mask &= df["network_region"] == region
        if technology:
            mask &= df["technology_type"] == technology

        combo_df = df[mask]
        if len(combo_df) < 10:
            return {"is_anomaly": False}

        # All-time baseline rate (incidents per month)
        total_months = max(1.0, (df["timestamp"].max() - df["timestamp"].min()).days / 30.0)
        baseline_rate = len(combo_df) / total_months

        if baseline_rate < 0.5:
            return {"is_anomaly": False}

        # Recent 3-month rate
        cutoff = df["timestamp"].max() - pd.Timedelta(days=90)
        recent_count = len(combo_df[combo_df["timestamp"] >= cutoff])
        recent_rate = recent_count / 3.0

        multiplier = round(recent_rate / baseline_rate, 1) if baseline_rate > 0 else 1.0

        if multiplier < 1.8:
            return {"is_anomaly": False}

        parts = [p for p in [region, technology] if p]
        combo_label = " / ".join(parts) if parts else "Network"

        return {
            "is_anomaly": True,
            "combination": combo_label,
            "current_rate": round(recent_rate, 1),
            "baseline_rate": round(baseline_rate, 1),
            "multiplier": multiplier,
            "severity": "HIGH" if multiplier >= 3.0 else "MEDIUM",
            "message": (
                f"{combo_label} incidents are {multiplier}x above baseline "
                f"({recent_rate:.1f}/mo recent vs {baseline_rate:.1f}/mo avg)"
            ),
        }

    except Exception:
        return {"is_anomaly": False}
