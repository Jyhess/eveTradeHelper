import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Deals from '@/views/Deals.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
    { path: '/deals', name: 'deals', component: Deals }
  ]
})

describe('Deals Component - Number Formatting', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(Deals, {
      global: {
        plugins: [router],
        stubs: {
          TreeSelect: { template: '<div></div>' }
        }
      }
    })
  })

  afterEach(() => {
    wrapper.unmount()
  })

  describe('formatPrice', () => {
    it('should format prices >= 1000 using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(wrapper.vm.formatPrice(1000)).toBe('1,000')
      expect(wrapper.vm.formatPrice(10000)).toBe('10,000')
      expect(wrapper.vm.formatPrice(1000000)).toBe('1,000,000')
      expect(wrapper.vm.formatPrice(1234567)).toBe('1,234,567')
    })

    it('should format prices < 1000 with 2 decimals', () => {
      expect(wrapper.vm.formatPrice(100)).toBe('100.00')
      expect(wrapper.vm.formatPrice(99.99)).toBe('99.99')
      expect(wrapper.vm.formatPrice(0.5)).toBe('0.50')
    })

    it('should return N/A for null or undefined prices', () => {
      expect(wrapper.vm.formatPrice(null)).toBe('N/A')
      expect(wrapper.vm.formatPrice(undefined)).toBe('N/A')
    })

    it('should handle zero price', () => {
      expect(wrapper.vm.formatPrice(0)).toBe('0.00')
    })
  })

  describe('formatVolume', () => {
    it('should format volumes >= 1000 using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(wrapper.vm.formatVolume(1000)).toBe('1,000')
      expect(wrapper.vm.formatVolume(10000)).toBe('10,000')
      expect(wrapper.vm.formatVolume(1000000)).toBe('1,000,000')
      expect(wrapper.vm.formatVolume(1234567.89)).toBe('1,234,568')
    })

    it('should format volumes < 1000 with 2 decimals', () => {
      expect(wrapper.vm.formatVolume(100)).toBe('100.00')
      expect(wrapper.vm.formatVolume(99.99)).toBe('99.99')
      expect(wrapper.vm.formatVolume(0.5)).toBe('0.50')
    })

    it('should return N/A for null or undefined volumes', () => {
      expect(wrapper.vm.formatVolume(null)).toBe('N/A')
      expect(wrapper.vm.formatVolume(undefined)).toBe('N/A')
    })

    it('should handle zero volume', () => {
      expect(wrapper.vm.formatVolume(0)).toBe('0.00')
    })
  })

  describe('formatNumber', () => {
    it('should format numbers using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(wrapper.vm.formatNumber(1000)).toBe('1,000')
      expect(wrapper.vm.formatNumber(10000)).toBe('10,000')
      expect(wrapper.vm.formatNumber(1000000)).toBe('1,000,000')
      expect(wrapper.vm.formatNumber(1234567)).toBe('1,234,567')
    })

    it('should format small numbers without separators', () => {
      expect(wrapper.vm.formatNumber(100)).toBe('100')
      expect(wrapper.vm.formatNumber(99)).toBe('99')
      expect(wrapper.vm.formatNumber(0)).toBe('0')
    })

    it('should return N/A for null or undefined numbers', () => {
      expect(wrapper.vm.formatNumber(null)).toBe('N/A')
      expect(wrapper.vm.formatNumber(undefined)).toBe('N/A')
    })
  })

  describe('formatNumberInput', () => {
    it('should format numbers using browser locale', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(wrapper.vm.formatNumberInput(1000)).toBe('1,000')
      expect(wrapper.vm.formatNumberInput(10000)).toBe('10,000')
      expect(wrapper.vm.formatNumberInput(1000000)).toBe('1,000,000')
      expect(wrapper.vm.formatNumberInput(1234567)).toBe('1,234,567')
    })

    it('should format small numbers without separators', () => {
      expect(wrapper.vm.formatNumberInput(100)).toBe('100')
      expect(wrapper.vm.formatNumberInput(99)).toBe('99')
      expect(wrapper.vm.formatNumberInput(0)).toBe('0')
    })

    it('should handle string inputs', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator
      expect(wrapper.vm.formatNumberInput('1000')).toBe('1,000')
      expect(wrapper.vm.formatNumberInput('10000')).toBe('10,000')
    })

    it('should handle decimal numbers', () => {
      // In test environment, navigator is not available, so it defaults to 'en-US'
      // Format will use commas as thousands separator and point as decimal separator
      expect(wrapper.vm.formatNumberInput(1000.5)).toBe('1,000.5')
      expect(wrapper.vm.formatNumberInput(99.99)).toBe('99.99')
    })

    it('should return empty string for null, undefined, or empty values', () => {
      expect(wrapper.vm.formatNumberInput(null)).toBe('')
      expect(wrapper.vm.formatNumberInput(undefined)).toBe('')
      expect(wrapper.vm.formatNumberInput('')).toBe('')
    })

    it('should return empty string for invalid values', () => {
      expect(wrapper.vm.formatNumberInput('invalid')).toBe('')
      expect(wrapper.vm.formatNumberInput(-1)).toBe('')
    })
  })

  describe('parseNumberInput', () => {
    it('should parse numbers with non-breaking spaces', () => {
      expect(wrapper.vm.parseNumberInput('1\u00A0000')).toBe(1000)
      expect(wrapper.vm.parseNumberInput('10\u00A0000')).toBe(10000)
      expect(wrapper.vm.parseNumberInput('1\u00A0000\u00A0000')).toBe(1000000)
    })

    it('should parse numbers with regular spaces', () => {
      expect(wrapper.vm.parseNumberInput('1 000')).toBe(1000)
      expect(wrapper.vm.parseNumberInput('10 000')).toBe(10000)
    })

    it('should parse numbers without spaces', () => {
      expect(wrapper.vm.parseNumberInput('1000')).toBe(1000)
      expect(wrapper.vm.parseNumberInput('10000')).toBe(10000)
    })

    it('should handle decimal numbers', () => {
      expect(wrapper.vm.parseNumberInput('1000.5')).toBe(1000.5)
      expect(wrapper.vm.parseNumberInput('99.99')).toBe(99.99)
    })

    it('should handle comma as decimal separator', () => {
      expect(wrapper.vm.parseNumberInput('1000,5')).toBe(1000.5)
      expect(wrapper.vm.parseNumberInput('99,99')).toBe(99.99)
    })

    it('should return null for empty or invalid values', () => {
      expect(wrapper.vm.parseNumberInput('')).toBe(null)
      expect(wrapper.vm.parseNumberInput(null)).toBe(null)
      expect(wrapper.vm.parseNumberInput(undefined)).toBe(null)
      expect(wrapper.vm.parseNumberInput('invalid')).toBe(null)
    })
  })
})

