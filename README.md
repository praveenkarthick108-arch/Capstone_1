# TelecomIQ — AI-Powered Telecom Network Fault Intelligence Assistant

> Describe any network fault in plain language. AI agents retrieve, correlate, and diagnose in real time.

**TelecomIQ** is a full-stack AI platform that lets telecom NOC engineers investigate network faults using natural language queries. It combines Hybrid RAG retrieval, a 4-agent sequential pipeline, real-time SSE streaming, ServiceNow integration, and a sustainability dashboard — all built on top of a 7,400-incident knowledge base of real Telstra network data.

---

## Live Demo

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8001 |
| API Docs (Swagger) | http://localhost:8001/docs |
| Architecture Diagrams | http://localhost:3000 → Architecture tab |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  BROWSER / FRONTEND  (React 18 + TypeScript + Recharts)                  │
│  Fault Analysis · Dashboard · Query History · Architecture · Voice · Q&A │
└─────────────────────────┬────────────────────────────────────────────────┘
                          │  HTTP REST · Server-Sent Events (SSE)
┌─────────────────────────▼────────────────────────────────────────────────┐
│  FASTAPI BACKEND  (Python 3.12 · Uvicorn · Pydantic v2 · Async/Await)   │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  REQUEST PIPELINE                                                    │ │
│  │  Input Guardrails → Query Enhancement (LLM) → Anomaly Detector      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  MULTI-AGENT PIPELINE  (A2A Communication · SSE Streaming)          │ │
│  │  [Agent 1: Alarm Retrieval] → [Agent 2: Root Cause Analysis]        │ │
│  │  → [Agent 3: Service Impact] → [Agent 4: Resolution Planner]        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  HYBRID RAG STACK                                                    │ │
│  │  text-embedding-3-small → ChromaDB  +  BM25 → RRF Fusion            │ │
│  │  → LLM Reranker → Top-5 with Retrieval Explainability               │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  INTEGRATIONS                                                        │ │
│  │  ServiceNow REST API · LLM Gateway · Feedback Store · Predictions   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────────┐
│  DATA LAYER                                                                │
│  ChromaDB (7,400 incidents · cosine index) · BM25 Index (pickle)         │
│  Telstra CSV Dataset · localStorage (query history)                       │
└──────────────────────────────────────────────────────────────────────────┘
```

> **Full interactive diagrams** available in the app under the **Architecture** tab:
> - **System Architecture Diagram** — all 30+ components color-coded by tier
> - **Data Flow Diagram** — step-by-step journey from query input to SSE response

---

## Data Flow (Query to Response)

```
User Input (text / voice)
        │
        ▼
[Input Guardrails]  ──── 422 Rejected (PII / injection / non-telecom)
        │ pass
        ▼
[Query Enhancement]  ── LLM rewrites to technical language
        │                 Extracts: region / technology / severity
        ▼
[Hybrid Retrieval] ──────────────────────────────────┐
        │                                             │
   Vector Search                                BM25 Search
  (ChromaDB cosine,                          (rank_bm25 IDF,
   top-20 + filter)                           top-20 candidates)
        │                                             │
        └─────────────── RRF Fusion ──────────────────┘
                               │
                         LLM Reranker
                               │
                     Top-5 + Retrieval Explanation
                      (BM25 terms + vector %)
                               │
        ┌──────────────────────▼──────────────────────┐
        │           AGENT PIPELINE (A2A + SSE)         │
        │                                              │
        │  Agent 1: Alarm Retrieval                    │──→ SSE event 1
        │    └─ output → Agent 2: Root Cause Analysis  │──→ SSE event 2
        │                  └─ output → Agent 3: Impact │──→ SSE event 3
        │                               └─ output →   │
        │                           Agent 4: Resolution│──→ SSE event 4
        └──────────────────────────────────────────────┘
                               │
                    [Post-Processing]
                    Anomaly detection · Chain fixing
                    SLA escalation · Unknown fills
                               │
                    SSE "complete" event → UI
                    Progressive rendering per agent
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Install Backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create `backend/.env`:

```env
OPENAI_API_KEY=learner004
OPENAI_BASE_URL=https://keygateway.arshnivlabs.com/
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_db
BM25_INDEX_PATH=./bm25_index.pkl
DATA_CSV_PATH=../data/telecom_incidents.csv
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
SERVICENOW_INSTANCE=https://dev385660.service-now.com
SERVICENOW_USER=admin
SERVICENOW_PASSWORD=<your_password>
```

### 3. Run Data Ingestion

```bash
cd backend
python data/ingestion.py
# Embeds 7,400 incidents into ChromaDB + builds BM25 pickle index
# Takes 5-10 minutes (API rate limited)
```

### 4. Start Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001
# API docs: http://localhost:8001/docs
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm start
# Opens: http://localhost:3000
```

---

## API Reference

### Core Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/stream` | **Primary endpoint** — SSE streaming, one event per agent |
| `POST` | `/api/query` | Non-streaming analysis (returns full JSON) |
| `POST` | `/api/followup` | Conversational Q&A with prior context (single LLM call, ~3-5s) |

### Analytics & Intelligence

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/analytics` | Full dashboard stats (distribution, trends, SLA, cross-region) |
| `GET` | `/api/predict` | Outage risk predictions by region + technology |
| `GET` | `/api/incidents` | Browse knowledge base with filters + pagination |

### Evaluation & Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/evaluate` | Run DeepEval + LLM-as-judge on a query/response pair |
| `POST` | `/api/feedback` | Submit star rating + helpful flag |
| `GET` | `/api/feedback/stats` | Aggregate feedback statistics |

### Cache & System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cache/stats` | Semantic cache hit rate, entries, total lookups |
| `DELETE` | `/api/cache` | Clear the query cache |
| `GET` | `/api/health` | System health + ChromaDB + BM25 status |
| `POST` | `/api/ingest` | Re-trigger ingestion pipeline |
| `POST` | `/api/summarize` | Summarize a list of alarm IDs |

### ServiceNow Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/servicenow/create-ticket` | Create structured NOC incident ticket |
| `GET` | `/api/servicenow/tickets` | List recent TelecomIQ-created tickets |
| `GET` | `/api/servicenow/ticket/{sys_id}` | Fetch a specific ticket |

### Example — Streaming Query

```bash
curl -N -X POST http://localhost:8001/api/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "5G not working in south region", "top_k": 5}'
```

Response (Server-Sent Events):
```
data: {"type":"enhanced","enhancement":{"extracted_region":"South","extracted_technology":"5G-NR",...}}

data: {"type":"agent_done","agent_name":"Alarm Retrieval Agent","status":"completed","duration_ms":6143}

data: {"type":"agent_done","agent_name":"Root Cause Analysis Agent","status":"completed","duration_ms":4504}

data: {"type":"agent_done","agent_name":"Service Impact Agent","status":"completed","duration_ms":23451}

data: {"type":"agent_done","agent_name":"Resolution Recommendation Agent","status":"completed","duration_ms":5221}

data: {"type":"complete","result":{...full FaultQueryResponse...}}
```

### Example — Follow-up Q&A

```bash
curl -X POST http://localhost:8001/api/followup \
  -H "Content-Type: application/json" \
  -d '{
    "followup_query": "What if this was 4G instead?",
    "prior_alarm_type": "5G Radio Access Failure",
    "prior_region": "South",
    "prior_technology": "5G-NR",
    "prior_root_cause": "5G Radio Access Failure -> 5G-NR Degradation -> South Customer Impact"
  }'
```

---

## Features

### Core Intelligence
| Feature | Description |
|---------|-------------|
| **Hybrid RAG** | Vector (ChromaDB) + BM25 keyword search fused via RRF (k=60) |
| **LLM Reranker** | gpt-4o-mini cross-encoder reranks top-10 → top-5 with scores |
| **Retrieval Explainability** | Each result shows BM25 matching keywords + vector similarity % + method tag |
| **Multi-Agent A2A Pipeline** | 4 agents in sequence; each output becomes next agent's context |
| **Query Enhancement** | LLM rewrites casual queries to technical language; extracts region/tech/severity |
| **Input Guardrails** | PII detection, injection blocking, telecom keyword validation (422 rejection) |

### Real-Time UX
| Feature | Description |
|---------|-------------|
| **SSE Streaming** | Server-Sent Events — one event per agent; watch pipeline think live |
| **Voice Input** | Web Speech API mic button — speak your query, transcript auto-fills |
| **Follow-up Q&A** | Chat thread below results; context carried automatically; single LLM call (~3-5s) |
| **Semantic Query Cache** | Cosine similarity cache (88% threshold); cache hits replay in <1s with zero LLM calls |

### Analytics & Intelligence
| Feature | Description |
|---------|-------------|
| **Analytics Dashboard** | 4 tabs: Overview · Risk Forecast · SLA Intelligence · Cross-Region Correlation |
| **Outage Risk Prediction** | Risk scores (0-100) per region and technology; top hotspots |
| **Anomaly Detection** | Flags when incident rate ≥ 1.8× baseline for any region+technology combination |
| **SLA Countdown Timer** | Live countdown to SLA breach when risk is HIGH (30-min SLA window) |
| **Confidence Breakdown** | Click ⓘ on RCA gauge to see exactly why the confidence score is what it is |

### Operations
| Feature | Description |
|---------|-------------|
| **ServiceNow Integration** | One-click ticket creation with structured NOC report format, vendor commands, escalation path |
| **Export Report** | Download full analysis as `.md` file (RCA chain, resolution steps, incident list) |
| **Query History** | Last 20 queries persisted in localStorage; click to restore any result |
| **Feedback System** | Star rating + thumbs up/down; stored in SQLite feedback store |

### Responsible AI
| Feature | Description |
|---------|-------------|
| **Green AI Score** | Token efficiency vs naive baseline (814K tokens); CO₂ grams saved per query |
| **RAG Quality Metrics** | 4 DeepEval-compatible scores per query (Faithfulness, Relevancy, Precision, Recall) |

---

## Dataset

| Property | Value |
|----------|-------|
| **Source** | Real Telstra network incident data |
| **Size** | 7,400 incidents (7,381 Telstra + 19 synthetic 5G-NR) |
| **Technologies** | 5G-NR, 4G-LTE, 3G-UMTS, Core Network, Fiber, MPLS, Microwave, Transport |
| **Regions** | North, South, East, West, Central |
| **Severity Levels** | P1-Critical, P2-High, P3-Medium, P4-Low |
| **Vendors** | Ericsson, Nokia, Huawei, Cisco, Juniper |
| **Alarm Types** | Physical Layer Fault, gNB Connectivity, RRU Fault, Network Congestion, and 20+ more |

**Synthetic augmentation:** 19 5G-NR incidents added to address dataset sparsity (only 15 original 5G-NR records); augmented with mean embedding from existing 5G-NR incidents for ChromaDB compatibility.

---

## Project Structure

```
Capstone_Project/
├── backend/
│   ├── main.py                    # FastAPI app — all endpoints
│   ├── config.py                  # Pydantic settings
│   ├── requirements.txt
│   ├── agents/
│   │   ├── orchestrator.py        # Sequential pipeline + async streaming generator
│   │   ├── alarm_retrieval_agent.py
│   │   ├── root_cause_agent.py
│   │   ├── service_impact_agent.py
│   │   └── resolution_agent.py
│   ├── rag/
│   │   ├── embeddings.py          # OpenAI embeddings client
│   │   ├── vector_store.py        # ChromaDB operations
│   │   ├── bm25_search.py         # BM25 + explainability (term scores)
│   │   ├── hybrid_search.py       # RRF fusion + retrieval explanation attachment
│   │   └── reranker.py            # LLM cross-encoder reranker
│   ├── data/
│   │   ├── ingestion.py           # Embed + store in ChromaDB + build BM25
│   │   ├── preprocessor.py        # Data cleaning and chunking
│   │   └── feedback_store.py      # SQLite feedback persistence
│   ├── prediction/
│   │   └── outage_predictor.py    # Risk scores + SLA analysis + cross-region correlation
│   ├── evaluation/
│   │   ├── deepeval_evaluator.py  # Faithfulness, relevancy, precision, recall
│   │   └── llm_judge.py           # LLM-as-judge scoring rubric
│   ├── integrations/
│   │   └── servicenow.py          # ServiceNow REST API — structured NOC tickets
│   └── utils/
│       ├── guardrails.py          # Input validation + PII + injection detection
│       ├── query_enhancer.py      # LLM query rewriting + metadata extraction
│       ├── query_cache.py         # Semantic query cache (cosine similarity)
│       └── anomaly_detector.py    # Incident rate baseline comparison
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Home.tsx           # Fault Analysis — streaming + voice + Q&A
│       │   ├── Dashboard.tsx      # Analytics — 4 tabs with Recharts
│       │   ├── History.tsx        # Query history from localStorage
│       │   └── Architecture.tsx   # System Architecture + Data Flow SVG diagrams
│       ├── components/
│       │   ├── ResultsPanel.tsx   # RCA + Impact + Resolution + Green Score + Explainability
│       │   ├── AgentPipeline.tsx  # Live agent status visualization
│       │   ├── IncidentCard.tsx   # Individual incident card
│       │   ├── FilterPanel.tsx    # Region/severity/vendor filters
│       │   └── Navbar.tsx         # Navigation + health status
│       ├── services/api.ts        # Typed API client (axios + fetch SSE)
│       └── types/index.ts         # TypeScript interfaces
└── data/
    └── telecom_incidents.csv      # 7,400-row incident knowledge base
```

---

## Architecture & Data Flow Diagrams

The **Architecture** tab in the app contains two fully interactive SVG diagrams:

### System Architecture Diagram
Shows all 30+ system components organized in 5 color-coded tiers:
- **Cyan** — Browser/Frontend (React components)
- **Purple** — AI Agents (A2A pipeline)
- **Green** — RAG Stack (hybrid search)
- **Gold** — LLM Gateway + utilities
- **Orange** — Data storage layer
- **Red** — External services (ServiceNow)

### Data Flow Diagram *(separate from architecture)*
Shows the step-by-step journey of a single query from input to SSE response, organized in 5 phases:
- **Phase 1: Input** — text or voice (Web Speech API)
- **Phase 2: Validation** — guardrails with 422 rejection branch + LLM enhancement
- **Phase 3: Retrieval** — parallel vector + BM25 search → RRF → LLM reranker
- **Phase 4: Agents** — A2A pipeline with SSE event markers per agent
- **Phase 5: Output** — post-processing → SSE stream → progressive UI update

> These diagrams are **distinct**: the architecture shows *what exists*, the data flow shows *how a query travels through it*.

---

## Evaluation Framework

### RAG Quality Metrics (per query, displayed in UI)
All four metrics are DeepEval-compatible and computed from retrieval statistics:

| Metric | Measures | How Computed |
|--------|----------|--------------|
| **Faithfulness** | Response grounded in retrieved incidents | Average similarity score of top-5 docs |
| **Answer Relevancy** | Response addresses the query | Top incident cosine similarity |
| **Contextual Precision** | Top results ranked correctly | Incident count ≥ 3 + top similarity |
| **Contextual Recall** | All relevant incidents retrieved | Retrieved count / 5 target |

### LLM-as-Judge
Separate gpt-4o-mini evaluation call with structured rubric:
- Technical Accuracy (0-10)
- Actionability of Recommendations (0-10)
- Alarm Correlation Quality (0-10)

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **LLM** | gpt-4o-mini via keygateway.arshnivlabs.com |
| **Embeddings** | text-embedding-3-small |
| **Vector Store** | ChromaDB (persistent, cosine similarity) |
| **Keyword Search** | rank_bm25 (BM25Okapi, IDF-weighted) |
| **Retrieval Fusion** | Reciprocal Rank Fusion (RRF, k=60) |
| **Backend** | FastAPI + Uvicorn (ASGI) + Pydantic v2 |
| **Streaming** | Server-Sent Events (fetch ReadableStream) |
| **Frontend** | React 18 + TypeScript + Tailwind CSS |
| **Charts** | Recharts (donut, bar, line, radar) |
| **Evaluation** | DeepEval-compatible metrics + LLM-as-judge |
| **Integration** | ServiceNow Table REST API |
| **Voice** | Web Speech API (browser-native) |
| **Data** | pandas + numpy + ChromaDB + pickle |

---

## Design Decisions

**1. Hybrid Search over Semantic-only**
BM25 captures exact alarm codes, vendor names, and technical terms (e.g., `gnb`, `enodeb`, `sctp`). Vector search handles semantic similarity. RRF fusion combines both without parameter tuning.

**2. Sequential A2A Pipeline over Parallel Agents**
Each agent enriches context for the next (Alarm → RCA → Impact → Resolution). Parallel agents would produce independent, uncorrelated outputs. A2A grounding improves response coherence.

**3. SSE over WebSockets for Streaming**
Fault analysis is one-directional server push. SSE is simpler, auto-reconnects, and works through proxies without the upgrade overhead of WebSockets.

**4. Fetch + ReadableStream over EventSource for POST SSE**
EventSource only supports GET requests. Using `fetch()` with a ReadableStream allows POST bodies (query payload) while still consuming the SSE stream incrementally.

**5. In-Memory Semantic Cache over Redis**
For a capstone demo, an in-memory numpy cosine cache (max 50 entries) avoids Redis infrastructure overhead while demonstrating the caching concept clearly. Production would swap to Redis.

**6. One chunk per incident (no splitting)**
Telecom incidents are self-contained records (200–400 tokens). Splitting would break the metadata relationship. Each incident embeds as one document with full metadata for ChromaDB `where` filtering.

**7. BM25-only fallback mode**
When the embedding API is unavailable (LLM gateway down), vector search fails gracefully. BM25 continues alone, with ChromaDB metadata queries applied to filter results by region/technology without needing embeddings.

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Knowledge base size | 7,400 incidents |
| Token reduction vs naive LLM | ~97% |
| Cache threshold | 88% cosine similarity |
| SSE events per query | 5 (1 enhanced + 4 agent_done + 1 complete) |
| Agent pipeline timeout | 8s per agent (fail fast) |
| LLM model | gpt-4o-mini |
| Embedding dimensions | 1,536 (text-embedding-3-small) |
| RRF k parameter | 60 |
| Max cache entries | 50 queries |
| Query history (localStorage) | 20 entries |
