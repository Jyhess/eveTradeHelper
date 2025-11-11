import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ComboBox from '@/components/ComboBox.vue'

describe('ComboBox Component', () => {
  let wrapper
  const options = [
    { value: 1, label: 'Option 1' },
    { value: 2, label: 'Option 2' },
    { value: 3, label: 'Option 3' }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the component with input and options', () => {
    wrapper = mount(ComboBox, {
      props: {
        options,
        modelValue: null
      }
    })

    expect(wrapper.find('.combo-box').exists()).toBe(true)
    expect(wrapper.find('.combo-input').exists()).toBe(true)
  })

  it('should filter options based on input text', async () => {
    wrapper = mount(ComboBox, {
      props: {
        options,
        modelValue: null
      }
    })

    const input = wrapper.find('.combo-input')
    await input.trigger('focus')
    await input.setValue('Option 1')
    await wrapper.vm.$nextTick()

    const dropdown = wrapper.find('.combo-dropdown')
    expect(dropdown.exists()).toBe(true)
    const optionElements = wrapper.findAll('.combo-option')
    expect(optionElements.length).toBe(1)
    expect(optionElements[0].text()).toBe('Option 1')
  })

  it('should show dropdown when input is focused', async () => {
    wrapper = mount(ComboBox, {
      props: {
        options,
        modelValue: null
      }
    })

    const input = wrapper.find('.combo-input')
    await input.trigger('focus')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.combo-dropdown').exists()).toBe(true)
  })

  it('should emit update:modelValue when option is selected', async () => {
    wrapper = mount(ComboBox, {
      props: {
        options,
        modelValue: null
      }
    })

    const input = wrapper.find('.combo-input')
    await input.trigger('focus')
    await wrapper.vm.$nextTick()

    const optionElement = wrapper.find('.combo-option')
    expect(optionElement.exists()).toBe(true)
    await optionElement.trigger('mousedown')
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([options[0].value])
  })

  it('should navigate with arrow keys', async () => {
    wrapper = mount(ComboBox, {
      props: {
        options,
        modelValue: null
      }
    })

    const input = wrapper.find('.combo-input')
    await input.trigger('focus')
    await wrapper.vm.$nextTick()

    await input.trigger('keydown', { key: 'ArrowDown', preventDefault: () => {} })
    await wrapper.vm.$nextTick()
    const highlighted1 = wrapper.findAll('.combo-option.highlighted')
    expect(highlighted1.length).toBe(1)

    await input.trigger('keydown', { key: 'ArrowDown', preventDefault: () => {} })
    await wrapper.vm.$nextTick()
    const highlighted2 = wrapper.findAll('.combo-option.highlighted')
    expect(highlighted2.length).toBe(1)

    await input.trigger('keydown', { key: 'ArrowUp', preventDefault: () => {} })
    await wrapper.vm.$nextTick()
    const highlighted3 = wrapper.findAll('.combo-option.highlighted')
    expect(highlighted3.length).toBe(1)
  })

  it('should select option with Enter key', async () => {
    wrapper = mount(ComboBox, {
      props: {
        options,
        modelValue: null
      }
    })

    const input = wrapper.find('.combo-input')
    await input.trigger('focus')
    await wrapper.vm.$nextTick()

    await input.trigger('keydown', { key: 'ArrowDown', preventDefault: () => {} })
    await wrapper.vm.$nextTick()
    const highlighted = wrapper.findAll('.combo-option.highlighted')
    expect(highlighted.length).toBe(1)

    await input.trigger('keydown', { key: 'Enter', preventDefault: () => {} })
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([options[0].value])
  })
})

