from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IncidentRecord(BaseModel):
    alarm_id: str
    incident_description: str
    network_region: str
    technology_type: str
    severity: str
    outage_duration: int
    device_vendor: str
    resolution_notes: str
    timestamp: str
    service_impact: str
    alarm_type: str
    affected_subscribers: int
    similarity_score: float = 0.0


class AlarmRetrievalResult(BaseModel):
    retrieved_incidents: list[IncidentRecord]
    alarm_patterns: list[str]
    dominant_alarm_type: str
    search_metadata: dict


class RootCauseResult(BaseModel):
    probable_causes: list[dict]
    root_cause_chain: str
    correlated_alarms: list[str]
    confidence_score: float
    technical_explanation: str


class ServiceImpactResult(BaseModel):
    affected_subscribers: int
    sla_breach_risk: str
    impacted_services: list[str]
    business_impact_score: float
    revenue_impact_estimate: str
    affected_regions: list[str]


class ResolutionResult(BaseModel):
    immediate_steps: list[dict]
    escalation_path: str
    prevention_measures: list[str]
    estimated_resolution_time: str
    vendor_specific_commands: list[dict]


class AgentStatus(BaseModel):
    name: str
    status: str
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None


class FaultQueryResponse(BaseModel):
    query_id: str
    original_query: str
    timestamp: str
    agent_statuses: list[AgentStatus]
    alarm_retrieval: AlarmRetrievalResult
    root_cause_analysis: RootCauseResult
    service_impact: ServiceImpactResult
    resolution_recommendations: ResolutionResult
    processing_time_ms: int


class EvaluationResult(BaseModel):
    faithfulness_score: float
    answer_relevancy_score: float
    contextual_precision_score: float
    contextual_recall_score: float
    llm_judge_scores: dict
    overall_quality_score: float
    evaluation_summary: str


class AnalyticsResponse(BaseModel):
    total_incidents: int
    severity_distribution: dict
    technology_distribution: dict
    region_distribution: dict
    vendor_distribution: dict
    alarm_type_distribution: dict
    avg_outage_duration: float
    avg_affected_subscribers: float
    monthly_trends: list[dict]
    top_recurring_issues: list[dict]


class HealthResponse(BaseModel):
    status: str
    vector_store_ready: bool
    bm25_index_ready: bool
    model: str
    embedding_model: str
    total_indexed_incidents: int
