import axios from 'axios'

// Simple cache implementation
const cache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

// Create axios instance with custom configuration
const api = axios.create({
  baseURL: '',
  timeout: 10000,
})

// Request interceptor for caching GET requests
api.interceptors.request.use((config) => {
  // Only cache GET requests
  if (config.method === 'get') {
    const cacheKey = `${config.url}?${new URLSearchParams(config.params).toString()}`
    const cachedResponse = cache.get(cacheKey)

    if (cachedResponse && Date.now() - cachedResponse.timestamp < CACHE_DURATION) {
      // Return cached response by creating a resolved promise
      return Promise.reject({
        config,
        response: cachedResponse.data,
        cached: true
      })
    }
  }

  return config
})

// Response interceptor for caching and error handling
api.interceptors.response.use(
  (response) => {
    const method = response.config.method?.toLowerCase()

    // Cache successful GET responses
    if (method === 'get') {
      const cacheKey = `${response.config.url}?${new URLSearchParams(response.config.params).toString()}`
      cache.set(cacheKey, {
        data: response,
        timestamp: Date.now()
      })
    }

    // Invalidate cache after mutations (POST, PUT, DELETE, PATCH)
    if (['post', 'put', 'delete', 'patch'].includes(method)) {
      // Extract resource path from URL (e.g., /api/v1/agents/)
      const url = response.config.url || ''
      const resourceMatch = url.match(/\/api\/v1\/(\w+)/)
      if (resourceMatch) {
        const resource = resourceMatch[1]
        // Clear all cached entries for this resource
        clearCache(resource)
        // Also clear monitoring cache as it depends on all resources
        clearCache('monitoring')
      }
    }

    return response
  },
  (error) => {
    // Handle cached responses
    if (error.cached) {
      return Promise.resolve(error.response)
    }

    // Handle auth errors
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      if (url.includes('/auth/') || url.includes('/users/me')) {
        // Clear cache on auth errors
        cache.clear()
        // Auth store logout will be handled by the auth store interceptor
      }
    }

    return Promise.reject(error)
  }
)

// Clear cache function for manual cache invalidation
export const clearCache = (pattern) => {
  if (pattern) {
    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key)
      }
    }
  } else {
    cache.clear()
  }
}

// Set authorization header
export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// API service methods
export const apiService = {
  // Authentication
  auth: {
    login: (email, password) => api.post('/auth/jwt/login',
      new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ),
    register: (email, password) => api.post('/auth/register', { email, password }),
    me: () => api.get('/users/me'),
    updateProfile: (data) => api.put('/users/profile', data)
  },

  // Scripts
  scripts: {
    list: (skip = 0, limit = 100) => api.get('/api/v1/scripts/', { params: { skip, limit } }),
    get: (id) => api.get(`/api/v1/scripts/${id}`),
    create: (data) => api.post('/api/v1/scripts/', data),
    update: (id, data) => api.put(`/api/v1/scripts/${id}`, data),
    delete: (id) => api.delete(`/api/v1/scripts/${id}`),
    upload: (formData) => api.post('/api/v1/scripts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Agents
  agents: {
    list: (skip = 0, limit = 100, status = null) => api.get('/api/v1/agents/', {
      params: { skip, limit, ...(status && { status }) }
    }),
    get: (id) => api.get(`/api/v1/agents/${id}`),
    create: (data) => api.post('/api/v1/agents/', data),
    update: (id, data) => api.put(`/api/v1/agents/${id}`, data),
    delete: (id) => api.delete(`/api/v1/agents/${id}`),
    start: (id) => api.post(`/api/v1/agents/${id}/start`),
    stop: (id) => api.post(`/api/v1/agents/${id}/stop`),
    restart: (id) => api.post(`/api/v1/agents/${id}/restart`)
  },

  // Jobs
  jobs: {
    list: (skip = 0, limit = 100) => api.get('/api/v1/jobs/', { params: { skip, limit } }),
    get: (id) => api.get(`/api/v1/jobs/${id}`),
    create: (data) => api.post('/api/v1/jobs/', data),
    update: (id, data) => api.put(`/api/v1/jobs/${id}`, data),
    delete: (id) => api.delete(`/api/v1/jobs/${id}`),
    execute: (id) => api.post(`/api/v1/jobs/${id}/execute`),
    executions: (id, skip = 0, limit = 50) => api.get(`/api/v1/jobs/${id}/executions`, {
      params: { skip, limit }
    })
  },

  // Monitoring
  monitoring: {
    status: () => api.get('/api/v1/monitoring/status'),
    executions: (limit) => api.get('/api/v1/monitoring/executions/recent', {
      params: limit ? { limit } : {}
    })
  },

  // Credentials
  credentials: {
    list: (skip = 0, limit = 100) => api.get('/api/v1/credentials/', { params: { skip, limit } }),
    get: (id) => api.get(`/api/v1/credentials/${id}`),
    create: (data) => api.post('/api/v1/credentials/', data),
    update: (id, data) => api.put(`/api/v1/credentials/${id}`, data),
    delete: (id) => api.delete(`/api/v1/credentials/${id}`)
  }
}

export default api