<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card v-if="credential">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-test-tube</v-icon>
        Test Credential
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-6">
        <div class="mb-4">
          <div class="text-subtitle-2 text-grey mb-1">Credential</div>
          <div class="font-weight-medium">{{ credential.name }}</div>
        </div>

        <v-text-field
          v-model="userPassword"
          label="Your Login Password"
          type="password"
          variant="outlined"
          :error-messages="errorMessage"
          :rules="[v => !!v || 'Password is required']"
        />

        <!-- Test Results -->
        <v-expand-transition>
          <v-card v-if="testResult" :color="testResult.success ? 'success' : 'error'" variant="tonal" class="mt-4">
            <v-card-text>
              <div class="d-flex align-center mb-2">
                <v-icon :color="testResult.success ? 'success' : 'error'" class="mr-2">
                  {{ testResult.success ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
                <span class="font-weight-medium">
                  {{ testResult.success ? 'Test Passed' : 'Test Failed' }}
                </span>
              </div>
              <div class="text-body-2">{{ testResult.message }}</div>
              <div v-if="testResult.details" class="text-caption mt-2">
                <pre>{{ JSON.stringify(testResult.details, null, 2) }}</pre>
              </div>
            </v-card-text>
          </v-card>
        </v-expand-transition>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn @click="closeDialog">Close</v-btn>
        <v-btn
          color="primary"
          :loading="testing"
          :disabled="!userPassword"
          @click="testCredential"
        >
          Test
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: Boolean,
  credential: Object
})

const emit = defineEmits(['update:modelValue'])

// Dialog state
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Test state
const userPassword = ref('')
const testing = ref(false)
const errorMessage = ref('')
const testResult = ref(null)

// Watch dialog changes
watch(dialog, (isOpen) => {
  if (!isOpen) {
    userPassword.value = ''
    errorMessage.value = ''
    testResult.value = null
  }
})

const testCredential = async () => {
  testing.value = true
  errorMessage.value = ''
  testResult.value = null

  try {
    const response = await axios.post(
      `/api/v1/credentials/${props.credential.id}/test`,
      { user_password: userPassword.value }
    )

    testResult.value = response.data
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Failed to test credential'
  } finally {
    testing.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
}
</script>