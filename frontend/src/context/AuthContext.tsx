import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import Keycloak, { KeycloakInstance, KeycloakProfile } from 'keycloak-js';

interface User {
  id: string;
  username: string;
  email: string;
  fullName: string;
  roles: string[];
}

interface AuthContextType {
  keycloak: KeycloakInstance | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getToken: () => Promise<string | undefined>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const KEYCLOAK_CONFIG = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'sentinel-lens',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'sentinel-lens-frontend',
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [keycloak, setKeycloak] = useState<KeycloakInstance | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const kc = new Keycloak(KEYCLOAK_CONFIG);
    setKeycloak(kc);

    kc.init({
      onLoad: 'check-sso',
      silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
      pkceMethod: 'S256',
    })
      .then((authenticated) => {
        if (authenticated) {
          return kc.loadUserProfile().then((profile: KeycloakProfile) => {
            const roles = kc.realmAccess?.roles || [];
            setUser({
              id: profile.id || '',
              username: profile.username || '',
              email: profile.email || '',
              fullName: `${profile.firstName || ''} ${profile.lastName || ''}`.trim() || profile.username || '',
              roles,
            });
          });
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const login = async () => {
    if (keycloak) {
      await keycloak.login({ pkceMethod: 'S256' });
    }
  };

  const logout = async () => {
    if (keycloak) {
      await keycloak.logout({ redirectUri: window.location.origin });
    }
  };

  const getToken = async (): Promise<string | undefined> => {
    if (keycloak && keycloak.token) {
      try {
        await keycloak.updateToken(30);
        return keycloak.token;
      } catch {
        await login();
        return keycloak.token;
      }
    }
    return undefined;
  };

  return (
    <AuthContext.Provider value={{ keycloak, user, isAuthenticated: !!user, loading, login, logout, getToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
