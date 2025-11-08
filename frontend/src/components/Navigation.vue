<template>
  <nav class="main-navigation">
    <div class="nav-container">
      <div class="nav-logo">
        <router-link to="/" class="logo-link">Eve Trade Helper</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/regions" class="nav-link" active-class="active">
          Regions
        </router-link>
        <router-link to="/markets" class="nav-link" active-class="active">
          Market
        </router-link>
        <router-link to="/deals" class="nav-link" active-class="active">
          Deals
        </router-link>
      </div>
    </div>
    <div class="breadcrumb-container" v-if="breadcrumbItems.length > 0">
      <Breadcrumb :items="breadcrumbItems" />
    </div>
  </nav>
</template>

<script>
import Breadcrumb from './Breadcrumb.vue'
import eventBus from '../utils/eventBus'

export default {
  name: 'Navigation',
  components: {
    Breadcrumb
  },
  data() {
    return {
      breadcrumbData: {
        regionName: '',
        regionId: null,
        constellationName: '',
        constellationId: null,
        systemName: '',
        systemId: null
      }
    }
  },
  computed: {
    breadcrumbItems() {
      const route = this.$route
      const items = []
      
      // Always start with Home
      items.push({ label: 'Home', path: '/regions' })
      
      // Detect current route and build breadcrumb
      if (route.name === 'Regions' || route.name === 'Home') {
        items.push({ label: 'Regions', path: '/regions' })
      } else if (route.name === 'Constellations') {
        items.push({ label: 'Regions', path: '/regions' })
        if (this.breadcrumbData.regionName) {
          items.push({
            label: this.breadcrumbData.regionName,
            path: `/regions/${this.breadcrumbData.regionId}/constellations`
          })
        }
      } else if (route.name === 'Systems') {
        items.push({ label: 'Regions', path: '/regions' })
        if (this.breadcrumbData.regionName) {
          items.push({
            label: this.breadcrumbData.regionName,
            path: `/regions/${this.breadcrumbData.regionId}/constellations`
          })
        }
        if (this.breadcrumbData.constellationName) {
          items.push({
            label: this.breadcrumbData.constellationName,
            path: `/constellations/${this.breadcrumbData.constellationId}/systems`
          })
        }
      } else if (route.name === 'SystemDetail') {
        items.push({ label: 'Regions', path: '/regions' })
        if (this.breadcrumbData.regionName) {
          items.push({
            label: this.breadcrumbData.regionName,
            path: `/regions/${this.breadcrumbData.regionId}/constellations`
          })
        }
        if (this.breadcrumbData.constellationName) {
          items.push({
            label: this.breadcrumbData.constellationName,
            path: `/constellations/${this.breadcrumbData.constellationId}/systems`
          })
        }
        if (this.breadcrumbData.systemName) {
          items.push({
            label: this.breadcrumbData.systemName,
            path: `/systems/${this.breadcrumbData.systemId}`
          })
        }
      } else if (route.name === 'Market' || route.name === 'MarketRegion' || route.name === 'MarketConstellation' || route.name === 'MarketSystem') {
        items.push({ label: 'Regions', path: '/regions' })
        if (this.breadcrumbData.regionId && this.breadcrumbData.regionName) {
          items.push({
            label: this.breadcrumbData.regionName,
            path: `/regions/${this.breadcrumbData.regionId}/constellations`
          })
        }
        if (this.breadcrumbData.constellationId && this.breadcrumbData.constellationName) {
          items.push({
            label: this.breadcrumbData.constellationName,
            path: `/constellations/${this.breadcrumbData.constellationId}/systems`
          })
        }
        if (this.breadcrumbData.systemId && this.breadcrumbData.systemName) {
          items.push({
            label: this.breadcrumbData.systemName,
            path: `/systems/${this.breadcrumbData.systemId}`
          })
        }
        items.push({
          label: 'Market',
          path: route.path
        })
      } else if (route.name === 'Deals' || route.name === 'DealsRegion') {
        items.push({ label: 'Deals', path: '/deals' })
        if (this.breadcrumbData.regionName) {
          items.push({
            label: this.breadcrumbData.regionName,
            path: null
          })
        }
      }
      
      return items
    }
  },
  mounted() {
    // Listen to events to update breadcrumb
    eventBus.on('breadcrumb-update', this.updateBreadcrumb)
  },
  beforeUnmount() {
    eventBus.off('breadcrumb-update', this.updateBreadcrumb)
  },
  watch: {
    $route() {
      // Reset breadcrumb data on route change
      this.breadcrumbData = {
        regionName: '',
        regionId: null,
        constellationName: '',
        constellationId: null,
        systemName: '',
        systemId: null
      }
    }
  },
  methods: {
    updateBreadcrumb(data) {
      this.breadcrumbData = { ...this.breadcrumbData, ...data }
    }
  }
}
</script>

<style scoped>
.main-navigation {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
  margin-bottom: 20px;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
}

.nav-logo {
  font-size: 1.5em;
  font-weight: 700;
}

.logo-link {
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s;
}

.logo-link:hover {
  color: #5568d3;
}

.nav-links {
  display: flex;
  gap: 30px;
  align-items: center;
}

.nav-link {
  color: #333;
  text-decoration: none;
  font-size: 1.1em;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.2s;
  position: relative;
}

.nav-link:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.nav-link.active {
  color: #667eea;
  background: rgba(102, 126, 234, 0.15);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 3px;
  background: #667eea;
  border-radius: 2px;
}

.breadcrumb-container {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.98);
}
</style>
