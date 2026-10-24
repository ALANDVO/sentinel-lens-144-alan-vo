import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Login() {
  const { isAuthenticated, loading, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (loading) {
    return (
      <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div className="loading"><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <div className="card" style={{ maxWidth: '400px', width: '100%' }}>
        <h1 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Sentinel Lens</h1>
        <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
          Security Audit Dashboard
        </p>
        <div style={{ textAlign: 'center' }}>
          <button onClick={login} className="btn-primary" style={{ width: '100%', padding: '0.75rem 1.5rem', fontSize: '1rem' }}>
            Sign in with Keycloak
          </button>
        </div>
        <p style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          Demo mode: authentication bypassed in development
        </p>
      </div>
    </div>
  );
}
