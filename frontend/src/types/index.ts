export interface RetrievalExplanation {
  top_bm25_terms: string[];
  vector_similarity: number;
  retrieval_method: 'hybrid' | 'vector' | 'keyword';
}

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
  retrieval_explanation?: RetrievalExplanation;
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

export interface QueryEnhancement {
  original_query: string;
  technical_query: string;
  was_enhanced: boolean;
  enhancement_notes: string;
  extracted_region?: string | null;
  extracted_technology?: string | null;
  extracted_severity?: string | null;
}

export interface CacheInfo {
  is_cache_hit: boolean;
  similarity: number;
  cached_query: string;
  hit_number: number;
}

export interface TokenEfficiency {
  estimated_tokens_used: number;
  baseline_tokens: number;
  retrieved_incidents_count: number;
  savings_pct: number;
  co2_used_g: number;
  co2_saved_g: number;
  co2_baseline_g: number;
  efficiency_label: 'Excellent' | 'Good' | 'Moderate';
}

export interface AnomalyAlert {
  is_anomaly: boolean;
  combination?: string;
  current_rate?: number;
  baseline_rate?: number;
  multiplier?: number;
  severity?: 'HIGH' | 'MEDIUM';
  message?: string;
}

export interface FaultQueryResponse {
  query_id: string;
  original_query: string;
  timestamp: string;
  agent_statuses: AgentStatus[];
  query_enhancement?: QueryEnhancement;
  anomaly_alert?: AnomalyAlert;
  cache_info?: CacheInfo;
  token_efficiency?: TokenEfficiency;
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
    cross_region_risk?: string;
    propagation_risk?: string;
    affected_regions?: string[];
  };
  service_impact: {
    affected_subscribers: number;
    sla_breach_risk: string;
    sla_breach_probability?: number;
    impacted_services: string[];
    business_impact_score: number;
    revenue_impact_estimate: string;
    affected_regions: string[];
    proactive_alert?: string;
    mttr_estimate_minutes?: number;
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
  sla_breach_rate_pct: number;
  cross_region_correlation: {
    regions?: string[];
    correlation_matrix?: Record<string, Record<string, number>>;
    propagation_patterns?: Array<{
      alarm_type: string;
      affected_regions: string[];
      spread_count: number;
      incident_count: number;
    }>;
  };
  risk_by_region: RegionRisk[];
}

export interface RegionRisk {
  region: string;
  risk_score: number;
  risk_level: string;
  incident_count: number;
  top_alarm_type: string;
  top_technology: string;
  avg_outage_minutes: number;
  critical_incident_pct: number;
  avg_recurrence: number;
  contributing_factors: string[];
  recommended_action: string;
}

export interface PredictionResponse {
  by_region: RegionRisk[];
  by_technology: Array<{
    technology: string;
    risk_score: number;
    risk_level: string;
    incident_count: number;
    top_alarm_type: string;
    avg_outage_minutes: number;
    p1_count: number;
    avg_recurrence: number;
  }>;
  hotspots: Array<{
    region: string;
    technology: string;
    risk_score: number;
    risk_level: string;
    incident_count: number;
    top_alarm: string;
    avg_outage_minutes: number;
  }>;
  sla_analysis: {
    total_incidents: number;
    sla_breaches: number;
    sla_breach_rate_pct: number;
    at_risk_incidents: number;
    breach_by_region: Record<string, number>;
    breach_by_technology: Record<string, number>;
    breach_probability_by_severity: Record<string, number>;
    next_breach_risk_by_region: Record<string, number>;
    avg_breach_duration_minutes: number;
    sla_threshold_minutes: number;
    estimated_total_downtime_hours: number;
  };
  generated_at: string;
}

export interface FeedbackRequest {
  query_id: string;
  query: string;
  rating: number;
  helpful: boolean;
  comment?: string;
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

export type StreamEvent =
  | { type: 'enhanced'; enhancement: QueryEnhancement }
  | { type: 'agent_done'; agent_name: string; status: 'completed' | 'failed'; duration_ms: number }
  | { type: 'complete'; result: FaultQueryResponse }
  | { type: 'error'; message: string };

export interface FollowupRequest {
  followup_query: string;
  prior_alarm_type?: string;
  prior_region?: string;
  prior_technology?: string;
  prior_root_cause?: string;
  prior_query?: string;
}

export interface ServiceNowTicket {
  status: string;
  sys_id: string;
  ticket_number: string;
  ticket_url: string;
  state: string;
  priority: string;
  short_description: string;
  created_at: string;
}
