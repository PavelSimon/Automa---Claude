/**
 * WebSocket Store
 *
 * Manages WebSocket connection for real-time updates from the backend.
 * Handles agent status changes, job execution completions, and system metrics.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
  // State
  const socket = ref(null)
  const connected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000 // 3 seconds
  const messages = ref([])

  // Computed
  const isConnected = computed(() => connected.value)

  // Actions
  function connect() {
    if (socket.value?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    try {
      // Use relative URL to leverage Vite proxy in development
      // In production, this will be resolved to the actual host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host // includes port (e.g., 192.168.1.40:8002)
      const wsUrl = `${protocol}//${host}/ws`

      console.log('Connecting to WebSocket:', wsUrl)
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        connected.value = true
        reconnectAttempts.value = 0
        console.log('WebSocket connected')
      }

      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      socket.value.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      socket.value.onclose = () => {
        connected.value = false
        console.log('WebSocket disconnected')
        attemptReconnect()
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
    }
  }

  function disconnect() {
    if (socket.value) {
      socket.value.close()
      socket.value = null
      connected.value = false
    }
  }

  function attemptReconnect() {
    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++
      console.log(`Attempting to reconnect (${reconnectAttempts.value}/${maxReconnectAttempts})...`)

      setTimeout(() => {
        connect()
      }, reconnectDelay)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  function handleMessage(message) {
    messages.value.push(message)

    // Keep only last 100 messages
    if (messages.value.length > 100) {
      messages.value.shift()
    }

    // Dispatch to specific handlers based on message type
    switch (message.type) {
      case 'connected':
        console.log('WebSocket connection confirmed:', message.message)
        break

      case 'agent_status_change':
        handleAgentStatusChange(message.data)
        break

      case 'job_execution_complete':
        handleJobExecutionComplete(message.data)
        break

      case 'system_metrics':
        handleSystemMetrics(message.data)
        break

      default:
        console.log('Unknown message type:', message.type)
    }
  }

  function handleAgentStatusChange(data) {
    console.log('Agent status changed:', data)
    // Emit event that can be listened to by components
    window.dispatchEvent(new CustomEvent('agent-status-change', { detail: data }))
  }

  function handleJobExecutionComplete(data) {
    console.log('Job execution complete:', data)
    // Emit event that can be listened to by components
    window.dispatchEvent(new CustomEvent('job-execution-complete', { detail: data }))
  }

  function handleSystemMetrics(data) {
    console.log('System metrics update:', data)
    // Emit event that can be listened to by components
    window.dispatchEvent(new CustomEvent('system-metrics-update', { detail: data }))
  }

  function send(message) {
    if (socket.value?.readyState === WebSocket.OPEN) {
      socket.value.send(JSON.stringify(message))
    } else {
      console.error('Cannot send message: WebSocket not connected')
    }
  }

  // Start keepalive ping
  let pingInterval = null

  function startKeepalive() {
    if (pingInterval) return

    pingInterval = setInterval(() => {
      if (socket.value?.readyState === WebSocket.OPEN) {
        socket.value.send('ping')
      }
    }, 30000) // Ping every 30 seconds
  }

  function stopKeepalive() {
    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }
  }

  return {
    // State
    connected,
    isConnected,
    messages,

    // Actions
    connect,
    disconnect,
    send,
    startKeepalive,
    stopKeepalive
  }
})
