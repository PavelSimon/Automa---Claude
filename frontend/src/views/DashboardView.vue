<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Dashboard</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Scripts</div>
            <div class="text-h4 text-primary" v-if="!loading">{{ stats.scripts }}</div>
            <v-skeleton-loader v-else type="text" width="60"></v-skeleton-loader>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Active Agents</div>
            <div class="text-h4 text-success" v-if="!loading">{{ stats.activeAgents }}</div>
            <v-skeleton-loader v-else type="text" width="60"></v-skeleton-loader>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Scheduled Jobs</div>
            <div class="text-h4 text-info" v-if="!loading">{{ stats.scheduledJobs }}</div>
            <v-skeleton-loader v-else type="text" width="60"></v-skeleton-loader>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Recent Executions</div>
            <div class="text-h4 text-warning" v-if="!loading">{{ stats.recentExecutions }}</div>
            <v-skeleton-loader v-else type="text" width="60"></v-skeleton-loader>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Recent Activity</v-card-title>
          <v-card-text>
            <v-list v-if="!loading">
              <v-list-item v-for="activity in recentActivity" :key="activity.id">
                <v-list-item-content>
                  <v-list-item-title>{{ activity.action }}</v-list-item-title>
                  <v-list-item-subtitle>{{ activity.timestamp }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
              <v-list-item v-if="recentActivity.length === 0">
                <v-list-item-content>
                  <v-list-item-title class="text-disabled">No recent activity</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>
            <v-skeleton-loader v-else type="list-item-two-line@3"></v-skeleton-loader>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>System Status</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6">
                <div class="text-subtitle2">API Status</div>
                <v-chip color="success" small>Online</v-chip>
              </v-col>
              <v-col cols="6">
                <div class="text-subtitle2">Docker Status</div>
                <v-chip :color="dockerStatus ? 'success' : 'error'" small>
                  {{ dockerStatus ? 'Available' : 'Unavailable' }}
                </v-chip>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/api'
import { formatRelativeTime } from '@/utils/datetime'

const stats = ref({
  scripts: 0,
  activeAgents: 0,
  scheduledJobs: 0,
  recentExecutions: 0
})

const recentActivity = ref([])
const dockerStatus = ref(true)
const loading = ref(false)

const loadDashboardData = async () => {
  loading.value = true
  try {
    // Load scripts count
    const scriptsResponse = await apiService.scripts.list()
    const scripts = scriptsResponse.data

    // Load agents count (and active agents)
    const agentsResponse = await apiService.agents.list()
    const agents = agentsResponse.data
    const activeAgents = agents.filter(agent => agent.status === 'running')

    // Load jobs count (and active jobs)
    const jobsResponse = await apiService.jobs.list()
    const jobs = jobsResponse.data
    const activeJobs = jobs.filter(job => job.is_active)

    // Load recent executions
    const executionsResponse = await apiService.monitoring.executions()
    const executions = executionsResponse.data

    // Update stats
    stats.value = {
      scripts: scripts.length,
      activeAgents: activeAgents.length,
      scheduledJobs: activeJobs.length,
      recentExecutions: executions.length
    }

    // Build recent activity from API data
    const activities = []

    // Add recent script creations
    scripts.slice(-3).forEach(script => {
      activities.push({
        id: `script-${script.id}`,
        action: `Script "${script.name}" created`,
        timestamp: formatRelativeTime(script.created_at)
      })
    })

    // Add recent agent activities
    agents.slice(-2).forEach(agent => {
      activities.push({
        id: `agent-${agent.id}`,
        action: `Agent "${agent.name}" ${agent.status}`,
        timestamp: formatRelativeTime(agent.updated_at || agent.created_at)
      })
    })

    // Add recent executions
    executions.slice(0, 2).forEach(execution => {
      activities.push({
        id: `execution-${execution.id}`,
        action: `Job execution ${execution.status}`,
        timestamp: formatRelativeTime(execution.started_at)
      })
    })

    // Sort by most recent and take first 5
    recentActivity.value = activities
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 5)

  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    // Keep default values on error
  } finally {
    loading.value = false
  }
}


onMounted(async () => {
  await loadDashboardData()
})
</script>