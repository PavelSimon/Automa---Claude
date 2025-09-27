import { defineStore } from 'pinia'
import { apiService, setAuthToken, clearCache } from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    isLoading: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(email, password) {
      this.isLoading = true
      try {
        const response = await apiService.auth.login(email, password)

        this.token = response.data.access_token
        localStorage.setItem('token', this.token)

        // Set authorization header
        setAuthToken(this.token)

        // Fetch user data
        await this.fetchUser()

        return { success: true }
      } catch (error) {
        console.error('Login error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Login failed'
        }
      } finally {
        this.isLoading = false
      }
    },

    async register(email, password) {
      this.isLoading = true
      try {
        await apiService.auth.register(email, password)

        // Auto-login after registration
        return await this.login(email, password)
      } catch (error) {
        console.error('Registration error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Registration failed'
        }
      } finally {
        this.isLoading = false
      }
    },

    async fetchUser() {
      try {
        const response = await apiService.auth.me()
        this.user = response.data
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.logout()
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      setAuthToken(null)
      clearCache()
    },

    async initializeAuth() {
      if (this.token) {
        setAuthToken(this.token)
        await this.fetchUser()
      }
    }
  }
})

// Auth error handling is now managed by the API service