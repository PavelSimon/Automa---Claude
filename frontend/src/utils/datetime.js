/**
 * DateTime utility functions for consistent date/time formatting
 */

/**
 * Format a date string to local date format (DD/MM/YYYY or MM/DD/YYYY based on locale)
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted date string
 */
export function formatDate(dateString) {
  if (!dateString) return 'N/A'

  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid date'

    return date.toLocaleDateString('sk-SK', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  } catch (error) {
    console.warn('Error formatting date:', error)
    return 'Invalid date'
  }
}

/**
 * Format a date string to local datetime format with time
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Formatted datetime string
 */
export function formatDateTime(dateString) {
  if (!dateString) return 'N/A'

  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid date'

    return date.toLocaleString('sk-SK', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short'
    })
  } catch (error) {
    console.warn('Error formatting datetime:', error)
    return 'Invalid date'
  }
}

/**
 * Format relative time (e.g., "2 hours ago", "just now")
 * @param {string} dateString - ISO date string from backend
 * @returns {string} Relative time string
 */
export function formatRelativeTime(dateString) {
  if (!dateString) return 'Unknown'

  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'Invalid date'

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
  } catch (error) {
    console.warn('Error formatting relative time:', error)
    return 'Unknown'
  }
}

/**
 * Format duration between two timestamps
 * @param {string} startTime - ISO start time string
 * @param {string} endTime - ISO end time string
 * @returns {string} Duration string (e.g., "2h 15m", "45s")
 */
export function formatDuration(startTime, endTime) {
  if (!startTime || !endTime) return 'N/A'

  try {
    const start = new Date(startTime)
    const end = new Date(endTime)

    if (isNaN(start.getTime()) || isNaN(end.getTime())) return 'Invalid duration'

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
  } catch (error) {
    console.warn('Error formatting duration:', error)
    return 'Invalid duration'
  }
}

/**
 * Get current timestamp in ISO format for the backend
 * @returns {string} ISO timestamp string
 */
export function getCurrentTimestamp() {
  return new Date().toISOString()
}