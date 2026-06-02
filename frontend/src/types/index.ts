export interface IncidentRecord {
  alarm_id: string;
  incident_description: string;
  network_region: string;
  technology_type: string;
  severity: string;
  outage_duration: number;
  device_vendor: string;
  resolution_notes: string;
  timestamp: string;
  service_impact: string;
  alarm_type: string;
  affected_subscribers: number;
  similarity_score: number;
}

export interface AgentStatus {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration_ms?: number;
  tokens_used?: number;
}

export interface ProbableCause {
  cause: string;
  confidence: number;
  evidence: string;
  category: string;
}

export interface ResolutionStep {
  step: number;
  action: string;
  command?: string;
  expected_outcome: string;
  priority: string;
}

export interface VendorCommand {
  vendor: string;
  command: string;
  purpose: string;
}

export interface FaultQueryResponse {
  query_id: string;
  original_query: string;
  timestamp: string;
  agent_statuses: AgentStatus[];
  alarm_retrieval: {
    retrieved_incidents: IncidentRecord[];
    alarm_patterns: string[];
    dominant_alarm_type: string;
    search_metadata: Record<string, any>;
  };
  root_cause_analysis: {
    probable_causes: ProbableCause[];
    root_cause_chain: string;
    correlated_alarms: string[];
    confidence_score: number;
    technical_explanation: string;
  };
  service_impact: {
    affected_subscribers: number;
    sla_breach_risk: string;
    impacted_services: string[];
    business_impact_score: number;
    revenue_impact_estimate: string;
    affected_regions: string[];
  };
  resolution_recommendations: {
    immediate_steps: ResolutionStep[];
    escalation_path: string;
    prevention_measures: string[];
    estimated_resolution_time: string;
    vendor_specific_commands: VendorCommand[];
  };
  processing_time_ms: number;
}

export interface AnalyticsResponse {
  total_incidents: number;
  severity_distribution: Record<string, number>;
  technology_distribution: Record<string, number>;
  region_distribution: Record<string, number>;
  vendor_distribution: Record<string, number>;
  alarm_type_distribution: Record<string, number>;
  avg_outage_duration: number;
  avg_affected_subscribers: number;
  monthly_trends: Array<{ month: string; incidents: number; avg_duration: number }>;
  top_recurring_issues: Array<{ alarm_type: string; severity: string; count: number }>;
}

export interface HealthResponse {
  status: string;
  vector_store_ready: boolean;
  bm25_index_ready: boolean;
  model: string;
  embedding_model: string;
  total_indexed_incidents: number;
}

export interface QueryFilters {
  network_region?: string;
  technology_type?: string;
  severity?: string;
  device_vendor?: string;
}
