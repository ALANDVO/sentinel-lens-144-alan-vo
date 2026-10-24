import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock Keycloak
vi.mock('keycloak-js', () => ({
  default: vi.fn().mockImplementation(() => ({
    init: vi.fn().mockResolvedValue(false),
    login: vi.fn(),
    logout: vi.fn(),
    loadUserProfile: vi.fn().mockResolvedValue({}),
    updateToken: vi.fn().mockResolvedValue(true),
    token: 'mock-token',
    realmAccess: { roles: ['viewer'] },
  })),
}))
