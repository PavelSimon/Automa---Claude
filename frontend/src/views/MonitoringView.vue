<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Monitoring</h1>
      </v-col>
    </v-row>

    <!-- System Status -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>System Status</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6">
                <div class="text-subtitle2 mb-2">API Server</div>
                <v-chip color="success" small>
                  <v-icon left>mdi-check-circle</v-icon>
                  Online
                </v-chip>
              </v-col>
              <v-col cols="6">
                <div class="text-subtitle2 mb-2">Database</div>
                <v-chip color="success" small>
                  <v-icon left>mdi-database</v-icon>
                  Connected
                </v-chip>
              </v-col>
              <v-col cols="6">
                <div class="text-subtitle2 mb-2">Docker</div>
                <v-chip :color="dockerStatus ? 'success' : 'error'" small>
                  <v-icon left>{{ dockerStatus ? 'mdi-docker' : 'mdi-close-circle' }}</v-icon>
                  {{ dockerStatus ? 'Available' : 'Unavailable' }}
                </v-chip>
              </v-col>
              <v-col cols="6">
                <div class="text-subtitle2 mb-2">Scheduler</div>
                <v-chip color="success" small>
                  <v-icon left>mdi-clock</v-icon>
                  Running
                </v-chip>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Resource Usage</v-card-title>
          <v-card-text>
            <div class="mb-3">
              <div class="text-subtitle2">CPU Usage</div>
              <v-progress-linear
                :model-value="resourceUsage.cpu"
                color="primary"
                height="20"
              >
                {{ resourceUsage.cpu }}%
              </v-progress-linear>
            </div>
            <div class="mb-3">
              <div class="text-subtitle2">Memory Usage</div>
              <v-progress-linear
                :model-value="resourceUsage.memory"
                color="warning"
                height="20"
              >
                {{ resourceUsage.memory }}%
              </v-progress-linear>
            </div>
            <div class="mb-3">
              <div class="text-subtitle2">Disk Usage</div>
              <v-progress-linear
                :model-value="resourceUsage.disk"
                color="info"
                height="20"
              >
                {{ resourceUsage.disk }}%
              </v-progress-linear>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Active Agents -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Active Agents</v-card-title>
          <v-data-table
            :headers="agentHeaders"
            :items="activeAgents"
            :loading="loading"
            class="elevation-1"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.status)"
                small
              >
                <v-icon left>{{ getStatusIcon(item.status) }}</v-icon>
                {{ item.status }}
              </v-chip>
            </template>

            <template v-slot:item.last_execution="{ item }">
              {{ item.last_execution ? formatDateTime(item.last_execution) : 'Never' }}
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon
                small
                @click="viewLogs(item)"
                color="info"
              >
                <v-icon>mdi-text-box</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="restartAgent(item)"
                color="warning"
              >
                <v-icon>mdi-restart</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Executions -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Recent Job Executions</v-card-title>
          <v-data-table
            :headers="executionHeaders"
            :items="recentExecutions"
            :loading="loading"
            class="elevation-1"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getExecutionStatusColor(item.status)"
                small
              >
                <v-icon left>{{ getExecutionStatusIcon(item.status) }}</v-icon>
                {{ item.status }}
              </v-chip>
            </template>

            <template v-slot:item.started_at="{ item }">
              {{ formatDateTime(item.started_at) }}
            </template>

            <template v-slot:item.duration="{ item }">
              {{ calculateDuration(item.started_at, item.finished_at) }}
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon
                small
                @click="viewExecutionDetails(item)"
                color="info"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const dockerStatus = ref(true)
const activeAgents = ref([])
const recentExecutions = ref([])
const refreshInterval = ref(null)

const resourceUsage = ref({
  cpu: 25,
  memory: 45,
  disk: 60
})

const agentHeaders = [
  { title: 'Name', key: 'name' },
  { title: 'Status', key: 'status' },
  { title: 'Last Execution', key: 'last_execution' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const executionHeaders = [
  { title: 'Job', key: 'job_name' },
  { title: 'Agent', key: 'agent_name' },
  { title: 'Status', key: 'status' },
  { title: 'Started', key: 'started_at' },
  { title: 'Duration', key: 'duration' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const getStatusColor = (status) => {
  switch (status) {
    case 'running': return 'success'
    case 'stopped': return 'grey'
    case 'error': return 'error'
    default: return 'grey'
  }
}

const getStatusIcon = (status) => {
  switch (status) {
    case 'running': return 'mdi-play-circle'
    case 'stopped': return 'mdi-stop-circle'
    case 'error': return 'mdi-alert-circle'
    default: return 'mdi-help-circle'
  }
}

const getExecutionStatusColor = (status) => {
  switch (status) {
    case 'success': return 'success'
    case 'failed': return 'error'
    case 'running': return 'info'
    case 'timeout': return 'warning'
    default: return 'grey'
  }
}

const getExecutionStatusIcon = (status) => {
  switch (status) {
    case 'success': return 'mdi-check-circle'
    case 'failed': return 'mdi-close-circle'
    case 'running': return 'mdi-loading'
    case 'timeout': return 'mdi-clock-alert'
    default: return 'mdi-help-circle'
  }
}

const loadMonitoringData = async () => {
  loading.value = true
  try {
    // Load active agents
    const agentsResponse = await axios.get('/api/v1/agents?status=running')
    activeAgents.value = agentsResponse.data

    // Load recent executions
    const executionsResponse = await axios.get('/api/v1/executions/recent')
    recentExecutions.value = executionsResponse.data

    // Check Docker status
    try {
      await axios.get('/api/v1/monitoring/docker')
      dockerStatus.value = true
    } catch {
      dockerStatus.value = false
    }

    // Simulate resource usage (in real app, this would come from system monitoring)
    resourceUsage.value = {
      cpu: Math.floor(Math.random() * 50) + 10,
      memory: Math.floor(Math.random() * 60) + 20,
      disk: Math.floor(Math.random() * 40) + 40
    }
  } catch (error) {
    console.error('Failed to load monitoring data:', error)
    // Use mock data for demonstration
    activeAgents.value = [
      {
        id: 1,
        name: 'Email Processor',
        status: 'running',
        last_execution: new Date().toISOString()
      },
      {
        id: 2,
        name: 'Data Sync Agent',
        status: 'running',
        last_execution: new Date(Date.now() - 3600000).toISOString()
      }
    ]

    recentExecutions.value = [
      {
        id: 1,
        job_name: 'Daily Report',
        agent_name: 'Email Processor',
        status: 'success',
        started_at: new Date(Date.now() - 1800000).toISOString(),
        finished_at: new Date(Date.now() - 1700000).toISOString()
      },
      {
        id: 2,
        job_name: 'Data Backup',
        agent_name: 'Data Sync Agent',
        status: 'failed',
        started_at: new Date(Date.now() - 7200000).toISOString(),
        finished_at: new Date(Date.now() - 7100000).toISOString()
      }
    ]
  } finally {
    loading.value = false
  }
}

const viewLogs = (agent) => {
  console.log(`Viewing logs for agent: ${agent.name}`)
  // TODO: Implement logs viewer
}

const restartAgent = async (agent) => {
  try {
    await axios.post(`/api/v1/agents/${agent.id}/restart`)
    await loadMonitoringData()
  } catch (error) {
    console.error('Failed to restart agent:', error)
  }
}

const viewExecutionDetails = (execution) => {
  console.log(`Viewing details for execution: ${execution.id}`)
  // TODO: Implement execution details dialog
}

const calculateDuration = (start, end) => {
  if (!start || !end) return 'N/A'
  const duration = new Date(end) - new Date(start)
  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) return `${hours}h ${minutes % 60}m`
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`
  return `${seconds}s`
}

const formatDateTime = (dateString) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  loadMonitoringData()
  // Refresh data every 30 seconds
  refreshInterval.value = setInterval(loadMonitoringData, 30000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})
</script>