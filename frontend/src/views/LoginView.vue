<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Login to Automa</v-toolbar-title>
          </v-toolbar>

          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="Email"
                name="login"
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

              <v-alert v-if="error" type="error" class="mb-4">
                {{ error }}
              </v-alert>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              @click="handleLogin"
              :loading="authStore.isLoading"
              block
            >
              Login
            </v-btn>
          </v-card-actions>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text @click="$router.push('/register')">
              Don't have an account? Register
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
const error = ref('')
const emailErrors = ref([])
const passwordErrors = ref([])

const handleLogin = async () => {
  // Reset errors
  error.value = ''
  emailErrors.value = []
  passwordErrors.value = []

  // Basic validation
  if (!email.value) {
    emailErrors.value.push('Email is required')
  }
  if (!password.value) {
    passwordErrors.value.push('Password is required')
  }

  if (emailErrors.value.length || passwordErrors.value.length) {
    return
  }

  const result = await authStore.login(email.value, password.value)

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error
  }
}
</script>