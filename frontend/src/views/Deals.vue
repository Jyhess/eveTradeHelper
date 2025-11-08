<template>
  <div class="deals-page">
    <div class="card">
      <div class="search-section">
        <div class="form-group">
          <label for="region-select">Region:</label>
          <select id="region-select" v-model="selectedRegionId" @change="onRegionChange">
            <option value="">Select a region...</option>
            <option v-for="region in regions" :key="region.region_id" :value="region.region_id">
              {{ region.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="group-select">Market Group:</label>
          <div v-if="loadingGroups" class="loading-small">Loading groups...</div>
          <TreeSelect v-else :tree="marketGroupsTree" :value="selectedGroupId" placeholder="Select a group..."
            :disabled="!selectedRegionId || loadingGroups" @input="handleGroupSelect" @change="handleGroupChange" />
        </div>

        <div class="form-group thresholds-row">
          <div class="threshold-item">
            <label for="min-profit-input">Profit Threshold (ISK):</label>
            <input id="min-profit-input" type="text" v-model="minProfitIskDisplay" placeholder="100 000"
              :disabled="!selectedGroupId" @input="handleMinProfitInput" @blur="handleMinProfitBlur" />
          </div>
          <div class="threshold-item">
            <label for="max-volume-input">Max Transport Volume (m³):</label>
            <input id="max-volume-input" type="text" v-model="maxTransportVolumeDisplay" placeholder="Unlimited"
              :disabled="!selectedGroupId" @input="handleMaxVolumeInput" @blur="handleMaxVolumeBlur" />
          </div>
          <div class="threshold-item">
            <label for="max-buy-cost-input">Max Purchase Amount (ISK):</label>
            <input id="max-buy-cost-input" type="text" v-model="maxBuyCostDisplay" placeholder="Unlimited"
              :disabled="!selectedGroupId" @input="handleMaxBuyCostInput" @blur="handleMaxBuyCostBlur" />
          </div>
        </div>

        <div class="form-group">
          <button type="button" class="btn-add-regions" @click="toggleAdjacentRegionsPanel"
            :disabled="!selectedRegionId">
            {{ showAdjacentRegionsPanel ? 'Hide' : 'Add Adjacent Regions' }}
          </button>

          <div v-if="showAdjacentRegionsPanel && adjacentRegions.length > 0" class="adjacent-regions-panel">
            <label class="panel-label">Select adjacent regions to include:</label>
            <div class="regions-checkboxes">
              <label v-for="region in adjacentRegions" :key="region.region_id" class="region-checkbox-label">
                <input type="checkbox" :value="region.region_id" v-model="selectedAdjacentRegions"
                  :disabled="loadingAdjacentRegions" @change="saveSettings" />
                <span>{{ region.name }}</span>
              </label>
            </div>
            <small v-if="selectedAdjacentRegions.length > 0" class="hint">
              {{ selectedAdjacentRegions.length }} additional region(s) selected
            </small>
          </div>
          <div v-else-if="showAdjacentRegionsPanel && loadingAdjacentRegions" class="adjacent-regions-panel">
            <div class="loading-small">Loading adjacent regions...</div>
          </div>
          <div v-else-if="showAdjacentRegionsPanel && !loadingAdjacentRegions" class="adjacent-regions-panel">
            <p class="no-adjacent-regions">No adjacent regions found</p>
          </div>
        </div>

        <button class="search-button" @click="searchDeals"
          :disabled="!selectedRegionId || !selectedGroupId || searching">
          {{ searching ? 'Searching...' : 'Search for Deals' }}
        </button>
      </div>

      <div v-if="error" class="error">
        {{ error }}
      </div>

      <div v-if="searchResults" class="results-section">
        <div class="results-header">
          <h2>Results</h2>
          <div class="results-stats">
            <p>
              <strong>{{ filteredDealsCount }}</strong> deal(s) found
              <span v-if="selectedAdjacentRegions.length > 0">
                across <strong>{{ 1 + selectedAdjacentRegions.length }}</strong> region(s)
              </span>
              across <strong>{{ searchResults.total_types }}</strong> analyzed type(s)
            </p>
            <p>
              Total potential profit: <strong>{{ formatPrice(searchResults.total_profit_isk || 0) }} ISK</strong>
            </p>
            <p>
              Profit threshold: <strong>{{ formatPrice(searchResults.min_profit_isk || 0) }} ISK</strong> |
              <span v-if="searchResults.max_transport_volume">
                Max volume: <strong>{{ formatVolume(searchResults.max_transport_volume) }} m³</strong> |
              </span>
              <span v-if="searchResults.max_buy_cost">
                Max purchase amount: <strong>{{ formatPrice(searchResults.max_buy_cost) }} ISK</strong> |
              </span>
              <span v-if="selectedAdjacentRegions.length > 0">
                Regions: <strong>{{ regionName }}</strong> + {{ selectedAdjacentRegions.length }} other(s) |
              </span>
              <span v-else>
                Region: <strong>{{ regionName }}</strong> |
              </span>
              Group: <strong>{{ groupName }}</strong>
            </p>
          </div>
        </div>

        <div v-if="filteredDealsCount === 0" class="no-results">
          <p>
            No deals found with the following criteria:
          </p>
          <ul style="text-align: left; display: inline-block;">
            <li>Profit threshold: {{ formatPrice(searchResults.min_profit_isk || 0) }} ISK</li>
            <li v-if="searchResults.max_transport_volume">
              Max volume: {{ formatVolume(searchResults.max_transport_volume) }} m³
            </li>
            <li v-if="searchResults.max_buy_cost">
              Max purchase amount: {{ formatPrice(searchResults.max_buy_cost) }} ISK
            </li>
          </ul>
          <p>Try reducing the profit threshold, increasing the max volume or max purchase amount, or selecting another group.</p>
        </div>

        <div v-else class="deals-list">
          <div class="sort-controls">
            <label>Sort by:</label>
            <select v-model="sortBy" class="sort-select">
              <option value="profit">Profit (%)</option>
              <option value="jumps">Number of jumps</option>
              <option value="profit_isk">Profit (ISK)</option>
            </select>
          </div>
          <div v-for="deal in sortedDeals" :key="`${deal.type_id}-${getDealRegionId(deal)}`" class="deal-item">
            <div class="deal-header">
              <h3>{{ deal.type_name }}</h3>
              <div class="deal-header-right">
                <span v-if="getDealRegionName(deal) && getDealRegionName(deal) !== regionName" class="region-badge">
                  {{ getDealRegionName(deal) }}
                </span>
                <div class="profit-badge" :class="getProfitBadgeClass(deal.profit_percent)">
                  {{ deal.profit_percent }}% profit
                </div>
              </div>
            </div>
            <div class="deal-details">
              <!-- Line 1: Financial calculation -->
              <div class="detail-line financial-line">
                <span class="detail-label">Finance:</span>
                <span class="detail-content">
                  <span class="volume">{{ deal.tradable_volume.toLocaleString('en-US') }}</span>
                  <span class="operator">×</span>
                  <span class="price">{{ formatPrice(deal.buy_price) }} ISK</span>
                  <span class="equals">=</span>
                  <span class="total-buy">{{ formatPrice(deal.total_buy_cost) }} ISK</span>
                  <span class="arrow">→</span>
                  <span class="price">{{ formatPrice(deal.sell_price) }} ISK</span>
                  <span class="equals">=</span>
                  <span class="total-sell">{{ formatPrice(deal.total_sell_revenue) }} ISK</span>
                  <span class="arrow">=></span>
                  <span class="profit-total">{{ formatPrice(deal.profit_isk) }} ISK ({{ deal.profit_percent }}%)</span>
                </span>
              </div>

              <!-- Line 2: Transport -->
              <div class="detail-line transport-line">
                <span class="detail-label">Transport:</span>
                <span class="detail-content">
                  <span class="volume">{{ deal.tradable_volume.toLocaleString('en-US') }}</span>
                  <span class="operator">×</span>
                  <span class="volume-unit">{{ formatVolume(deal.item_volume) }} m³</span>
                  <span class="equals">=</span>
                  <span class="total-volume">{{ formatVolume(deal.total_transport_volume) }} m³</span>
                  <span class="separator">•</span>
                  <span class="jumps-label">Jumps:</span>
                  <span class="jumps-value">
                    <span v-if="deal.jumps !== null && deal.jumps !== undefined">{{ deal.jumps }}</span>
                    <span v-else>Unknown</span>
                  </span>
                  <span class="separator">•</span>
                  <span class="time-label">Time:</span>
                  <span class="time-value">
                    <span v-if="deal.estimated_time_minutes !== null && deal.estimated_time_minutes !== undefined">
                      {{ formatTime(deal.estimated_time_minutes) }}
                    </span>
                    <span v-else>Unknown</span>
                  </span>
                </span>
              </div>

              <!-- Line 3: Route -->
              <div v-if="deal.route_details && deal.route_details.length > 0" class="detail-line route-line">
                <span class="detail-label">Route:</span>
                <span class="detail-content route-content">
                  <span class="route-start-container">
                    <router-link v-if="deal.buy_system_id" :to="`/markets/system/${deal.buy_system_id}?type_id=${deal.type_id}`" class="route-system-link">
                      {{ deal.route_details[0].name }}
                    </router-link>
                    <span v-else class="route-start">{{ deal.route_details[0].name }}</span>
                    <span v-if="isSystemNotInCurrentRegion(deal.buy_system_id, deal.buy_region_id)" class="region-indicator">
                      (
                      <router-link v-if="deal.buy_region_id" :to="`/markets/region/${deal.buy_region_id}?type_id=${deal.type_id}`" class="region-link">
                        {{ getRegionName(deal.buy_region_id) }}
                      </router-link>
                      <span v-else>{{ getRegionName(deal.buy_region_id) }}</span>
                      )
                    </span>
                  </span>
                  <span class="route-separator">[</span>
                  <div class="route-systems-inline">
                    <div v-for="(system, index) in deal.route_details" :key="system.system_id"
                      class="route-system-inline">
                      <div class="danger-indicator-small" :class="getDangerClass(system.security_status)"
                        :title="`${system.name}\nSecurity: ${system.security_status.toFixed(1)}`">
                        <span class="tooltip-text-small">{{ system.name }}<br>Security: {{
                          system.security_status.toFixed(1) }}</span>
                      </div>
                      <span v-if="index < deal.route_details.length - 1" class="route-arrow-small">→</span>
                    </div>
                  </div>
                  <span class="route-separator">]</span>
                  <span class="route-end-container">
                    <router-link v-if="deal.sell_system_id" :to="`/markets/system/${deal.sell_system_id}?type_id=${deal.type_id}`" class="route-system-link">
                      {{ deal.route_details[deal.route_details.length - 1].name }}
                    </router-link>
                    <span v-else class="route-end">{{ deal.route_details[deal.route_details.length - 1].name }}</span>
                    <span v-if="isSystemNotInCurrentRegion(deal.sell_system_id, deal.sell_region_id)" class="region-indicator">
                      (
                      <router-link v-if="deal.sell_region_id" :to="`/markets/region/${deal.sell_region_id}?type_id=${deal.type_id}`" class="region-link">
                        {{ getRegionName(deal.sell_region_id) }}
                      </router-link>
                      <span v-else>{{ getRegionName(deal.sell_region_id) }}</span>
                      )
                    </span>
                  </span>
                </span>
              </div>

              <!-- Line 4: Orders -->
              <div class="detail-line orders-line">
                <span class="detail-label">Orders:</span>
                <span class="detail-content">
                  <span class="orders-buy">{{ deal.buy_order_count }} buy</span>
                  <span class="orders-separator">-</span>
                  <span class="orders-sell">{{ deal.sell_order_count }} sell</span>
                  <span class="separator">•</span>
                  <router-link :to="`/markets/region/${getDealRegionId(deal)}?type_id=${deal.type_id}`"
                    class="market-link-inline">
                    📊 Market Details
                  </router-link>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import TreeSelect from '../components/TreeSelect.vue'
import eventBus from '../utils/eventBus'

export default {
  name: 'Deals',
  components: {
    TreeSelect
  },
  data() {
    return {
      regions: [],
      selectedRegionId: null,
      regionName: '',
      marketGroups: [],
      marketGroupsTree: [],
      selectedGroupId: null,
      groupName: '',
      loadingGroups: false,
      minProfitIsk: 100000, // Minimum profit threshold in ISK
      maxTransportVolume: null, // null = unlimited
      maxBuyCost: null, // null = unlimited - Maximum purchase amount in ISK
      showAdjacentRegionsPanel: false, // Show adjacent regions selection panel
      adjacentRegions: [], // List of adjacent regions
      selectedAdjacentRegions: [], // IDs of selected adjacent regions
      loadingAdjacentRegions: false, // Loading adjacent regions in progress
      searching: false,
      searchResults: null,
      error: '',
      sortBy: 'profit_isk', // Default sort by total profits (ISK)
      isLoadingSettings: false, // Flag to avoid saving during initial load
      // Formatted values for display in inputs
      minProfitIskDisplay: '',
      maxTransportVolumeDisplay: '',
      maxBuyCostDisplay: ''
    }
  },
  computed: {
    sortedDeals() {
      if (!this.searchResults || !this.searchResults.deals) {
        return []
      }
      // Deals are already filtered on backend, we only sort
      const deals = [...this.searchResults.deals]

      // Sort according to selected criterion
      switch (this.sortBy) {
        case 'jumps':
          return deals.sort((a, b) => {
            const aJumps = a.jumps !== null && a.jumps !== undefined ? a.jumps : Infinity
            const bJumps = b.jumps !== null && b.jumps !== undefined ? b.jumps : Infinity
            return aJumps - bJumps
          })
        case 'profit_isk':
          return deals.sort((a, b) => (b.profit_isk || 0) - (a.profit_isk || 0))
        case 'profit':
        default:
          return deals.sort((a, b) => (b.profit_percent || 0) - (a.profit_percent || 0))
      }
    },
    filteredDealsCount() {
      // Counter to display how many deals are returned
      if (!this.searchResults || !this.searchResults.deals) {
        return 0
      }
      return this.searchResults.deals.length
    }
  },
  async mounted() {
    await this.fetchRegions()

    // Load saved values from localStorage
    await this.loadSettings()

    // If we have a regionId in props (from a route), load it (priority over localStorage)
    const routeRegionId = this.$route.params.regionId || this.$route.query.region_id
    if (routeRegionId) {
      this.selectedRegionId = parseInt(routeRegionId)
      this.isLoadingSettings = false // Disable flag because we're loading from route
      await this.onRegionChange()

      // If we have a group_id in query params, select it (priority over localStorage)
      const groupId = this.$route.query.group_id
      if (groupId) {
        await this.$nextTick() // Wait for groups to be loaded
        this.selectedGroupId = parseInt(groupId)
        const group = this.marketGroups.find(g => g.group_id === this.selectedGroupId)
        if (group) {
          this.groupName = group.name
        }
      }
    } else if (this.selectedRegionId) {
      // If we loaded a region from localStorage, load groups
      // Disable flag before calling onRegionChange to allow saving
      this.isLoadingSettings = false
      await this.$nextTick()
      await this.onRegionChange()
    } else {
      // No region loaded, disable flag
      this.isLoadingSettings = false
    }

    // Initialize display values if they haven't been
    if (!this.minProfitIskDisplay || this.minProfitIskDisplay === '') {
      this.minProfitIskDisplay = this.formatNumberInput(this.minProfitIsk)
    }

    // Ensure flag is always disabled at end of mount
    this.isLoadingSettings = false
  },
  methods: {
    saveSettings() {
      // Don't save during initial load
      if (this.isLoadingSettings) {
        return
      }
      // Save values to localStorage
      const settings = {
        selectedRegionId: this.selectedRegionId,
        selectedGroupId: this.selectedGroupId,
        minProfitIsk: this.minProfitIsk,
        maxTransportVolume: this.maxTransportVolume,
        maxBuyCost: this.maxBuyCost,
        selectedAdjacentRegions: this.selectedAdjacentRegions,
        showAdjacentRegionsPanel: this.showAdjacentRegionsPanel
      }
      try {
        localStorage.setItem('deals_settings', JSON.stringify(settings))
        console.log('Settings saved:', settings) // Debug
      } catch (error) {
        console.warn('Unable to save settings to localStorage:', error)
      }
    },
    async loadSettings() {
      // Load values from localStorage
      this.isLoadingSettings = true
      try {
        const saved = localStorage.getItem('deals_settings')
        if (saved) {
          const settings = JSON.parse(saved)

          // Restore values if they exist
          if (settings.selectedRegionId !== undefined && settings.selectedRegionId !== null) {
            this.selectedRegionId = settings.selectedRegionId
          }
          if (settings.selectedGroupId !== undefined && settings.selectedGroupId !== null) {
            this.selectedGroupId = settings.selectedGroupId
          }
          if (settings.minProfitIsk !== undefined && settings.minProfitIsk !== null) {
            this.minProfitIsk = settings.minProfitIsk
            this.minProfitIskDisplay = this.formatNumberInput(this.minProfitIsk)
          }
          if (settings.maxTransportVolume !== undefined) {
            this.maxTransportVolume = settings.maxTransportVolume
            this.maxTransportVolumeDisplay = this.formatNumberInput(this.maxTransportVolume)
          }
          if (settings.maxBuyCost !== undefined) {
            this.maxBuyCost = settings.maxBuyCost
            this.maxBuyCostDisplay = this.formatNumberInput(this.maxBuyCost)
          }
          if (settings.selectedAdjacentRegions !== undefined && Array.isArray(settings.selectedAdjacentRegions)) {
            this.selectedAdjacentRegions = settings.selectedAdjacentRegions
          }
          if (settings.showAdjacentRegionsPanel !== undefined) {
            this.showAdjacentRegionsPanel = settings.showAdjacentRegionsPanel
          }
        }
      } catch (error) {
        console.warn('Unable to load settings from localStorage:', error)
      }
      // Initialize display values if they haven't been loaded
      if (!this.minProfitIskDisplay || this.minProfitIskDisplay === '') {
        this.minProfitIskDisplay = this.formatNumberInput(this.minProfitIsk)
      }
      if ((!this.maxTransportVolumeDisplay || this.maxTransportVolumeDisplay === '') && this.maxTransportVolume !== null) {
        this.maxTransportVolumeDisplay = this.formatNumberInput(this.maxTransportVolume)
      }
      if ((!this.maxBuyCostDisplay || this.maxBuyCostDisplay === '') && this.maxBuyCost !== null) {
        this.maxBuyCostDisplay = this.formatNumberInput(this.maxBuyCost)
      }
      // Flag will be disabled after mounted() finishes
    },
    async fetchRegions() {
      try {
        const data = await api.regions.getRegions()
        this.regions = data.regions || []
        // Find region name if selectedRegionId is already defined
        if (this.selectedRegionId) {
          const region = this.regions.find(r => r.region_id === this.selectedRegionId)
          if (region) {
            this.regionName = region.name
          }
        }
      } catch (error) {
        this.error = 'Error loading regions: ' + error.message
      }
    },
    async onRegionChange() {
      if (!this.selectedRegionId) {
        this.marketGroups = []
        this.selectedGroupId = null
        this.regionName = ''
        this.adjacentRegions = []
        this.selectedAdjacentRegions = []
        this.showAdjacentRegionsPanel = false
        this.saveSettings() // Save changes
        return
      }

      const region = this.regions.find(r => r.region_id === this.selectedRegionId)
      if (region) {
        this.regionName = region.name
        // Update breadcrumb
        eventBus.emit('breadcrumb-update', {
          regionName: this.regionName,
          regionId: this.selectedRegionId
        })
      }

      // Reset adjacent regions (they change according to region)
      this.adjacentRegions = []
      // If we change region manually (not during initial load), reset selections
      if (!this.isLoadingSettings) {
        // This is a manual region change, reset selections
        this.selectedAdjacentRegions = []
      }
      if (this.showAdjacentRegionsPanel) {
        await this.fetchAdjacentRegions()
      }

      await this.fetchMarketGroups()

      // Restore selected group after loading groups
      if (this.selectedGroupId) {
        await this.$nextTick()
        const group = this.findGroupInTree(this.marketGroupsTree, this.selectedGroupId)
        if (group) {
          this.groupName = group.name
        } else {
          const flatGroup = this.marketGroups.find(g => g.group_id === this.selectedGroupId)
          if (flatGroup) {
            this.groupName = flatGroup.name
          }
        }
      }

      this.saveSettings() // Save changes
    },
    async toggleAdjacentRegionsPanel() {
      this.showAdjacentRegionsPanel = !this.showAdjacentRegionsPanel
      if (this.showAdjacentRegionsPanel && this.adjacentRegions.length === 0 && this.selectedRegionId) {
        await this.fetchAdjacentRegions()
      }
      this.saveSettings() // Save panel state
    },
    async fetchAdjacentRegions() {
      if (!this.selectedRegionId) return

      this.loadingAdjacentRegions = true
      try {
        const data = await api.regions.getAdjacentRegions(this.selectedRegionId)
        this.adjacentRegions = data.adjacent_regions || []
        // Filter selected adjacent regions to keep only those that still exist
        // (in case some adjacent regions are no longer available)
        this.selectedAdjacentRegions = this.selectedAdjacentRegions.filter(regionId =>
          this.adjacentRegions.some(r => r.region_id === regionId)
        )
        this.saveSettings() // Save after filtering
      } catch (error) {
        console.error('Error loading adjacent regions:', error)
        this.error = 'Error loading adjacent regions: ' + error.message
        this.adjacentRegions = []
      } finally {
        this.loadingAdjacentRegions = false
      }
    },
    async fetchMarketGroups() {
      if (!this.selectedRegionId) return

      this.loadingGroups = true
      this.error = ''
      this.marketGroups = []
      this.marketGroupsTree = []

      try {
        const data = await api.markets.getCategories()
        const categories = data.categories || []

        // Build hierarchical tree
        this.marketGroupsTree = this.buildTree(categories)

        // Also keep flat list for compatibility
        this.marketGroups = categories.map(cat => ({
          group_id: cat.group_id,
          name: cat.name
        }))

        // Find group name if selectedGroupId is already defined
        if (this.selectedGroupId) {
          const group = this.findGroupInTree(this.marketGroupsTree, this.selectedGroupId)
          if (group) {
            this.groupName = group.name
          } else {
            const flatGroup = this.marketGroups.find(g => g.group_id === this.selectedGroupId)
            if (flatGroup) {
              this.groupName = flatGroup.name
            }
          }
        }
      } catch (error) {
        this.error = 'Error loading market groups: ' + error.message
      } finally {
        this.loadingGroups = false
      }
    },
    buildTree(categories) {
      if (!categories || categories.length === 0) {
        return []
      }

      // Create a map for fast access
      const categoryMap = new Map()
      const rootNodes = []

      // First pass: create all nodes
      categories.forEach(category => {
        categoryMap.set(category.group_id, {
          ...category,
          children: []
        })
      })

      // Second pass: build tree
      categories.forEach(category => {
        const node = categoryMap.get(category.group_id)

        if (category.parent_group_id && categoryMap.has(category.parent_group_id)) {
          // Add this node as child of its parent
          const parent = categoryMap.get(category.parent_group_id)
          parent.children.push(node)
        } else {
          // It's a root node
          rootNodes.push(node)
        }
      })

      // Sort nodes and their children recursively
      const sortNodes = (nodes) => {
        nodes.sort((a, b) => a.name.localeCompare(b.name))
        nodes.forEach(node => {
          if (node.children.length > 0) {
            sortNodes(node.children)
          }
        })
      }

      sortNodes(rootNodes)

      return rootNodes
    },
    handleGroupSelect(groupId) {
      this.selectedGroupId = groupId
      this.saveSettings() // Save group change
    },
    handleGroupChange(group) {
      if (group) {
        this.groupName = group.name
      }
    },
    findGroupInTree(tree, groupId) {
      // Recursive search in tree
      for (const node of tree) {
        if (node.group_id === groupId) {
          return node
        }
        if (node.children && node.children.length > 0) {
          const found = this.findGroupInTree(node.children, groupId)
          if (found) {
            return found
          }
        }
      }
      return null
    },
    async searchDeals() {
      if (!this.selectedRegionId || !this.selectedGroupId) {
        this.error = 'Please select a region and a market group'
        return
      }

      this.searching = true
      this.error = ''
      this.searchResults = null

      if (this.selectedGroupId) {
        const group = this.findGroupInTree(this.marketGroupsTree, this.selectedGroupId)
        if (group) {
          this.groupName = group.name
        } else {
          const flatGroup = this.marketGroups.find(g => g.group_id === this.selectedGroupId)
          if (flatGroup) {
            this.groupName = flatGroup.name
          }
        }
      }

      try {
        // Prepare parameters
        const params = {
          region_id: this.selectedRegionId,
          group_id: this.selectedGroupId,
          min_profit_isk: this.minProfitIsk
        }
        if (this.maxTransportVolume !== null && this.maxTransportVolume > 0) {
          params.max_transport_volume = this.maxTransportVolume
        }
        if (this.maxBuyCost !== null && this.maxBuyCost > 0) {
          params.max_buy_cost = this.maxBuyCost
        }
        // Add selected adjacent regions if they exist
        if (this.selectedAdjacentRegions.length > 0) {
          params.additional_regions = this.selectedAdjacentRegions.join(',')
        }

        const data = await api.markets.searchDeals(params)
        this.searchResults = data

        // Save parameters after successful search
        this.saveSettings()
      } catch (error) {
        this.error = 'Error during search: ' + error.message
      } finally {
        this.searching = false
      }
    },
    formatNumberInput(value) {
      // Format a numeric value for display in an input with thousands separator
      if (value === null || value === undefined || value === '') {
        return ''
      }
      // Convert to number if necessary
      let numValue = value
      if (typeof value === 'string') {
        numValue = parseFloat(value.replace(/\s/g, '').replace(',', '.'))
      }
      if (isNaN(numValue) || numValue < 0) {
        return ''
      }
      // Format with space separator for thousands
      // Use toLocaleString then replace non-breaking spaces with normal spaces
      const formatted = numValue.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: numValue % 1 === 0 ? 0 : 2, // No decimals if integer
        useGrouping: true
      })
      return formatted.replace(/\u00A0/g, ' ') // Replace non-breaking spaces with normal spaces
    },
    parseNumberInput(inputValue) {
      // Parse an input value to a number (removes spaces)
      if (!inputValue || inputValue === '') {
        return null
      }
      // Remove spaces and convert to number
      const cleaned = inputValue.toString().replace(/\s/g, '').replace(',', '.')
      const parsed = parseFloat(cleaned)
      return isNaN(parsed) ? null : parsed
    },
    handleMinProfitInput(event) {
      const inputValue = event.target.value
      // Keep value as is during input (allows free typing)
      this.minProfitIskDisplay = inputValue

      const value = this.parseNumberInput(inputValue)
      if (value !== null && value >= 0) {
        this.minProfitIsk = value
      } else if (inputValue === '' || inputValue.trim() === '') {
        this.minProfitIsk = 0
      }
      this.saveSettings()
    },
    handleMinProfitBlur(event) {
      // Format value on blur
      const value = this.parseNumberInput(event.target.value)
      if (value !== null && value >= 0) {
        this.minProfitIsk = value
        this.minProfitIskDisplay = this.formatNumberInput(value)
      } else {
        this.minProfitIsk = 100000 // Default value
        this.minProfitIskDisplay = this.formatNumberInput(100000)
      }
      this.saveSettings()
    },
    handleMaxVolumeInput(event) {
      const inputValue = event.target.value
      // Keep value as is during input
      this.maxTransportVolumeDisplay = inputValue

      const value = this.parseNumberInput(inputValue)
      this.maxTransportVolume = value
      this.saveSettings()
    },
    handleMaxVolumeBlur(event) {
      // Format value on blur
      const value = this.parseNumberInput(event.target.value)
      this.maxTransportVolume = value
      if (value !== null && value >= 0) {
        this.maxTransportVolumeDisplay = this.formatNumberInput(value)
      } else {
        this.maxTransportVolumeDisplay = ''
      }
      this.saveSettings()
    },
    handleMaxBuyCostInput(event) {
      const inputValue = event.target.value
      // Keep value as is during input
      this.maxBuyCostDisplay = inputValue

      const value = this.parseNumberInput(inputValue)
      this.maxBuyCost = value
      this.saveSettings()
    },
    handleMaxBuyCostBlur(event) {
      // Format value on blur
      const value = this.parseNumberInput(event.target.value)
      this.maxBuyCost = value
      if (value !== null && value >= 0) {
        this.maxBuyCostDisplay = this.formatNumberInput(value)
      } else {
        this.maxBuyCostDisplay = ''
      }
      this.saveSettings()
    },
    formatPrice(price) {
      if (!price && price !== 0) return 'N/A'
      if (price >= 1000) {
        return Math.round(price).toLocaleString('en-US')
      }
      return price.toFixed(2)
    },
    formatVolume(volume) {
      if (!volume && volume !== 0) return 'N/A'
      // Format with 2 decimals for small volumes, rounded for large ones
      if (volume >= 1000) {
        return Math.round(volume).toLocaleString('en-US')
      }
      return volume.toFixed(2)
    },
    formatTime(minutes) {
      if (!minutes && minutes !== 0) return 'N/A'
      if (minutes < 60) {
        return `${minutes} min`
      }
      const hours = Math.floor(minutes / 60)
      const mins = minutes % 60
      if (mins === 0) {
        return `${hours}h`
      }
      return `${hours}h ${mins}min`
    },
    getProfitBadgeClass(profitPercent) {
      if (profitPercent >= 20) return 'profit-excellent'
      if (profitPercent >= 10) return 'profit-good'
      if (profitPercent >= 5) return 'profit-medium'
      return 'profit-low'
    },
    getDealRegionId(deal) {
      // Returns main region if no region specified, otherwise the best region (buy or sell)
      return deal.buy_region_id || deal.sell_region_id || this.selectedRegionId
    },
    getDealRegionName(deal) {
      // Retrieves region name from the regions list
      const regionId = deal.buy_region_id || deal.sell_region_id
      if (!regionId || regionId === this.selectedRegionId) {
        return null
      }
      // Search in loaded regions
      const region = this.regions.find(r => r.region_id === regionId)
      if (region) {
        return region.name
      }
      // Search in adjacent regions
      const adjacentRegion = this.adjacentRegions.find(r => r.region_id === regionId)
      if (adjacentRegion) {
        return adjacentRegion.name
      }
      return `Region ${regionId}`
    },
    getDangerClass(securityStatus) {
      if (securityStatus < 0) return 'danger-negative'
      if (securityStatus <= 0.2) return 'danger-red'
      if (securityStatus <= 0.4) return 'danger-orange'
      if (securityStatus <= 0.5) return 'danger-yellow'
      if (securityStatus <= 0.6) return 'danger-green'
      if (securityStatus <= 0.8) return 'danger-green' // Green also up to 0.8
      return 'danger-blue' // > 0.8
    },
    isSystemNotInCurrentRegion(systemId, regionId) {
      // Returns true if the system is not in the current region
      // If we don't have a current region selected, we cannot determine
      if (!this.selectedRegionId) {
        return false
      }
      // If we don't have a regionId in the data, we cannot determine
      if (!regionId) {
        return false
      }
      // If we have a systemId but no regionId, we cannot determine
      if (systemId && !regionId) {
        return false
      }
      // Compare the system's region with the current region
      return regionId !== this.selectedRegionId
    },
    getRegionName(regionId) {
      // Retrieves a region name by its ID
      if (!regionId) {
        return 'Unknown region'
      }
      // Search in loaded regions
      const region = this.regions.find(r => r.region_id === regionId)
      if (region) {
        return region.name
      }
      // Search in adjacent regions
      const adjacentRegion = this.adjacentRegions.find(r => r.region_id === regionId)
      if (adjacentRegion) {
        return adjacentRegion.name
      }
      return `Region ${regionId}`
    }
  }
}
</script>

<style scoped>
.deals-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: #333;
}


.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.search-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.thresholds-row {
  flex-direction: row;
  gap: 20px;
  align-items: flex-end;
}

.form-group.thresholds-row .threshold-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #667eea;
}

.form-group select,
.form-group input {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1em;
}

.form-group small.hint {
  display: block;
  margin-top: 4px;
  font-size: 0.85em;
  color: #666;
  font-style: italic;
}

.btn-add-regions {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-add-regions:hover:not(:disabled) {
  background: #5568d3;
}

.btn-add-regions:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.adjacent-regions-panel {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.panel-label {
  display: block;
  margin-bottom: 10px;
  font-weight: 500;
  color: #333;
}

.regions-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding: 5px;
}

.region-checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  padding: 5px;
  border-radius: 4px;
  transition: background 0.2s;
}

.region-checkbox-label:hover {
  background: #e8e8e8;
}

.region-checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.region-checkbox-label span {
  color: #333;
}

.no-adjacent-regions {
  color: #999;
  font-style: italic;
  margin: 0;
}

.form-group select:disabled,
.form-group input:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
}

.search-button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.search-button:hover:not(:disabled) {
  background: #5568d3;
}

.search-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading-small {
  font-size: 0.9em;
  color: #667eea;
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

.results-section {
  margin-top: 30px;
}

.results-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.results-header h2 {
  color: #667eea;
  margin-bottom: 10px;
}

.results-stats {
  color: #666;
  font-size: 0.95em;
}

.results-stats p {
  margin: 5px 0;
}

.no-results {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

.deals-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.deal-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
  transition: box-shadow 0.3s;
}

.deal-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.deal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.deal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.3em;
}

.deal-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.region-badge {
  padding: 4px 10px;
  background: #e7f3ff;
  color: #0066cc;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
  border: 1px solid #b3d9ff;
}

.profit-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9em;
  color: white;
}

.profit-excellent {
  background: #28a745;
}

.profit-good {
  background: #17a2b8;
}

.profit-medium {
  background: #ffc107;
  color: #333;
}

.profit-low {
  background: #fd7e14;
}

.deal-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.price-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.price-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background: white;
  border-radius: 4px;
}

.price-label {
  font-weight: 500;
  color: #666;
}

.price-value {
  font-weight: 600;
  font-size: 1.1em;
}

.buy-price {
  color: #28a745;
}

.sell-price {
  color: #dc3545;
}

.profit-item {
  background: #f0f8ff;
  border: 1px solid #667eea;
}

.profit-value {
  color: #667eea;
  font-size: 1.2em;
}

.order-stats {
  display: flex;
  gap: 10px;
  font-size: 0.9em;
  color: #666;
  font-style: italic;
}

.jumps-info {
  color: #667eea;
  font-weight: 600;
}

.jumps-info.unknown {
  color: #999;
  font-weight: normal;
}

.volume-info {
  color: #667eea;
  font-weight: 500;
}

/* Compact detail lines */
.detail-line {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: 6px;
  font-size: 0.95em;
  gap: 12px;
}

.detail-label {
  font-weight: 600;
  color: #667eea;
  min-width: 80px;
  flex-shrink: 0;
}

.detail-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

/* Financial line */
.financial-line {
  background: #f8f9fa;
  border-left: 3px solid #667eea;
}

.financial-line .volume,
.financial-line .price {
  color: #666;
}

.financial-line .operator,
.financial-line .equals {
  color: #999;
  font-weight: 600;
}

.financial-line .total-buy {
  color: #dc3545;
  font-weight: 600;
}

.financial-line .total-sell {
  color: #28a745;
  font-weight: 600;
}

.financial-line .profit-total {
  color: #667eea;
  font-weight: 700;
  font-size: 1.05em;
}

.financial-line .arrow {
  color: #999;
  margin: 0 4px;
}

/* Ligne transport */
.transport-line {
  background: #e7f3ff;
  border-left: 3px solid #0066cc;
}

.transport-line .volume,
.transport-line .volume-unit {
  color: #0066cc;
}

.transport-line .total-volume {
  color: #0066cc;
  font-weight: 600;
}

.transport-line .jumps-label,
.transport-line .time-label {
  color: #666;
  margin-left: 8px;
}

.transport-line .jumps-value,
.transport-line .time-value {
  color: #333;
  font-weight: 600;
}

.transport-line .separator {
  color: #999;
  margin: 0 4px;
}

/* Ligne route */
.route-line {
  background: #fff3cd;
  border-left: 3px solid #ffc107;
}

.route-content {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.route-start,
.route-end {
  font-weight: 700;
  color: #856404;
}

.route-start-container,
.route-end-container {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.route-system-link {
  font-weight: 700;
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s;
}

.route-system-link:hover {
  color: #5568d3;
  text-decoration: underline;
}

.region-indicator {
  font-size: 0.85em;
  color: #dc3545;
  font-weight: 600;
  font-style: italic;
}

.region-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}

.region-link:hover {
  color: #5568d3;
  text-decoration: underline;
}

.route-separator {
  color: #856404;
  font-weight: 600;
}

.route-systems-inline {
  display: flex;
  align-items: center;
  gap: 3px;
}

.route-system-inline {
  display: flex;
  align-items: center;
  gap: 3px;
}

.danger-indicator-small {
  position: relative;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  cursor: help;
  transition: transform 0.2s;
}

.danger-indicator-small:hover {
  transform: scale(1.3);
}

.danger-indicator-small .tooltip-text-small {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 0.85em;
  white-space: nowrap;
  z-index: 1000;
  transition: opacity 0.3s, visibility 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  line-height: 1.4;
}

.danger-indicator-small:hover .tooltip-text-small {
  visibility: visible;
  opacity: 1;
}

.danger-indicator-small .tooltip-text-small::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: #333;
}

.route-arrow-small {
  color: #856404;
  font-size: 0.9em;
  font-weight: 600;
  margin: 0 2px;
}

/* Ligne ordres */
.orders-line {
  background: #d1ecf1;
  border-left: 3px solid #0c5460;
}

.orders-line .orders-buy {
  color: #dc3545;
  font-weight: 600;
}

.orders-line .orders-separator {
  color: #0c5460;
  font-weight: 600;
  margin: 0 4px;
}

.orders-line .orders-sell {
  color: #28a745;
  font-weight: 600;
}

.orders-line .separator {
  color: #999;
  margin: 0 8px;
}

.market-link-inline {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}

.market-link-inline:hover {
  color: #5568d3;
  text-decoration: underline;
}

.danger-indicator {
  position: relative;
  width: 20px;
  height: 20px;
  border-radius: 3px;
  border: 2px solid rgba(0, 0, 0, 0.2);
  cursor: help;
  transition: transform 0.2s;
}

.danger-indicator:hover {
  transform: scale(1.2);
}

.danger-indicator .tooltip-text {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  background-color: #333;
  color: white;
  text-align: center;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.85em;
  white-space: normal;
  z-index: 1000;
  pointer-events: none;
  transition: opacity 0.3s, visibility 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  min-width: 120px;
  line-height: 1.4;
}

.danger-indicator:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}

.danger-indicator .tooltip-text::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: #333;
}

.danger-negative {
  background: #000000;
  /* Black for security < 0 */
}

.danger-red {
  background: #f56565;
  /* Red for security <= 0.2 */
}

.danger-orange {
  background: #ed8936;
  /* Orange for security <= 0.4 */
}

.danger-yellow {
  background: #f6e05e;
  /* Yellow for security <= 0.5 */
}

.danger-green {
  background: #48bb78;
  /* Green for security <= 0.6 (or up to 0.8) */
}

.danger-blue {
  background: #4299e1;
  /* Blue for security > 0.8 */
}

.route-arrow {
  color: #856404;
  font-size: 1.2em;
  font-weight: 600;
}


.sort-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.sort-controls label {
  font-weight: 600;
  color: #667eea;
}

.sort-select {
  padding: 6px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 0.95em;
  background: white;
}
</style>
