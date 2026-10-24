import { Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { AuditList } from './pages/AuditList';
import { AuditDetail } from './pages/AuditDetail';
import { NewAudit } from './pages/NewAudit';
import { Login } from './pages/Login';
import { useAuth } from './hooks/useAuth';
import { AuthProvider } from './context/AuthContext';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <Navbar />
      <main className="page">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <AuditList />
              </PrivateRoute>
            }
          />
          <Route
            path="/audits/new"
            element={
              <PrivateRoute>
                <NewAudit />
              </PrivateRoute>
            }
          />
          <Route
            path="/audits/:id"
            element={
              <PrivateRoute>
                <AuditDetail />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </AuthProvider>
  );
}

export default App;
