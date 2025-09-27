<template>
  <v-app>
    <v-navigation-drawer v-if="isAuthenticated" v-model="drawer" app>
      <v-list>
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard">
          <v-list-item-title>Dashboard</v-list-item-title>
        </v-list-item>

        <v-list-item to="/scripts" prepend-icon="mdi-file-code">
          <v-list-item-title>Scripts</v-list-item-title>
        </v-list-item>

        <v-list-item to="/agents" prepend-icon="mdi-robot">
          <v-list-item-title>Agents</v-list-item-title>
        </v-list-item>

        <v-list-item to="/jobs" prepend-icon="mdi-clock">
          <v-list-item-title>Jobs</v-list-item-title>
        </v-list-item>

        <v-list-item to="/monitoring" prepend-icon="mdi-monitor">
          <v-list-item-title>Monitoring</v-list-item-title>
        </v-list-item>

        <v-list-item to="/credentials" prepend-icon="mdi-key-variant">
          <v-list-item-title>Credentials</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar v-if="isAuthenticated" app>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>

      <v-toolbar-title>Automa</v-toolbar-title>

      <v-spacer></v-spacer>

      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" icon>
            <v-icon>mdi-account</v-icon>
          </v-btn>
        </template>

        <v-list>
          <v-list-item to="/profile" prepend-icon="mdi-account-edit">
            <v-list-item-title>Profile</v-list-item-title>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item @click="logout" prepend-icon="mdi-logout">
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const theme = useTheme()

const drawer = ref(true)
const isAuthenticated = computed(() => authStore.isAuthenticated)

// Watch for auth changes and keep drawer state
watch(isAuthenticated, (newValue) => {
  if (newValue && !drawer.value) {
    drawer.value = true
  }
}, { immediate: true })

// Handle theme changes
const handleThemeChange = (event) => {
  theme.global.name.value = event.detail.isDark ? 'dark' : 'light'
}

onMounted(() => {
  // Set initial theme
  theme.global.name.value = themeStore.currentTheme

  // Listen for theme change events
  window.addEventListener('themeChange', handleThemeChange)

  // Initialize theme from user profile when user data is available
  watch(() => authStore.user, (user) => {
    if (user && user.dark_mode !== undefined) {
      themeStore.initializeFromUser(user.dark_mode)
    }
  }, { immediate: true })
})

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>