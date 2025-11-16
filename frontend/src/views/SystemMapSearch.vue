<template>
  <div class="system-map-search-page">
    <div class="card">
      <h1>System Map</h1>
      <p class="page-description">
        Select a system below to view the system map with all systems within 3 jumps and their connections.
      </p>

      <div class="search-container">
        <div class="search-method">
          <SystemSelector
            title="Select System"
            id-prefix="system-map-search"
            :region-id="regionId"
            :constellation-id="constellationId"
            :system-id="selectedSystemId"
            @region-change="handleRegionChange"
            @constellation-change="handleConstellationChange"
            @system-change="handleSystemChange"
          />
          <button
            class="search-button"
            :disabled="!selectedSystemId"
            @click="goToMapFromSelector"
          >
            View Map
          </button>
        </div>
      </div>

      <div v-if="error" class="error">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import SystemSelector from '../components/SystemSelector.vue'

export default {
  name: 'SystemMapSearch',
  components: {
    SystemSelector
  },
  data() {
    return {
      regionId: null,
      constellationId: null,
      selectedSystemId: null,
      error: ''
    }
  },
  methods: {
    goToMapFromSelector() {
      if (!this.selectedSystemId) {
        this.error = 'Please select a system'
        return
      }

      this.error = ''
      this.$router.push(`/systems/${this.selectedSystemId}/map`)
    },
    handleRegionChange(regionId) {
      this.regionId = regionId
      this.constellationId = null
      this.selectedSystemId = null
    },
    handleConstellationChange(constellationId) {
      this.constellationId = constellationId
      this.selectedSystemId = null
    },
    handleSystemChange(systemId) {
      this.selectedSystemId = systemId
    }
  }
}
</script>

<style scoped>
.system-map-search-page {
  min-height: 100vh;
  padding: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

h1 {
  color: #667eea;
  margin-bottom: 10px;
}

.page-description {
  color: #666;
  margin-bottom: 30px;
  font-size: 1.1em;
}

.search-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.search-method {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.search-method h2 {
  color: #4299e1;
  font-size: 1.3em;
  margin-bottom: 15px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.input-group label {
  font-weight: 500;
  color: #333;
  min-width: 100px;
}

.input-group input {
  flex: 1;
  min-width: 200px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
}

.search-button {
  padding: 10px 20px;
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.search-button:hover:not(:disabled) {
  background: #38a169;
  transform: translateY(-1px);
}

.search-button:disabled {
  background: #ccc;
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
</style>

