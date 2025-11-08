import { describe, it, expect } from 'vitest'
import {
  API_BASE_URL,
  API_TIMEOUT_MS,
  DEFAULT_PAGE_SIZE,
  ROUTES,
  ERROR_MESSAGES
} from '@/constants'

describe('Constants', () => {
  describe('API Configuration', () => {
    it('should have API_BASE_URL defined', () => {
      expect(API_BASE_URL).toBeDefined()
      expect(typeof API_BASE_URL).toBe('string')
    })

    it('should have API_TIMEOUT_MS defined', () => {
      expect(API_TIMEOUT_MS).toBeDefined()
      expect(typeof API_TIMEOUT_MS).toBe('number')
      expect(API_TIMEOUT_MS).toBeGreaterThan(0)
    })
  })

  describe('Default Values', () => {
    it('should have DEFAULT_PAGE_SIZE defined', () => {
      expect(DEFAULT_PAGE_SIZE).toBeDefined()
      expect(typeof DEFAULT_PAGE_SIZE).toBe('number')
      expect(DEFAULT_PAGE_SIZE).toBeGreaterThan(0)
    })
  })

  describe('Routes', () => {
    it('should have all required routes defined', () => {
      expect(ROUTES.HOME).toBeDefined()
      expect(ROUTES.REGIONS).toBeDefined()
      expect(ROUTES.CONSTELLATIONS).toBeDefined()
      expect(ROUTES.SYSTEMS).toBeDefined()
      expect(ROUTES.MARKET).toBeDefined()
      expect(ROUTES.DEALS).toBeDefined()
    })

    it('should have routes as strings', () => {
      Object.values(ROUTES).forEach(route => {
        expect(typeof route).toBe('string')
      })
    })
  })

  describe('Error Messages', () => {
    it('should have all required error messages defined', () => {
      expect(ERROR_MESSAGES.NETWORK_ERROR).toBeDefined()
      expect(ERROR_MESSAGES.API_ERROR).toBeDefined()
      expect(ERROR_MESSAGES.NOT_FOUND).toBeDefined()
      expect(ERROR_MESSAGES.UNAUTHORIZED).toBeDefined()
      expect(ERROR_MESSAGES.GENERIC).toBeDefined()
    })

    it('should have error messages as strings', () => {
      Object.values(ERROR_MESSAGES).forEach(message => {
        expect(typeof message).toBe('string')
        expect(message.length).toBeGreaterThan(0)
      })
    })
  })
})

