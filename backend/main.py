"""
AI-Powered Telecom Network Fault Intelligence Assistant
FastAPI Backend — main entry point
"""
import sys
import os
import json
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models.request_models import FaultQueryRequest, EvaluationRequest, IngestRequest
from models.response_models import (
    FaultQueryResponse, EvaluationResult, AnalyticsResponse,
    HealthResponse, IncidentRecord, AlarmRetrievalResult,
    RootCauseResult, ServiceImpactResult, ResolutionResult, AgentStatus,
)
from agents.orchestrator import run_pipeline
from rag.vector_store import get_collection_count, get_all_metadatas
from rag.bm25_search import is_index_ready
from evaluation.llm_judge import judge_response
from utils.guardrails import validate_query, sanitize_query
from utils.logger import get_logger

logger = get_logger("main")

app = FastAPI(
    title="Telecom Fault Intelligence Assistant API",
    description="AI-powered telecom network fault analysis using RAG + multi-agent intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    total = get_collection_count()
    return HealthResponse(
        status="healthy" if total > 0 else "degraded",
        vector_store_ready=total > 0,
        bm25_index_ready=is_index_ready(),
        model=settings.MODEL_NAME,
        embedding_model=settings.EMBEDDING_MODEL,
        total_indexed_incidents=total,
    )


@app.post("/api/query", response_model=FaultQueryResponse, tags=["Analysis"])
async def fault_query(request: FaultQueryRequest):
    """Main endpoint: natural language fault query → multi-agent analysis."""
    is_valid, error_msg = validate_query(request.query)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)

    clean_query = sanitize_query(request.query)
    logger.info(f"New fault query: '{clean_query[:80]}'")

    result = run_pipeline(
        query=clean_query,
        network_region=request.network_region,
        technology_type=request.technology_type,
        severity=request.severity,
        device_vendor=request.device_vendor,
        top_k=request.top_k,
    )

    retrieval = result["alarm_retrieval"]
    rca = result["root_cause_analysis"]
    impact = result["service_impact"]
    resolution = result["resolution_recommendations"]
    ts = datetime.utcnow().isoformat() + "Z"

    incidents = [
        IncidentRecord(**{k: v for k, v in inc.items() if k in IncidentRecord.model_fields})
        for inc in retrieval.get("retrieved_incidents", [])
    ]

    return FaultQueryResponse(
        query_id=result["query_id"],
        original_query=result["original_query"],
        timestamp=ts,
        agent_statuses=[AgentStatus(**s) for s in result["agent_statuses"]],
        alarm_retrieval=AlarmRetrievalResult(
            retrieved_incidents=incidents,
            alarm_patterns=retrieval.get("alarm_patterns", []),
            dominant_alarm_type=retrieval.get("dominant_alarm_type", "Unknown"),
            search_metadata=retrieval.get("search_metadata", {}),
        ),
        root_cause_analysis=RootCauseResult(
            probable_causes=rca.get("probable_causes", []),
            root_cause_chain=rca.get("root_cause_chain", ""),
            correlated_alarms=rca.get("correlated_alarms", []),
            confidence_score=float(rca.get("confidence_score", 0.0)),
            technical_explanation=rca.get("technical_explanation", ""),
        ),
        service_impact=ServiceImpactResult(
            affected_subscribers=int(impact.get("affected_subscribers", 0)),
            sla_breach_risk=impact.get("sla_breach_risk", "UNKNOWN"),
            impacted_services=impact.get("impacted_services", []),
            business_impact_score=float(impact.get("business_impact_score", 0.0)),
            revenue_impact_estimate=impact.get("revenue_impact_estimate", "Unknown"),
            affected_regions=impact.get("affected_regions", []),
        ),
        resolution_recommendations=ResolutionResult(
            immediate_steps=resolution.get("immediate_steps", []),
            escalation_path=resolution.get("escalation_path", ""),
            prevention_measures=resolution.get("prevention_measures", []),
            estimated_resolution_time=resolution.get("estimated_resolution_time", ""),
            vendor_specific_commands=resolution.get("vendor_specific_commands", []),
        ),
        processing_time_ms=result["processing_time_ms"],
    )


@app.get("/api/incidents", tags=["Data"])
async def list_incidents(
    network_region: str = Query(None),
    technology_type: str = Query(None),
    severity: str = Query(None),
    device_vendor: str = Query(None),
    alarm_type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Browse incidents with filters and pagination."""
    metadatas = get_all_metadatas(limit=500)

    if network_region:
        metadatas = [m for m in metadatas if m.get("network_region") == network_region]
    if technology_type:
        metadatas = [m for m in metadatas if m.get("technology_type") == technology_type]
    if severity:
        metadatas = [m for m in metadatas if m.get("severity") == severity]
    if device_vendor:
        metadatas = [m for m in metadatas if m.get("device_vendor") == device_vendor]
    if alarm_type:
        metadatas = [m for m in metadatas if m.get("alarm_type") == alarm_type]

    total = len(metadatas)
    start = (page - 1) * page_size
    page_data = metadatas[start: start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "incidents": page_data,
    }


@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics():
    """Dashboard analytics: distributions, trends, and KPIs."""
    metadatas = get_all_metadatas(limit=500)

    if not metadatas:
        return AnalyticsResponse(
            total_incidents=0, severity_distribution={}, technology_distribution={},
            region_distribution={}, vendor_distribution={}, alarm_type_distribution={},
            avg_outage_duration=0.0, avg_affected_subscribers=0.0,
            monthly_trends=[], top_recurring_issues=[],
        )

    severity_dist = dict(Counter(m.get("severity", "Unknown") for m in metadatas))
    tech_dist = dict(Counter(m.get("technology_type", "Unknown") for m in metadatas))
    region_dist = dict(Counter(m.get("network_region", "Unknown") for m in metadatas))
    vendor_dist = dict(Counter(m.get("device_vendor", "Unknown") for m in metadatas))
    alarm_dist = dict(Counter(m.get("alarm_type", "Unknown") for m in metadatas))

    durations = [m.get("outage_duration", 0) for m in metadatas if m.get("outage_duration")]
    subscribers = [m.get("affected_subscribers", 0) for m in metadatas if m.get("affected_subscribers")]

    avg_duration = sum(durations) / len(durations) if durations else 0.0
    avg_subs = sum(subscribers) / len(subscribers) if subscribers else 0.0

    monthly: dict[str, dict] = {}
    for m in metadatas:
        ts = m.get("timestamp", "")
        if ts and len(ts) >= 7:
            month_key = ts[:7]
            if month_key not in monthly:
                monthly[month_key] = {"month": month_key, "incidents": 0, "avg_duration": 0, "total_duration": 0}
            monthly[month_key]["incidents"] += 1
            monthly[month_key]["total_duration"] += m.get("outage_duration", 0)

    monthly_trends = []
    for mk, mv in sorted(monthly.items())[-12:]:
        mv["avg_duration"] = round(mv["total_duration"] / max(mv["incidents"], 1), 1)
        del mv["total_duration"]
        monthly_trends.append(mv)

    alarm_severity_pairs = Counter(
        (m.get("alarm_type", "Unknown"), m.get("severity", "Unknown"))
        for m in metadatas
    )
    top_recurring = [
        {"alarm_type": k[0], "severity": k[1], "count": v}
        for k, v in alarm_severity_pairs.most_common(10)
    ]

    return AnalyticsResponse(
        total_incidents=len(metadatas),
        severity_distribution=severity_dist,
        technology_distribution=tech_dist,
        region_distribution=region_dist,
        vendor_distribution=vendor_dist,
        alarm_type_distribution=alarm_dist,
        avg_outage_duration=round(avg_duration, 2),
        avg_affected_subscribers=round(avg_subs, 0),
        monthly_trends=monthly_trends,
        top_recurring_issues=top_recurring,
    )


@app.post("/api/evaluate", response_model=EvaluationResult, tags=["Evaluation"])
async def evaluate_response(request: EvaluationRequest):
    """Run DeepEval + LLM-as-judge evaluation on a query-response pair."""
    is_valid, err = validate_query(request.query)
    if not is_valid:
        raise HTTPException(status_code=422, detail=err)

    result = judge_response(
        query=request.query,
        response_text=request.response,
        context_docs=request.retrieved_contexts,
    )

    return EvaluationResult(**result)


@app.post("/api/ingest", tags=["Admin"])
async def trigger_ingestion(request: IngestRequest):
    """Trigger data ingestion pipeline (admin endpoint)."""
    from data.ingestion import run_ingestion
    try:
        count = run_ingestion(csv_path=request.csv_path, force_reingest=request.force_reingest)
        return {"status": "success", "records_ingested": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Telecom Fault Intelligence Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
