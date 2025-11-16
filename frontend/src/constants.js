/**
 * Application constants
 * Centralized constants to avoid magic numbers and strings throughout the codebase
 */

// API Configuration
export const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5001/api/v1'

// Default Values
export const DEFAULT_PAGE_SIZE = 50
export const DEFAULT_DEBOUNCE_DELAY_MS = 300
export const DEFAULT_SEARCH_MIN_LENGTH = 2
export const DEFAULT_MAX_DETOUR_JUMPS = 0
export const DEFAULT_MAX_JUMPS = 3

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
  DEALS: '/deals',
  SYSTEM_TO_SYSTEM_DEALS: '/deals/system-to-system',
  SYSTEM_MAP: '/systems/:systemId/map'
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

// Security Status Colors (used for routes, systems, and connections)
export const SECURITY_COLORS = {
  NEGATIVE: '#000000', // Black for security < 0
  RED: '#f56565', // Red for security <= 0.2
  ORANGE: '#ed8936', // Orange for security <= 0.4
  YELLOW: '#f6e05e', // Yellow for security <= 0.5
  GREEN: '#48bb78', // Green for security <= 0.8
  BLUE: '#4299e1' // Blue for security > 0.8
}

// Security Status Stroke Colors (for borders/outlines)
export const SECURITY_STROKE_COLORS = {
  NEGATIVE: '#ffffff', // White stroke for black background
  RED: '#742a2a', // Dark red stroke
  ORANGE: '#7c2d12', // Dark orange stroke
  YELLOW: '#744210', // Dark yellow stroke
  GREEN: '#22543d', // Dark green stroke
  BLUE: '#2c5282' // Dark blue stroke
}

// Connection Line Colors (based on minimum security of connected systems)
export const CONNECTION_COLORS = {
  NULL: SECURITY_COLORS.NEGATIVE, // Black for null sec connections
  LOW: SECURITY_COLORS.RED, // Red for low sec (<= 0.2)
  VERY_LOW: SECURITY_COLORS.ORANGE, // Orange for very low sec (<= 0.4)
  LOW_SEC: SECURITY_COLORS.YELLOW, // Yellow for low sec (<= 0.5)
  HIGH_SEC: '#bee3f8' // Light blue for high sec (> 0.5)
}
