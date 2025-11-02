import { createRouter, createWebHistory } from 'vue-router'
import Regions from '../views/Regions.vue'
import Constellations from '../views/Constellations.vue'
import Systems from '../views/Systems.vue'
import Market from '../views/Market.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

