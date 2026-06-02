"""
Data preprocessing pipeline: cleaning, chunking, metadata extraction.
"""
import pandas as pd
import re
from typing import Any


def load_and_clean(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.drop_duplicates(subset=["alarm_id"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["incident_description", "resolution_notes"])
    df["incident_description"] = df["incident_description"].str.strip()
    df["resolution_notes"] = df["resolution_notes"].str.strip()
    df["outage_duration"] = pd.to_numeric(df["outage_duration"], errors="coerce").fillna(0).astype(int)
    df["affected_subscribers"] = pd.to_numeric(df["affected_subscribers"], errors="coerce").fillna(0).astype(int)
    df["resolution_time_minutes"] = pd.to_numeric(df["resolution_time_minutes"], errors="coerce").fillna(0).astype(int)
    df["recurrence_count"] = pd.to_numeric(df["recurrence_count"], errors="coerce").fillna(0).astype(int)
    return df


def build_searchable_text(row: pd.Series) -> str:
    """Concatenates key fields into a rich semantic chunk for embedding."""
    parts = [
        f"Alarm: {row['alarm_id']}",
        f"Region: {row['network_region']}",
        f"Technology: {row['technology_type']}",
        f"Severity: {row['severity']}",
        f"Vendor: {row['device_vendor']}",
        f"Alarm Type: {row['alarm_type']}",
        f"Service Impact: {row['service_impact']}",
        f"Description: {row['incident_description']}",
        f"Resolution: {row['resolution_notes']}",
    ]
    return " | ".join(parts)


def extract_metadata(row: pd.Series) -> dict[str, Any]:
    """Extracts ChromaDB-compatible metadata (str/int/float/bool only)."""
    return {
        "alarm_id": str(row["alarm_id"]),
        "network_region": str(row["network_region"]),
        "technology_type": str(row["technology_type"]),
        "severity": str(row["severity"]),
        "device_vendor": str(row["device_vendor"]),
        "alarm_type": str(row["alarm_type"]),
        "outage_duration": int(row["outage_duration"]),
        "affected_subscribers": int(row["affected_subscribers"]),
        "resolution_time_minutes": int(row["resolution_time_minutes"]),
        "recurrence_count": int(row["recurrence_count"]),
        "service_impact": str(row["service_impact"]),
        "resolution_notes": str(row["resolution_notes"])[:500],
        "incident_description": str(row["incident_description"])[:500],
        "timestamp": str(row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else row["timestamp"]),
        "severity_rank": {"P1-Critical": 4, "P2-High": 3, "P3-Medium": 2, "P4-Low": 1}.get(
            str(row["severity"]), 1
        ),
    }


def prepare_documents(df: pd.DataFrame) -> tuple[list[str], list[str], list[dict]]:
    """Returns (ids, texts, metadatas) ready for ChromaDB ingestion."""
    ids, texts, metadatas = [], [], []
    for _, row in df.iterrows():
        ids.append(str(row["alarm_id"]))
        texts.append(build_searchable_text(row))
        metadatas.append(extract_metadata(row))
    return ids, texts, metadatas


def get_bm25_corpus(df: pd.DataFrame) -> list[list[str]]:
    """Tokenized corpus for BM25 index."""
    corpus = []
    for _, row in df.iterrows():
        text = f"{row['incident_description']} {row['resolution_notes']} {row['alarm_type']} {row['technology_type']}"
        tokens = re.findall(r"\b\w+\b", text.lower())
        corpus.append(tokens)
    return corpus
