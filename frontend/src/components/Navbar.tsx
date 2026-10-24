import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Navbar() {
  const { user, isAuthenticated, logout, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <nav className="navbar">
        <div className="navbar-brand">Sentinel Lens</div>
        <div className="loading"><div className="spinner" /></div>
      </nav>
    );
  }

  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        Sentinel Lens
      </NavLink>
      <nav className="navbar-nav">
        {isAuthenticated && (
          <>
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Audits
            </NavLink>
            <NavLink to="/audits/new" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              New Audit
            </NavLink>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', marginRight: '1rem' }}>
              {user?.fullName || user?.username}
            </span>
            <button onClick={logout} className="btn-secondary">
              Logout
            </button>
          </>
        )}
      </nav>
    </nav>
  );
}
