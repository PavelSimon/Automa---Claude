/**
 * DateTime utility functions for consistent date/time formatting
 */

/**
 * Parse database datetime string as UTC and convert to local Date object
 * @param {string} dateString - Database datetime string (assumed to be UTC)
 * @returns {Date|null} Local Date object or null if invalid
 */
function parseDBDateTime(dateString) {
  if (!dateString) return null

  try {
    // Database returns datetime without timezone info, but it's actually UTC
    // If it doesn't contain 'T' or 'Z', assume it's in format "YYYY-MM-DD HH:MM:SS"
    let isoString = dateString

    if (!dateString.includes('T') && !dateString.includes('Z') && !dateString.includes('+')) {
      // Convert "YYYY-MM-DD HH:MM:SS" to ISO format and treat as UTC
      isoString = dateString.replace(' ', 'T') + 'Z'
    }

    const date = new Date(isoString)
    return isNaN(date.getTime()) ? null : date
  } catch (error) {
    console.warn('Error parsing database datetime:', error)
    return null
  }
}

/**
 * Format a date string to local date format (DD/MM/YYYY or MM/DD/YYYY based on locale)
 * @param {string} dateString - Database datetime string (UTC)
 * @returns {string} Formatted date string
 */
export function formatDate(dateString) {
  if (!dateString) return 'N/A'

  const date = parseDBDateTime(dateString)
  if (!date) return 'Invalid date'

  return date.toLocaleDateString('sk-SK', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * Format a date string to local datetime format with time
 * @param {string} dateString - Database datetime string (UTC)
 * @returns {string} Formatted datetime string
 */
export function formatDateTime(dateString) {
  if (!dateString) return 'N/A'

  const date = parseDBDateTime(dateString)
  if (!date) return 'Invalid date'

  return date.toLocaleString('sk-SK', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  })
}

/**
 * Format relative time (e.g., "2 hours ago", "just now")
 * @param {string} dateString - Database datetime string (UTC)
 * @returns {string} Relative time string
 */
export function formatRelativeTime(dateString) {
  if (!dateString) return 'Unknown'

  const date = parseDBDateTime(dateString)
  if (!date) return 'Invalid date'

  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Práve teraz'
  if (diffMins < 60) return `Pred ${diffMins} min${diffMins === 1 ? '' : 'útami'}`
  if (diffHours < 24) return `Pred ${diffHours} hodino${diffHours === 1 ? 'u' : diffHours < 5 ? 'ami' : 'ami'}`
  if (diffDays < 7) return `Pred ${diffDays} dň${diffDays === 1 ? 'om' : 'ami'}`

  return formatDate(dateString)
}

/**
 * Format duration between two timestamps
 * @param {string} startTime - Database datetime string (UTC)
 * @param {string} endTime - Database datetime string (UTC)
 * @returns {string} Duration string (e.g., "2h 15m", "45s")
 */
export function formatDuration(startTime, endTime) {
  if (!startTime || !endTime) return 'N/A'

  const start = parseDBDateTime(startTime)
  const end = parseDBDateTime(endTime)

  if (!start || !end) return 'Invalid duration'

  const duration = end - start
  if (duration < 0) return '0s'

  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}d ${hours % 24}h`
  if (hours > 0) return `${hours}h ${minutes % 60}m`
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`
  return `${seconds}s`
}

/**
 * Get current timestamp in ISO format for the backend
 * @returns {string} ISO timestamp string
 */
export function getCurrentTimestamp() {
  return new Date().toISOString()
}