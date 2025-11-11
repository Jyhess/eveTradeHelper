<template>
  <div class="system-selection-container">
    <h3>{{ title }}</h3>
    <div class="cascade-selectors">
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
      loadingSystems: false
    }
  },
  computed: {
    regionOptions() {
      return this.regions.map(region => ({
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
  mounted() {
    this.localRegionId = this.regionId
    this.localConstellationId = this.constellationId
    this.localSystemId = this.systemId

    if (this.localRegionId && this.localConstellationId) {
      this.loadConstellations(this.localRegionId)
      this.loadSystems(this.localConstellationId)
    } else if (this.localRegionId) {
      this.loadConstellations(this.localRegionId)
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
</style>

