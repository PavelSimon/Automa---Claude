import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../stores/auth'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    auth: {
      login: vi.fn(),
      register: vi.fn(),
      me: vi.fn()
    }
  },
  setAuthToken: vi.fn(),
  clearCache: vi.fn()
}))

// Mock localStorage
const mockLocalStorage = (() => {
  let store = {}
  return {
    getItem: vi.fn(key => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn(key => { delete store[key] }),
    clear: vi.fn(() => { store = {} })
  }
})()

Object.defineProperty(window, 'localStorage', { value: mockLocalStorage })

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    mockLocalStorage.clear()
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const authStore = useAuthStore()

      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(authStore.isLoading).toBe(false)
    })

    it('should get token from localStorage if available', () => {
      mockLocalStorage.setItem('token', 'test-token')

      const authStore = useAuthStore()
      expect(authStore.token).toBe('test-token')
    })
  })

  describe('Getters', () => {
    it('should return false for isAuthenticated when no token', () => {
      const authStore = useAuthStore()
      expect(authStore.isAuthenticated).toBe(false)
    })

    it('should return true for isAuthenticated when token exists', () => {
      const authStore = useAuthStore()
      authStore.token = 'test-token'
      expect(authStore.isAuthenticated).toBe(true)
    })
  })

  describe('Actions', () => {
    it('should handle successful login', async () => {
      const { apiService } = await import('../../services/api')
      apiService.auth.login.mockResolvedValue({
        data: { access_token: 'new-token' }
      })
      apiService.auth.me.mockResolvedValue({
        data: { id: 1, email: 'test@example.com' }
      })

      const authStore = useAuthStore()
      const result = await authStore.login('test@example.com', 'password')

      expect(result.success).toBe(true)
      expect(authStore.token).toBe('new-token')
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('token', 'new-token')
    })

    it('should handle login failure', async () => {
      const { apiService } = await import('../../services/api')
      apiService.auth.login.mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } }
      })

      const authStore = useAuthStore()
      const result = await authStore.login('test@example.com', 'wrong-password')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Invalid credentials')
    })

    it('should logout correctly', () => {
      const authStore = useAuthStore()
      authStore.user = { id: 1, email: 'test@example.com' }
      authStore.token = 'test-token'

      authStore.logout()

      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token')
    })
  })
})