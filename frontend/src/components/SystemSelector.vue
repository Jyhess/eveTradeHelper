<template>
  <div class="system-selection-container">
    <h3>{{ title }}</h3>
    <div class="cascade-selectors">
      <div class="form-group quick-search-group">
        <label :for="`${idPrefix}-quick-search`">Quick Search:</label>
        <div class="quick-search-wrapper">
          <input
            :id="`${idPrefix}-quick-search`"
            v-model="quickSearchText"
            type="text"
            class="quick-search-input"
            placeholder="System or constellation name..."
            @input="handleQuickSearch"
            @keydown.enter="handleQuickSearchEnter"
          />
          <Loader v-if="searching" message="Searching..." size="small" />
          <div v-if="quickSearchResults.length > 0" class="quick-search-results">
            <div
              v-for="result in quickSearchResults"
              :key="result.key"
              class="quick-search-result"
              @click="selectQuickSearchResult(result)"
            >
              <strong>{{ result.name }}</strong>
              <span class="result-type">{{ result.type }}</span>
            </div>
          </div>
          <div v-else-if="quickSearchText && !searching && quickSearchPerformed" class="quick-search-no-results">
            No results found
          </div>
        </div>
      </div>
      <div class="form-group">
        <label :for="`${idPrefix}-region-select`">Region:</label>
        <ComboBox
          :id="`${idPrefix}-region-select`"
          ref="regionCombo"
          v-model="localRegionId"
          :options="regionOptions"
          placeholder="Select a region..."
          @change="onRegionChange"
        />
      </div>

      <div class="form-group">
        <label :for="`${idPrefix}-constellation-select`">Constellation:</label>
        <Loader v-if="loadingConstellations" message="Loading..." size="small" />
        <ComboBox
          v-else
          :id="`${idPrefix}-constellation-select`"
          ref="constellationCombo"
          v-model="localConstellationId"
          :options="constellationOptions"
          placeholder="Select a constellation..."
          :disabled="!localRegionId"
          @change="onConstellationChange"
        />
      </div>

      <div class="form-group">
        <label :for="`${idPrefix}-system-select`">System:</label>
        <Loader v-if="loadingSystems" message="Loading..." size="small" />
        <ComboBox
          v-else
          :id="`${idPrefix}-system-select`"
          ref="systemCombo"
          v-model="localSystemId"
          :options="systemOptions"
          placeholder="Select a system..."
          :disabled="!localConstellationId"
          @change="onSystemChange"
          @next="onSystemNext"
        />
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import Loader from './Loader.vue'
import ComboBox from './ComboBox.vue'

export default {
  name: 'SystemSelector',
  components: {
    Loader,
    ComboBox
  },
  props: {
    title: {
      type: String,
      required: true
    },
    idPrefix: {
      type: String,
      required: true
    },
    regionId: {
      type: Number,
      default: null
    },
    constellationId: {
      type: Number,
      default: null
    },
    systemId: {
      type: Number,
      default: null
    },
    regions: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:regionId', 'update:constellationId', 'update:systemId', 'region-change', 'constellation-change', 'system-change', 'system-next', 'error'],
  data() {
    return {
      localRegionId: null,
      localConstellationId: null,
      localSystemId: null,
      constellations: [],
      systems: [],
      loadingConstellations: false,
      loadingSystems: false,
      quickSearchText: '',
      searching: false,
      quickSearchResults: [],
      quickSearchPerformed: false,
      allRegions: [],
      allConstellations: {},
      allSystems: {},
      searchTimeout: null
    }
  },
  computed: {
    regionOptions() {
      const regionsToUse = this.regions.length > 0 ? this.regions : this.allRegions
      return regionsToUse.map(region => ({
        value: region.region_id,
        label: region.name
      }))
    },
    constellationOptions() {
      return this.constellations.map(constellation => ({
        value: constellation.constellation_id,
        label: constellation.name
      }))
    },
    systemOptions() {
      return this.systems.map(system => ({
        value: system.system_id,
        label: system.name
      }))
    }
  },
  watch: {
    async regionId(newValue, oldValue) {
      if (newValue !== oldValue && newValue !== null) {
        this.localRegionId = newValue
        if (this.$el) {
          // Component is mounted, load constellations
          await this.loadConstellations(newValue)
        }
      }
    },
    async constellationId(newValue, oldValue) {
      if (newValue !== oldValue && newValue !== null) {
        this.localConstellationId = newValue
        if (this.localRegionId && this.$el) {
          // Component is mounted, load systems
          await this.loadSystems(newValue)
        }
      }
    },
    systemId(newValue) {
      this.localSystemId = newValue
    },
    localRegionId(newValue) {
      this.$emit('update:regionId', newValue)
    },
    localConstellationId(newValue) {
      this.$emit('update:constellationId', newValue)
    },
    localSystemId(newValue) {
      this.$emit('update:systemId', newValue)
    }
  },
  async mounted() {
    this.localRegionId = this.regionId
    this.localConstellationId = this.constellationId
    this.localSystemId = this.systemId

    await this.loadAllRegions()

    if (this.localRegionId && this.localConstellationId) {
      await this.loadConstellations(this.localRegionId)
      await this.loadSystems(this.localConstellationId)
    } else if (this.localRegionId) {
      await this.loadConstellations(this.localRegionId)
    }
  },
  methods: {
    async onRegionChange() {
      this.localConstellationId = null
      this.constellations = []
      this.localSystemId = null
      this.systems = []
      this.$emit('region-change', this.localRegionId)

      if (!this.localRegionId) {
        return
      }

      await this.loadConstellations(this.localRegionId)
      this.focusConstellationCombo()
    },
    async onConstellationChange() {
      this.localSystemId = null
      this.systems = []
      this.$emit('constellation-change', this.localConstellationId)

      if (!this.localConstellationId) {
        return
      }

      await this.loadSystems(this.localConstellationId)
      this.focusSystemCombo()
    },
    onSystemChange() {
      this.$emit('system-change', this.localSystemId)
    },
    onSystemNext() {
      this.$emit('system-next')
    },
    async loadConstellations(regionId) {
      this.loadingConstellations = true
      try {
        const data = await api.regions.getConstellations(regionId)
        this.constellations = data.constellations || []
      } catch (error) {
        this.$emit('error', `Error loading constellations: ${error.message}`)
      } finally {
        this.loadingConstellations = false
      }
    },
    async loadSystems(constellationId) {
      this.loadingSystems = true
      try {
        const data = await api.constellations.getSystems(constellationId)
        this.systems = data.systems || []
      } catch (error) {
        this.$emit('error', `Error loading systems: ${error.message}`)
      } finally {
        this.loadingSystems = false
      }
    },
    focusConstellationCombo() {
      this.$nextTick(() => {
        // eslint-disable-next-line no-undef
        setTimeout(() => {
          const combo = this.$refs.constellationCombo
          if (combo && combo.focus) {
            combo.focus()
          }
        }, 100)
      })
    },
    focusSystemCombo() {
      this.$nextTick(() => {
        // eslint-disable-next-line no-undef
        setTimeout(() => {
          const combo = this.$refs.systemCombo
          if (combo && combo.focus) {
            combo.focus()
          }
        }, 100)
      })
    },
    async loadAllRegions() {
      try {
        const data = await api.regions.getRegions()
        this.allRegions = data.regions || []
      } catch (error) {
        console.error('Error loading all regions:', error)
      }
    },
    async loadAllConstellationsForRegion(regionId) {
      if (this.allConstellations[regionId]) {
        return this.allConstellations[regionId]
      }

      try {
        const data = await api.regions.getConstellations(regionId)
        const constellations = data.constellations || []
        this.allConstellations[regionId] = constellations
        return constellations
      } catch (error) {
        console.error(`Error loading constellations for region ${regionId}:`, error)
        return []
      }
    },
    async loadAllSystemsForConstellation(constellationId) {
      if (this.allSystems[constellationId]) {
        return this.allSystems[constellationId]
      }

      try {
        const data = await api.constellations.getSystems(constellationId)
        const systems = data.systems || []
        this.allSystems[constellationId] = systems
        return systems
      } catch (error) {
        console.error(`Error loading systems for constellation ${constellationId}:`, error)
        return []
      }
    },
    handleQuickSearch() {
      if (this.searchTimeout) {
        // eslint-disable-next-line no-undef
        clearTimeout(this.searchTimeout)
      }

      const searchText = this.quickSearchText.trim().toLowerCase()

      if (!searchText || searchText.length < 2) {
        this.quickSearchResults = []
        this.quickSearchPerformed = false
        this.searching = false
        return
      }

      this.searching = true
      this.quickSearchPerformed = false
      this.quickSearchResults = []

      // eslint-disable-next-line no-undef
      this.searchTimeout = setTimeout(() => {
        this.performQuickSearch(searchText)
      }, 300)
    },
    async performQuickSearch(searchText) {
      const results = []

      if (!searchText || searchText.trim().length < 2) {
        this.quickSearchResults = []
        this.quickSearchPerformed = true
        this.searching = false
        return
      }

      try {
        const searchTerm = searchText.trim()
        console.log('Performing quick search with:', searchTerm)
        
        const [systemsData, constellationsData] = await Promise.all([
          api.systems.getAllSystems(searchTerm),
          api.constellations.getAllConstellations(searchTerm)
        ])

        console.log('Systems data:', systemsData)
        console.log('Constellations data:', constellationsData)

        const systems = systemsData?.systems || []
        const constellations = constellationsData?.constellations || []

        console.log('Found systems:', systems.length)
        console.log('Found constellations:', constellations.length)

        for (const constellation of constellations) {
          if (constellation && constellation.constellation_id && constellation.name) {
            results.push({
              key: `constellation-${constellation.constellation_id}`,
              name: constellation.name,
              type: 'Constellation',
              regionId: constellation.region_id,
              regionName: '',
              constellationId: constellation.constellation_id,
              systemId: null
            })
          }
        }

        for (const system of systems) {
          if (system && system.system_id && system.name) {
            results.push({
              key: `system-${system.system_id}`,
              name: system.name,
              type: 'System',
              regionId: system.region_id,
              regionName: '',
              constellationId: system.constellation_id,
              constellationName: '',
              systemId: system.system_id
            })
          }
        }
      } catch (error) {
        console.error('Error in performQuickSearch:', error)
        console.error('Error details:', error.response?.data || error.message)
        this.$emit('error', `Error searching: ${error.message}`)
      }

      console.log('Final results:', results.length)
      this.quickSearchResults = results.slice(0, 20)
      this.quickSearchPerformed = true
      this.searching = false
    },
    handleQuickSearchEnter() {
      if (this.quickSearchResults.length === 1) {
        this.selectQuickSearchResult(this.quickSearchResults[0])
      }
    },
    async selectQuickSearchResult(result) {
      this.quickSearchText = ''
      this.quickSearchResults = []
      this.quickSearchPerformed = false

      if (result.systemId) {
        this.localRegionId = result.regionId
        this.localConstellationId = result.constellationId
        this.localSystemId = result.systemId

        await this.loadConstellations(result.regionId)
        await this.loadSystems(result.constellationId)

        this.$emit('update:regionId', result.regionId)
        this.$emit('update:constellationId', result.constellationId)
        this.$emit('update:systemId', result.systemId)
        this.$emit('region-change', result.regionId)
        this.$emit('constellation-change', result.constellationId)
        this.$emit('system-change', result.systemId)
      } else if (result.constellationId) {
        this.localRegionId = result.regionId
        this.localConstellationId = result.constellationId
        this.localSystemId = null

        await this.loadConstellations(result.regionId)
        await this.loadSystems(result.constellationId)

        this.$emit('update:regionId', result.regionId)
        this.$emit('update:constellationId', result.constellationId)
        this.$emit('update:systemId', null)
        this.$emit('region-change', result.regionId)
        this.$emit('constellation-change', result.constellationId)

        this.focusSystemCombo()
      }
    }
  }
}
</script>

<style scoped>
.system-selection-container {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.system-selection-container h3 {
  margin: 0 0 15px 0;
  color: #667eea;
  font-size: 1.2em;
}

.cascade-selectors {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  align-items: start;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.quick-search-group {
  position: relative;
}

.quick-search-wrapper {
  position: relative;
}

.quick-search-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  box-sizing: border-box;
}

.quick-search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.quick-search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.quick-search-result {
  padding: 10px 15px;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-search-result:hover {
  background: #f0f0f0;
}

.quick-search-result strong {
  color: #333;
}

.result-type {
  font-size: 0.85em;
  color: #667eea;
  font-weight: 500;
  padding: 2px 8px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 4px;
}

.quick-search-no-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  padding: 10px;
  text-align: center;
  color: #999;
  font-style: italic;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}
</style>

