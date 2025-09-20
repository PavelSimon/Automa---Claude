<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Register for Automa</v-toolbar-title>
          </v-toolbar>

          <v-card-text>
            <v-form @submit.prevent="handleRegister">
              <v-text-field
                v-model="email"
                label="Email"
                name="email"
                prepend-icon="mdi-account"
                type="email"
                required
                :error-messages="emailErrors"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="Password"
                name="password"
                prepend-icon="mdi-lock"
                type="password"
                required
                :error-messages="passwordErrors"
              ></v-text-field>

              <v-text-field
                v-model="confirmPassword"
                label="Confirm Password"
                name="confirmPassword"
                prepend-icon="mdi-lock-check"
                type="password"
                required
                :error-messages="confirmPasswordErrors"
              ></v-text-field>

              <v-alert v-if="error" type="error" class="mb-4">
                {{ error }}
              </v-alert>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              @click="handleRegister"
              :loading="authStore.isLoading"
              block
            >
              Register
            </v-btn>
          </v-card-actions>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text @click="$router.push('/login')">
              Already have an account? Login
            </v-btn>
            <v-spacer></v-spacer>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const emailErrors = ref([])
const passwordErrors = ref([])
const confirmPasswordErrors = ref([])

const handleRegister = async () => {
  // Reset errors
  error.value = ''
  emailErrors.value = []
  passwordErrors.value = []
  confirmPasswordErrors.value = []

  // Basic validation
  if (!email.value) {
    emailErrors.value.push('Email is required')
  }
  if (!password.value) {
    passwordErrors.value.push('Password is required')
  }
  if (password.value.length < 6) {
    passwordErrors.value.push('Password must be at least 6 characters')
  }
  if (!confirmPassword.value) {
    confirmPasswordErrors.value.push('Please confirm your password')
  }
  if (password.value !== confirmPassword.value) {
    confirmPasswordErrors.value.push('Passwords do not match')
  }

  if (emailErrors.value.length || passwordErrors.value.length || confirmPasswordErrors.value.length) {
    return
  }

  const result = await authStore.register(email.value, password.value)

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error
  }
}
</script>