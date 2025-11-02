<template>
  <div class="systems-page">
    <h1>Eve Trade Helper</h1>
    <p class="subtitle">Systèmes</p>
    
    <Breadcrumb :items="breadcrumbItems" />
    
    <div class="card">
      <div v-if="loading" class="loading">
        Chargement des systèmes...
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="systems.length > 0" class="systems-container">
        <div class="stats">
          <p><strong>{{ total }} systèmes</strong> dans la constellation <strong>{{ constellationName }}</strong></p>
        </div>
        
        <div class="systems-grid">
          <div 
            v-for="system in systems" 
            :key="system.system_id" 
            class="system-card"
          >
            <h3>{{ system.name }}</h3>
            <div class="system-info">
              <p class="system-id">ID: {{ system.system_id }}</p>
              <p class="security-status" :class="getSecurityClass(system.security_status)">
                <strong>Sécurité: {{ system.security_status.toFixed(1) }}</strong>
                <span v-if="system.security_class">{{ system.security_class }}</span>
              </p>
              <p class="planets-count">
                <strong>{{ system.planets?.length || 0 }}</strong> planète(s)
              </p>
              <div v-if="system.position" class="position">
                <small>
                  Position: ({{ Math.round(system.position.x) }}, {{ Math.round(system.position.y) }}, {{ Math.round(system.position.z) }})
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">
        Aucun système trouvé pour cette constellation.
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Breadcrumb from '../components/Breadcrumb.vue'

export default {
  name: 'Systems',
  components: {
    Breadcrumb
  },
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
  computed: {
    breadcrumbItems() {
      const items = [
        { label: 'Accueil', path: '/regions' },
        { label: 'Régions', path: '/regions' }
      ]
      
      if (this.regionName) {
        items.push({
          label: this.regionName,
          path: `/regions/${this.regionId}/constellations`
        })
      }
      
      if (this.constellationName) {
        items.push({
          label: this.constellationName,
          path: `/constellations/${this.constellationId}/systems`
        })
      }
      
      return items
    }
  },
  methods: {
    async fetchSystems() {
      this.loading = true
      this.error = ''
      this.systems = []
      
      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/constellations/${this.constellationId}/systems`
        )
        this.systems = response.data.systems || []
        this.total = response.data.total || 0
        
        // Récupérer le nom de la constellation et de la région
        if (this.systems.length > 0) {
          await this.fetchConstellationInfo()
        }
      } catch (error) {
        this.error = 'Erreur: ' + (error.response?.data?.error || error.message)
        console.error('Erreur lors du chargement des systèmes:', error)
      } finally {
        this.loading = false
      }
    },
    async fetchConstellationInfo() {
      try {
        // Récupérer toutes les régions pour trouver celle qui contient cette constellation
        const regionsResponse = await axios.get('http://localhost:5000/api/v1/regions')
        const regions = regionsResponse.data.regions || []
        
        for (const region of regions) {
          const constellationsResponse = await axios.get(
            `http://localhost:5000/api/v1/regions/${region.region_id}/constellations`
          )
          const constellation = constellationsResponse.data.constellations?.find(
            c => c.constellation_id === parseInt(this.constellationId)
          )
          
          if (constellation) {
            this.constellationName = constellation.name
            this.regionId = region.region_id
            this.regionName = region.name
            break
          }
        }
      } catch (error) {
        console.error('Erreur lors de la récupération des informations:', error)
      }
    },
    getSecurityClass(securityStatus) {
      if (securityStatus >= 0.5) return 'high-sec'
      if (securityStatus > 0.0) return 'low-sec'
      return 'null-sec'
    }
  },
  mounted() {
    this.fetchSystems()
  },
  watch: {
    constellationId() {
      this.fetchSystems()
    }
  }
}
</script>

<style scoped>
.systems-page {
  min-height: 100vh;
  padding: 20px;
}

h1 {
  font-size: 2.5em;
  color: white;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
  text-align: center;
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2em;
  margin-bottom: 30px;
  text-align: center;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
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
  transition: transform 0.2s, box-shadow 0.2s;
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

.security-status.high-sec {
  background: #c6f6d5;
  color: #22543d;
}

.security-status.low-sec {
  background: #feebc8;
  color: #7c2d12;
}

.security-status.null-sec {
  background: #fed7d7;
  color: #742a2a;
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
</style>

