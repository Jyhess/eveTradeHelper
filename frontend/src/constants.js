/**
 * Application constants
 * Centralized constants to avoid magic numbers and strings throughout the codebase
 */

// API Configuration
export const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5001/api/v1'
export const API_TIMEOUT_MS = 10000

// Default Values
export const DEFAULT_PAGE_SIZE = 50
export const DEFAULT_DEBOUNCE_DELAY_MS = 300
export const DEFAULT_SEARCH_MIN_LENGTH = 2

// UI Constants
export const LOADING_DELAY_MS = 200 // Minimum time to show loading indicator
export const TOAST_DURATION_MS = 3000

// Routes
export const ROUTES = {
  HOME: '/',
  REGIONS: '/regions',
  CONSTELLATIONS: '/constellations',
  SYSTEMS: '/systems',
  MARKET: '/market',
  DEALS: '/deals'
}

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  API_ERROR: 'An error occurred while fetching data.',
  NOT_FOUND: 'The requested resource was not found.',
  UNAUTHORIZED: 'You are not authorized to access this resource.',
  GENERIC: 'An unexpected error occurred.'
}

// Text Limits
export const MAX_DESCRIPTION_LENGTH = 150
export const MAX_SEARCH_RESULTS = 100
