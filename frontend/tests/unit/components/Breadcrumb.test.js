import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Breadcrumb from '@/components/Breadcrumb.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
    { path: '/regions', name: 'regions', component: { template: '<div>Regions</div>' } }
  ]
})

describe('Breadcrumb Component', () => {
  it('should render breadcrumb items', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Regions', path: '/regions' },
      { label: 'Current Page' }
    ]

    const wrapper = mount(Breadcrumb, {
      props: { items },
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.find('.breadcrumb').exists()).toBe(true)
    expect(wrapper.findAll('.breadcrumb-item')).toHaveLength(3)
  })

  it('should not render when items array is empty', () => {
    const wrapper = mount(Breadcrumb, {
      props: { items: [] },
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.find('.breadcrumb').exists()).toBe(false)
  })

  it('should render router-link for non-last items', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Current' }
    ]

    const wrapper = mount(Breadcrumb, {
      props: { items },
      global: {
        plugins: [router]
      }
    })

    const links = wrapper.findAll('.breadcrumb-link')
    expect(links).toHaveLength(1)
    expect(links[0].text()).toBe('Home')
  })

  it('should render span for last item', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Current' }
    ]

    const wrapper = mount(Breadcrumb, {
      props: { items },
      global: {
        plugins: [router]
      }
    })

    const current = wrapper.find('.breadcrumb-current')
    expect(current.exists()).toBe(true)
    expect(current.text()).toBe('Current')
  })

  it('should use name property if label is not provided', () => {
    const items = [
      { name: 'Home', path: '/' },
      { name: 'Current' }
    ]

    const wrapper = mount(Breadcrumb, {
      props: { items },
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.text()).toContain('Home')
    expect(wrapper.text()).toContain('Current')
  })

  it('should add active class to last item', () => {
    const items = [
      { label: 'Home', path: '/' },
      { label: 'Current' }
    ]

    const wrapper = mount(Breadcrumb, {
      props: { items },
      global: {
        plugins: [router]
      }
    })

    const itemsElements = wrapper.findAll('.breadcrumb-item')
    expect(itemsElements[1].classes()).toContain('active')
  })
})

