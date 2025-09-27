import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
// Tree-shaking: Import only the components we actually use
import {
  VApp,
  VAppBar,
  VAppBarNavIcon,
  VNavigationDrawer,
  VToolbar,
  VToolbarTitle,
  VBtn,
  VCard,
  VCardText,
  VCardTitle,
  VCardActions,
  VContainer,
  VRow,
  VCol,
  VList,
  VListItem,
  VListItemTitle,
  VListItemSubtitle,
  VDataTable,
  VForm,
  VTextField,
  VSelect,
  VSwitch,
  VDialog,
  VIcon,
  VSpacer,
  VDivider,
  VAlert,
  VChip
} from 'vuetify/components'
import { Ripple, Intersect } from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const vuetify = createVuetify({
  components: {
    VApp,
    VAppBar,
    VAppBarNavIcon,
    VNavigationDrawer,
    VToolbar,
    VToolbarTitle,
    VBtn,
    VCard,
    VCardText,
    VCardTitle,
    VCardActions,
    VContainer,
    VRow,
    VCol,
    VList,
    VListItem,
    VListItemTitle,
    VListItemSubtitle,
    VDataTable,
    VForm,
    VTextField,
    VSelect,
    VSwitch,
    VDialog,
    VIcon,
    VSpacer,
    VDivider,
    VAlert,
    VChip
  },
  directives: {
    Ripple,
    Intersect
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'light'
  }
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(vuetify)

// Initialize authentication after Pinia is set up
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')