import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { api, ApiAuditRun } from '../api/client';
import { formatDistanceToNow } from 'date-fns';

export function AuditList() {
  const [audits, setAudits] = useState<ApiAuditRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ target_repo: '', status: '' });
  const [pagination, setPagination] = useState({ limit: 20, offset: 0, total: 0 });

  useEffect(() => {
    loadAudits();
  }, [filters, pagination.offset]);

  async function loadAudits() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listAuditRuns({
        target_repo: filters.target_repo || undefined,
        status: filters.status || undefined,
        limit: pagination.limit,
        offset: pagination.offset,
      });
      setAudits(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audits');
    } finally {
      setLoading(false);
    }
  }

  function getStatusBadge(status: string) {
    return <span className={`badge badge-${status}`}>{status}</span>;
  }

  function getProfileBadge(profile: string) {
    return <span className="badge" style={{ background: 'var(--color-bg)', color: 'var(--color-text)' }}>{profile}</span>;
  }

  if (loading && audits.length === 0) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Audit Runs</h1>
        <NavLink to="/audits/new" className="btn-primary">
          New Audit
        </NavLink>
      </div>

      <div className="card">
        <div className="filters">
          <div className="filter-group">
            <label className="form-label">Repository</label>
            <input
              type="text"
              className="input"
              placeholder="Filter by repository..."
              value={filters.target_repo}
              onChange={(e) => setFilters({ ...filters, target_repo: e.target.value })}
            />
          </div>
          <div className="filter-group">
            <label className="form-label">Status</label>
            <select
              className="input"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {error && (
          <div style={{ color: 'var(--color-danger)', marginBottom: '1rem', padding: '0.75rem', background: '#fef2f2', borderRadius: 'var(--radius)' }}>
            {error}
          </div>
        )}

        {audits.length === 0 ? (
          <div className="empty-state">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>No audit runs found</p>
            <NavLink to="/audits/new" className="btn-primary" style={{ marginTop: '1rem', display: 'inline-block' }}>
              Create your first audit
            </NavLink>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Repository</th>
                    <th>Ref</th>
                    <th>Profile</th>
                    <th>Status</th>
                    <th>Findings</th>
                    <th>Coverage</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {audits.map((audit) => (
                    <tr key={audit.id}>
                      <td>
                        <NavLink to={`/audits/${audit.id}`} style={{ fontWeight: 500 }}>
                          {audit.target_repo}
                        </NavLink>
                      </td>
                      <td>{audit.target_ref || '-'}</td>
                      <td>{getProfileBadge(audit.profile)}</td>
                      <td>{getStatusBadge(audit.status)}</td>
                      <td>{audit.findings_count}</td>
                      <td>{audit.coverage_units_count}</td>
                      <td>{formatDistanceToNow(new Date(audit.created_at), { addSuffix: true })}</td>
                      <td>
                        <NavLink to={`/audits/${audit.id}`} className="btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}>
                          View
                        </NavLink>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <button
                onClick={() => setPagination({ ...pagination, offset: Math.max(0, pagination.offset - pagination.limit) })}
                disabled={pagination.offset === 0}
              >
                Previous
              </button>
              <span>
                Page {Math.floor(pagination.offset / pagination.limit) + 1}
              </span>
              <button
                onClick={() => setPagination({ ...pagination, offset: pagination.offset + pagination.limit })}
                disabled={audits.length < pagination.limit}
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
