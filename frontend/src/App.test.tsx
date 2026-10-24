import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'

// Mock AuthContext
vi.mock('./context/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => ({
    isAuthenticated: true,
    loading: false,
    user: { username: 'testuser', email: 'test@example.com', fullName: 'Test User', roles: ['viewer'], id: '1' },
    login: vi.fn(),
    logout: vi.fn(),
    getToken: vi.fn(),
  }),
}))

describe('App', () => {
  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    expect(screen.getByText('Sentinel Lens')).toBeInTheDocument()
  })
})
