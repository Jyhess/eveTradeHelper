import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MarketGroupSelector from '@/components/MarketGroupSelector.vue'
import api from '@/services/api'

vi.mock('@/services/api', () => ({
  default: {
    markets: {
      getCategories: vi.fn()
    }
  }
}))

describe('MarketGroupSelector Component', () => {
  let wrapper

  const mockCategories = [
    {
      group_id: 1,
      name: 'Root Group 1',
      parent_group_id: null,
      types: [101, 102]
    },
    {
      group_id: 2,
      name: 'Child Group 1',
      parent_group_id: 1,
      types: [201, 202]
    },
    {
      group_id: 3,
      name: 'Root Group 2',
      parent_group_id: null,
      types: [301]
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    api.markets.getCategories.mockResolvedValue({
      categories: mockCategories
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('should render the component with label', () => {
    wrapper = mount(MarketGroupSelector)

    expect(wrapper.find('.form-group').exists()).toBe(true)
    expect(wrapper.find('label').exists()).toBe(true)
    expect(wrapper.find('label').text()).toBe('Market Group:')
  })

  it('should show loader while fetching groups', async () => {
    api.markets.getCategories.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ categories: [] }), 100))
    )

    wrapper = mount(MarketGroupSelector)
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent({ name: 'Loader' }).exists()).toBe(true)
  })

  it('should fetch and display market groups', async () => {
    wrapper = mount(MarketGroupSelector)

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(api.markets.getCategories).toHaveBeenCalled()
    expect(wrapper.findComponent({ name: 'TreeSelect' }).exists()).toBe(true)
  })

  it('should build tree structure correctly', async () => {
    wrapper = mount(MarketGroupSelector)

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    const treeSelect = wrapper.findComponent({ name: 'TreeSelect' })
    expect(treeSelect.exists()).toBe(true)
    expect(treeSelect.props('tree')).toBeDefined()
    expect(Array.isArray(treeSelect.props('tree'))).toBe(true)
  })

  it('should emit update:selected-group-id when group is selected', async () => {
    wrapper = mount(MarketGroupSelector)

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    const treeSelect = wrapper.findComponent({ name: 'TreeSelect' })
    await treeSelect.vm.$emit('input', 1)
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:selected-group-id')).toBeTruthy()
    expect(wrapper.emitted('update:selected-group-id')[0]).toEqual([1])
  })

  it('should emit group-change when group changes', async () => {
    wrapper = mount(MarketGroupSelector)

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    const mockGroup = { group_id: 1, name: 'Test Group' }
    const treeSelect = wrapper.findComponent({ name: 'TreeSelect' })
    await treeSelect.vm.$emit('change', mockGroup)
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('group-change')).toBeTruthy()
    expect(wrapper.emitted('group-change')[0]).toEqual([mockGroup])
  })

  it('should emit error when API call fails', async () => {
    const errorMessage = 'Failed to load groups'
    api.markets.getCategories.mockRejectedValue(new Error(errorMessage))

    wrapper = mount(MarketGroupSelector)

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(wrapper.emitted('error')).toBeTruthy()
    expect(wrapper.emitted('error')[0][0]).toContain(errorMessage)
  })

  it('should disable TreeSelect when disabled prop is true', async () => {
    wrapper = mount(MarketGroupSelector, {
      props: {
        disabled: true
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    const treeSelect = wrapper.findComponent({ name: 'TreeSelect' })
    expect(treeSelect.exists()).toBe(true)
    expect(treeSelect.props('disabled')).toBe(true)
  })

  it('should pass selectedGroupId to TreeSelect', async () => {
    wrapper = mount(MarketGroupSelector, {
      props: {
        selectedGroupId: 2
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    const treeSelect = wrapper.findComponent({ name: 'TreeSelect' })
    expect(treeSelect.props('value')).toBe(2)
  })

  it('should use custom id prop', () => {
    wrapper = mount(MarketGroupSelector, {
      props: {
        id: 'custom-group-select'
      }
    })

    const label = wrapper.find('label')
    expect(label.attributes('for')).toBe('custom-group-select')
  })
})

