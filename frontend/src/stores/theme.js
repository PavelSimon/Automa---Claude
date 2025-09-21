import { defineStore } from 'pinia'
import { useTheme } from 'vuetify'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDarkMode: localStorage.getItem('darkMode') === 'true' || false
  }),

  getters: {
    currentTheme: (state) => state.isDarkMode ? 'dark' : 'light'
  },

  actions: {
    toggleTheme() {
      this.isDarkMode = !this.isDarkMode
      this.applyTheme()
      this.saveToStorage()
    },

    setDarkMode(enabled) {
      this.isDarkMode = enabled
      this.applyTheme()
      this.saveToStorage()
    },

    applyTheme() {
      // This will be called from the component that has access to vuetify theme
      if (typeof window !== 'undefined') {
        const event = new CustomEvent('themeChange', {
          detail: { isDark: this.isDarkMode }
        })
        window.dispatchEvent(event)
      }
    },

    saveToStorage() {
      localStorage.setItem('darkMode', this.isDarkMode.toString())
    },

    initializeFromUser(userDarkMode) {
      // Initialize from user profile, but respect local storage if different
      if (userDarkMode !== undefined && localStorage.getItem('darkMode') === null) {
        this.setDarkMode(userDarkMode)
      } else {
        this.applyTheme()
      }
    }
  }
})