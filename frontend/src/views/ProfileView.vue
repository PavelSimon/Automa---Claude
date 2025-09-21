<template>
  <div>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">User Profile</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8" lg="6">
        <v-card>
          <v-card-title>Profile Information</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="saveProfile">
              <v-text-field
                v-model="profileForm.email"
                label="Email"
                disabled
                hint="Email cannot be changed"
                persistent-hint
              ></v-text-field>

              <v-text-field
                v-model="profileForm.first_name"
                label="First Name"
                clearable
              ></v-text-field>

              <v-text-field
                v-model="profileForm.last_name"
                label="Last Name"
                clearable
              ></v-text-field>

              <v-select
                v-model="profileForm.timezone"
                :items="timezones"
                item-title="label"
                item-value="value"
                label="Timezone"
                hint="Select your local timezone for proper time display"
                persistent-hint
                :loading="loadingTimezones"
              ></v-select>

              <v-switch
                v-model="profileForm.dark_mode"
                label="Dark Mode"
                hint="Enable dark theme for the application"
                persistent-hint
                color="primary"
              ></v-switch>

              <div class="mt-4">
                <v-btn
                  type="submit"
                  color="primary"
                  :loading="saving"
                  :disabled="!hasChanges"
                >
                  Save Changes
                </v-btn>
                <v-btn
                  class="ml-2"
                  @click="resetForm"
                  :disabled="!hasChanges"
                >
                  Reset
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4" lg="6">
        <v-card>
          <v-card-title>Account Information</v-card-title>
          <v-card-text>
            <div class="mb-3">
              <div class="text-subtitle2">Account Status</div>
              <v-chip
                :color="user.is_active ? 'success' : 'error'"
                small
              >
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </v-chip>
            </div>

            <div class="mb-3">
              <div class="text-subtitle2">Member Since</div>
              <div class="text-body-1">{{ formatDate(user.created_at) }}</div>
            </div>

            <div class="mb-3">
              <div class="text-subtitle2">Current Timezone</div>
              <div class="text-body-1">{{ user.timezone || 'Europe/Bratislava' }}</div>
            </div>

            <div class="mb-3">
              <div class="text-subtitle2">Local Time</div>
              <div class="text-body-1">{{ currentLocalTime }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Success/Error Messages -->
    <v-snackbar
      v-model="showMessage"
      :color="messageColor"
      :timeout="3000"
    >
      {{ message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { formatDate } from '@/utils/datetime'

const authStore = useAuthStore()
const themeStore = useThemeStore()

const user = ref({})
const originalProfile = ref({})
const profileForm = ref({
  email: '',
  first_name: '',
  last_name: '',
  timezone: 'Europe/Bratislava',
  dark_mode: false
})

const timezones = ref([])
const loading = ref(false)
const saving = ref(false)
const loadingTimezones = ref(false)
const showMessage = ref(false)
const message = ref('')
const messageColor = ref('success')
const currentLocalTime = ref('')

// Update local time every second
let timeInterval = null

const hasChanges = computed(() => {
  return JSON.stringify(profileForm.value) !== JSON.stringify(originalProfile.value)
})

const loadProfile = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/profile/me')
    user.value = response.data

    profileForm.value = {
      email: user.value.email,
      first_name: user.value.first_name || '',
      last_name: user.value.last_name || '',
      timezone: user.value.timezone || 'Europe/Bratislava',
      dark_mode: user.value.dark_mode !== undefined ? user.value.dark_mode : themeStore.isDarkMode
    }

    originalProfile.value = { ...profileForm.value }
  } catch (error) {
    console.error('Failed to load profile:', error)
    showErrorMessage('Failed to load profile information')
  } finally {
    loading.value = false
  }
}

const loadTimezones = async () => {
  loadingTimezones.value = true
  try {
    const response = await axios.get('/api/v1/profile/timezones')
    timezones.value = response.data.timezones
  } catch (error) {
    console.error('Failed to load timezones:', error)
    // Fallback timezones
    timezones.value = [
      { value: 'Europe/Bratislava', label: 'Europe/Bratislava (CET/CEST)' },
      { value: 'Europe/Prague', label: 'Europe/Prague (CET/CEST)' },
      { value: 'UTC', label: 'UTC (Coordinated Universal Time)' }
    ]
  } finally {
    loadingTimezones.value = false
  }
}

const saveProfile = async () => {
  saving.value = true
  try {
    const updateData = {
      first_name: profileForm.value.first_name || null,
      last_name: profileForm.value.last_name || null,
      timezone: profileForm.value.timezone,
      dark_mode: profileForm.value.dark_mode
    }

    await axios.put('/api/v1/profile/me', updateData)

    // Update theme store with new dark mode setting
    themeStore.setDarkMode(profileForm.value.dark_mode)

    // Update original form data
    originalProfile.value = { ...profileForm.value }

    // Reload profile to get updated data
    await loadProfile()

    showSuccessMessage('Profile updated successfully')
  } catch (error) {
    console.error('Failed to save profile:', error)
    showErrorMessage('Failed to save profile changes')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  profileForm.value = { ...originalProfile.value }
}

const showSuccessMessage = (msg) => {
  message.value = msg
  messageColor.value = 'success'
  showMessage.value = true
}

const showErrorMessage = (msg) => {
  message.value = msg
  messageColor.value = 'error'
  showMessage.value = true
}

const updateLocalTime = () => {
  const now = new Date()
  currentLocalTime.value = now.toLocaleString('sk-SK', {
    timeZone: profileForm.value.timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  })
}

// Watch timezone changes to update local time
watch(() => profileForm.value.timezone, () => {
  updateLocalTime()
})

// Watch dark mode changes to apply theme immediately
watch(() => profileForm.value.dark_mode, (newValue) => {
  themeStore.setDarkMode(newValue)
})

onMounted(async () => {
  await Promise.all([
    loadProfile(),
    loadTimezones()
  ])

  // Start time updates
  updateLocalTime()
  timeInterval = setInterval(updateLocalTime, 1000)
})

// Cleanup
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>