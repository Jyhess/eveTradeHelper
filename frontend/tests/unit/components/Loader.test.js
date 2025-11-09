import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Loader from '@/components/Loader.vue'

describe('Loader Component', () => {
  it('should render default loader with spinner and text', () => {
    const wrapper = mount(Loader, {
      props: {
        message: 'Loading...'
      }
    })

    expect(wrapper.find('.loader-spinner').exists()).toBe(true)
    expect(wrapper.find('.loader-text').exists()).toBe(true)
    expect(wrapper.find('.loader-text').text()).toBe('Loading...')
  })

  it('should render small variant when size prop is small', () => {
    const wrapper = mount(Loader, {
      props: {
        message: 'Loading...',
        size: 'small'
      }
    })

    expect(wrapper.find('.loader').classes()).toContain('loader-small')
    expect(wrapper.find('.loader-spinner').classes()).toContain('loader-spinner-small')
  })

  it('should render full overlay variant when variant prop is overlay', () => {
    const wrapper = mount(Loader, {
      props: {
        message: 'Loading...',
        variant: 'overlay'
      }
    })

    expect(wrapper.find('.loader').classes()).toContain('loader-overlay')
  })

  it('should render inline variant by default', () => {
    const wrapper = mount(Loader, {
      props: {
        message: 'Loading...'
      }
    })

    expect(wrapper.find('.loader').classes()).toContain('loader-inline')
  })

  it('should not render text when message is empty', () => {
    const wrapper = mount(Loader, {
      props: {
        message: ''
      }
    })

    expect(wrapper.find('.loader-text').exists()).toBe(false)
  })

  it('should render custom message', () => {
    const wrapper = mount(Loader, {
      props: {
        message: 'Searching for deals...'
      }
    })

    expect(wrapper.find('.loader-text').text()).toBe('Searching for deals...')
  })
})

