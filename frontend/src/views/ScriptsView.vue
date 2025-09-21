<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Scripts</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="showCreateDialog = true">
              <v-icon left>mdi-plus</v-icon>
              New Script
            </v-btn>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="scripts"
            :loading="loading"
            class="elevation-1"
          >
            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>

            <template v-slot:item.actions="{ item }">
              <v-btn
                icon
                small
                @click="editScript(item)"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn
                icon
                small
                @click="deleteScript(item)"
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
          {{ editingScript ? 'Edit Script' : 'Create New Script' }}
        </v-card-title>

        <v-card-text>
          <v-form @submit.prevent="saveScript">
            <v-text-field
              v-model="scriptForm.name"
              label="Script Name"
              required
            ></v-text-field>

            <v-textarea
              v-model="scriptForm.description"
              label="Description"
              rows="3"
            ></v-textarea>

            <v-textarea
              v-model="scriptForm.content"
              label="Python Code"
              rows="10"
              placeholder="# Enter your Python code here"
            ></v-textarea>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveScript" :loading="saving">
            {{ editingScript ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { formatDate } from '@/utils/datetime'

const scripts = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingScript = ref(null)

const scriptForm = ref({
  name: '',
  description: '',
  content: ''
})

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Description', key: 'description' },
  { title: 'Created', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const loadScripts = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/scripts/')
    scripts.value = response.data
  } catch (error) {
    console.error('Failed to load scripts:', error)
  } finally {
    loading.value = false
  }
}

const saveScript = async () => {
  saving.value = true
  try {
    if (editingScript.value) {
      await axios.put(`/api/v1/scripts/${editingScript.value.id}`, scriptForm.value)
    } else {
      await axios.post('/api/v1/scripts/', scriptForm.value)
    }
    await loadScripts()
    closeDialog()
  } catch (error) {
    console.error('Failed to save script:', error)
  } finally {
    saving.value = false
  }
}

const editScript = (script) => {
  editingScript.value = script
  scriptForm.value = {
    name: script.name,
    description: script.description || '',
    content: script.content || ''
  }
  showCreateDialog.value = true
}

const deleteScript = async (script) => {
  if (confirm(`Are you sure you want to delete "${script.name}"?`)) {
    try {
      await axios.delete(`/api/v1/scripts/${script.id}`)
      await loadScripts()
    } catch (error) {
      console.error('Failed to delete script:', error)
    }
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingScript.value = null
  scriptForm.value = {
    name: '',
    description: '',
    content: ''
  }
}


onMounted(() => {
  loadScripts()
})
</script>