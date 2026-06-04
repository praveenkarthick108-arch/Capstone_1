"""
AI-Powered Telecom Network Fault Intelligence Assistant
FastAPI Backend — main entry point
"""
import sys
import os
import json
import asyncio
import httpx
from datetime import datetime
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import OpenAI

from config import settings
from models.request_models import (
    FaultQueryRequest, EvaluationRequest, IngestRequest,
    FeedbackRequest, SummarizeRequest, ServiceNowTicketRequest, FollowupRequest,
)
from models.response_models import (
    FaultQueryResponse, EvaluationResult, AnalyticsResponse,
    HealthResponse, IncidentRecord, AlarmRetrievalResult,
    RootCauseResult, ServiceImpactResult, ResolutionResult, AgentStatus,
    PredictionResponse, SummaryResponse, FeedbackResponse, QueryEnhancement,
)
from agents.orchestrator import run_pipeline, run_pipeline_stream
from rag.vector_store import get_collection_count, get_all_metadatas, get_collection
from rag.bm25_search import is_index_ready
from evaluation.llm_judge import judge_response
from utils.guardrails import validate_query, sanitize_query
from utils.query_enhancer import enhance_query
from utils.anomaly_detector import detect_anomaly
from utils.query_cache import query_cache, compute_token_efficiency
from utils.logger import get_logger
from data.feedback_store import save_feedback, get_feedback_stats, get_all_feedback
from integrations.servicenow import create_incident, get_incident, list_recent_incidents
from prediction.outage_predictor import (
    predict_by_region, predict_by_technology,
    predict_hotspots, get_sla_analysis, get_cross_region_correlation,
    get_alarm_frequency_trend,
)

logger = get_logger("main")

app = FastAPI(
    title="Telecom Fault Intelligence Assistant API",
    description="AI-powered telecom network fault analysis using RAG + multi-agent intelligence",
    version="2.0.0",
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


def _get_llm_client() -> OpenAI:
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        http_client=httpx.Client(verify=False),
    )


# ─────────────────────────── SYSTEM ───────────────────────────

@app.get("/api/cache/stats", tags=["System"])
async def cache_stats():
    """Return semantic query cache statistics."""
    return query_cache.stats()

@app.delete("/api/cache", tags=["System"])
async def cache_clear():
    """Clear the semantic query cache."""
    query_cache.clear()
    return {"message": "Cache cleared"}

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


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Telecom Fault Intelligence Assistant API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": [
            "/api/query", "/api/incidents", "/api/analytics",
            "/api/predict", "/api/summarize", "/api/feedback",
            "/api/evaluate", "/api/ingest",
        ],
    }


# ─────────────────────────── ANALYSIS ───────────────────────────

@app.post("/api/query", response_model=FaultQueryResponse, tags=["Analysis"])
async def fault_query(request: FaultQueryRequest):
    """Main endpoint: natural language fault query → query enhancement → multi-agent analysis."""
    is_valid, error_msg = validate_query(request.query)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)

    clean_query = sanitize_query(request.query)
    logger.info(f"New fault query: '{clean_query[:80]}'")

    # Enhance query: rewrite to technical language and auto-extract filters
    enhancement = enhance_query(clean_query)
    technical_query = enhancement["technical_query"]

    # Auto-extracted filters — only apply REGION from enhancer.
    # Technology (only 2 5G-NR incidents in 7,381) and severity are NOT used as ChromaDB filters
    # because auto-extracted values over-restrict results to zero.
    # Both are surfaced in the enhancement banner and used in the rewritten query text.
    effective_region = request.network_region or enhancement.get("network_region")
    effective_tech = request.technology_type  # only if user explicitly set it in the request
    effective_severity = request.severity  # only if user explicitly set it in the request
    # Keep extracted tech for post-processing fallback display (not used as a DB filter)
    _extracted_tech = enhancement.get("technology_type")

    logger.info(
        f"Enhanced: '{technical_query[:80]}' "
        f"[region={effective_region}, tech={effective_tech}, sev={effective_severity}]"
    )

    result = run_pipeline(
        query=technical_query,
        network_region=effective_region,
        technology_type=effective_tech,
        severity=effective_severity,
        device_vendor=request.device_vendor,
        top_k=request.top_k,
    )

    retrieval = result["alarm_retrieval"]
    rca = result["root_cause_analysis"]
    impact = result["service_impact"]
    resolution = result["resolution_recommendations"]

    # ── Post-process: fill "Unknown" fallback values using enhancement signals ──
    # Derive dominant_alarm_type from retrieved incident metadata or technology keyword
    if not retrieval.get("dominant_alarm_type") or retrieval["dominant_alarm_type"] == "Unknown":
        inc_types = [i.get("alarm_type", "") for i in retrieval.get("retrieved_incidents", []) if i.get("alarm_type")]
        if inc_types:
            retrieval["dominant_alarm_type"] = Counter(inc_types).most_common(1)[0][0]
        elif effective_tech or _extracted_tech:
            _TECH_ALARM = {
                "5G-NR": "5G Radio Access Failure",
                "4G-LTE": "LTE eNodeB Connectivity Failure",
                "Fiber": "Optical Fiber Link Break",
                "MPLS": "MPLS Label Path Disruption",
                "SD-WAN": "SD-WAN Tunnel Down",
                "3G-UMTS": "UMTS RNC Node Failure",
            }
            retrieval["dominant_alarm_type"] = _TECH_ALARM.get(
                effective_tech or _extracted_tech, "Network Element Failure"
            )

    # Fill affected_regions from enhancement when agent returned empty list
    if not impact.get("affected_regions") and effective_region:
        impact["affected_regions"] = [effective_region]

    # Escalate SLA risk when enhancement signals critical severity but LLM fell back
    if impact.get("sla_breach_risk") == "LOW" and enhancement.get("severity") == "P1-Critical":
        impact["sla_breach_risk"] = "HIGH"
        if impact.get("affected_subscribers", 0) == 0:
            impact["affected_subscribers"] = 15000  # conservative estimate for critical incident

    # Fix root_cause_chain: override when "Unknown" OR when LLM fell back (confidence<=0.65)
    _tech_hint = effective_tech or _extracted_tech
    _chain_needs_fix = (
        not rca.get("root_cause_chain")
        or rca["root_cause_chain"].startswith("Unknown")
        or float(rca.get("confidence_score", 1.0)) <= 0.65
    )
    if _chain_needs_fix:
        _alarm = retrieval.get("dominant_alarm_type", "Equipment Failure")
        _tech = _tech_hint or "Network"
        _region = effective_region or "Multi-Region"
        rca["root_cause_chain"] = f"{_alarm} -> {_tech} Service Degradation -> {_region} Customer Impact"
    else:
        # Strip any Unicode arrows (→) from LLM output to avoid encoding issues
        rca["root_cause_chain"] = rca["root_cause_chain"].replace("→", "->").replace("→", "->")

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
        query_enhancement=QueryEnhancement(
            original_query=clean_query,
            technical_query=technical_query,
            was_enhanced=enhancement.get("was_enhanced", False),
            enhancement_notes=enhancement.get("enhancement_notes", ""),
            extracted_region=enhancement.get("network_region"),
            extracted_technology=enhancement.get("technology_type"),
            extracted_severity=enhancement.get("severity"),
        ),
    )


def _postprocess(result: dict, clean_query: str, technical_query: str, enhancement: dict,
                 effective_region, effective_tech, _extracted_tech) -> FaultQueryResponse:
    """Shared post-processing for both /api/query and /api/stream."""
    retrieval = result["alarm_retrieval"]
    rca = result["root_cause_analysis"]
    impact = result["service_impact"]
    resolution = result["resolution_recommendations"]

    if not retrieval.get("dominant_alarm_type") or retrieval["dominant_alarm_type"] == "Unknown":
        inc_types = [i.get("alarm_type", "") for i in retrieval.get("retrieved_incidents", []) if i.get("alarm_type")]
        if inc_types:
            retrieval["dominant_alarm_type"] = Counter(inc_types).most_common(1)[0][0]
        elif effective_tech or _extracted_tech:
            _TECH_ALARM = {"5G-NR": "5G Radio Access Failure", "4G-LTE": "LTE eNodeB Connectivity Failure",
                           "Fiber": "Optical Fiber Link Break", "MPLS": "MPLS Label Path Disruption",
                           "SD-WAN": "SD-WAN Tunnel Down", "3G-UMTS": "UMTS RNC Node Failure"}
            retrieval["dominant_alarm_type"] = _TECH_ALARM.get(effective_tech or _extracted_tech, "Network Element Failure")

    if not impact.get("affected_regions") and effective_region:
        impact["affected_regions"] = [effective_region]
    if impact.get("sla_breach_risk") == "LOW" and enhancement.get("severity") == "P1-Critical":
        impact["sla_breach_risk"] = "HIGH"
        if impact.get("affected_subscribers", 0) == 0:
            impact["affected_subscribers"] = 15000

    _tech_hint = effective_tech or _extracted_tech
    _chain_needs_fix = (not rca.get("root_cause_chain") or rca["root_cause_chain"].startswith("Unknown")
                        or float(rca.get("confidence_score", 1.0)) <= 0.65)
    if _chain_needs_fix:
        _alarm = retrieval.get("dominant_alarm_type", "Equipment Failure")
        rca["root_cause_chain"] = f"{_alarm} -> {_tech_hint or 'Network'} Service Degradation -> {effective_region or 'Multi-Region'} Customer Impact"
    else:
        rca["root_cause_chain"] = rca["root_cause_chain"].replace("→", "->")

    ts = datetime.utcnow().isoformat() + "Z"
    incidents = [
        IncidentRecord(**{k: v for k, v in inc.items() if k in IncidentRecord.model_fields})
        for inc in retrieval.get("retrieved_incidents", [])
    ]
    return FaultQueryResponse(
        query_id=result["query_id"],
        original_query=result.get("original_query", clean_query),
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
        query_enhancement=QueryEnhancement(
            original_query=clean_query,
            technical_query=technical_query,
            was_enhanced=enhancement.get("was_enhanced", False),
            enhancement_notes=enhancement.get("enhancement_notes", ""),
            extracted_region=enhancement.get("network_region"),
            extracted_technology=enhancement.get("technology_type"),
            extracted_severity=enhancement.get("severity"),
        ),
        anomaly_alert=detect_anomaly(
            region=effective_region,
            technology=_extracted_tech or effective_tech,
        ) or None,
        token_efficiency=compute_token_efficiency(
            original_query=clean_query,
            retrieved_incidents=retrieval.get("retrieved_incidents", []),
            rca_explanation=rca.get("technical_explanation", ""),
            resolution_steps=[s.get("action", "") for s in resolution.get("immediate_steps", [])],
        ),
    )


@app.post("/api/stream", tags=["Analysis"])
async def fault_query_stream(request: FaultQueryRequest):
    """Streaming SSE endpoint — yields one event per agent as it completes."""
    is_valid, error_msg = validate_query(request.query)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_msg)

    clean_query = sanitize_query(request.query)
    enhancement = enhance_query(clean_query)
    technical_query = enhancement["technical_query"]
    effective_region = request.network_region or enhancement.get("network_region")
    effective_tech = request.technology_type
    effective_severity = request.severity
    _extracted_tech = enhancement.get("technology_type")

    # ── Semantic cache check ────────────────────────────────────────────────
    query_embedding = None
    try:
        from rag.embeddings import embed_query as _embed
        query_embedding = await asyncio.to_thread(_embed, clean_query)
    except Exception:
        pass  # cache will fall back to text similarity

    cache_hit = query_cache.lookup(clean_query, query_embedding)

    async def event_gen():
        # Event 0: enhancement (fast — no LLM, shows immediately)
        enh_payload = {
            "type": "enhanced",
            "enhancement": {
                "original_query": clean_query, "technical_query": technical_query,
                "was_enhanced": enhancement.get("was_enhanced", False),
                "enhancement_notes": enhancement.get("enhancement_notes", ""),
                "extracted_region": enhancement.get("network_region"),
                "extracted_technology": enhancement.get("technology_type"),
                "extracted_severity": enhancement.get("severity"),
            }
        }
        yield f"data: {json.dumps(enh_payload)}\n\n"

        # ── Cache hit: replay agent statuses instantly, return cached result ──
        if cache_hit:
            cached = cache_hit["result"]
            for status in cached.get("agent_statuses", []):
                await asyncio.sleep(0.12)  # brief delay for visual effect
                yield f"data: {json.dumps({'type': 'agent_done', 'agent_name': status['name'], 'status': 'completed', 'duration_ms': status.get('duration_ms', 0)})}\n\n"
            cached["cache_info"] = {
                "is_cache_hit": True,
                "similarity": cache_hit["similarity"],
                "cached_query": cache_hit["cached_query"],
                "hit_number": cache_hit["hit_number"],
            }
            yield f"data: {json.dumps({'type': 'complete', 'result': cached, 'cache_hit': True, 'similarity': cache_hit['similarity']})}\n\n"
            return

        # ── Cache miss: run full pipeline ──
        pipeline_result = None
        async for event in run_pipeline_stream(
            query=technical_query, network_region=effective_region,
            technology_type=effective_tech, severity=effective_severity,
            device_vendor=request.device_vendor, top_k=request.top_k,
        ):
            if event["type"] == "agent_done":
                yield f"data: {json.dumps({'type': 'agent_done', 'agent_name': event['agent_name'], 'status': event['status'], 'duration_ms': event['duration_ms']})}\n\n"
            elif event["type"] == "pipeline_complete":
                pipeline_result = event

        if pipeline_result:
            full = _postprocess(pipeline_result, clean_query, technical_query, enhancement,
                                effective_region, effective_tech, _extracted_tech)
            full_dict = full.model_dump()
            # Store in cache for future similar queries
            query_cache.store(clean_query, full_dict, query_embedding)
            yield f"data: {json.dumps({'type': 'complete', 'result': full_dict})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/followup", tags=["Analysis"])
async def followup_query(request: FollowupRequest):
    """Conversational Q&A follow-up — single LLM call using prior analysis as context."""
    system_prompt = (
        "You are a telecom network fault intelligence assistant. "
        "Answer the engineer's follow-up question concisely and specifically, "
        "referencing the prior fault analysis context. "
        "Keep answers to 2–5 sentences. Use plain text — no markdown headers or bullet lists."
    )
    context_lines = []
    if request.prior_query:
        context_lines.append(f"Original fault: {request.prior_query}")
    if request.prior_alarm_type:
        context_lines.append(f"Alarm type: {request.prior_alarm_type}")
    if request.prior_technology:
        context_lines.append(f"Technology: {request.prior_technology}")
    if request.prior_region:
        context_lines.append(f"Region: {request.prior_region}")
    if request.prior_root_cause:
        context_lines.append(f"Root cause chain: {request.prior_root_cause}")

    user_message = (
        "Prior analysis context:\n" + "\n".join(context_lines) +
        f"\n\nFollow-up question: {request.followup_query}"
    )

    try:
        client = _get_llm_client()
        resp = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=300,
                temperature=0.4,
            )
        )
        answer = resp.choices[0].message.content.strip()
    except Exception:
        # Fallback when LLM is unavailable
        answer = (
            f"Based on the prior analysis (root cause: {request.prior_root_cause or 'unknown'}), "
            f"your question about '{request.followup_query}' relates to the "
            f"{request.prior_technology or 'network'} fault in the {request.prior_region or 'affected'} region. "
            "Please refer to the resolution steps above for specific actions."
        )

    return {"answer": answer, "question": request.followup_query}


# ─────────────────────────── PREDICTION ───────────────────────────

@app.get("/api/predict", response_model=PredictionResponse, tags=["Prediction"])
async def get_predictions(
    region: str = Query(None, description="Filter by network region"),
    technology: str = Query(None, description="Filter by technology type"),
):
    """
    Predictive outage intelligence: statistical risk scoring across regions,
    technologies, and hotspot combinations based on 7,381 historical incidents.
    """
    try:
        regions = predict_by_region()
        techs = predict_by_technology()
        hotspots = predict_hotspots(top_n=10)
        sla = get_sla_analysis()

        if region:
            regions = [r for r in regions if r["region"].lower() == region.lower()]
        if technology:
            techs = [t for t in techs if t["technology"].lower() == technology.lower()]

        return PredictionResponse(
            by_region=regions,
            by_technology=techs,
            hotspots=hotspots,
            sla_analysis=sla,
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── SUMMARIZE ───────────────────────────

@app.post("/api/summarize", response_model=SummaryResponse, tags=["Analysis"])
async def summarize_outage(request: SummarizeRequest):
    """
    Automated outage summarization: given a list of alarm IDs, generates an
    executive summary of the incident cluster with key findings and priority.
    """
    try:
        collection = get_collection()
        fetch = collection.get(
            ids=request.alarm_ids[:20],
            include=["documents", "metadatas"],
        )
        if not fetch["ids"]:
            raise HTTPException(status_code=404, detail="No matching alarm IDs found")

        metadatas = fetch["metadatas"]
        documents = fetch["documents"]
        sev_dist = dict(Counter(m.get("severity", "Unknown") for m in metadatas))
        regions = list({m.get("network_region", "") for m in metadatas if m.get("network_region")})
        alarm_types = list({m.get("alarm_type", "") for m in metadatas if m.get("alarm_type")})
        avg_dur = sum(m.get("outage_duration", 0) for m in metadatas) / len(metadatas)
        total_subs = sum(m.get("affected_subscribers", 0) for m in metadatas)

        incident_lines = "\n".join([
            f"- {m.get('alarm_id','?')} | {m.get('alarm_type','?')} | {m.get('severity','?')} | {m.get('network_region','?')} | {m.get('outage_duration',0)}min"
            for m in metadatas[:10]
        ])

        context_hint = f"\nAdditional context: {request.context}" if request.context else ""
        prompt = f"""You are a telecom NOC manager. Generate a concise executive summary for these {len(metadatas)} network incidents.{context_hint}

INCIDENTS:
{incident_lines}

AGGREGATE STATS:
- Severity distribution: {json.dumps(sev_dist)}
- Affected regions: {', '.join(regions)}
- Alarm types: {', '.join(alarm_types[:5])}
- Avg outage duration: {avg_dur:.0f} minutes
- Total affected subscribers: {total_subs:,}

Return JSON:
{{"summary":"3-4 sentence exec summary","key_findings":["finding1","finding2","finding3"],"recommended_priority":"P1|P2|P3|P4","estimated_total_impact":"X customers, Y hours"}}
Return ONLY the JSON."""

        client = _get_llm_client()
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        content = response.choices[0].message.content.strip()
        try:
            parsed = json.loads(content)
        except Exception:
            import re
            m = re.search(r'\{.*\}', content, re.DOTALL)
            parsed = json.loads(m.group()) if m else {}

        return SummaryResponse(
            summary=parsed.get("summary", "Incident cluster analysis complete."),
            alarm_ids=request.alarm_ids,
            incident_count=len(metadatas),
            severity_summary=sev_dist,
            key_findings=parsed.get("key_findings", []),
            recommended_priority=parsed.get("recommended_priority", "P3"),
            generated_at=datetime.utcnow().isoformat() + "Z",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarize failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────── FEEDBACK ───────────────────────────

@app.post("/api/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(request: FeedbackRequest):
    """Feedback loop: submit a rating on a query response to improve retrieval quality."""
    try:
        entry = save_feedback(
            query_id=request.query_id,
            query=request.query,
            rating=request.rating,
            helpful=request.helpful,
            comment=request.comment or "",
        )
        return FeedbackResponse(
            id=entry["id"],
            query_id=entry["query_id"],
            rating=entry["rating"],
            helpful=entry["helpful"],
            message="Thank you for your feedback! It will be used to improve retrieval quality.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feedback/stats", tags=["Feedback"])
async def get_feedback_statistics():
    """Aggregated feedback statistics across all submitted ratings."""
    return get_feedback_stats()


@app.get("/api/feedback/all", tags=["Feedback"])
async def list_all_feedback():
    """All stored feedback entries."""
    return {"feedback": get_all_feedback()}


# ─────────────────────────── DATA ───────────────────────────

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
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "incidents": metadatas[start: start + page_size],
    }


# ─────────────────────────── ANALYTICS ───────────────────────────

@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics():
    """Dashboard analytics: distributions, trends, KPIs, SLA health, and cross-region correlation."""
    metadatas = get_all_metadatas(limit=500)

    if not metadatas:
        return AnalyticsResponse(
            total_incidents=0, severity_distribution={}, technology_distribution={},
            region_distribution={}, vendor_distribution={}, alarm_type_distribution={},
            avg_outage_duration=0.0, avg_affected_subscribers=0.0,
            monthly_trends=[], top_recurring_issues=[],
            sla_breach_rate_pct=0.0, cross_region_correlation={}, risk_by_region=[],
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

    # SLA breach rate (outages > 30min)
    breached = sum(1 for m in metadatas if m.get("outage_duration", 0) > 30)
    sla_breach_rate = round(breached / len(metadatas) * 100, 1) if metadatas else 0.0

    monthly: dict[str, dict] = {}
    for m in metadatas:
        ts = m.get("timestamp", "")
        if ts and len(ts) >= 7:
            mk = ts[:7]
            if mk not in monthly:
                monthly[mk] = {"month": mk, "incidents": 0, "avg_duration": 0, "total_duration": 0}
            monthly[mk]["incidents"] += 1
            monthly[mk]["total_duration"] += m.get("outage_duration", 0)

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

    # Cross-region correlation (from full dataset via predictor)
    try:
        cross_corr = get_cross_region_correlation()
    except Exception:
        cross_corr = {}

    # Risk by region (from predictor)
    try:
        risk_regions = predict_by_region()
    except Exception:
        risk_regions = []

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
        sla_breach_rate_pct=sla_breach_rate,
        cross_region_correlation=cross_corr,
        risk_by_region=risk_regions,
    )


# ─────────────────────────── EVALUATION ───────────────────────────

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


# ─────────────────────────── SERVICENOW ───────────────────────────

@app.post("/api/servicenow/create-ticket", tags=["ServiceNow"])
async def servicenow_create_ticket(request: ServiceNowTicketRequest):
    """
    OSS/BSS Integration: create a real ServiceNow incident from a fault analysis result.
    Returns the ticket number, sys_id, and a direct link to the ticket.
    """
    try:
        result = create_incident(
            query=request.query,
            alarm_type=request.alarm_type,
            region=request.region,
            technology=request.technology,
            severity=request.severity,
            root_cause_chain=request.root_cause_chain,
            technical_explanation=request.technical_explanation,
            resolution_steps=request.resolution_steps,
            affected_subscribers=request.affected_subscribers,
            sla_breach_risk=request.sla_breach_risk,
            query_id=request.query_id,
            confidence_score=request.confidence_score,
            probable_causes=request.probable_causes,
            revenue_impact=request.revenue_impact,
            business_impact_score=request.business_impact_score,
            impacted_services=request.impacted_services,
            escalation_path=request.escalation_path,
            estimated_resolution_time=request.estimated_resolution_time,
            vendor_commands=request.vendor_commands,
            prevention_measures=request.prevention_measures,
        )
        logger.info(f"ServiceNow ticket created: {result['ticket_number']}")
        return {"status": "created", **result}
    except Exception as e:
        logger.error(f"ServiceNow ticket creation failed: {e}")
        raise HTTPException(status_code=502, detail=f"ServiceNow error: {str(e)}")


@app.get("/api/servicenow/ticket/{sys_id}", tags=["ServiceNow"])
async def servicenow_get_ticket(sys_id: str):
    """Fetch a ServiceNow incident by sys_id."""
    try:
        result = get_incident(sys_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ServiceNow error: {str(e)}")


@app.get("/api/servicenow/tickets", tags=["ServiceNow"])
async def servicenow_list_tickets(limit: int = Query(10, ge=1, le=50)):
    """List recent AI-created ServiceNow incidents."""
    try:
        tickets = list_recent_incidents(limit=limit)
        return {"tickets": tickets, "count": len(tickets)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ServiceNow error: {str(e)}")


# ─────────────────────────── ADMIN ───────────────────────────

@app.post("/api/ingest", tags=["Admin"])
async def trigger_ingestion(request: IngestRequest):
    """Trigger data ingestion pipeline (admin endpoint)."""
    from data.ingestion import run_ingestion
    try:
        count = run_ingestion(csv_path=request.csv_path, force_reingest=request.force_reingest)
        return {"status": "success", "records_ingested": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
