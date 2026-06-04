from pydantic import BaseModel, Field
from typing import Optional


class FaultQueryRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500, description="Natural language fault description")
    network_region: Optional[str] = Field(None, description="Filter by region: North, South, East, West, Central")
    technology_type: Optional[str] = Field(None, description="Filter by technology: 5G-NR, 4G-LTE, 3G-UMTS, Fiber, MPLS, SD-WAN")
    severity: Optional[str] = Field(None, description="Filter by severity: P1-Critical, P2-High, P3-Medium, P4-Low")
    device_vendor: Optional[str] = Field(None, description="Filter by vendor: Ericsson, Nokia, Huawei, Cisco, Juniper")
    top_k: int = Field(default=5, ge=1, le=20)


class EvaluationRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    response: str = Field(..., min_length=10)
    retrieved_contexts: list[str] = Field(..., min_length=1)


class IngestRequest(BaseModel):
    csv_path: Optional[str] = None
    force_reingest: bool = False


class FeedbackRequest(BaseModel):
    query_id: str = Field(..., description="ID from a prior /api/query response")
    query: str = Field(..., min_length=3, max_length=500)
    rating: int = Field(..., ge=1, le=5, description="1-5 star rating")
    helpful: bool = Field(..., description="Thumbs up / down")
    comment: Optional[str] = Field(default="", max_length=1000)


class SummarizeRequest(BaseModel):
    alarm_ids: list[str] = Field(..., min_length=1, description="List of alarm IDs to summarize")
    context: Optional[str] = Field(default="", max_length=500, description="Additional context for summarization")


class FollowupRequest(BaseModel):
    followup_query: str = Field(..., min_length=3, max_length=500, description="Follow-up question in context of prior result")
    prior_alarm_type: str = Field(default="", description="Dominant alarm type from prior result")
    prior_region: str = Field(default="", description="Region from prior result")
    prior_technology: str = Field(default="", description="Technology from prior result")
    prior_root_cause: str = Field(default="", description="Root cause chain from prior result")
    prior_query: str = Field(default="", description="Original query from prior result")


class ServiceNowTicketRequest(BaseModel):
    query_id: str = Field(..., description="Query ID from /api/query response")
    query: str = Field(..., min_length=5, max_length=500)
    alarm_type: str
    region: str
    technology: str
    severity: str
    root_cause_chain: str
    technical_explanation: str
    resolution_steps: list[str] = Field(default=[])
    affected_subscribers: int = Field(default=0)
    sla_breach_risk: str = Field(default="UNKNOWN")
    # Enrichment fields
    confidence_score: float = Field(default=0.0)
    probable_causes: list[dict] = Field(default=[])
    revenue_impact: str = Field(default="Unknown")
    business_impact_score: float = Field(default=0.0)
    impacted_services: list[str] = Field(default=[])
    escalation_path: str = Field(default="")
    estimated_resolution_time: str = Field(default="")
    vendor_commands: list[dict] = Field(default=[])
    prevention_measures: list[str] = Field(default=[])
