import { useState, useEffect } from 'react';
import { useParams, NavLink } from 'react-router-dom';
import { api, ApiAuditRun, ApiFinding, ApiCoverageUnit } from '../api/client';
import { formatDistanceToNow } from 'date-fns';

export function AuditDetail() {
  const { id } = useParams<{ id: string }>();
  const auditId = Number(id);
  const [audit, setAudit] = useState<ApiAuditRun | null>(null);
  const [findings, setFindings] = useState<ApiFinding[]>([]);
  const [coverage, setCoverage] = useState<ApiCoverageUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'findings' | 'coverage' | 'export'>('overview');
  const [importModal, setImportModal] = useState(false);
  const [priorRunId, setPriorRunId] = useState('');

  useEffect(() => {
    loadAudit();
  }, [auditId]);

  async function loadAudit() {
    setLoading(true);
    setError(null);
    try {
      const [auditData, findingsData, coverageData] = await Promise.all([
        api.getAuditRun(auditId),
        api.listFindings(auditId, { limit: 100 }),
        api.listCoverage(auditId, { limit: 200 }),
      ]);
      setAudit(auditData);
      setFindings(findingsData);
      setCoverage(coverageData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit');
    } finally {
      setLoading(false);
    }
  }

  async function handleImport() {
    if (!priorRunId) return;
    setError(null);
    try {
      await api.importPriorRun(auditId, Number(priorRunId));
      setImportModal(false);
      setPriorRunId('');
      await loadAudit();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    }
  }

  async function handleExport() {
    try {
      const data = await api.exportAudit(auditId, 'json');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-${auditId}-export.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  }

  function getStatusBadge(status: string) {
    return <span className={`badge badge-${status}`}>{status}</span>;
  }

  function getSeverityBadge(severity: string) {
    return <span className={`badge badge-${severity}`}>{severity}</span>;
  }

  function getCoverageBadge(status: string) {
    return <span className={`badge`} style={{ background: 'var(--color-bg)', color: 'var(--color-text)' }}>{status}</span>;
  }

  if (loading && !audit) {
    return <div className="loading"><div className="spinner" /></div>;
  }

  if (error && !audit) {
    return (
      <div className="card" style={{ maxWidth: '600px' }}>
        <p style={{ color: 'var(--color-danger)' }}>Failed to load audit: {error}</p>
        <NavLink to="/" className="btn-secondary" style={{ marginTop: '1rem', display: 'inline-block' }}>
          Back to Audits
        </NavLink>
      </div>
    );
  }

  return (
    <div>
      {audit && (
        <div className="page-header">
          <div>
            <NavLink to="/" className="btn-secondary" style={{ marginRight: '1rem' }}>
              ← Back
            </NavLink>
            <h1 className="page-title" style={{ display: 'inline' }}>
              {audit.target_repo}
            </h1>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span>{getStatusBadge(audit.status)}</span>
            <span className="badge" style={{ background: 'var(--color-bg)', color: 'var(--color-text)' }}>
              {audit.profile}
            </span>
          </div>
        </div>
      )}

      {error && (
        <div style={{ color: 'var(--color-danger)', marginBottom: '1rem', padding: '0.75rem', background: '#fef2f2', borderRadius: 'var(--radius)' }}>
          {error}
        </div>
      )}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>Repository</p>
            <p style={{ fontWeight: 500 }}>{audit?.target_repo}</p>
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>Reference</p>
            <p>{audit?.target_ref || 'default branch'}</p>
          </div>
          <div style={{ flex: 1, minWidth: '150px' }}>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>Profile</p>
            <p>{audit?.profile}</p>
          </div>
          <div style={{ flex: 1, minWidth: '150px' }}>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>Created</p>
            <p>{audit ? formatDistanceToNow(new Date(audit.created_at), { addSuffix: true }) : '-'}</p>
          </div>
          <div style={{ flex: 1, minWidth: '150px' }}>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>Status</p>
            <p>{getStatusBadge(audit?.status || '')}</p>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <nav style={{ borderBottom: '1px solid var(--color-border)', marginBottom: '1rem' }}>
          {[
            { id: 'overview', label: 'Overview', count: audit?.findings_count },
            { id: 'findings', label: 'Findings', count: findings.length },
            { id: 'coverage', label: 'Coverage', count: coverage.length },
            { id: 'export', label: 'Export' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: '0.75rem 1.5rem',
                border: 'none',
                background: 'transparent',
                color: activeTab === tab.id ? 'var(--color-primary)' : 'var(--color-text-muted)',
                fontWeight: activeTab === tab.id ? 600 : 400,
                borderBottom: activeTab === tab.id ? '2px solid var(--color-primary)' : '2px solid transparent',
                marginBottom: '-1px',
                cursor: 'pointer',
              }}
            >
              {tab.label} {tab.count !== undefined && <span className="badge" style={{ marginLeft: '0.5rem', background: 'var(--color-bg)' }}>{tab.count}</span>}
            </button>
          ))}
        </nav>

        {activeTab === 'overview' && (
          <div>
            <h3 style={{ marginBottom: '1rem' }}>Summary</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Total Findings</p>
                <p style={{ fontSize: '2rem', fontWeight: 700 }}>{findings.length}</p>
              </div>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Confirmed</p>
                <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-success)' }}>
                  {findings.filter(f => f.status === 'confirmed').length}
                </p>
              </div>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Needs Validation</p>
                <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-warning)' }}>
                  {findings.filter(f => f.status === 'needs_validation').length}
                </p>
              </div>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Rejected</p>
                <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-danger)' }}>
                  {findings.filter(f => f.status === 'rejected').length}
                </p>
              </div>
            </div>

            <h3 style={{ marginTop: '2rem', marginBottom: '1rem' }}>Coverage</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Total Units</p>
                <p style={{ fontSize: '2rem', fontWeight: 700 }}>{coverage.length}</p>
              </div>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Covered</p>
                <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-success)' }}>
                  {coverage.filter(c => c.status === 'covered').length}
                </p>
              </div>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Deferred</p>
                <p style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-warning)' }}>
                  {coverage.filter(c => c.status === 'deferred').length}
                </p>
              </div>
              <div style={{ padding: '1rem', background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Prior Covered</p>
                <p style={{ fontSize: '2rem', fontWeight: 700 }}>
                  {coverage.filter(c => c.status.startsWith('prior_')).length}
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'findings' && (
          <div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Severity</th>
                    <th>Status</th>
                    <th>Attack Class</th>
                    <th>Location</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {findings.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                        No findings yet. Run the audit to discover vulnerabilities.
                      </td>
                    </tr>
                  ) : (
                    findings.map((finding) => (
                      <tr key={finding.id}>
                        <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {finding.title}
                        </td>
                        <td>{getSeverityBadge(finding.severity)}</td>
                        <td>{getStatusBadge(finding.status)}</td>
                        <td>{finding.attack_class}</td>
                        <td>
                          {finding.file_path && (
                            <>
                              {finding.file_path}
                              {finding.line_start && (
                                <>:{finding.line_start}{finding.line_end && `-${finding.line_end}`}</>
                              )}
                            </>
                          )}
                        </td>
                        <td>{formatDistanceToNow(new Date(finding.created_at), { addSuffix: true })}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'coverage' && (
          <div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Unit ID</th>
                    <th>Type</th>
                    <th>Attack Class</th>
                    <th>Status</th>
                    <th>File</th>
                    <th>Lines</th>
                  </tr>
                </thead>
                <tbody>
                  {coverage.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)' }}>
                        No coverage data. Run the audit to map coverage.
                      </td>
                    </tr>
                  ) : (
                    coverage.map((unit) => (
                      <tr key={unit.id}>
                        <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'monospace', fontSize: '0.875rem' }}>
                          {unit.unit_id}
                        </td>
                        <td>{unit.unit_type}</td>
                        <td>{unit.attack_class}</td>
                        <td>{getCoverageBadge(unit.status)}</td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{unit.file_path}</td>
                        <td>
                          {unit.line_start && `${unit.line_start}${unit.line_end && `-${unit.line_end}`}`}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'export' && (
          <div style={{ maxWidth: '600px' }}>
            <h3 style={{ marginBottom: '1rem' }}>Export Audit Data</h3>
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
              Download a complete JSON export of this audit run including all findings and coverage data.
            </p>
            <button onClick={handleExport} className="btn-primary" disabled={loading}>
              Download JSON Export
            </button>

            <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
              <h3 style={{ marginBottom: '1rem' }}>Import Prior Run</h3>
              <p style={{ color: 'var(--color-text-muted)', marginBottom: '1rem', fontSize: '0.875rem' }}>
                Import confirmed findings from a previous audit run of the same repository as prior coverage units.
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', maxWidth: '400px' }}>
                <input
                  type="number"
                  className="input"
                  placeholder="Prior Run ID"
                  value={priorRunId}
                  onChange={(e) => setPriorRunId(e.target.value)}
                />
                <button onClick={() => setImportModal(true)} className="btn-secondary">
                  Import
                </button>
              </div>
            </div>
          </div>
        )}

        {importModal && (
          <div className="modal-overlay" onClick={() => setImportModal(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Import Prior Run</h3>
                <button onClick={() => setImportModal(false)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
              </div>
              <div className="modal-body">
                <p>Import confirmed findings from run <strong>{priorRunId}</strong> as prior coverage?</p>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                  This will create coverage units with status "prior_covered_same_source" for each confirmed finding.
                </p>
              </div>
              <div className="modal-footer">
                <button onClick={() => setImportModal(false)} className="btn-secondary">Cancel</button>
                <button onClick={handleImport} className="btn-primary" disabled={loading}>
                  {loading ? 'Importing...' : 'Confirm Import'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
