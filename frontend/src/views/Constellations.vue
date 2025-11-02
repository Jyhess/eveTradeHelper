<template>
  <div class="constellations-page">
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
          <div class="action-links">
            <p class="market-link">
              <router-link :to="`/markets/region/${regionId}`" class="market-button">
                📊 Voir le marché de cette région
              </router-link>
            </p>
            <p class="deals-link">
              <router-link :to="`/deals/region/${regionId}`" class="deals-button">
                💰 Trouver les bonnes affaires
              </router-link>
            </p>
          </div>
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
import eventBus from '../utils/eventBus'

export default {
  name: 'Constellations',
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
        
        // Mettre à jour le breadcrumb dans le header
        if (this.regionName) {
          eventBus.emit('breadcrumb-update', {
            regionName: this.regionName,
            regionId: this.regionId
          })
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

.action-links {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 10px;
  flex-wrap: wrap;
}

.market-link,
.deals-link {
  margin: 0;
}

.market-button,
.deals-button {
  display: inline-block;
  padding: 10px 20px;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.2s, transform 0.2s;
}

.market-button {
  background: #48bb78;
}

.market-button:hover {
  background: #38a169;
  transform: translateY(-1px);
}

.deals-button {
  background: #667eea;
}

.deals-button:hover {
  background: #5568d3;
  transform: translateY(-1px);
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

