import { describe, it, expect } from 'vitest'
import {
  formatPrice,
  formatVolume,
  formatNumber,
  formatNumberInput,
  parseNumberInput
} from '@/utils/numberFormatter'

describe('numberFormatter', () => {
  describe('formatPrice', () => {
    it('should format prices >= 1000 using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(formatPrice(1000)).toBe('1,000')
      expect(formatPrice(10000)).toBe('10,000')
      expect(formatPrice(1000000)).toBe('1,000,000')
      expect(formatPrice(1234567)).toBe('1,234,567')
    })

    it('should format prices < 1000 with 2 decimals', () => {
      expect(formatPrice(100)).toBe('100.00')
      expect(formatPrice(99.99)).toBe('99.99')
      expect(formatPrice(0.5)).toBe('0.50')
    })

    it('should return N/A for null or undefined prices', () => {
      expect(formatPrice(null)).toBe('N/A')
      expect(formatPrice(undefined)).toBe('N/A')
    })

    it('should handle zero price', () => {
      expect(formatPrice(0)).toBe('0.00')
    })
  })

  describe('formatVolume', () => {
    it('should format volumes >= 1000 using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(formatVolume(1000)).toBe('1,000')
      expect(formatVolume(10000)).toBe('10,000')
      expect(formatVolume(1000000)).toBe('1,000,000')
      expect(formatVolume(1234567.89)).toBe('1,234,568')
    })

    it('should format volumes < 1000 with 2 decimals', () => {
      expect(formatVolume(100)).toBe('100.00')
      expect(formatVolume(99.99)).toBe('99.99')
      expect(formatVolume(0.5)).toBe('0.50')
    })

    it('should return N/A for null or undefined volumes', () => {
      expect(formatVolume(null)).toBe('N/A')
      expect(formatVolume(undefined)).toBe('N/A')
    })

    it('should handle zero volume', () => {
      expect(formatVolume(0)).toBe('0.00')
    })
  })

  describe('formatNumber', () => {
    it('should format numbers using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(formatNumber(1000)).toBe('1,000')
      expect(formatNumber(10000)).toBe('10,000')
      expect(formatNumber(1000000)).toBe('1,000,000')
      expect(formatNumber(1234567)).toBe('1,234,567')
    })

    it('should format small numbers without separators', () => {
      expect(formatNumber(100)).toBe('100')
      expect(formatNumber(99)).toBe('99')
      expect(formatNumber(0)).toBe('0')
    })

    it('should return N/A for null or undefined numbers', () => {
      expect(formatNumber(null)).toBe('N/A')
      expect(formatNumber(undefined)).toBe('N/A')
    })
  })

  describe('formatNumberInput', () => {
    it('should format numbers using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(formatNumberInput(1000)).toBe('1,000')
      expect(formatNumberInput(10000)).toBe('10,000')
      expect(formatNumberInput(1000000)).toBe('1,000,000')
      expect(formatNumberInput(1234567)).toBe('1,234,567')
    })

    it('should format small numbers without separators', () => {
      expect(formatNumberInput(100)).toBe('100')
      expect(formatNumberInput(99)).toBe('99')
      expect(formatNumberInput(0)).toBe('0')
    })

    it('should handle string inputs', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(formatNumberInput('1000')).toBe('1,000')
      expect(formatNumberInput('10000')).toBe('10,000')
    })

    it('should handle decimal numbers', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator and point as decimal separator
      expect(formatNumberInput(1000.5)).toBe('1,000.5')
      expect(formatNumberInput(99.99)).toBe('99.99')
    })

    it('should return empty string for null, undefined, or empty values', () => {
      expect(formatNumberInput(null)).toBe('')
      expect(formatNumberInput(undefined)).toBe('')
      expect(formatNumberInput('')).toBe('')
    })

    it('should return empty string for invalid values', () => {
      expect(formatNumberInput('invalid')).toBe('')
      expect(formatNumberInput(-1)).toBe('')
    })
  })

  describe('parseNumberInput', () => {
    it('should parse numbers with various space types', () => {
      // Should handle non-breaking spaces (U+00A0)
      expect(parseNumberInput('1\u00A0000')).toBe(1000)
      expect(parseNumberInput('10\u00A0000')).toBe(10000)
      expect(parseNumberInput('1\u00A0000\u00A0000')).toBe(1000000)
      // Should handle narrow no-break spaces (U+202F from fr-FR)
      expect(parseNumberInput('1\u202F000')).toBe(1000)
      expect(parseNumberInput('10\u202F000')).toBe(10000)
    })

    it('should parse numbers with regular spaces', () => {
      expect(parseNumberInput('1 000')).toBe(1000)
      expect(parseNumberInput('10 000')).toBe(10000)
    })

    it('should parse numbers without spaces', () => {
      expect(parseNumberInput('1000')).toBe(1000)
      expect(parseNumberInput('10000')).toBe(10000)
    })

    it('should handle decimal numbers', () => {
      expect(parseNumberInput('1000.5')).toBe(1000.5)
      expect(parseNumberInput('99.99')).toBe(99.99)
    })

    it('should handle comma as decimal separator', () => {
      expect(parseNumberInput('1000,5')).toBe(1000.5)
      expect(parseNumberInput('99,99')).toBe(99.99)
    })

    it('should return null for empty or invalid values', () => {
      expect(parseNumberInput('')).toBe(null)
      expect(parseNumberInput(null)).toBe(null)
      expect(parseNumberInput(undefined)).toBe(null)
      expect(parseNumberInput('invalid')).toBe(null)
    })
  })
})

