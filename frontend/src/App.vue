<template>
  <div id="app">
    <div class="container">
      <h1>Eve Trade Helper</h1>
      <p class="subtitle">Régions d'Eve Online</p>
      
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
            <div 
              v-for="region in regions" 
              :key="region.region_id" 
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
                <button 
                  @click="showConstellations(region.region_id, region.name)" 
                  class="btn-constellations"
                  :disabled="loadingConstellations === region.region_id"
                >
                  {{ loadingConstellations === region.region_id ? 'Chargement...' : 'Voir les constellations' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Modal pour afficher les constellations -->
      <div v-if="showModal" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>Constellations de {{ selectedRegionName }}</h2>
            <button class="btn-close" @click="closeModal">×</button>
          </div>
          <div class="modal-body">
            <div v-if="constellationsLoading" class="loading">
              Chargement des constellations...
            </div>
            <div v-else-if="constellationsError" class="error">
              {{ constellationsError }}
            </div>
            <div v-else-if="constellations.length > 0" class="constellations-grid">
              <div 
                v-for="constellation in constellations" 
                :key="constellation.constellation_id" 
                class="constellation-card"
              >
                <h4>{{ constellation.name }}</h4>
                <div class="constellation-info">
                  <p class="constellation-id">ID: {{ constellation.constellation_id }}</p>
                  <p class="systems-count">
                    <strong>{{ constellation.systems?.length || 0 }}</strong> système(s)
                  </p>
                  <div v-if="constellation.position" class="position">
                    <small>
                      Position: ({{ constellation.position.x }}, {{ constellation.position.y }}, {{ constellation.position.z }})
                    </small>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="no-data">
              Aucune constellation trouvée pour cette région.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      regions: [],
      total: 0,
      loading: false,
      error: '',
      showModal: false,
      selectedRegionId: null,
      selectedRegionName: '',
      constellations: [],
      constellationsLoading: false,
      constellationsError: '',
      loadingConstellations: null
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
    },
    async showConstellations(regionId, regionName) {
      this.selectedRegionId = regionId
      this.selectedRegionName = regionName
      this.showModal = true
      this.constellations = []
      this.constellationsError = ''
      this.constellationsLoading = true
      this.loadingConstellations = regionId
      
      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/regions/${regionId}/constellations`
        )
        this.constellations = response.data.constellations || []
      } catch (error) {
        this.constellationsError = 'Erreur: ' + (error.response?.data?.error || error.message)
        console.error('Erreur lors du chargement des constellations:', error)
      } finally {
        this.constellationsLoading = false
        this.loadingConstellations = null
      }
    },
    closeModal() {
      this.showModal = false
      this.selectedRegionId = null
      this.selectedRegionName = ''
      this.constellations = []
      this.constellationsError = ''
    }
  }
}
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 20px;
}

body {
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
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

.btn:active:not(:disabled) {
  transform: translateY(0);
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

.regions-container {
  margin-top: 30px;
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
}

.region-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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

.btn-constellations {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  border: none;
  padding: 8px 20px;
  font-size: 0.9em;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-top: 15px;
  width: 100%;
}

.btn-constellations:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
}

.btn-constellations:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 2px solid #e0e0e0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5em;
}

.btn-close {
  background: transparent;
  border: none;
  color: white;
  font-size: 2em;
  cursor: pointer;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 30px;
  overflow-y: auto;
  flex: 1;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #667eea;
  font-size: 1.1em;
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

.constellation-card h4 {
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

.systems-count strong {
  color: #48bb78;
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

