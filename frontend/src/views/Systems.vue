<template>
  <div class="systems-page">
    <div class="card">
      <div v-if="loading" class="loading">Loading systems...</div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="systems.length > 0" class="systems-container">
        <div class="stats">
          <p>
            <strong>{{ total }} systems</strong> in constellation
            <strong>{{ constellationName }}</strong>
          </p>
          <p class="market-link">
            <router-link :to="`/markets/constellation/${constellationId}`" class="market-button">
              📊 View market for this constellation
            </router-link>
          </p>
        </div>

        <div class="systems-grid">
          <div v-for="system in systems" :key="system.system_id" class="system-card">
            <h3>{{ system.name }}</h3>
            <div class="system-info">
              <p class="system-id">ID: {{ system.system_id }}</p>
              <p class="security-status" :class="getSecurityClass(system.security_status)">
                <strong>Security: {{ system.security_status.toFixed(1) }}</strong>
                <span v-if="system.security_class">{{ system.security_class }}</span>
              </p>
              <p class="planets-count">
                <strong>{{ system.planets?.length || 0 }}</strong> planet(s)
              </p>
              <div v-if="system.position" class="position">
                <small>
                  Position: ({{ Math.round(system.position.x) }},
                  {{ Math.round(system.position.y) }}, {{ Math.round(system.position.z) }})
                </small>
              </div>
              <router-link :to="`/systems/${system.system_id}`" class="system-detail-link">
                View details and connections →
              </router-link>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">No systems found for this constellation.</div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import eventBus from '../utils/eventBus'

export default {
  name: 'Systems',
  props: {
    constellationId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      systems: [],
      total: 0,
      loading: false,
      error: '',
      constellationName: '',
      regionId: null,
      regionName: ''
    }
  },
  watch: {
    constellationId() {
      this.fetchSystems()
    }
  },
  mounted() {
    this.fetchSystems()
  },
  methods: {
    async fetchSystems() {
      this.loading = true
      this.error = ''
      this.systems = []

      try {
        const data = await api.constellations.getSystems(this.constellationId)
        this.systems = data.systems || []
        this.total = data.total || 0

        // Retrieve constellation and region names
        if (this.systems.length > 0) {
          await this.fetchConstellationInfo()
        }
      } catch (error) {
        this.error = 'Error: ' + error.message
      } finally {
        this.loading = false
      }
    },
    async fetchConstellationInfo() {
      try {
        // Retrieve all regions to find the one containing this constellation
        const regionsData = await api.regions.getRegions()
        const regions = regionsData.regions || []

        for (const region of regions) {
          const constellationsData = await api.regions.getConstellations(region.region_id)
          const constellation = constellationsData.constellations?.find(
            c => c.constellation_id === parseInt(this.constellationId)
          )

          if (constellation) {
            this.constellationName = constellation.name
            this.regionId = region.region_id
            this.regionName = region.name
            // Update breadcrumb in header
            eventBus.emit('breadcrumb-update', {
              regionName: this.regionName,
              regionId: this.regionId,
              constellationName: this.constellationName,
              constellationId: this.constellationId
            })
            break
          }
        }
      } catch (error) {
        console.error('Error retrieving information:', error)
      }
    },
    getSecurityClass(securityStatus) {
      if (securityStatus < 0) return 'sec-negative'
      if (securityStatus <= 0.2) return 'sec-red'
      if (securityStatus <= 0.4) return 'sec-orange'
      if (securityStatus <= 0.5) return 'sec-yellow'
      if (securityStatus <= 0.6) return 'sec-green'
      if (securityStatus <= 0.8) return 'sec-green' // Green also up to 0.8
      return 'sec-blue' // > 0.8
    }
  }
}
</script>

<style scoped>
.systems-page {
  min-height: 100vh;
  padding: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #667eea;
  font-size: 1.1em;
}

.error {
  margin-top: 20px;
  padding: 15px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  font-size: 1.1em;
}

.stats {
  margin: 20px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
}

.stats p {
  margin: 0;
  font-size: 1.1em;
  color: #667eea;
}

.market-link {
  margin-top: 10px;
}

.market-button {
  display: inline-block;
  padding: 10px 20px;
  background: #48bb78;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition:
    background 0.2s,
    transform 0.2s;
}

.market-button:hover {
  background: #38a169;
  transform: translateY(-1px);
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

.systems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.system-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.system-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.system-card h3 {
  margin: 0 0 10px 0;
  color: #4299e1;
  font-size: 1.2em;
  border-bottom: 2px solid #4299e1;
  padding-bottom: 8px;
}

.system-info {
  text-align: left;
}

.system-id {
  font-size: 0.85em;
  color: #666;
  margin: 5px 0;
}

.security-status {
  margin: 10px 0;
  padding: 8px;
  border-radius: 4px;
  font-size: 0.95em;
}

.security-status.sec-negative {
  background: #000000;
  color: #ffffff;
}

.security-status.sec-red {
  background: #fed7d7;
  color: #742a2a;
}

.security-status.sec-orange {
  background: #feebc8;
  color: #7c2d12;
}

.security-status.sec-yellow {
  background: #fef9e7;
  color: #744210;
}

.security-status.sec-green {
  background: #c6f6d5;
  color: #22543d;
}

.security-status.sec-blue {
  background: #bee3f8;
  color: #2c5282;
}

.security-status strong {
  display: block;
  margin-bottom: 4px;
}

.planets-count {
  margin: 10px 0;
  color: #333;
  font-size: 0.95em;
}

.planets-count strong {
  color: #4299e1;
  font-size: 1.1em;
}

.position {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  color: #888;
  font-size: 0.85em;
}

.system-detail-link {
  display: inline-block;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
  color: #4299e1;
  text-decoration: none;
  font-size: 0.9em;
  font-weight: 500;
  transition: color 0.2s;
}

.system-detail-link:hover {
  color: #667eea;
  text-decoration: underline;
}
</style>
