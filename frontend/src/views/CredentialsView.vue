<template>
  <div>
    <v-container fluid>
      <div class="d-flex justify-space-between align-center mb-4">
        <h1 class="text-h4">Credentials</h1>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          New Credential
        </v-btn>
      </div>

      <!-- Filters and Search -->
      <v-card class="mb-4">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="search"
                prepend-inner-icon="mdi-magnify"
                label="Search credentials"
                variant="outlined"
                density="compact"
                clearable
                @input="loadCredentials"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-select
                v-model="typeFilter"
                :items="credentialTypes"
                item-title="display_name"
                item-value="name"
                label="Filter by type"
                variant="outlined"
                density="compact"
                clearable
                @update:model-value="loadCredentials"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-combobox
                v-model="tagFilter"
                :items="availableTags"
                label="Filter by tags"
                variant="outlined"
                density="compact"
                multiple
                chips
                clearable
                @update:model-value="loadCredentials"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Credentials List -->
      <v-card>
        <v-data-table
          :headers="headers"
          :items="credentials"
          :loading="loading"
          item-key="id"
          :items-per-page="25"
        >
          <template v-slot:item.credential_type="{ item }">
            <v-chip :color="getTypeColor(item.credential_type)" variant="tonal" size="small">
              <v-icon start>{{ getTypeIcon(item.credential_type) }}</v-icon>
              {{ getTypeDisplayName(item.credential_type) }}
            </v-chip>
          </template>

          <template v-slot:item.tags="{ item }">
            <v-chip
              v-for="tag in item.tags"
              :key="tag"
              size="x-small"
              class="mr-1"
              variant="outlined"
            >
              {{ tag }}
            </v-chip>
          </template>

          <template v-slot:item.expires_at="{ item }">
            <span v-if="item.expires_at" :class="getExpiryClass(item.expires_at)">
              {{ formatDateTime(item.expires_at) }}
            </span>
            <span v-else class="text-grey">Never</span>
          </template>

          <template v-slot:item.is_active="{ item }">
            <v-chip :color="item.is_active ? 'success' : 'warning'" variant="tonal" size="small">
              {{ item.is_active ? 'Active' : 'Inactive' }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <v-menu>
              <template v-slot:activator="{ props }">
                <v-btn
                  icon="mdi-dots-vertical"
                  size="small"
                  variant="text"
                  v-bind="props"
                />
              </template>
              <v-list>
                <v-list-item @click="viewCredential(item)">
                  <v-list-item-title>
                    <v-icon start>mdi-eye</v-icon>
                    View
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="editCredential(item)">
                  <v-list-item-title>
                    <v-icon start>mdi-pencil</v-icon>
                    Edit
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="testCredential(item)">
                  <v-list-item-title>
                    <v-icon start>mdi-test-tube</v-icon>
                    Test
                  </v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="deleteCredential(item)" class="text-error">
                  <v-list-item-title>
                    <v-icon start>mdi-delete</v-icon>
                    Delete
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </template>
        </v-data-table>
      </v-card>
    </v-container>

    <!-- Create/Edit Dialog -->
    <CredentialDialog
      v-model="dialogOpen"
      :credential="selectedCredential"
      :credential-types="credentialTypes"
      @saved="onCredentialSaved"
    />

    <!-- View Dialog -->
    <CredentialViewDialog
      v-model="viewDialogOpen"
      :credential="selectedCredential"
      @test="testCredential"
    />

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialogOpen" max-width="400">
      <v-card>
        <v-card-title>Delete Credential</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ selectedCredential?.name }}"?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="deleteDialogOpen = false">Cancel</v-btn>
          <v-btn color="error" @click="confirmDelete" :loading="deleting">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Test Dialog -->
    <CredentialTestDialog
      v-model="testDialogOpen"
      :credential="selectedCredential"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { formatDateTime } from '@/utils/datetime'
import CredentialDialog from '@/components/CredentialDialog.vue'
import CredentialViewDialog from '@/components/CredentialViewDialog.vue'
import CredentialTestDialog from '@/components/CredentialTestDialog.vue'

const router = useRouter()

// Data
const credentials = ref([])
const credentialTypes = ref([])
const loading = ref(false)
const search = ref('')
const typeFilter = ref(null)
const tagFilter = ref([])
const availableTags = ref([])

// Dialog states
const dialogOpen = ref(false)
const viewDialogOpen = ref(false)
const deleteDialogOpen = ref(false)
const testDialogOpen = ref(false)
const selectedCredential = ref(null)
const deleting = ref(false)

// Table headers
const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Type', key: 'credential_type', sortable: true },
  { title: 'Tags', key: 'tags', sortable: false },
  { title: 'Expires', key: 'expires_at', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Created', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, width: '80' }
]

// Methods
const loadCredentials = async () => {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (typeFilter.value) params.credential_type = typeFilter.value
    if (tagFilter.value?.length) params.tags = tagFilter.value

    const response = await api.get('/api/v1/credentials/', { params })
    credentials.value = response.data

    // Extract unique tags
    const tags = new Set()
    credentials.value.forEach(cred => {
      if (cred.tags) {
        cred.tags.forEach(tag => tags.add(tag))
      }
    })
    availableTags.value = Array.from(tags).sort()

  } catch (error) {
    console.error('Failed to load credentials:', error)
  } finally {
    loading.value = false
  }
}

const loadCredentialTypes = async () => {
  try {
    const response = await api.get('/api/v1/credentials/types/')
    credentialTypes.value = response.data
  } catch (error) {
    console.error('Failed to load credential types:', error)
  }
}

const openCreateDialog = () => {
  selectedCredential.value = null
  dialogOpen.value = true
}

const viewCredential = (credential) => {
  selectedCredential.value = credential
  viewDialogOpen.value = true
}

const editCredential = (credential) => {
  selectedCredential.value = credential
  dialogOpen.value = true
}

const testCredential = (credential) => {
  selectedCredential.value = credential
  testDialogOpen.value = true
}

const deleteCredential = (credential) => {
  selectedCredential.value = credential
  deleteDialogOpen.value = true
}

const confirmDelete = async () => {
  deleting.value = true
  try {
    await api.delete(`/api/v1/credentials/${selectedCredential.value.id}`)
    await loadCredentials()
    deleteDialogOpen.value = false
  } catch (error) {
    console.error('Failed to delete credential:', error)
    // TODO: Show error toast
  } finally {
    deleting.value = false
  }
}

const onCredentialSaved = () => {
  loadCredentials()
  dialogOpen.value = false
}

// Utility functions
const getTypeColor = (type) => {
  const colors = {
    api_key: 'blue',
    user_pass: 'green',
    oauth: 'orange',
    ssh_key: 'purple',
    db_connection: 'red',
    custom: 'grey'
  }
  return colors[type] || 'grey'
}

const getTypeIcon = (type) => {
  const icons = {
    api_key: 'mdi-key',
    user_pass: 'mdi-account-key',
    oauth: 'mdi-shield-key',
    ssh_key: 'mdi-console',
    db_connection: 'mdi-database-key',
    custom: 'mdi-cog'
  }
  return icons[type] || 'mdi-help'
}

const getTypeDisplayName = (type) => {
  const typeObj = credentialTypes.value.find(t => t.name === type)
  return typeObj?.display_name || type
}

const getExpiryClass = (expiryDate) => {
  const now = new Date()
  const expiry = new Date(expiryDate)
  const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)

  if (daysUntilExpiry < 0) return 'text-error'
  if (daysUntilExpiry < 7) return 'text-warning'
  return 'text-success'
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadCredentials(),
    loadCredentialTypes()
  ])
})
</script>