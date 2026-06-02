"""
Agent Orchestrator: Coordinates 4-agent pipeline with A2A message passing.
Query → Alarm Retrieval → Root Cause → Service Impact → Resolution → Final Response
"""
import sys
import os
import time
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import alarm_retrieval_agent, root_cause_agent, service_impact_agent, resolution_agent
from utils.logger import get_logger

logger = get_logger("Orchestrator")


def run_pipeline(
    query: str,
    network_region: str = None,
    technology_type: str = None,
    severity: str = None,
    device_vendor: str = None,
    top_k: int = 5,
) -> dict:
    pipeline_start = time.time()
    query_id = str(uuid.uuid4())[:8]
    agent_statuses = []

    logger.info(f"[{query_id}] Starting 4-agent pipeline for: '{query[:80]}'")

    # Agent 1: Alarm Retrieval
    t0 = time.time()
    try:
        retrieval_result = alarm_retrieval_agent.run(
            query=query,
            network_region=network_region,
            technology_type=technology_type,
            severity=severity,
            device_vendor=device_vendor,
            top_k=top_k,
        )
        agent_statuses.append({
            "name": "Alarm Retrieval Agent",
            "status": "completed",
            "duration_ms": int((time.time() - t0) * 1000),
        })
        logger.info(f"[{query_id}] Agent 1 complete: {len(retrieval_result['retrieved_incidents'])} incidents retrieved")
    except Exception as e:
        logger.error(f"[{query_id}] Agent 1 failed: {e}")
        agent_statuses.append({"name": "Alarm Retrieval Agent", "status": "failed", "duration_ms": int((time.time() - t0) * 1000)})
        retrieval_result = {"retrieved_incidents": [], "alarm_patterns": [], "dominant_alarm_type": "Unknown", "search_metadata": {}}

    # Agent 2: Root Cause Analysis (receives retrieval context)
    t0 = time.time()
    try:
        rca_result = root_cause_agent.run(query=query, retrieval_result=retrieval_result)
        agent_statuses.append({
            "name": "Root Cause Analysis Agent",
            "status": "completed",
            "duration_ms": int((time.time() - t0) * 1000),
        })
        logger.info(f"[{query_id}] Agent 2 complete: confidence={rca_result.get('confidence_score', 0):.0%}")
    except Exception as e:
        logger.error(f"[{query_id}] Agent 2 failed: {e}")
        agent_statuses.append({"name": "Root Cause Analysis Agent", "status": "failed", "duration_ms": int((time.time() - t0) * 1000)})
        rca_result = {"probable_causes": [], "root_cause_chain": "Analysis failed", "correlated_alarms": [], "confidence_score": 0.0, "technical_explanation": ""}

    # Agent 3: Service Impact (receives retrieval + RCA context)
    t0 = time.time()
    try:
        impact_result = service_impact_agent.run(query=query, retrieval_result=retrieval_result, rca_result=rca_result)
        agent_statuses.append({
            "name": "Service Impact Agent",
            "status": "completed",
            "duration_ms": int((time.time() - t0) * 1000),
        })
        logger.info(f"[{query_id}] Agent 3 complete: SLA risk={impact_result.get('sla_breach_risk','?')}")
    except Exception as e:
        logger.error(f"[{query_id}] Agent 3 failed: {e}")
        agent_statuses.append({"name": "Service Impact Agent", "status": "failed", "duration_ms": int((time.time() - t0) * 1000)})
        impact_result = {"affected_subscribers": 0, "sla_breach_risk": "UNKNOWN", "impacted_services": [], "business_impact_score": 0.0, "revenue_impact_estimate": "Unknown", "affected_regions": []}

    # Agent 4: Resolution (receives all prior context)
    t0 = time.time()
    try:
        resolution_result = resolution_agent.run(
            query=query,
            retrieval_result=retrieval_result,
            rca_result=rca_result,
            impact_result=impact_result,
        )
        agent_statuses.append({
            "name": "Resolution Recommendation Agent",
            "status": "completed",
            "duration_ms": int((time.time() - t0) * 1000),
        })
        logger.info(f"[{query_id}] Agent 4 complete: {len(resolution_result.get('immediate_steps', []))} steps generated")
    except Exception as e:
        logger.error(f"[{query_id}] Agent 4 failed: {e}")
        agent_statuses.append({"name": "Resolution Recommendation Agent", "status": "failed", "duration_ms": int((time.time() - t0) * 1000)})
        resolution_result = {"immediate_steps": [], "escalation_path": "", "prevention_measures": [], "estimated_resolution_time": "Unknown", "vendor_specific_commands": []}

    total_ms = int((time.time() - pipeline_start) * 1000)
    logger.info(f"[{query_id}] Pipeline complete in {total_ms}ms")

    return {
        "query_id": query_id,
        "original_query": query,
        "agent_statuses": agent_statuses,
        "alarm_retrieval": retrieval_result,
        "root_cause_analysis": rca_result,
        "service_impact": impact_result,
        "resolution_recommendations": resolution_result,
        "processing_time_ms": total_ms,
    }
