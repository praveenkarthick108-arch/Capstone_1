"""Add synthetic 5G incidents to ChromaDB using average embedding from similar incidents."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from rag.vector_store import get_collection

collection = get_collection()

# Get IDs of synthetic incidents not yet in ChromaDB
existing = set(collection.get(include=[])['ids'])
synth_ids = [
    "SYN-5G-S01","SYN-5G-S02","SYN-5G-S03","SYN-5G-S04","SYN-5G-S05",
    "SYN-5G-S06","SYN-5G-S07","SYN-5G-S08","SYN-5G-S09","SYN-5G-S10",
    "SYN-5G-N01","SYN-5G-N02","SYN-5G-N03",
    "SYN-5G-W01","SYN-5G-W02",
    "SYN-5G-E01","SYN-5G-E02",
    "SYN-5G-C01","SYN-5G-C02",
]
missing = [i for i in synth_ids if i not in existing]
print(f"Synthetic IDs missing from ChromaDB: {len(missing)}")

if not missing:
    print("All synthetic incidents already in ChromaDB.")
    import sys; sys.exit(0)

# Get average embedding from existing 5G-NR incidents
print("Fetching embeddings of existing 5G-NR incidents for averaging...")
existing_5g_ids = []
try:
    r = collection.get(where={"technology_type": "5G-NR"}, include=["embeddings"])
    existing_5g_ids = r["ids"]
    embeddings_5g = np.array(r["embeddings"])
    mean_emb_5g = embeddings_5g.mean(axis=0)
    norm = np.linalg.norm(mean_emb_5g)
    mean_emb_5g = (mean_emb_5g / norm).tolist()
    print(f"  Got {len(existing_5g_ids)} existing 5G-NR embeddings, avg computed (dim={len(mean_emb_5g)})")
except Exception as e:
    print(f"  Could not get 5G-NR embeddings: {e}")
    print("  Falling back to South region average...")
    try:
        r = collection.get(where={"network_region": "South"}, include=["embeddings"])
        embs = np.array(r["embeddings"])
        mean_emb_5g = (embs.mean(axis=0) / np.linalg.norm(embs.mean(axis=0))).tolist()
        print(f"  Got South embeddings, avg computed (dim={len(mean_emb_5g)})")
    except Exception as e2:
        print(f"  FAILED: {e2}")
        sys.exit(1)

# Load synthetic records from CSV
import pandas as pd
csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'telecom_incidents.csv')
df = pd.read_csv(csv_path)
synth_df = df[df['alarm_id'].isin(missing)]
print(f"Adding {len(synth_df)} synthetic incidents to ChromaDB with averaged embeddings...")

ids = []
texts = []
embeddings = []
metadatas = []

for _, row in synth_df.iterrows():
    doc_text = (f"Alarm: {row['alarm_id']} | {row.get('incident_description','')} "
                f"Resolution: {row.get('resolution_notes','')}")
    ids.append(str(row['alarm_id']))
    texts.append(doc_text)
    embeddings.append(mean_emb_5g)
    metadatas.append({
        'alarm_id': str(row['alarm_id']),
        'network_region': str(row.get('network_region', '')),
        'technology_type': str(row.get('technology_type', '')),
        'severity': str(row.get('severity', '')),
        'alarm_type': str(row.get('alarm_type', '')),
        'device_vendor': str(row.get('device_vendor', '')),
        'outage_duration': int(row.get('outage_duration', 0)),
        'affected_subscribers': int(row.get('affected_subscribers', 0)),
        'recurrence_count': int(row.get('recurrence_count', 0)),
        'service_impact': str(row.get('service_impact', '')),
        'resolution_notes': str(row.get('resolution_notes', '')),
        'timestamp': str(row.get('timestamp', '')),
        'resolution_time_minutes': int(row.get('resolution_time_minutes', 0)),
    })

collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
print(f"Done. ChromaDB total: {collection.count()}")

# Verify
verify = collection.get(where={"technology_type": "5G-NR"}, include=["metadatas"])
south_5g = [m for m in verify["metadatas"] if m.get("network_region") == "South"]
print(f"South 5G-NR in ChromaDB: {len(south_5g)}")
for m in south_5g[:3]:
    print(f"  {m['alarm_id']}: {m['alarm_type']}")
