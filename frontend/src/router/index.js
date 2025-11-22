import { createRouter, createWebHistory } from 'vue-router'
import Regions from '../views/Regions.vue'
import Constellations from '../views/Constellations.vue'
import Systems from '../views/Systems.vue'
import Market from '../views/Market.vue'
import Deals from '../views/Deals.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/regions'
  },
  {
    path: '/regions',
    name: 'Regions',
    component: Regions
  },
  {
    path: '/regions/:regionId/constellations',
    name: 'Constellations',
    component: Constellations,
    props: route => ({ regionId: parseInt(route.params.regionId) })
  },
  {
    path: '/constellations/:constellationId/systems',
    name: 'Systems',
    component: Systems,
    props: route => ({ constellationId: parseInt(route.params.constellationId) })
  },
  {
    path: '/systems/:systemId/map',
    name: 'SystemMap',
    component: () => import('../views/SystemMap.vue'),
    props: route => ({
      systemId: parseInt(route.params.systemId),
      maxJumps: route.query.maxJumps ? parseInt(route.query.maxJumps) : undefined
    })
  },
  {
    path: '/systems/:systemId',
    name: 'SystemDetail',
    component: () => import('../views/SystemDetail.vue'),
    props: route => ({ systemId: parseInt(route.params.systemId) })
  },
  {
    path: '/markets',
    name: 'Market',
    component: Market
  },
  {
    path: '/markets/region/:regionId',
    name: 'MarketRegion',
    component: Market,
    props: route => ({ regionId: parseInt(route.params.regionId) })
  },
  {
    path: '/markets/constellation/:constellationId',
    name: 'MarketConstellation',
    component: Market,
    props: route => ({ constellationId: parseInt(route.params.constellationId) })
  },
  {
    path: '/markets/system/:systemId',
    name: 'MarketSystem',
    component: Market,
    props: route => ({ systemId: parseInt(route.params.systemId) })
  },
  {
    path: '/deals',
    name: 'Deals',
    component: Deals
  },
  {
    path: '/deals/region/:regionId',
    name: 'DealsRegion',
    component: Deals,
    props: route => ({ regionId: parseInt(route.params.regionId) })
  },
  {
    path: '/deals/system-to-system',
    name: 'SystemToSystemDeals',
    component: () => import('../views/SystemToSystemDeals.vue')
  },
  {
    path: '/system-map',
    name: 'SystemMapSearch',
    component: () => import('../views/SystemMapSearch.vue')
  },
  {
    path: '/markets/types/:typeId/prices',
    name: 'TypePrices',
    component: () => import('../views/TypePrices.vue'),
    props: route => ({ typeId: parseInt(route.params.typeId) })
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Update document title based on route
router.beforeEach((to, from, next) => {
  const baseTitle = 'Eve Trade Helper'
  let pageTitle = baseTitle

  if (to.name === 'Regions' || to.name === 'Home') {
    pageTitle = 'Regions - ' + baseTitle
  } else if (to.name === 'Constellations') {
    pageTitle = 'Constellations - ' + baseTitle
  } else if (to.name === 'Systems') {
    pageTitle = 'Systems - ' + baseTitle
  } else if (to.name === 'SystemDetail') {
    pageTitle = 'System Details - ' + baseTitle
  } else if (to.name === 'SystemMap') {
    pageTitle = 'System Map - ' + baseTitle
  } else if (to.name === 'Market' || to.name === 'MarketRegion' || to.name === 'MarketConstellation' || to.name === 'MarketSystem') {
    pageTitle = 'Market - ' + baseTitle
  } else if (to.name === 'Deals' || to.name === 'DealsRegion') {
    pageTitle = 'Deals - ' + baseTitle
  } else if (to.name === 'SystemToSystemDeals') {
    pageTitle = 'System to System Deals - ' + baseTitle
  } else if (to.name === 'SystemMapSearch') {
    pageTitle = 'System Map - ' + baseTitle
  } else if (to.name === 'TypePrices') {
    pageTitle = 'Type Prices - ' + baseTitle
  }

  document.title = pageTitle
  next()
})

export default router
