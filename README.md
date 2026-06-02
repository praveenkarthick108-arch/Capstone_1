# AI-Powered Telecom Network Fault Intelligence Assistant

An AI-powered system enabling telecom engineers to investigate network faults using **natural language queries**, **semantic incident retrieval**, and **multi-agent root-cause analysis**.

---

## Architecture Overview

```
Engineer Query (NL)
        │
        ▼
┌─────────────────────────────────┐
│       FastAPI Backend           │
│  ┌──────────────────────────┐   │
│  │   Input Guardrails       │   │   ← Validates telecom relevance, PII
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │   Hybrid RAG Layer       │   │   ← Vector (ChromaDB) + BM25 + RRF fusion
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │  Multi-Agent Pipeline    │   │
│  │  1. Alarm Retrieval      │   │   ← Semantic + keyword search + reranking
│  │  2. Root Cause Analysis  │   │   ← 5-Why, alarm correlation, 3GPP knowledge
│  │  3. Service Impact       │   │   ← Subscriber/SLA/revenue assessment
│  │  4. Resolution Planner   │   │   ← Vendor-specific step-by-step playbook
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │  Evaluation Framework    │   │   ← DeepEval + LLM-as-judge
│  └──────────────────────────┘   │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│     React Frontend              │
│  Animated Agent Pipeline View   │
│  RCA Dashboard + Incident Cards │
│  Analytics Dashboard (Recharts) │
└─────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Configure Environment

```bash
cp .env.example backend/.env
# The .env already contains the keygateway API key
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Generate Dataset

```bash
python data/generator.py
# Creates: data/telecom_incidents.csv (500 records)
```

### 4. Run Data Ingestion (embeds dataset into ChromaDB + builds BM25 index)

```bash
cd backend
python data/ingestion.py
# Takes ~3-5 minutes (API rate limited)
```

### 5. Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 6. Start Frontend

```bash
cd frontend
npm install
npm start
# Opens: http://localhost:3000
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | Main fault analysis — runs 4-agent pipeline |
| `GET` | `/api/analytics` | Dashboard statistics |
| `GET` | `/api/incidents` | Browse incidents with filters |
| `POST` | `/api/evaluate` | Run DeepEval + LLM-as-judge |
| `POST` | `/api/ingest` | Trigger dataset re-ingestion |
| `GET` | `/api/health` | System health check |

### Example: Fault Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "5G gNB sites in North region showing X2 interface failures after firmware upgrade",
    "network_region": "North",
    "technology_type": "5G-NR",
    "top_k": 5
  }'
```

### Example: Evaluation

```bash
curl -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MPLS core router LDP session flap",
    "response": "Root cause identified as BGP route policy misconfiguration...",
    "retrieved_contexts": ["Incident ALM-2024-00123: MPLS LDP flap..."]
  }'
```

---

## Dataset

**Source:** Synthetic 5G Network Performance Dataset (500 records)  
**Format:** CSV  
**Key Fields:**
- `alarm_id`, `incident_description`, `network_region`, `technology_type`
- `severity` (P1-Critical → P4-Low), `outage_duration`, `device_vendor`
- `resolution_notes`, `timestamp`, `service_impact`
- `alarm_type`, `affected_subscribers`, `resolution_time_minutes`, `recurrence_count`

**Severity Distribution:** ~25% each of P1/P2/P3/P4

---

## Evaluation Framework

The system implements a dual evaluation approach:

**DeepEval Metrics:**
- Faithfulness (response grounded in retrieved context)
- Answer Relevancy (response addresses the query)
- Contextual Precision (retrieved docs ranked correctly)
- Contextual Recall (relevant docs retrieved)

**LLM-as-Judge Rubric:**
- Technical Accuracy (0-10)
- Actionability of Recommendations (0-10)
- Alarm Correlation Quality (0-10)

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| LLM | gpt-4o-mini via keygateway |
| Embeddings | text-embedding-3-small |
| Vector Store | ChromaDB (cosine similarity) |
| Keyword Search | BM25 (rank-bm25) |
| Retrieval Fusion | Reciprocal Rank Fusion (RRF, k=60) |
| Backend | FastAPI + uvicorn |
| Evaluation | DeepEval + LLM-as-judge |
| Frontend | React + TypeScript + Tailwind + Recharts |

---

## Design Decisions

1. **Hybrid Search over Semantic-only:** BM25 captures exact alarm codes/vendor names; vector search handles semantic similarity. RRF fusion combines both without parameter tuning.

2. **Sequential Agent Pipeline over Parallel:** Each agent enriches context for the next (Alarm → RCA → Impact → Resolution). This grounding improves response quality over independent parallel agents.

3. **ChromaDB over Pinecone/Weaviate:** Zero-infrastructure setup for development. Persistent client maintains embeddings across restarts.

4. **One chunk per incident:** Telecom incidents are self-contained records (200-400 tokens). No splitting needed; metadata-rich embeddings enable precise filtering.
