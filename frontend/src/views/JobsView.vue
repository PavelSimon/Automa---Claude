<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Scheduled Jobs</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="showCreateDialog = true">
              <v-icon left>mdi-plus</v-icon>
              New Job
            </v-btn>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="jobs"
            :loading="loading"
            class="elevation-1"
          >
            <template v-slot:item.schedule_type="{ item }">
              <v-chip :color="getScheduleColor(item.schedule_type)" small>
                {{ item.schedule_type }}
              </v-chip>
            </template>

            <template v-slot:item.is_active="{ item }">
              <v-icon :color="item.is_active ? 'success' : 'error'">
                {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </v-icon>
            </template>

            <template v-slot:item.next_run="{ item }">
              {{ item.next_run ? formatDateTime(item.next_run) : 'N/A' }}
            </template>

            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon
                small
                @click="executeJob(item)"
                color="success"
              >
                <v-icon>mdi-play</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="editJob(item)"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="viewExecutions(item)"
                color="info"
              >
                <v-icon>mdi-history</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="deleteJob(item)"
                color="error"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ editingJob ? 'Edit Job' : 'Create New Job' }}
        </v-card-title>

        <v-card-text>
          <v-form @submit.prevent="saveJob">
            <v-text-field
              v-model="jobForm.name"
              label="Job Name"
              required
            ></v-text-field>

            <v-select
              v-model="jobForm.agent_id"
              :items="agents"
              item-title="name"
              item-value="id"
              label="Agent"
              required
            ></v-select>

            <v-select
              v-model="jobForm.schedule_type"
              :items="scheduleTypes"
              label="Schedule Type"
              required
              @update:model-value="onScheduleTypeChange"
            ></v-select>

            <v-text-field
              v-if="jobForm.schedule_type === 'cron'"
              v-model="jobForm.cron_expression"
              label="Cron Expression"
              placeholder="0 0 * * *"
              hint="Format: minute hour day month day-of-week"
            ></v-text-field>

            <v-text-field
              v-if="jobForm.schedule_type === 'interval'"
              v-model.number="jobForm.interval_seconds"
              label="Interval (seconds)"
              type="number"
              min="60"
            ></v-text-field>

            <v-switch
              v-model="jobForm.is_active"
              label="Active"
            ></v-switch>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveJob" :loading="saving">
            {{ editingJob ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const jobs = ref([])
const agents = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingJob = ref(null)

const jobForm = ref({
  name: '',
  agent_id: null,
  schedule_type: 'once',
  cron_expression: '',
  interval_seconds: 3600,
  is_active: true
})

const scheduleTypes = [
  { title: 'Once', value: 'once' },
  { title: 'Interval', value: 'interval' },
  { title: 'Cron', value: 'cron' }
]

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Agent', key: 'agent_name' },
  { title: 'Schedule', key: 'schedule_type' },
  { title: 'Next Run', key: 'next_run' },
  { title: 'Active', key: 'is_active' },
  { title: 'Created', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const getScheduleColor = (type) => {
  switch (type) {
    case 'once': return 'blue'
    case 'interval': return 'green'
    case 'cron': return 'purple'
    default: return 'grey'
  }
}

const onScheduleTypeChange = () => {
  if (jobForm.value.schedule_type === 'once') {
    jobForm.value.cron_expression = ''
    jobForm.value.interval_seconds = null
  } else if (jobForm.value.schedule_type === 'interval') {
    jobForm.value.cron_expression = ''
    jobForm.value.interval_seconds = jobForm.value.interval_seconds || 3600
  } else if (jobForm.value.schedule_type === 'cron') {
    jobForm.value.interval_seconds = null
    jobForm.value.cron_expression = jobForm.value.cron_expression || '0 0 * * *'
  }
}

const loadJobs = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/jobs')
    jobs.value = response.data
  } catch (error) {
    console.error('Failed to load jobs:', error)
  } finally {
    loading.value = false
  }
}

const loadAgents = async () => {
  try {
    const response = await axios.get('/api/v1/agents')
    agents.value = response.data
  } catch (error) {
    console.error('Failed to load agents:', error)
  }
}

const saveJob = async () => {
  saving.value = true
  try {
    if (editingJob.value) {
      await axios.put(`/api/v1/jobs/${editingJob.value.id}`, jobForm.value)
    } else {
      await axios.post('/api/v1/jobs', jobForm.value)
    }
    await loadJobs()
    closeDialog()
  } catch (error) {
    console.error('Failed to save job:', error)
  } finally {
    saving.value = false
  }
}

const executeJob = async (job) => {
  try {
    await axios.post(`/api/v1/jobs/${job.id}/execute`)
    console.log(`Job "${job.name}" executed`)
  } catch (error) {
    console.error('Failed to execute job:', error)
  }
}

const editJob = (job) => {
  editingJob.value = job
  jobForm.value = {
    name: job.name,
    agent_id: job.agent_id,
    schedule_type: job.schedule_type,
    cron_expression: job.cron_expression || '',
    interval_seconds: job.interval_seconds,
    is_active: job.is_active
  }
  showCreateDialog.value = true
}

const viewExecutions = (job) => {
  console.log(`Viewing executions for job: ${job.name}`)
  // TODO: Implement executions view
}

const deleteJob = async (job) => {
  if (confirm(`Are you sure you want to delete "${job.name}"?`)) {
    try {
      await axios.delete(`/api/v1/jobs/${job.id}`)
      await loadJobs()
    } catch (error) {
      console.error('Failed to delete job:', error)
    }
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingJob.value = null
  jobForm.value = {
    name: '',
    agent_id: null,
    schedule_type: 'once',
    cron_expression: '',
    interval_seconds: 3600,
    is_active: true
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const formatDateTime = (dateString) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  loadJobs()
  loadAgents()
})
</script>