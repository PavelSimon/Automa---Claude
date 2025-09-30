<template>
  <v-dialog v-model="dialog" max-width="800" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-key-variant</v-icon>
        {{ isEditing ? 'Edit Credential' : 'New Credential' }}
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-6">
        <v-form ref="form" v-model="valid">
          <!-- Basic Information -->
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.name"
                label="Name"
                :rules="[v => !!v || 'Name is required']"
                variant="outlined"
                required
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="formData.credential_type"
                :items="credentialTypes"
                item-title="display_name"
                item-value="name"
                label="Type"
                :rules="[v => !!v || 'Type is required']"
                variant="outlined"
                required
                :disabled="isEditing"
                @update:model-value="onTypeChange"
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12">
              <v-textarea
                v-model="formData.description"
                label="Description"
                variant="outlined"
                rows="2"
              />
            </v-col>
          </v-row>

          <!-- Tags -->
          <v-row>
            <v-col cols="12" md="6">
              <v-combobox
                v-model="formData.tags"
                label="Tags"
                variant="outlined"
                multiple
                chips
                closable-chips
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.expires_at"
                label="Expires At (optional)"
                variant="outlined"
                type="datetime-local"
              />
            </v-col>
          </v-row>

          <!-- Type-specific credential data -->
          <v-divider class="my-4" />
          <h3 class="mb-4">Credential Data</h3>

          <!-- API Key -->
          <div v-if="formData.credential_type === 'api_key'">
            <v-text-field
              v-model="credentialData.api_key"
              label="API Key"
              :rules="[v => !!v || 'API Key is required']"
              variant="outlined"
              :type="showApiKey ? 'text' : 'password'"
              :append-inner-icon="showApiKey ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showApiKey = !showApiKey"
              required
            />
            <v-text-field
              v-model="credentialData.base_url"
              label="Base URL (optional)"
              variant="outlined"
            />
            <v-textarea
              v-model="headersText"
              label="Headers (JSON format, optional)"
              variant="outlined"
              rows="3"
              placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json"}'
            />
          </div>

          <!-- Username/Password -->
          <div v-if="formData.credential_type === 'user_pass'">
            <v-text-field
              v-model="credentialData.username"
              label="Username"
              :rules="[v => !!v || 'Username is required']"
              variant="outlined"
              required
            />
            <v-text-field
              v-model="credentialData.password"
              label="Password"
              :rules="[v => !!v || 'Password is required']"
              variant="outlined"
              :type="showPassword ? 'text' : 'password'"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              required
            />
            <v-text-field
              v-model="credentialData.domain"
              label="Domain (optional)"
              variant="outlined"
            />
          </div>

          <!-- OAuth -->
          <div v-if="formData.credential_type === 'oauth'">
            <v-text-field
              v-model="credentialData.access_token"
              label="Access Token"
              :rules="[v => !!v || 'Access Token is required']"
              variant="outlined"
              :type="showAccessToken ? 'text' : 'password'"
              :append-inner-icon="showAccessToken ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showAccessToken = !showAccessToken"
              required
            />
            <v-text-field
              v-model="credentialData.refresh_token"
              label="Refresh Token (optional)"
              variant="outlined"
              :type="showRefreshToken ? 'text' : 'password'"
              :append-inner-icon="showRefreshToken ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showRefreshToken = !showRefreshToken"
            />
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="credentialData.token_type"
                  label="Token Type (optional)"
                  variant="outlined"
                  placeholder="Bearer"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="credentialData.expires_in"
                  label="Expires In (seconds, optional)"
                  variant="outlined"
                  type="number"
                />
              </v-col>
            </v-row>
          </div>

          <!-- SSH Key -->
          <div v-if="formData.credential_type === 'ssh_key'">
            <v-textarea
              v-model="credentialData.private_key"
              label="Private Key"
              :rules="[v => !!v || 'Private Key is required']"
              variant="outlined"
              rows="8"
              required
            />
            <v-textarea
              v-model="credentialData.public_key"
              label="Public Key (optional)"
              variant="outlined"
              rows="3"
            />
            <v-text-field
              v-model="credentialData.passphrase"
              label="Passphrase (optional)"
              variant="outlined"
              :type="showPassphrase ? 'text' : 'password'"
              :append-inner-icon="showPassphrase ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassphrase = !showPassphrase"
            />
          </div>

          <!-- Database Connection -->
          <div v-if="formData.credential_type === 'db_connection'">
            <v-text-field
              v-model="credentialData.connection_string"
              label="Connection String"
              :rules="[v => !!v || 'Connection String is required']"
              variant="outlined"
              required
            />
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="credentialData.username"
                  label="Username (optional)"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="credentialData.password"
                  label="Password (optional)"
                  variant="outlined"
                  :type="showDbPassword ? 'text' : 'password'"
                  :append-inner-icon="showDbPassword ? 'mdi-eye-off' : 'mdi-eye'"
                  @click:append-inner="showDbPassword = !showDbPassword"
                />
              </v-col>
            </v-row>
            <v-text-field
              v-model="credentialData.database"
              label="Database (optional)"
              variant="outlined"
            />
          </div>

          <!-- Custom -->
          <div v-if="formData.credential_type === 'custom'">
            <v-textarea
              v-model="customDataText"
              label="Custom Data (JSON format)"
              variant="outlined"
              rows="10"
              placeholder='{"key1": "value1", "key2": "value2"}'
            />
          </div>

          <!-- User Password for Encryption -->
          <v-divider class="my-4" />
          <h3 class="mb-4">Authentication</h3>
          <v-text-field
            v-model="userPassword"
            label="Your Login Password"
            :rules="[v => !!v || 'Password is required for encryption']"
            variant="outlined"
            type="password"
            required
            hint="Your login password is required to encrypt the credential data"
            persistent-hint
          />
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn @click="closeDialog">Cancel</v-btn>
        <v-btn
          color="primary"
          :loading="saving"
          :disabled="!valid"
          @click="saveCredential"
        >
          {{ isEditing ? 'Update' : 'Create' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import api from '@/services/api'

const props = defineProps({
  modelValue: Boolean,
  credential: Object,
  credentialTypes: Array
})

const emit = defineEmits(['update:modelValue', 'saved'])

// Dialog state
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Form state
const form = ref(null)
const valid = ref(false)
const saving = ref(false)

// Visibility toggles
const showApiKey = ref(false)
const showPassword = ref(false)
const showAccessToken = ref(false)
const showRefreshToken = ref(false)
const showPassphrase = ref(false)
const showDbPassword = ref(false)

// Form data
const formData = ref({
  name: '',
  description: '',
  credential_type: '',
  tags: [],
  expires_at: ''
})

const credentialData = ref({})
const userPassword = ref('')
const headersText = ref('')
const customDataText = ref('')

const isEditing = computed(() => !!props.credential)

// Helper functions (must be defined before watch)
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    credential_type: '',
    tags: [],
    expires_at: ''
  }
  credentialData.value = {}
  userPassword.value = ''
  resetTypeSpecificFields()
}

const resetTypeSpecificFields = () => {
  headersText.value = ''
  customDataText.value = ''
}

// Watch for credential changes
watch(() => props.credential, (newCredential) => {
  if (newCredential) {
    formData.value = {
      name: newCredential.name,
      description: newCredential.description || '',
      credential_type: newCredential.credential_type,
      tags: newCredential.tags || [],
      expires_at: newCredential.expires_at ? formatDateTimeLocal(newCredential.expires_at) : ''
    }
    // Reset credential data when editing (user needs to re-enter)
    credentialData.value = {}
    resetTypeSpecificFields()
  } else {
    resetForm()
  }
}, { immediate: true })

// Watch for dialog changes
watch(dialog, (isOpen) => {
  if (isOpen) {
    nextTick(() => {
      if (form.value) {
        form.value.resetValidation()
      }
    })
  } else {
    resetVisibilityToggles()
    userPassword.value = ''
  }
})

const onTypeChange = () => {
  credentialData.value = {}
  resetTypeSpecificFields()
}

const resetVisibilityToggles = () => {
  showApiKey.value = false
  showPassword.value = false
  showAccessToken.value = false
  showRefreshToken.value = false
  showPassphrase.value = false
  showDbPassword.value = false
}

const formatDateTimeLocal = (isoString) => {
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const saveCredential = async () => {
  if (!form.value.validate()) return

  saving.value = true
  try {
    // Prepare credential data based on type
    let finalCredentialData = { ...credentialData.value }

    // Handle type-specific data preparation
    if (formData.value.credential_type === 'api_key' && headersText.value) {
      try {
        finalCredentialData.headers = JSON.parse(headersText.value)
      } catch (e) {
        throw new Error('Invalid JSON format in headers')
      }
    }

    if (formData.value.credential_type === 'custom') {
      try {
        finalCredentialData = JSON.parse(customDataText.value || '{}')
      } catch (e) {
        throw new Error('Invalid JSON format in custom data')
      }
    }

    const payload = {
      ...formData.value,
      credential_data: finalCredentialData,
      user_password: userPassword.value,
      expires_at: formData.value.expires_at || null
    }

    if (isEditing.value) {
      await api.put(`/api/v1/credentials/${props.credential.id}`, payload)
    } else {
      await api.post('/api/v1/credentials/', payload)
    }

    emit('saved')
  } catch (error) {
    console.error('Failed to save credential:', error)
    // TODO: Show error message
  } finally {
    saving.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
}
</script>