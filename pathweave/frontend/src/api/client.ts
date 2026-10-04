// PathWeave API client

import type {
  AnalyzeRequest,
  GeneSuggestion,
  JobProgress,
  OrganismInfo,
} from '@/types/api';

const BASE = '/api';

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  analyze: (body: AnalyzeRequest) =>
    request<{ job_id: string; message: string }>('/analyze', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getJob: (id: string) =>
    request<JobProgress>(`/jobs/${id}`),

  getDemo: () =>
    request<{ job_id: string; message: string }>('/demo'),

  getOrganisms: () =>
    request<OrganismInfo[]>('/organisms'),

  suggestGenes: (q: string) =>
    request<GeneSuggestion[]>(`/genes/suggest?q=${encodeURIComponent(q)}`),

  exportResults: (jobId: string, format: 'csv' | 'json') => {
    window.open(`${BASE}/export/${jobId}?format=${format}`, '_blank');
  },
};
