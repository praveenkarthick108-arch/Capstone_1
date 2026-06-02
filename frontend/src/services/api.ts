import axios from 'axios';
import { FaultQueryResponse, AnalyticsResponse, HealthResponse, QueryFilters } from '../types';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

export const queryFault = async (
  query: string,
  filters: QueryFilters = {},
  top_k: number = 5
): Promise<FaultQueryResponse> => {
  const { data } = await api.post<FaultQueryResponse>('/api/query', {
    query,
    ...filters,
    top_k,
  });
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
