import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import SystemToSystemDeals from '@/views/SystemToSystemDeals.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: {
    regions: {
      getRegions: vi.fn(),
      getConstellations: vi.fn()
    },
    constellations: {
      getSystems: vi.fn()
    },
    markets: {
      searchSystemToSystemDeals: vi.fn()
    }
  }
}))

describe('SystemToSystemDeals Component', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    api.regions.getRegions.mockResolvedValue({
      regions: [
        { region_id: 10000001, name: 'Test Region' }
      ]
    })
  })

  it('should render the component with cascade selectors', () => {
    wrapper = mount(SystemToSystemDeals)
    
    expect(wrapper.find('.system-to-system-deals-page').exists()).toBe(true)
    expect(wrapper.find('#from-region-select').exists()).toBe(true)
    expect(wrapper.find('#to-region-select').exists()).toBe(true)
    expect(wrapper.find('.search-button').exists()).toBe(true)
  })

  it('should disable search button when systems are not selected', () => {
    wrapper = mount(SystemToSystemDeals)
    
    const searchButton = wrapper.find('.search-button')
    expect(searchButton.attributes('disabled')).toBeDefined()
  })

  it('should enable search button when both systems are selected', async () => {
    wrapper = mount(SystemToSystemDeals, {
      data() {
        return {
          fromSystemId: 30000142,
          toSystemId: 30000144
        }
      }
    })
    
    await wrapper.vm.$nextTick()
    const searchButton = wrapper.find('.search-button')
    expect(searchButton.attributes('disabled')).toBeUndefined()
  })
})

