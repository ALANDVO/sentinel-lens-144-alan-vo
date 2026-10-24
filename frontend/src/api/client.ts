/** Typed API client */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...init } = options;
  
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  const response = await fetch(url.toString(), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),
  createAuditRun: (data: {
    target_repo: string;
    target_ref?: string;
    profile?: 'quick' | 'standard' | 'deep';
    config?: Record<string, unknown>;
  }) => request<ApiAuditRun>('/api/audits', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  listAuditRuns: (params?: {
    target_repo?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) => request<ApiAuditRun[]>('/api/audits', { params }),
  getAuditRun: (id: number) => request<ApiAuditRun>(`/api/audits/${id}`),
  listFindings: (auditId: number, params?: {
    status?: string;
    severity?: string;
    attack_class?: string;
    limit?: number;
    offset?: number;
  }) => request<ApiFinding[]>(`/api/audits/${auditId}/findings`, { params }),
  listCoverage: (auditId: number, params?: {
    status?: string;
    attack_class?: string;
    limit?: number;
    offset?: number;
  }) => request<ApiCoverageUnit[]>(`/api/audits/${auditId}/coverage`, { params }),
  importPriorRun: (auditId: number, priorRunId: number) =>
    request<{ imported: number; prior_run_id: number }>(`/api/audits/${auditId}/import`, {
      method: 'POST',
      body: JSON.stringify({ prior_run_id: priorRunId }),
    }),
  exportAudit: (auditId: number, format: 'json' | 'csv' = 'json') =>
    request<ApiExport>(`/api/audits/${auditId}/export`, { params: { format } }),
};

export interface ApiAuditRun {
  id: number;
  target_repo: string;
  target_ref: string | null;
  profile: 'quick' | 'standard' | 'deep';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  config: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  findings_count: number;
  coverage_units_count: number;
}

export interface ApiFinding {
  id: number;
  audit_run_id: number;
  status: 'proposed' | 'needs_validation' | 'confirmed' | 'rejected' | 'deferred';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info' | 'hardening';
  title: string;
  description: string;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  attack_class: string;
  evidence: Record<string, unknown>;
  remediation: Record<string, unknown>;
  verification: Record<string, unknown>;
  llm_explanation: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiCoverageUnit {
  id: number;
  audit_run_id: number;
  unit_id: string;
  unit_type: string;
  file_path: string;
  line_start: number | null;
  line_end: number | null;
  attack_class: string;
  status: 'planned' | 'hunting' | 'covered' | 'deferred' | 'out_of_scope' | 'prior_covered_same_source' | 'prior_needs_validation' | 'prior_confirmed_same_source';
  hunter_id: string | null;
  hunter_result: Record<string, unknown>;
  verifier_result: Record<string, unknown>;
  prior_run_id: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiExport {
  audit_run: {
    id: number;
    target_repo: string;
    target_ref: string | null;
    profile: string;
    status: string;
    created_at: string;
    completed_at: string | null;
  };
  findings: ApiFinding[];
  coverage: ApiCoverageUnit[];
}
