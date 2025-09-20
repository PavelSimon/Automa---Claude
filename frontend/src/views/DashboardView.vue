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
            <div class="text-h4 text-primary">{{ stats.scripts }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Active Agents</div>
            <div class="text-h4 text-success">{{ stats.activeAgents }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Scheduled Jobs</div>
            <div class="text-h4 text-info">{{ stats.scheduledJobs }}</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card>
          <v-card-text>
            <div class="text-h6">Recent Executions</div>
            <div class="text-h4 text-warning">{{ stats.recentExecutions }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Recent Activity</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item v-for="activity in recentActivity" :key="activity.id">
                <v-list-item-content>
                  <v-list-item-title>{{ activity.action }}</v-list-item-title>
                  <v-list-item-subtitle>{{ activity.timestamp }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
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

const stats = ref({
  scripts: 0,
  activeAgents: 0,
  scheduledJobs: 0,
  recentExecutions: 0
})

const recentActivity = ref([
  { id: 1, action: 'Script "data_processor.py" created', timestamp: '2 minutes ago' },
  { id: 2, action: 'Agent "Email Scheduler" started', timestamp: '15 minutes ago' },
  { id: 3, action: 'Job "Daily Report" executed successfully', timestamp: '1 hour ago' },
])

const dockerStatus = ref(true)

onMounted(async () => {
  // Load dashboard data
  // This would typically fetch from API endpoints
  stats.value = {
    scripts: 5,
    activeAgents: 2,
    scheduledJobs: 8,
    recentExecutions: 15
  }
})
</script>