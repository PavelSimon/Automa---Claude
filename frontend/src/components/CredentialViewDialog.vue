<template>
  <v-dialog v-model="dialog" max-width="600">
    <v-card v-if="credential">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-eye</v-icon>
        {{ credential.name }}
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-6">
        <!-- Basic Information -->
        <v-row>
          <v-col cols="6">
            <div class="text-subtitle-2 text-grey mb-1">Type</div>
            <v-chip :color="getTypeColor(credential.credential_type)" variant="tonal">
              <v-icon start>{{ getTypeIcon(credential.credential_type) }}</v-icon>
              {{ getTypeDisplayName(credential.credential_type) }}
            </v-chip>
          </v-col>
          <v-col cols="6">
            <div class="text-subtitle-2 text-grey mb-1">Status</div>
            <v-chip :color="credential.is_active ? 'success' : 'warning'" variant="tonal">
              {{ credential.is_active ? 'Active' : 'Inactive' }}
            </v-chip>
          </v-col>
        </v-row>

        <v-row v-if="credential.description">
          <v-col cols="12">
            <div class="text-subtitle-2 text-grey mb-1">Description</div>
            <div>{{ credential.description }}</div>
          </v-col>
        </v-row>

        <v-row v-if="credential.tags && credential.tags.length">
          <v-col cols="12">
            <div class="text-subtitle-2 text-grey mb-1">Tags</div>
            <v-chip
              v-for="tag in credential.tags"
              :key="tag"
              size="small"
              class="mr-1 mb-1"
              variant="outlined"
            >
              {{ tag }}
            </v-chip>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="6">
            <div class="text-subtitle-2 text-grey mb-1">Created</div>
            <div>{{ formatDateTime(credential.created_at) }}</div>
          </v-col>
          <v-col cols="6">
            <div class="text-subtitle-2 text-grey mb-1">Last Used</div>
            <div>{{ credential.last_used_at ? formatDateTime(credential.last_used_at) : 'Never' }}</div>
          </v-col>
        </v-row>

        <v-row v-if="credential.expires_at">
          <v-col cols="12">
            <div class="text-subtitle-2 text-grey mb-1">Expires</div>
            <div :class="getExpiryClass(credential.expires_at)">
              {{ formatDateTime(credential.expires_at) }}
            </div>
          </v-col>
        </v-row>

        <!-- Decrypt Section -->
        <v-divider class="my-4" />
        <div class="d-flex align-center mb-4">
          <h3>Credential Data</h3>
          <v-spacer />
          <v-btn
            v-if="!decryptedData"
            color="primary"
            variant="outlined"
            @click="showDecryptForm = true"
          >
            <v-icon start>mdi-lock-open</v-icon>
            Decrypt
          </v-btn>
        </div>

        <!-- Decrypt Form -->
        <v-expand-transition>
          <v-card v-if="showDecryptForm && !decryptedData" variant="outlined" class="mb-4">
            <v-card-text>
              <v-text-field
                v-model="userPassword"
                label="Your Login Password"
                type="password"
                variant="outlined"
                density="compact"
                :error-messages="decryptError"
              />
              <div class="d-flex justify-end mt-2">
                <v-btn @click="cancelDecrypt" class="mr-2">Cancel</v-btn>
                <v-btn
                  color="primary"
                  :loading="decrypting"
                  :disabled="!userPassword"
                  @click="decryptCredential"
                >
                  Decrypt
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-expand-transition>

        <!-- Decrypted Data Display -->
        <div v-if="decryptedData">
          <v-alert color="warning" variant="tonal" class="mb-4">
            <v-icon start>mdi-shield-alert</v-icon>
            Sensitive data is displayed. Handle with care.
          </v-alert>

          <v-card variant="outlined">
            <v-card-text>
              <pre class="text-body-2">{{ JSON.stringify(decryptedData.masked_data, null, 2) }}</pre>
            </v-card-text>
            <v-card-actions>
              <v-btn
                color="primary"
                variant="text"
                @click="showFullData = !showFullData"
              >
                {{ showFullData ? 'Hide' : 'Show' }} Full Data
              </v-btn>
              <v-btn
                color="warning"
                variant="text"
                @click="clearDecryptedData"
              >
                Clear
              </v-btn>
            </v-card-actions>
          </v-card>

          <!-- Full data display -->
          <v-expand-transition>
            <v-card v-if="showFullData" variant="outlined" class="mt-2">
              <v-card-title class="text-error">
                <v-icon start>mdi-alert</v-icon>
                Full Credential Data (Unmasked)
              </v-card-title>
              <v-card-text>
                <pre class="text-body-2">{{ JSON.stringify(decryptedData.credential_data, null, 2) }}</pre>
              </v-card-text>
            </v-card>
          </v-expand-transition>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-btn @click="$emit('test', credential)" color="primary" variant="outlined">
          <v-icon start>mdi-test-tube</v-icon>
          Test
        </v-btn>
        <v-spacer />
        <v-btn @click="closeDialog">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { formatDateTime } from '@/utils/datetime'

const props = defineProps({
  modelValue: Boolean,
  credential: Object
})

const emit = defineEmits(['update:modelValue', 'test'])

// Dialog state
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Decrypt state
const showDecryptForm = ref(false)
const userPassword = ref('')
const decrypting = ref(false)
const decryptError = ref('')
const decryptedData = ref(null)
const showFullData = ref(false)

// Watch dialog changes
watch(dialog, (isOpen) => {
  if (!isOpen) {
    clearDecryptedData()
    showDecryptForm.value = false
    userPassword.value = ''
    decryptError.value = ''
  }
})

const decryptCredential = async () => {
  decrypting.value = true
  decryptError.value = ''

  try {
    const response = await axios.post(
      `/api/v1/credentials/${props.credential.id}/decrypt`,
      { user_password: userPassword.value }
    )

    decryptedData.value = response.data
    showDecryptForm.value = false
    userPassword.value = ''
  } catch (error) {
    decryptError.value = error.response?.data?.detail || 'Failed to decrypt credential'
  } finally {
    decrypting.value = false
  }
}

const cancelDecrypt = () => {
  showDecryptForm.value = false
  userPassword.value = ''
  decryptError.value = ''
}

const clearDecryptedData = () => {
  decryptedData.value = null
  showFullData.value = false
}

const closeDialog = () => {
  dialog.value = false
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
  const typeNames = {
    api_key: 'API Key',
    user_pass: 'Username/Password',
    oauth: 'OAuth Token',
    ssh_key: 'SSH Key',
    db_connection: 'Database Connection',
    custom: 'Custom'
  }
  return typeNames[type] || type
}

const getExpiryClass = (expiryDate) => {
  const now = new Date()
  const expiry = new Date(expiryDate)
  const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24)

  if (daysUntilExpiry < 0) return 'text-error'
  if (daysUntilExpiry < 7) return 'text-warning'
  return 'text-success'
}
</script>