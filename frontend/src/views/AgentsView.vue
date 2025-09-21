<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Agents</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="showCreateDialog = true">
              <v-icon left>mdi-plus</v-icon>
              New Agent
            </v-btn>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="agents"
            :loading="loading"
            class="elevation-1"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.status)"
                small
              >
                {{ item.status }}
              </v-chip>
            </template>

            <template v-slot:item.is_active="{ item }">
              <v-icon :color="item.is_active ? 'success' : 'error'">
                {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </v-icon>
            </template>

            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon
                small
                @click="startAgent(item)"
                :disabled="item.status === 'running'"
                color="success"
              >
                <v-icon>mdi-play</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="stopAgent(item)"
                :disabled="item.status === 'stopped'"
                color="warning"
              >
                <v-icon>mdi-stop</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="editAgent(item)"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="deleteAgent(item)"
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
          {{ editingAgent ? 'Edit Agent' : 'Create New Agent' }}
        </v-card-title>

        <v-card-text>
          <v-form @submit.prevent="saveAgent">
            <v-text-field
              v-model="agentForm.name"
              label="Agent Name"
              required
            ></v-text-field>

            <v-textarea
              v-model="agentForm.description"
              label="Description"
              rows="3"
            ></v-textarea>

            <v-select
              v-model="agentForm.script_id"
              :items="scripts"
              item-title="name"
              item-value="id"
              label="Script"
              required
            ></v-select>

            <v-switch
              v-model="agentForm.is_active"
              label="Active"
            ></v-switch>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveAgent" :loading="saving">
            {{ editingAgent ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiService } from '@/services/api'
import { formatDate } from '@/utils/datetime'

const agents = ref([])
const scripts = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingAgent = ref(null)

const agentForm = ref({
  name: '',
  description: '',
  script_id: null,
  is_active: true
})

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Description', key: 'description' },
  { title: 'Status', key: 'status' },
  { title: 'Active', key: 'is_active' },
  { title: 'Created', key: 'created_at' },
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

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await apiService.agents.list()
    agents.value = response.data
  } catch (error) {
    console.error('Failed to load agents:', error)
  } finally {
    loading.value = false
  }
}

const loadScripts = async () => {
  try {
    const response = await apiService.scripts.list()
    scripts.value = response.data
  } catch (error) {
    console.error('Failed to load scripts:', error)
  }
}

const saveAgent = async () => {
  saving.value = true
  try {
    if (editingAgent.value) {
      await apiService.agents.update(editingAgent.value.id, agentForm.value)
    } else {
      await apiService.agents.create(agentForm.value)
    }
    await loadAgents()
    closeDialog()
  } catch (error) {
    console.error('Failed to save agent:', error)
  } finally {
    saving.value = false
  }
}

const startAgent = async (agent) => {
  try {
    await apiService.agents.start(agent.id)
    await loadAgents()
  } catch (error) {
    console.error('Failed to start agent:', error)
  }
}

const stopAgent = async (agent) => {
  try {
    await apiService.agents.stop(agent.id)
    await loadAgents()
  } catch (error) {
    console.error('Failed to stop agent:', error)
  }
}

const editAgent = (agent) => {
  editingAgent.value = agent
  agentForm.value = {
    name: agent.name,
    description: agent.description || '',
    script_id: agent.script_id,
    is_active: agent.is_active
  }
  showCreateDialog.value = true
}

const deleteAgent = async (agent) => {
  if (confirm(`Are you sure you want to delete "${agent.name}"?`)) {
    try {
      await apiService.agents.delete(agent.id)
      await loadAgents()
    } catch (error) {
      console.error('Failed to delete agent:', error)
    }
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingAgent.value = null
  agentForm.value = {
    name: '',
    description: '',
    script_id: null,
    is_active: true
  }
}


onMounted(() => {
  loadAgents()
  loadScripts()
})
</script>