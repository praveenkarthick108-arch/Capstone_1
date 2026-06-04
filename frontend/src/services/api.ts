import axios from 'axios';
import { FaultQueryResponse, AnalyticsResponse, HealthResponse, QueryFilters, PredictionResponse, FeedbackRequest, ServiceNowTicket, StreamEvent, FollowupRequest } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export const queryFault = async (
  query: string,
  filters: QueryFilters = {},
  top_k: number = 5
): Promise<FaultQueryResponse> => {
  const { data } = await api.post<FaultQueryResponse>('/api/query', { query, ...filters, top_k });
  return data;
};

export const getAnalytics = async (): Promise<AnalyticsResponse> => {
  const { data } = await api.get<AnalyticsResponse>('/api/analytics');
  return data;
};

export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get<HealthResponse>('/api/health');
  return data;
};

export const getIncidents = async (
  filters: Record<string, string> = {},
  page = 1,
  pageSize = 20
) => {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize), ...filters });
  const { data } = await api.get(`/api/incidents?${params}`);
  return data;
};

export const evaluateResponse = async (
  query: string,
  response: string,
  retrieved_contexts: string[]
) => {
  const { data } = await api.post('/api/evaluate', { query, response, retrieved_contexts });
  return data;
};

export const triggerIngestion = async (force = false) => {
  const { data } = await api.post('/api/ingest', { force_reingest: force });
  return data;
};

export const getPredictions = async (region?: string, technology?: string): Promise<PredictionResponse> => {
  const params = new URLSearchParams();
  if (region) params.set('region', region);
  if (technology) params.set('technology', technology);
  const { data } = await api.get<PredictionResponse>(`/api/predict?${params}`);
  return data;
};

export const submitFeedback = async (payload: FeedbackRequest) => {
  const { data } = await api.post('/api/feedback', payload);
  return data;
};

export const getFeedbackStats = async () => {
  const { data } = await api.get('/api/feedback/stats');
  return data;
};

export const summarizeOutage = async (alarm_ids: string[], context = '') => {
  const { data } = await api.post('/api/summarize', { alarm_ids, context });
  return data;
};

export const createServiceNowTicket = async (payload: {
  query_id: string;
  query: string;
  alarm_type: string;
  region: string;
  technology: string;
  severity: string;
  root_cause_chain: string;
  technical_explanation: string;
  resolution_steps: string[];
  affected_subscribers: number;
  sla_breach_risk: string;
  confidence_score?: number;
  probable_causes?: any[];
  revenue_impact?: string;
  business_impact_score?: number;
  impacted_services?: string[];
  escalation_path?: string;
  estimated_resolution_time?: string;
  vendor_commands?: any[];
  prevention_measures?: string[];
}): Promise<ServiceNowTicket> => {
  const { data } = await api.post<ServiceNowTicket>('/api/servicenow/create-ticket', payload);
  return data;
};

export const listServiceNowTickets = async (limit = 10) => {
  const { data } = await api.get(`/api/servicenow/tickets?limit=${limit}`);
  return data;
};

export const streamQuery = async (
  query: string,
  filters: QueryFilters = {},
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> => {
  const response = await fetch(`${API_BASE}/api/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, ...filters, top_k: 5 }),
    signal,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Stream failed' }));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() ?? '';
    for (const part of parts) {
      if (part.startsWith('data: ')) {
        try {
          onEvent(JSON.parse(part.slice(6)));
        } catch { /* ignore malformed chunks */ }
      }
    }
  }
};

export const followupQuery = async (payload: FollowupRequest): Promise<{ answer: string; question: string }> => {
  const { data } = await api.post<{ answer: string; question: string }>('/api/followup', payload);
  return data;
};
