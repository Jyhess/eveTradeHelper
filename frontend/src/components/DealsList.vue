<template>
  <div v-if="searchResults" class="results-section">
    <div class="results-header">
      <h2>Results</h2>
      <div class="results-stats">
        <p>
          <strong>{{ dealsCount }}</strong> deal(s) found
          <span v-if="selectedAdjacentRegions && selectedAdjacentRegions.length > 0">
            across <strong>{{ 1 + selectedAdjacentRegions.length }}</strong> region(s)
          </span>
          <span v-if="searchResults.total_types">
            across <strong>{{ searchResults.total_types }}</strong> analyzed type(s)
          </span>
        </p>
        <p>
          Total potential profit:
          <strong>{{ formatPrice(searchResults.total_profit_isk || 0) }} ISK</strong>
        </p>
        <p v-if="showSearchCriteria">
          Profit threshold:
          <strong>{{ formatPrice(searchResults.min_profit_isk || 0) }} ISK</strong> |
          <span v-if="searchResults.max_transport_volume">
            Max volume:
            <strong>{{ formatVolume(searchResults.max_transport_volume) }} m³</strong> |
          </span>
          <span v-if="searchResults.max_buy_cost">
            Max purchase amount:
            <strong>{{ formatPrice(searchResults.max_buy_cost) }} ISK</strong> |
          </span>
          <span v-if="selectedAdjacentRegions && selectedAdjacentRegions.length > 0">
            Regions: <strong>{{ currentRegionName }}</strong> +
            {{ selectedAdjacentRegions.length }} other(s) |
          </span>
          <span v-else-if="currentRegionName">
            Region: <strong>{{ currentRegionName }}</strong> |
          </span>
          <span v-if="groupName">
            Group: <strong>{{ groupName }}</strong>
          </span>
        </p>
      </div>
    </div>

    <div v-if="dealsCount === 0" class="no-results">
      <p>No deals found with the following criteria:</p>
      <ul style="text-align: left; display: inline-block">
        <li>Profit threshold: {{ formatPrice(searchResults.min_profit_isk || 0) }} ISK</li>
        <li v-if="searchResults.max_transport_volume">
          Max volume: {{ formatVolume(searchResults.max_transport_volume) }} m³
        </li>
        <li v-if="searchResults.max_buy_cost">
          Max purchase amount: {{ formatPrice(searchResults.max_buy_cost) }} ISK
        </li>
      </ul>
      <p>
        Try reducing the profit threshold, increasing the max volume or max purchase amount, or
        selecting another group.
      </p>
    </div>

    <div v-else class="deals-list">
      <div v-if="showSortControls" class="sort-controls">
        <label>Sort by:</label>
        <select :value="sortBy" class="sort-select" @change="$emit('update:sortBy', $event.target.value)">
          <option value="profit">Profit (%)</option>
          <option value="jumps">Number of jumps</option>
          <option value="profit_isk">Profit (ISK)</option>
        </select>
      </div>
      <DealItem
        v-for="deal in deals"
        :key="getDealKey(deal)"
        :deal="deal"
        :regions="regions"
        :adjacent-regions="adjacentRegions || []"
        :current-region-id="currentRegionId"
        :current-region-name="currentRegionName"
      />
    </div>
  </div>
</template>

<script>
import DealItem from './DealItem.vue'
import { formatPrice, formatVolume } from '../utils/numberFormatter'

export default {
  name: 'DealsList',
  components: {
    DealItem
  },
  props: {
    searchResults: {
      type: Object,
      default: null
    },
    deals: {
      type: Array,
      required: true
    },
    regions: {
      type: Array,
      default: () => []
    },
    adjacentRegions: {
      type: Array,
      default: () => []
    },
    selectedAdjacentRegions: {
      type: Array,
      default: () => []
    },
    currentRegionId: {
      type: Number,
      default: null
    },
    currentRegionName: {
      type: String,
      default: ''
    },
    groupName: {
      type: String,
      default: ''
    },
    sortBy: {
      type: String,
      default: 'profit_isk'
    },
    showSortControls: {
      type: Boolean,
      default: true
    },
    showSearchCriteria: {
      type: Boolean,
      default: true
    }
  },
  emits: ['update:sortBy'],
  computed: {
    dealsCount() {
      return this.deals.length
    }
  },
  methods: {
    formatPrice,
    formatVolume,
    getDealKey(deal) {
      return `${deal.type_id}-${deal.buy_region_id || deal.sell_region_id || 'default'}`
    }
  }
}
</script>

<style scoped>
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

