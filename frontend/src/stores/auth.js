import { defineStore } from 'pinia'
import axios from 'axios'

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
        const response = await axios.post('/auth/jwt/login', {
          username: email,
          password: password
        }, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        })

        this.token = response.data.access_token
        localStorage.setItem('token', this.token)

        // Set default authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

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
        await axios.post('/auth/register', {
          email,
          password
        })

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
        const response = await axios.get('/users/me')
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
      delete axios.defaults.headers.common['Authorization']
    },

    async initializeAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        await this.fetchUser()
      }
    }
  }
})

// Initialize axios interceptor for automatic logout on 401
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only logout on auth endpoints, not on API errors
      const url = error.config?.url || ''
      if (url.includes('/auth/') || url.includes('/users/me')) {
        const authStore = useAuthStore()
        authStore.logout()
      }
    }
    return Promise.reject(error)
  }
)