import { defineStore } from 'pinia'
import { apiService, setAuthToken, clearCache } from '../services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token'),
    tokenExpiration: localStorage.getItem('tokenExpiration') ? parseInt(localStorage.getItem('tokenExpiration')) : null,
    isLoading: false,
    showExpirationWarning: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    tokenExpiresIn: (state) => {
      if (!state.tokenExpiration) return null
      const now = Date.now()
      const expiresIn = state.tokenExpiration - now
      return expiresIn > 0 ? expiresIn : 0
    },
    tokenExpiresInMinutes: (state) => {
      const expiresIn = state.tokenExpiresIn
      return expiresIn ? Math.floor(expiresIn / 60000) : 0
    }
  },

  actions: {
    async login(email, password) {
      this.isLoading = true
      try {
        const response = await apiService.auth.login(email, password)

        this.token = response.data.access_token
        localStorage.setItem('token', this.token)

        // Calculate token expiration (30 minutes from now)
        const expirationTime = Date.now() + (30 * 60 * 1000)
        this.tokenExpiration = expirationTime
        localStorage.setItem('tokenExpiration', expirationTime.toString())

        // Set authorization header
        setAuthToken(this.token)

        // Start expiration check timer
        this.startExpirationCheck()

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
      this.tokenExpiration = null
      this.showExpirationWarning = false
      localStorage.removeItem('token')
      localStorage.removeItem('tokenExpiration')
      setAuthToken(null)
      clearCache()
      this.stopExpirationCheck()
    },

    async initializeAuth() {
      if (this.token) {
        setAuthToken(this.token)

        // Check if token is expired
        if (this.tokenExpiration && Date.now() >= this.tokenExpiration) {
          console.log('Token expired, logging out')
          this.logout()
          return
        }

        await this.fetchUser()
        this.startExpirationCheck()
      }
    },

    startExpirationCheck() {
      // Check every minute
      this.expirationCheckInterval = setInterval(() => {
        const expiresIn = this.tokenExpiresInMinutes

        // Show warning 5 minutes before expiration
        if (expiresIn <= 5 && expiresIn > 0) {
          this.showExpirationWarning = true
        }

        // Auto-logout when expired
        if (expiresIn <= 0 && this.token) {
          console.log('Token expired, auto-logout')
          this.logout()
        }
      }, 60000) // Check every minute
    },

    stopExpirationCheck() {
      if (this.expirationCheckInterval) {
        clearInterval(this.expirationCheckInterval)
        this.expirationCheckInterval = null
      }
    },

    dismissExpirationWarning() {
      this.showExpirationWarning = false
    }
  }
})

// Auth error handling is now managed by the API service