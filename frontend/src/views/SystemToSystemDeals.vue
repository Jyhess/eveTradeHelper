<template>
  <div class="system-to-system-deals-page">
    <div class="card">
      <h1>System to System Deals</h1>
      <p class="page-description">
        Find profitable items to transport between two systems
      </p>

      <div class="search-section">
        <SystemSelector
          ref="fromSystemSelector"
          title="From System"
          id-prefix="from"
          :region-id="fromRegionId"
          :constellation-id="fromConstellationId"
          :system-id="fromSystemId"
          :regions="regions"
          @update:region-id="fromRegionId = $event"
          @update:constellation-id="fromConstellationId = $event"
          @update:system-id="fromSystemId = $event"
          @region-change="onFromRegionChange"
          @constellation-change="onFromConstellationChange"
          @system-change="onFromSystemChange"
          @system-next="focusToSystemSelector"
        />

        <SystemSelector
          ref="toSystemSelector"
          title="To System"
          id-prefix="to"
          :region-id="toRegionId"
          :constellation-id="toConstellationId"
          :system-id="toSystemId"
          :regions="regions"
          @update:region-id="toRegionId = $event"
          @update:constellation-id="toConstellationId = $event"
          @update:system-id="toSystemId = $event"
          @region-change="onToRegionChange"
          @constellation-change="onToConstellationChange"
          @system-change="onToSystemChange"
          @system-next="focusNextField('min-profit-input')"
        />

        <MarketGroupSelector
          id="market-group-select"
          :selected-group-id="selectedGroupId"
          :disabled="!fromSystemId || !toSystemId"
          @update:selected-group-id="selectedGroupId = $event"
          @group-select="onGroupSelect"
          @group-change="onGroupChange"
          @error="error = $event"
        />

        <div class="form-group thresholds-row">
          <div class="threshold-item">
            <label for="min-profit-input">Min Profit (ISK):</label>
            <input
              id="min-profit-input"
              v-model="minProfitIskDisplay"
              type="text"
              placeholder="100 000"
              :disabled="!fromSystemId || !toSystemId"
              @input="handleMinProfitInput"
              @blur="handleMinProfitBlur"
              @keydown.enter="focusNextField('max-volume-input')"
            />
          </div>
          <div class="threshold-item">
            <label for="max-volume-input">Max Volume (m³):</label>
            <input
              id="max-volume-input"
              v-model="maxTransportVolumeDisplay"
              type="text"
              placeholder="Unlimited"
              :disabled="!fromSystemId || !toSystemId"
              @input="handleMaxVolumeInput"
              @blur="handleMaxVolumeBlur"
              @keydown.enter="focusNextField('max-buy-cost-input')"
            />
          </div>
          <div class="threshold-item">
            <label for="max-buy-cost-input">Max Buy Cost (ISK):</label>
            <input
              id="max-buy-cost-input"
              v-model="maxBuyCostDisplay"
              type="text"
              placeholder="Unlimited"
              :disabled="!fromSystemId || !toSystemId"
              @input="handleMaxBuyCostInput"
              @blur="handleMaxBuyCostBlur"
              @keydown.enter="searchDeals"
            />
          </div>
        </div>

        <button
          class="search-button"
          :disabled="!fromSystemId || !toSystemId || searching"
          @click="searchDeals"
        >
          {{ searching ? 'Searching...' : 'Search for Deals' }}
        </button>
      </div>

      <div v-if="error" class="error">
        {{ error }}
      </div>

      <Loader v-if="searching" message="Searching for deals..." variant="overlay" />

      <DealsList
        :search-results="searchResults"
        :deals="filteredDeals"
        :regions="regions"
        :current-region-id="null"
        :current-region-name="''"
        :group-name="groupName"
        :show-sort-controls="false"
        :show-search-criteria="false"
        :min-profit-isk="minProfitIsk"
        :max-transport-volume="maxTransportVolume"
        :max-buy-cost="maxBuyCost"
        @deal-updated="handleDealUpdated"
        @deal-removed="handleDealRemoved"
      />
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import Loader from '../components/Loader.vue'
import SystemSelector from '../components/SystemSelector.vue'
import MarketGroupSelector from '../components/MarketGroupSelector.vue'
import DealsList from '../components/DealsList.vue'
import {
  formatPrice,
  formatVolume,
  formatNumber,
  formatNumberInput,
  parseNumberInput
} from '../utils/numberFormatter'

export default {
  name: 'SystemToSystemDeals',
  components: {
    Loader,
    SystemSelector,
    MarketGroupSelector,
    DealsList
  },
  data() {
    return {
      regions: [],
      fromRegionId: null,
      fromConstellationId: null,
      fromSystemId: null,
      toRegionId: null,
      toConstellationId: null,
      toSystemId: null,
      selectedGroupId: null,
      groupName: '',
      minProfitIsk: 100000.0,
      minProfitIskDisplay: '100 000',
      maxTransportVolume: null,
      maxTransportVolumeDisplay: '',
      maxBuyCost: null,
      maxBuyCostDisplay: '',
      isLoadingSettings: true,
      searching: false,
      error: '',
      searchResults: null
    }
  },
  computed: {
    filteredDeals() {
      if (!this.searchResults || !this.searchResults.deals) return []
      return this.searchResults.deals.filter(deal => {
        if (this.minProfitIsk && deal.profit_isk < this.minProfitIsk) {
          return false
        }
        if (
          this.maxTransportVolume &&
          deal.total_transport_volume &&
          deal.total_transport_volume > this.maxTransportVolume
        ) {
          return false
        }
        if (this.maxBuyCost && deal.total_buy_cost && deal.total_buy_cost > this.maxBuyCost) {
          return false
        }
        return true
      })
    },
    filteredDealsCount() {
      return this.filteredDeals.length
    }
  },
  async mounted() {
    await this.fetchRegions()
    await this.loadSettings()
    this.isLoadingSettings = false
  },
  methods: {
    async fetchRegions() {
      this.error = ''
      try {
        const data = await api.regions.getRegions()
        this.regions = data.regions || []
      } catch (error) {
        this.error = 'Error loading regions: ' + error.message
      }
    },
    onFromRegionChange() {
      this.saveSettings()
    },
    onFromConstellationChange() {
      this.saveSettings()
    },
    onFromSystemChange() {
      this.saveSettings()
    },
    onToRegionChange() {
      this.saveSettings()
    },
    onToConstellationChange() {
      this.saveSettings()
    },
    onToSystemChange() {
      this.saveSettings()
    },
    onGroupSelect() {
      this.saveSettings()
    },
    onGroupChange(group) {
      if (group) {
        this.groupName = group.name
      }
    },
    focusToSystemSelector() {
      // eslint-disable-next-line no-undef
      setTimeout(() => {
        this.$nextTick(() => {
          const systemSelector = this.$refs.toSystemSelector
          if (systemSelector) {
            const regionCombo = systemSelector.$refs.regionCombo
            if (regionCombo && regionCombo.focus) {
              regionCombo.focus()
            }
          }
        })
      }, 50)
    },
    saveSettings() {
      if (this.isLoadingSettings) {
        return
      }
      const settings = {
        fromRegionId: this.fromRegionId,
        fromConstellationId: this.fromConstellationId,
        fromSystemId: this.fromSystemId,
        toRegionId: this.toRegionId,
        toConstellationId: this.toConstellationId,
        toSystemId: this.toSystemId,
        selectedGroupId: this.selectedGroupId,
        minProfitIsk: this.minProfitIsk,
        maxTransportVolume: this.maxTransportVolume,
        maxBuyCost: this.maxBuyCost
      }
      try {
        localStorage.setItem('system_to_system_deals_settings', JSON.stringify(settings))
      } catch (error) {
        console.warn('Unable to save settings to localStorage:', error)
      }
    },
    async loadSettings() {
      this.isLoadingSettings = true
      try {
        const saved = localStorage.getItem('system_to_system_deals_settings')
        if (saved) {
          const settings = JSON.parse(saved)

          // Restore from system values sequentially
          if (settings.fromRegionId !== undefined && settings.fromRegionId !== null) {
            this.fromRegionId = settings.fromRegionId
            await this.$nextTick()
            // Wait for SystemSelector watcher to load constellations
            const fromSelector = this.$refs.fromSystemSelector
            if (fromSelector) {
              // Wait for loading to complete
              while (fromSelector.loadingConstellations) {
                // eslint-disable-next-line no-undef
                await new Promise(resolve => setTimeout(resolve, 50))
              }
              // eslint-disable-next-line no-undef
              await new Promise(resolve => setTimeout(resolve, 100))
            }
            
            if (settings.fromConstellationId !== undefined && settings.fromConstellationId !== null) {
              this.fromConstellationId = settings.fromConstellationId
              await this.$nextTick()
              // Wait for SystemSelector watcher to load systems
              if (fromSelector) {
                while (fromSelector.loadingSystems) {
                  // eslint-disable-next-line no-undef
                  await new Promise(resolve => setTimeout(resolve, 50))
                }
                // eslint-disable-next-line no-undef
                await new Promise(resolve => setTimeout(resolve, 100))
              }
              
              if (settings.fromSystemId !== undefined && settings.fromSystemId !== null) {
                this.fromSystemId = settings.fromSystemId
                await this.$nextTick()
              }
            }
          }

          // Restore to system values sequentially
          if (settings.toRegionId !== undefined && settings.toRegionId !== null) {
            this.toRegionId = settings.toRegionId
            await this.$nextTick()
            // Wait for SystemSelector watcher to load constellations
            const toSelector = this.$refs.toSystemSelector
            if (toSelector) {
              // Wait for loading to complete
              while (toSelector.loadingConstellations) {
                // eslint-disable-next-line no-undef
                await new Promise(resolve => setTimeout(resolve, 50))
              }
              // eslint-disable-next-line no-undef
              await new Promise(resolve => setTimeout(resolve, 100))
            }
            
            if (settings.toConstellationId !== undefined && settings.toConstellationId !== null) {
              this.toConstellationId = settings.toConstellationId
              await this.$nextTick()
              // Wait for SystemSelector watcher to load systems
              if (toSelector) {
                while (toSelector.loadingSystems) {
                  // eslint-disable-next-line no-undef
                  await new Promise(resolve => setTimeout(resolve, 50))
                }
                // eslint-disable-next-line no-undef
                await new Promise(resolve => setTimeout(resolve, 100))
              }
              
              if (settings.toSystemId !== undefined && settings.toSystemId !== null) {
                this.toSystemId = settings.toSystemId
                await this.$nextTick()
              }
            }
          }

          if (settings.selectedGroupId !== undefined && settings.selectedGroupId !== null) {
            this.selectedGroupId = settings.selectedGroupId
          }
          if (settings.minProfitIsk !== undefined && settings.minProfitIsk !== null) {
            this.minProfitIsk = settings.minProfitIsk
            this.minProfitIskDisplay = formatNumberInput(settings.minProfitIsk.toString())
          }
          if (settings.maxTransportVolume !== undefined && settings.maxTransportVolume !== null) {
            this.maxTransportVolume = settings.maxTransportVolume
            this.maxTransportVolumeDisplay = formatNumberInput(settings.maxTransportVolume.toString())
          }
          if (settings.maxBuyCost !== undefined && settings.maxBuyCost !== null) {
            this.maxBuyCost = settings.maxBuyCost
            this.maxBuyCostDisplay = formatNumberInput(settings.maxBuyCost.toString())
          }
        }
      } catch (error) {
        console.warn('Unable to load settings from localStorage:', error)
      } finally {
        this.isLoadingSettings = false
      }
    },
    handleMinProfitInput(event) {
      const inputValue = event.target.value
      this.minProfitIskDisplay = inputValue
      const value = parseNumberInput(inputValue)
      if (value !== null && value >= 0) {
        this.minProfitIsk = value
      } else if (inputValue === '' || inputValue.trim() === '') {
        this.minProfitIsk = 0
      }
      this.saveSettings()
    },
    handleMinProfitBlur() {
      const parsed = parseNumberInput(this.minProfitIskDisplay)
      if (parsed !== null && parsed >= 0) {
        this.minProfitIsk = parsed
        this.minProfitIskDisplay = formatNumberInput(parsed.toString())
      } else {
        this.minProfitIsk = 100000
        this.minProfitIskDisplay = formatNumberInput('100000')
      }
      this.saveSettings()
    },
    handleMaxVolumeInput(event) {
      const inputValue = event.target.value
      this.maxTransportVolumeDisplay = inputValue
      const value = parseNumberInput(inputValue)
      this.maxTransportVolume = value
      this.saveSettings()
    },
    handleMaxVolumeBlur() {
      const parsed = parseNumberInput(this.maxTransportVolumeDisplay)
      this.maxTransportVolume = parsed
      if (parsed !== null && parsed >= 0) {
        this.maxTransportVolumeDisplay = formatNumberInput(parsed.toString())
      } else {
        this.maxTransportVolume = null
        this.maxTransportVolumeDisplay = ''
      }
      this.saveSettings()
    },
    handleMaxBuyCostInput(event) {
      const inputValue = event.target.value
      this.maxBuyCostDisplay = inputValue
      const value = parseNumberInput(inputValue)
      this.maxBuyCost = value
      this.saveSettings()
    },
    handleMaxBuyCostBlur() {
      const parsed = parseNumberInput(this.maxBuyCostDisplay)
      this.maxBuyCost = parsed
      if (parsed !== null && parsed >= 0) {
        this.maxBuyCostDisplay = formatNumberInput(parsed.toString())
      } else {
        this.maxBuyCost = null
        this.maxBuyCostDisplay = ''
      }
      this.saveSettings()
    },
    handleDealUpdated(event) {
      if (!this.searchResults || !this.searchResults.deals) {
        return
      }
      const index = this.searchResults.deals.findIndex(
        d =>
          d.type_id === event.oldDeal.type_id &&
          d.buy_region_id === event.oldDeal.buy_region_id &&
          d.sell_region_id === event.oldDeal.sell_region_id
      )
      if (index !== -1) {
        this.searchResults.deals[index] = event.newDeal
      }
    },
    handleDealRemoved(deal) {
      if (!this.searchResults || !this.searchResults.deals) {
        return
      }
      const index = this.searchResults.deals.findIndex(
        d =>
          d.type_id === deal.type_id &&
          d.buy_region_id === deal.buy_region_id &&
          d.sell_region_id === deal.sell_region_id
      )
      if (index !== -1) {
        this.searchResults.deals.splice(index, 1)
      }
    },
    async searchDeals() {
      if (!this.fromSystemId || !this.toSystemId) {
        this.error = 'Please select both systems'
        return
      }

      this.searching = true
      this.error = ''
      this.searchResults = null

      try {
        const params = {
          from_system_id: this.fromSystemId,
          to_system_id: this.toSystemId,
          min_profit_isk: this.minProfitIsk
        }
        if (this.selectedGroupId !== null && this.selectedGroupId !== undefined) {
          params.group_id = this.selectedGroupId
        }
        if (this.maxTransportVolume !== null && this.maxTransportVolume !== undefined) {
          params.max_transport_volume = this.maxTransportVolume
        }
        if (this.maxBuyCost !== null && this.maxBuyCost !== undefined) {
          params.max_buy_cost = this.maxBuyCost
        }

        const data = await api.markets.searchSystemToSystemDeals(params)
        this.searchResults = data
      } catch (error) {
        this.error = 'Error searching for deals: ' + error.message
      } finally {
        this.searching = false
      }
    },
    focusNextField(fieldId) {
      // Use setTimeout to ensure blur from previous element is complete
      // eslint-disable-next-line no-undef
      setTimeout(() => {
        this.$nextTick(() => {
          const nextField = document.getElementById(fieldId)
          if (nextField) {
            nextField.focus()
          }
        })
      }, 50)
    },
    formatPrice,
    formatVolume,
    formatNumber
  }
}
</script>

<style scoped>
.system-to-system-deals-page {
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
}

.search-section {
  margin-bottom: 30px;
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


.thresholds-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.threshold-item {
  flex: 1;
  min-width: 200px;
}

.threshold-item input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
}

.search-button {
  padding: 12px 30px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1.1em;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.search-button:hover:not(:disabled) {
  background: #5568d3;
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

