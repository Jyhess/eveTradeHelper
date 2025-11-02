<template>
  <div class="constellations-page">
    <h1>Eve Trade Helper</h1>
    <p class="subtitle">Constellations</p>
    
    <Breadcrumb :items="breadcrumbItems" />
    
    <div class="card">
      <div v-if="loading" class="loading">
        Chargement des constellations...
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="constellations.length > 0" class="constellations-container">
        <div class="stats">
          <p><strong>{{ total }} constellations</strong> dans la région <strong>{{ regionName }}</strong></p>
        </div>
        
        <div class="constellations-grid">
          <div 
            v-for="constellation in constellations" 
            :key="constellation.constellation_id" 
            class="constellation-card"
          >
            <h3>{{ constellation.name }}</h3>
            <div class="constellation-info">
              <p class="constellation-id">ID: {{ constellation.constellation_id }}</p>
              <p class="systems-count">
                <router-link 
                  :to="`/constellations/${constellation.constellation_id}/systems`"
                  class="systems-link"
                >
                  <strong>{{ constellation.systems?.length || 0 }}</strong> système(s)
                </router-link>
              </p>
              <div v-if="constellation.position" class="position">
                <small>
                  Position: ({{ constellation.position.x }}, {{ constellation.position.y }}, {{ constellation.position.z }})
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">
        Aucune constellation trouvée pour cette région.
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Breadcrumb from '../components/Breadcrumb.vue'

export default {
  name: 'Constellations',
  components: {
    Breadcrumb
  },
  props: {
    regionId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      constellations: [],
      total: 0,
      loading: false,
      error: '',
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
      
      return items
    }
  },
  methods: {
    async fetchConstellations() {
      this.loading = true
      this.error = ''
      this.constellations = []
      
      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/regions/${this.regionId}/constellations`
        )
        this.constellations = response.data.constellations || []
        this.total = response.data.total || 0
        
        // Récupérer le nom de la région depuis les régions
        if (this.constellations.length > 0) {
          await this.fetchRegionName()
        }
      } catch (error) {
        this.error = 'Erreur: ' + (error.response?.data?.error || error.message)
        console.error('Erreur lors du chargement des constellations:', error)
      } finally {
        this.loading = false
      }
    },
    async fetchRegionName() {
      try {
        const response = await axios.get('http://localhost:5000/api/v1/regions')
        const region = response.data.regions?.find(r => r.region_id === parseInt(this.regionId))
        if (region) {
          this.regionName = region.name
        }
      } catch (error) {
        console.error('Erreur lors de la récupération du nom de la région:', error)
      }
    }
  },
  mounted() {
    this.fetchConstellations()
  },
  watch: {
    regionId() {
      this.fetchConstellations()
    }
  }
}
</script>

<style scoped>
.constellations-page {
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

.constellations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.constellation-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.constellation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.constellation-card h3 {
  margin: 0 0 10px 0;
  color: #48bb78;
  font-size: 1.2em;
  border-bottom: 2px solid #48bb78;
  padding-bottom: 8px;
}

.constellation-info {
  text-align: left;
}

.constellation-id {
  font-size: 0.85em;
  color: #666;
  margin: 5px 0;
}

.systems-count {
  margin: 10px 0;
  color: #333;
  font-size: 0.95em;
}

.systems-count {
  margin: 10px 0;
  padding-top: 15px;
  border-top: 1px solid #ddd;
}

.systems-link {
  text-decoration: none;
  color: inherit;
  transition: color 0.2s;
}

.systems-link:hover {
  color: #4299e1;
}

.systems-link strong {
  color: #48bb78;
  font-size: 1.1em;
  transition: color 0.2s;
}

.systems-link:hover strong {
  color: #4299e1;
}

.position {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  color: #888;
  font-size: 0.85em;
}
</style>

