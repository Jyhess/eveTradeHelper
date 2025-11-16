import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import SystemSelector from '@/components/SystemSelector.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: {
    regions: {
      getRegions: vi.fn(),
      getConstellations: vi.fn()
    },
    constellations: {
      getSystems: vi.fn()
    }
  }
}))

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', name: 'home', component: { template: '<div>Home</div>' } }]
})

describe('SystemSelector Component', () => {
  let wrapper

  const mockRegions = [
    { region_id: 10000001, name: 'Test Region 1' },
    { region_id: 10000002, name: 'Test Region 2' }
  ]

  const mockConstellations = [
    { constellation_id: 20000001, name: 'Test Constellation 1' },
    { constellation_id: 20000002, name: 'Test Constellation 2' }
  ]

  const mockSystems = [
    { system_id: 30000001, name: 'Test System 1' },
    { system_id: 30000002, name: 'Test System 2' }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    api.regions.getRegions.mockResolvedValue({ regions: mockRegions })
    api.regions.getConstellations.mockResolvedValue({ constellations: mockConstellations })
    api.constellations.getSystems.mockResolvedValue({ systems: mockSystems })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('Component Rendering', () => {
    it('should render with required props', () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test'
        },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('h3').text()).toBe('Test Selector')
      expect(wrapper.find('input[placeholder*="System or constellation"]').exists()).toBe(true)
    })

    it('should render all form groups', () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('label[for="test-region-select"]').exists()).toBe(true)
      expect(wrapper.find('label[for="test-constellation-select"]').exists()).toBe(true)
      expect(wrapper.find('label[for="test-system-select"]').exists()).toBe(true)
    })

    it('should render quick search input', () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test'
        },
        global: {
          plugins: [router]
        }
      })

      const quickSearchInput = wrapper.find('input[placeholder*="System or constellation"]')
      expect(quickSearchInput.exists()).toBe(true)
    })
  })

  describe('Props Handling', () => {
    it('should initialize with provided regionId, constellationId, and systemId', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regionId: 10000001,
          constellationId: 20000001,
          systemId: 30000001,
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(wrapper.vm.localRegionId).toBe(10000001)
      expect(wrapper.vm.localConstellationId).toBe(20000001)
      expect(wrapper.vm.localSystemId).toBe(30000001)
    })

    it('should use regions prop when provided', () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.vm.regionOptions).toHaveLength(2)
      expect(wrapper.vm.regionOptions[0].label).toBe('Test Region 1')
    })

    it('should fallback to allRegions when regions prop is empty', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: []
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(api.regions.getRegions).toHaveBeenCalled()
      expect(wrapper.vm.allRegions).toEqual(mockRegions)
    })
  })

  describe('Region Selection', () => {
    it('should emit region-change when region is selected', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localRegionId = 10000001
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('update:regionId')).toBeTruthy()
      expect(wrapper.emitted('update:regionId')[0]).toEqual([10000001])
    })

    it('should load constellations when region is selected', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localRegionId = 10000001
      await wrapper.vm.$nextTick()

      await wrapper.vm.onRegionChange()
      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(api.regions.getConstellations).toHaveBeenCalledWith(10000001)
      expect(wrapper.vm.constellations).toHaveLength(2)
    })

    it('should clear constellation and system when region changes', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localConstellationId = 20000001
      wrapper.vm.localSystemId = 30000001
      await wrapper.vm.$nextTick()

      await wrapper.vm.onRegionChange()

      expect(wrapper.vm.localConstellationId).toBeNull()
      expect(wrapper.vm.localSystemId).toBeNull()
    })
  })

  describe('Constellation Selection', () => {
    it('should emit constellation-change when constellation is selected', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localRegionId = 10000001
      await wrapper.vm.$nextTick()

      wrapper.vm.localConstellationId = 20000001
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('update:constellationId')).toBeTruthy()
      expect(wrapper.emitted('update:constellationId')[0]).toEqual([20000001])
    })

    it('should load systems when constellation is selected', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localRegionId = 10000001
      wrapper.vm.localConstellationId = 20000001
      await wrapper.vm.$nextTick()

      await wrapper.vm.onConstellationChange()
      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(api.constellations.getSystems).toHaveBeenCalledWith(20000001)
      expect(wrapper.vm.systems).toHaveLength(2)
    })

    it('should clear system when constellation changes', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localSystemId = 30000001
      await wrapper.vm.$nextTick()

      await wrapper.vm.onConstellationChange()

      expect(wrapper.vm.localSystemId).toBeNull()
    })
  })

  describe('System Selection', () => {
    it('should emit system-change when system is selected', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.localSystemId = 30000001
      await wrapper.vm.$nextTick()

      expect(wrapper.emitted('update:systemId')).toBeTruthy()
      expect(wrapper.emitted('update:systemId')[0]).toEqual([30000001])
    })

    it('should emit system-next when system is selected', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.onSystemNext()

      expect(wrapper.emitted('system-next')).toBeTruthy()
    })
  })

  describe('Quick Search', () => {
    it('should not search with less than 2 characters', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      const quickSearchInput = wrapper.find('input[placeholder*="System or constellation"]')
      await quickSearchInput.setValue('J')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.quickSearchResults).toHaveLength(0)
      expect(wrapper.vm.searching).toBe(false)
    })

    it('should search for systems and constellations', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.allRegions = mockRegions
      wrapper.vm.allConstellations[10000001] = mockConstellations
      wrapper.vm.allSystems[20000001] = mockSystems

      const quickSearchInput = wrapper.find('input[placeholder*="System or constellation"]')
      await quickSearchInput.setValue('Test')
      await wrapper.vm.$nextTick()

      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 400))

      expect(wrapper.vm.quickSearchPerformed).toBe(true)
    })

    it('should select system from quick search results', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      const result = {
        key: 'system-30000001',
        name: 'Test System 1',
        type: 'System',
        regionId: 10000001,
        regionName: 'Test Region 1',
        constellationId: 20000001,
        constellationName: 'Test Constellation 1',
        systemId: 30000001
      }

      await wrapper.vm.selectQuickSearchResult(result)

      expect(wrapper.vm.localRegionId).toBe(10000001)
      expect(wrapper.vm.localConstellationId).toBe(20000001)
      expect(wrapper.vm.localSystemId).toBe(30000001)
      expect(wrapper.emitted('system-change')).toBeTruthy()
    })

    it('should select constellation from quick search results and focus system selector', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      const result = {
        key: 'constellation-20000001',
        name: 'Test Constellation 1',
        type: 'Constellation',
        regionId: 10000001,
        regionName: 'Test Region 1',
        constellationId: 20000001,
        systemId: null
      }

      const focusSystemComboSpy = vi.spyOn(wrapper.vm, 'focusSystemCombo')

      await wrapper.vm.selectQuickSearchResult(result)

      expect(wrapper.vm.localRegionId).toBe(10000001)
      expect(wrapper.vm.localConstellationId).toBe(20000001)
      expect(wrapper.vm.localSystemId).toBeNull()
      expect(wrapper.emitted('constellation-change')).toBeTruthy()
      expect(focusSystemComboSpy).toHaveBeenCalled()
    })

    it('should clear quick search results after selection', async () => {
      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.quickSearchText = 'Test'
      wrapper.vm.quickSearchResults = [{ key: 'test', name: 'Test' }]

      const result = {
        key: 'system-30000001',
        name: 'Test System 1',
        type: 'System',
        regionId: 10000001,
        constellationId: 20000001,
        systemId: 30000001
      }

      await wrapper.vm.selectQuickSearchResult(result)

      expect(wrapper.vm.quickSearchText).toBe('')
      expect(wrapper.vm.quickSearchResults).toHaveLength(0)
    })
  })

  describe('Error Handling', () => {
    it('should emit error when loading constellations fails', async () => {
      api.regions.getConstellations.mockRejectedValue(new Error('API Error'))

      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      await wrapper.vm.loadConstellations(10000001)

      expect(wrapper.emitted('error')).toBeTruthy()
      expect(wrapper.emitted('error')[0][0]).toContain('Error loading constellations')
    })

    it('should emit error when loading systems fails', async () => {
      api.constellations.getSystems.mockRejectedValue(new Error('API Error'))

      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      await wrapper.vm.loadSystems(20000001)

      expect(wrapper.emitted('error')).toBeTruthy()
      expect(wrapper.emitted('error')[0][0]).toContain('Error loading systems')
    })
  })

  describe('Loading States', () => {
    it('should show loading state when loading constellations', async () => {
      api.regions.getConstellations.mockImplementation(
        // eslint-disable-next-line no-undef
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.loadConstellations(10000001)

      await wrapper.vm.$nextTick()

      expect(wrapper.vm.loadingConstellations).toBe(true)
    })

    it('should show loading state when loading systems', async () => {
      api.constellations.getSystems.mockImplementation(
        // eslint-disable-next-line no-undef
        () => new Promise(resolve => setTimeout(resolve, 100))
      )

      wrapper = mount(SystemSelector, {
        props: {
          title: 'Test Selector',
          idPrefix: 'test',
          regions: mockRegions
        },
        global: {
          plugins: [router]
        }
      })

      await wrapper.vm.$nextTick()
      // eslint-disable-next-line no-undef
      await new Promise(resolve => setTimeout(resolve, 100))

      wrapper.vm.loadSystems(20000001)

      await wrapper.vm.$nextTick()

      expect(wrapper.vm.loadingSystems).toBe(true)
    })
  })
})

