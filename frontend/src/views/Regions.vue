<template>
  <div class="regions-page">
    <div class="card">
      <div v-if="error" class="error">{{ error }}</div>

      <div class="filter-section">
        <input
          v-model="searchFilter"
          type="text"
          class="filter-input"
          placeholder="Search for a region..."
          :disabled="loading"
        />
        <div v-if="!loading" class="filter-info">
          <span v-if="searchFilter">
            {{ filteredRegions.length }} region(s) found out of {{ total }}
          </span>
          <span v-else> {{ total }} region(s) total </span>
        </div>
      </div>

      <div v-if="loading" class="loading">Loading regions...</div>

      <div v-else-if="filteredRegions.length > 0" class="regions-container">
        <div class="stats">
          <p>
            <strong>{{ filteredRegions.length }}</strong> region(s)
            {{ searchFilter ? 'found' : 'loaded' }}
          </p>
        </div>

        <div class="regions-grid">
          <router-link
            v-for="region in filteredRegions"
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

      <div v-else-if="!loading && regions.length > 0" class="no-results">
        <p>No region matches your search "{{ searchFilter }}"</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'Regions',
  data() {
    return {
      regions: [],
      total: 0,
      loading: false,
      error: '',
      searchFilter: ''
    }
  },
  computed: {
    filteredRegions() {
      if (!this.searchFilter) {
        return this.regions
      }

      const filter = this.searchFilter.toLowerCase().trim()
      return this.regions.filter(
        region =>
          region.name.toLowerCase().includes(filter) ||
          region.description?.toLowerCase().includes(filter) ||
          region.region_id.toString().includes(filter)
      )
    }
  },
  mounted() {
    // Automatically load regions on mount
    this.fetchRegions()
  },
  methods: {
    async fetchRegions() {
      this.loading = true
      this.error = ''
      this.regions = []

      try {
        const data = await api.regions.getRegions()
        this.regions = data.regions || []
        this.total = data.total || 0
      } catch (error) {
        this.error = 'Error: ' + error.message
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.regions-page {
  min-height: 100vh;
  padding: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.filter-section {
  margin-bottom: 20px;
}

.filter-input {
  width: 100%;
  padding: 12px 20px;
  font-size: 1em;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
  box-sizing: border-box;
}

.filter-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.filter-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.filter-info {
  margin-top: 10px;
  color: #666;
  font-size: 0.9em;
  text-align: right;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #667eea;
  font-size: 1.1em;
}

.no-results {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
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
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
}

.region-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
