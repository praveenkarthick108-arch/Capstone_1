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
