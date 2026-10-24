import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export function NewAudit() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    target_repo: '',
    target_ref: '',
    profile: 'standard' as 'quick' | 'standard' | 'deep',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.createAuditRun({
        target_repo: formData.target_repo,
        target_ref: formData.target_ref || undefined,
        profile: formData.profile,
      });
      navigate(`/audits/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create audit');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">New Audit Run</h1>
      </div>

      <div className="card" style={{ maxWidth: '600px' }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="target_repo">Target Repository *</label>
            <input
              type="text"
              id="target_repo"
              className="input"
              placeholder="https://github.com/owner/repo or local path"
              value={formData.target_repo}
              onChange={(e) => setFormData({ ...formData, target_repo: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="target_ref">Target Reference</label>
            <input
              type="text"
              id="target_ref"
              className="input"
              placeholder="Branch, tag, or commit (optional)"
              value={formData.target_ref}
              onChange={(e) => setFormData({ ...formData, target_ref: e.target.value })}
            />
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Leave empty for default branch
            </p>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="profile">Audit Profile</label>
            <select
              id="profile"
              className="input"
              value={formData.profile}
              onChange={(e) => setFormData({ ...formData, profile: e.target.value as 'quick' | 'standard' | 'deep' })}
            >
              <option value="quick">Quick - Fast scan, lower coverage</option>
              <option value="standard">Standard - Balanced depth and speed</option>
              <option value="deep">Deep - Comprehensive analysis, higher cost</option>
            </select>
          </div>

          {error && (
            <div style={{ color: 'var(--color-danger)', marginBottom: '1rem', padding: '0.75rem', background: '#fef2f2', borderRadius: 'var(--radius)' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading || !formData.target_repo}>
              {loading ? 'Creating...' : 'Create Audit'}
            </button>
          </div>
        </form>

        <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
          <h3 style={{ marginBottom: '1rem' }}>Profile Comparison</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Profile</th>
                  <th>Depth</th>
                  <th>Speed</th>
                  <th>Cost</th>
                  <th>Best For</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Quick</strong></td>
                  <td>Single hunter wave</td>
                  <td>Fast</td>
                  <td>Low</td>
                  <td>Initial triage, CI gates</td>
                </tr>
                <tr>
                  <td><strong>Standard</strong></td>
                  <td>Two hunter waves + validation</td>
                  <td>Moderate</td>
                  <td>Medium</td>
                  <td>Regular audits, compliance</td>
                </tr>
                <tr>
                  <td><strong>Deep</strong></td>
                  <td>Multiple waves + LLM advisory</td>
                  <td>Slow</td>
                  <td>High</td>
                  <td>Critical systems, pre-release</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
