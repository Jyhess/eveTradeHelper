import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import SystemMap from '@/views/SystemMap.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: {
    systems: {
      getSystemMap: vi.fn()
    }
  }
}))

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
    { path: '/systems/:systemId/map', name: 'SystemMap', component: SystemMap, props: true }
  ]
})

describe('SystemMap Component', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('should display loading state when fetching map data', async () => {
    api.systems.getSystemMap.mockImplementation(() => new Promise(() => {}))

    wrapper = mount(SystemMap, {
      props: {
        systemId: 30000142
      },
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.find('.loader').exists() || wrapper.text().includes('Loading')).toBeTruthy()
  })

  it('should display error message when API call fails', async () => {
    const errorMessage = 'Failed to load system map'
    api.systems.getSystemMap.mockRejectedValue(new Error(errorMessage))

    wrapper = mount(SystemMap, {
      props: {
        systemId: 30000142
      },
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.text()).toContain('Error')
  })

  it('should display systems and connections when data is loaded', async () => {
    const mockData = {
      system_id: 30000142,
      max_jumps: 3,
      total_systems: 2,
      total_connections: 1,
      systems: [
        {
          system_id: 30000142,
          name: 'Jita',
          security_status: 0.9,
          security_class: 'B',
          jumps: 0
        },
        {
          system_id: 30000143,
          name: 'Perimeter',
          security_status: 0.9,
          security_class: 'B',
          jumps: 1
        }
      ],
      connections: [
        {
          from_system_id: 30000142,
          to_system_id: 30000143
        }
      ]
    }

    api.systems.getSystemMap.mockResolvedValue(mockData)

    wrapper = mount(SystemMap, {
      props: {
        systemId: 30000142
      },
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.text()).toContain('Jita')
    expect(wrapper.text()).toContain('Perimeter')
  })

  it('should call API with correct systemId and maxJumps', async () => {
    const mockData = {
      system_id: 30000142,
      max_jumps: 3,
      total_systems: 1,
      total_connections: 0,
      systems: [],
      connections: []
    }

    api.systems.getSystemMap.mockResolvedValue(mockData)

    wrapper = mount(SystemMap, {
      props: {
        systemId: 30000142,
        maxJumps: 3
      },
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(api.systems.getSystemMap).toHaveBeenCalledWith(30000142, 3)
  })

  it('should use default maxJumps when not provided', async () => {
    const mockData = {
      system_id: 30000142,
      max_jumps: 3,
      total_systems: 1,
      total_connections: 0,
      systems: [],
      connections: []
    }

    api.systems.getSystemMap.mockResolvedValue(mockData)

    wrapper = mount(SystemMap, {
      props: {
        systemId: 30000142
      },
      global: {
        plugins: [router]
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(api.systems.getSystemMap).toHaveBeenCalledWith(30000142, 3)
  })
})

