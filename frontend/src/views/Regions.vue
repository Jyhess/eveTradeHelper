<template>
  <div class="regions-page">
    <h1>Eve Trade Helper</h1>
    <p class="subtitle">Régions d'Eve Online</p>
    
    <Breadcrumb :items="breadcrumbItems" />
    
    <div class="card">
      <button @click="fetchRegions" class="btn" :disabled="loading">
        {{ loading ? 'Chargement...' : 'Charger les régions' }}
      </button>
      
      <div v-if="error" class="error">{{ error }}</div>
      
      <div v-if="regions.length > 0" class="regions-container">
        <div class="stats">
          <p><strong>{{ total }} régions</strong> chargées</p>
        </div>
        
        <div class="regions-grid">
          <router-link 
            v-for="region in regions" 
            :key="region.region_id" 
            :to="`/regions/${region.region_id}/constellations`"
            class="region-card"
          >
            <h3>{{ region.name }}</h3>
            <div class="region-info">
              <p class="region-id">ID: {{ region.region_id }}</p>
              <p v-if="region.description" class="region-desc">
                {{ region.description.substring(0, 150) }}...
              </p>
              <p class="constellations">
                <strong>{{ region.constellations?.length || 0 }}</strong> constellation(s)
              </p>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Breadcrumb from '../components/Breadcrumb.vue'

export default {
  name: 'Regions',
  components: {
    Breadcrumb
  },
  data() {
    return {
      regions: [],
      total: 0,
      loading: false,
      error: ''
    }
  },
  computed: {
    breadcrumbItems() {
      return [
        { label: 'Accueil', path: '/regions' },
        { label: 'Régions', path: '/regions' }
      ]
    }
  },
  methods: {
    async fetchRegions() {
      this.loading = true
      this.error = ''
      this.regions = []
      
      try {
        const response = await axios.get('http://localhost:5000/api/v1/regions')
        this.regions = response.data.regions || []
        this.total = response.data.total || 0
      } catch (error) {
        this.error = 'Erreur: ' + (error.response?.data?.error || error.message)
        console.error('Erreur lors du chargement des régions:', error)
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    // Charger automatiquement les régions au montage
    this.fetchRegions()
  }
}
</script>

<style scoped>
.regions-page {
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

.btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 30px;
  font-size: 1.1em;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-bottom: 20px;
}

.btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.regions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.region-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  transition: transform 0.2s, box-shadow 0.2s;
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
}

.region-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-color: #667eea;
}

.region-card h3 {
  margin: 0 0 15px 0;
  color: #667eea;
  font-size: 1.3em;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
}

.region-info {
  text-align: left;
}

.region-id {
  font-size: 0.9em;
  color: #666;
  margin: 5px 0;
}

.region-desc {
  font-size: 0.95em;
  color: #555;
  line-height: 1.5;
  margin: 10px 0;
  font-style: italic;
}

.constellations {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
  color: #333;
  font-size: 0.95em;
}

.constellations strong {
  color: #667eea;
  font-size: 1.1em;
}
</style>

