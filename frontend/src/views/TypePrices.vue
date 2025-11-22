<template>
  <div class="type-prices-page">
    <div class="card">
      <div class="page-header">
        <h1>Prices by Region</h1>
        <div class="type-selector-section">
          <div class="form-group">
            <label for="type-search">Search Product:</label>
            <div class="type-search-wrapper">
              <input
                id="type-search"
                v-model="typeSearchText"
                type="text"
                class="type-search-input"
                placeholder="Type name or ID..."
                @input="handleTypeSearch"
                @keydown.enter="handleTypeSearchEnter"
                @focus="showTypeResults = true"
                @blur="handleTypeSearchBlur"
              />
              <Loader v-if="searchingTypes" message="Searching..." size="small" />
              <div v-if="typeSearchResults.length > 0 && showTypeResults" class="type-search-results">
                <div
                  v-for="result in typeSearchResults"
                  :key="result.type_id"
                  class="type-search-result"
                  @click="selectType(result.type_id)"
                >
                  <strong>{{ result.name }}</strong>
                  <span class="result-type-id">ID: {{ result.type_id }}</span>
                </div>
              </div>
              <div
                v-else-if="typeSearchText && !searchingTypes && typeSearchPerformed && showTypeResults"
                class="type-search-no-results"
              >
                No results found
              </div>
            </div>
          </div>
        </div>
        <div v-if="typeDetails" class="type-info">
          <h2>{{ typeDetails.name }}</h2>
          <p v-if="typeDetails.description" class="type-description" v-html="processDescription(typeDetails.description)"></p>
        </div>
      </div>

      <Loader v-if="loading" message="Loading prices across all regions..." variant="overlay" />
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="pricesData && pricesData.regions" class="prices-container">
        <div class="prices-header">
          <div class="stats">
            <span class="stat-item">
              <strong>{{ filteredRegions.length }}</strong> regions with orders
            </span>
            <span class="stat-item">
              <strong>{{ regionsWithBuyOrders }}</strong> with buy orders
            </span>
            <span class="stat-item">
              <strong>{{ regionsWithSellOrders }}</strong> with sell orders
            </span>
          </div>
        </div>

        <div class="prices-table-container">
          <table class="prices-table">
            <thead>
              <tr>
                <th>Region</th>
                <th class="text-right">Max Buy Price</th>
                <th class="text-right">Min Sell Price</th>
                <th class="text-right">Spread</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="region in filteredRegions"
                :key="region.region_id"
                class="price-row"
                :class="{ 'has-both': region.max_buy_price && region.min_sell_price }"
              >
                <td class="region-name">
                  <router-link :to="`/markets/region/${region.region_id}`">
                    {{ region.region_name }}
                  </router-link>
                </td>
                <td class="text-right price-buy">
                  <span v-if="region.max_buy_price">{{ formatPrice(region.max_buy_price) }} ISK</span>
                  <span v-else class="no-data">-</span>
                </td>
                <td class="text-right price-sell">
                  <span v-if="region.min_sell_price">{{ formatPrice(region.min_sell_price) }} ISK</span>
                  <span v-else class="no-data">-</span>
                </td>
                <td class="text-right price-spread">
                  <span v-if="region.max_buy_price && region.min_sell_price">
                    {{ formatPrice(region.min_sell_price - region.max_buy_price) }} ISK
                    <span class="spread-percent">
                      ({{ calculateSpreadPercent(region.max_buy_price, region.min_sell_price) }}%)
                    </span>
                  </span>
                  <span v-else class="no-data">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Statistics section -->
        <div class="statistics-section">
          <h3>Statistics</h3>
          <div class="stats-grid">
            <div class="stat-card">
              <h4>Max Buy Price</h4>
              <div class="stat-values">
                <div class="stat-value">
                  <span class="stat-label">Min:</span>
                  <span v-if="stats.buy.min !== null" class="stat-number">
                    {{ formatPrice(stats.buy.min) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
                <div class="stat-value">
                  <span class="stat-label">Max:</span>
                  <span v-if="stats.buy.max !== null" class="stat-number">
                    {{ formatPrice(stats.buy.max) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
                <div class="stat-value">
                  <span class="stat-label">Average:</span>
                  <span v-if="stats.buy.average !== null" class="stat-number">
                    {{ formatPrice(stats.buy.average) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
              </div>
            </div>

            <div class="stat-card">
              <h4>Min Sell Price</h4>
              <div class="stat-values">
                <div class="stat-value">
                  <span class="stat-label">Min:</span>
                  <span v-if="stats.sell.min !== null" class="stat-number">
                    {{ formatPrice(stats.sell.min) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
                <div class="stat-value">
                  <span class="stat-label">Max:</span>
                  <span v-if="stats.sell.max !== null" class="stat-number">
                    {{ formatPrice(stats.sell.max) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
                <div class="stat-value">
                  <span class="stat-label">Average:</span>
                  <span v-if="stats.sell.average !== null" class="stat-number">
                    {{ formatPrice(stats.sell.average) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
              </div>
            </div>

            <div class="stat-card">
              <h4>Spread</h4>
              <div class="stat-values">
                <div class="stat-value">
                  <span class="stat-label">Min:</span>
                  <span v-if="stats.spread.min !== null" class="stat-number">
                    {{ formatPrice(stats.spread.min) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
                <div class="stat-value">
                  <span class="stat-label">Max:</span>
                  <span v-if="stats.spread.max !== null" class="stat-number">
                    {{ formatPrice(stats.spread.max) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
                <div class="stat-value">
                  <span class="stat-label">Average:</span>
                  <span v-if="stats.spread.average !== null" class="stat-number">
                    {{ formatPrice(stats.spread.average) }} ISK
                  </span>
                  <span v-else class="no-data">-</span>
                </div>
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
import Loader from '../components/Loader.vue'
import { formatPrice } from '../utils/numberFormatter'

export default {
  name: 'TypePrices',
  components: {
    Loader
  },
  props: {
    typeId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      loading: false,
      error: '',
      pricesData: null,
      typeDetails: null,
      typeSearchText: '',
      typeSearchResults: [],
      searchingTypes: false,
      typeSearchPerformed: false,
      showTypeResults: false,
      searchTimeout: null
    }
  },
  computed: {
    filteredRegions() {
      if (!this.pricesData || !this.pricesData.regions) return []
      // Filter out regions with neither buy nor sell orders
      return this.pricesData.regions.filter(
        r => r.max_buy_price !== null || r.min_sell_price !== null
      )
    },
    regionsWithBuyOrders() {
      return this.filteredRegions.filter(r => r.max_buy_price !== null).length
    },
    regionsWithSellOrders() {
      return this.filteredRegions.filter(r => r.min_sell_price !== null).length
    },
    buyPrices() {
      return this.filteredRegions
        .map(r => r.max_buy_price)
        .filter(price => price !== null)
    },
    sellPrices() {
      return this.filteredRegions
        .map(r => r.min_sell_price)
        .filter(price => price !== null)
    },
    spreads() {
      return this.filteredRegions
        .map(r => {
          if (r.max_buy_price !== null && r.min_sell_price !== null) {
            return r.min_sell_price - r.max_buy_price
          }
          return null
        })
        .filter(spread => spread !== null)
    },
    stats() {
      const calculateStats = (values) => {
        if (values.length === 0) return { min: null, max: null, average: null }
        const min = Math.min(...values)
        const max = Math.max(...values)
        const average = values.reduce((sum, val) => sum + val, 0) / values.length
        return { min, max, average }
      }

      return {
        buy: calculateStats(this.buyPrices),
        sell: calculateStats(this.sellPrices),
        spread: calculateStats(this.spreads)
      }
    }
  },
  watch: {
    async typeId() {
      await this.loadTypeDetails()
      await this.loadPrices()
      // Update search text when type changes
      if (this.typeDetails && this.typeDetails.name) {
        this.typeSearchText = this.typeDetails.name
      }
      this.typeSearchResults = []
      this.showTypeResults = false
    }
  },
  async mounted() {
    await this.loadTypeDetails()
    await this.loadPrices()
    
    if (this.typeDetails && this.typeDetails.name) {
      this.typeSearchText = this.typeDetails.name
    }
  },
  methods: {
    async loadTypeDetails() {
      try {
        const data = await api.universe.getType(this.typeId)
        this.typeDetails = data
      } catch (error) {
        console.error(`Error loading type details for ${this.typeId}:`, error)
        this.typeDetails = { name: `Type ${this.typeId}`, description: '' }
      }
    },
    async loadPrices() {
      this.loading = true
      this.error = ''

      try {
        const data = await api.markets.getTypePricesByRegion(this.typeId)
        this.pricesData = data
      } catch (error) {
        this.error = 'Error loading prices: ' + error.message
      } finally {
        this.loading = false
      }
    },
    calculateSpreadPercent(buyPrice, sellPrice) {
      if (!buyPrice || !sellPrice || buyPrice === 0) return 0
      return ((sellPrice - buyPrice) / buyPrice * 100).toFixed(2)
    },
    processDescription(description) {
      if (!description) return ''
      
      // Replace showinfo links with clickable links
      const showInfoPattern = /<a\s+href=showinfo:(\d+)>(.*?)<\/a>/gi
      
      const processed = description.replace(showInfoPattern, (match, typeId, linkText) => {
        return `<a href="/markets?type_id=${typeId}" class="description-link">${linkText}</a>`
      })
      
      return processed
    },
    formatPrice,
    async handleTypeSearch() {
      const searchText = this.typeSearchText.trim()
      
      const isNumeric = /^\d+$/.test(searchText)

      if (!isNumeric && searchText.length < 2) {
        this.typeSearchResults = []
        this.typeSearchPerformed = false
        this.showTypeResults = false
        return
      }
      
      if (this.searchTimeout) {
        window.clearTimeout(this.searchTimeout)
      }

      this.searchTimeout = window.setTimeout(async () => {
        this.searchingTypes = true
        this.showTypeResults = true
        try {
          const data = await api.markets.searchTypes(searchText)
          this.typeSearchResults = data.types || []
          this.typeSearchPerformed = true
        } catch (error) {
          console.error('Error searching item types:', error)
          this.typeSearchResults = []
          this.typeSearchPerformed = false
        } finally {
          this.searchingTypes = false
        }
      }, 300)
    },
    handleTypeSearchEnter() {
      if (this.typeSearchResults.length > 0) {
        this.selectType(this.typeSearchResults[0].type_id)
      }
    },
    selectType(typeId) {
      this.showTypeResults = false
      const selected = this.typeSearchResults.find(result => result.type_id === typeId)
      if (selected) {
        this.typeSearchText = selected.name
      }
      this.typeSearchResults = []
      this.$router.push(`/markets/types/${typeId}/prices`)
    },
    handleTypeSearchBlur() {
      window.setTimeout(() => {
        this.showTypeResults = false
      }, 200)
    }
  }
}
</script>

<style scoped>
.type-prices-page {
  min-height: 100vh;
  padding: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0 0 20px 0;
  color: #667eea;
  font-size: 2em;
}

.type-info {
  margin-top: 20px;
}

.type-info h2 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1.5em;
}

.type-description {
  color: #555;
  line-height: 1.6;
  margin: 0;
}

.description-link {
  color: #667eea;
  text-decoration: underline;
  cursor: pointer;
  transition: color 0.2s;
}

.description-link:hover {
  color: #5568d3;
  text-decoration: none;
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

.prices-container {
  margin-top: 20px;
}

.prices-header {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.stat-item {
  color: #555;
  font-size: 0.95em;
}

.stat-item strong {
  color: #667eea;
  font-weight: 600;
}

.prices-table-container {
  overflow-x: auto;
}

.prices-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.prices-table thead {
  background: #f8f9fa;
  position: sticky;
  top: 0;
  z-index: 10;
}

.prices-table th {
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
}

.prices-table th.text-right {
  text-align: right;
}

.prices-table tbody tr {
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
}

.prices-table tbody tr:hover {
  background: #f8f9fa;
}

.prices-table tbody tr.has-both {
  background: #f0f9ff;
}

.prices-table tbody tr.has-both:hover {
  background: #e0f2fe;
}

.prices-table td {
  padding: 12px 15px;
  color: #555;
}

.region-name {
  font-weight: 500;
}

.region-name a {
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s;
}

.region-name a:hover {
  color: #5568d3;
  text-decoration: underline;
}

.text-right {
  text-align: right;
}

.price-buy {
  color: #48bb78;
  font-weight: 600;
}

.price-sell {
  color: #ed8936;
  font-weight: 600;
}

.price-spread {
  color: #4299e1;
  font-weight: 600;
}

.spread-percent {
  font-size: 0.85em;
  color: #666;
  font-weight: 400;
  margin-left: 5px;
}

.no-data {
  color: #999;
  font-style: italic;
}

.statistics-section {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 2px solid #e0e0e0;
}

.statistics-section h3 {
  margin: 0 0 20px 0;
  color: #667eea;
  font-size: 1.5em;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e0e0e0;
}

.stat-card h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 1.1em;
  font-weight: 600;
}

.stat-values {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #666;
  font-size: 0.9em;
}

.stat-number {
  color: #333;
  font-weight: 600;
  font-size: 1em;
}

.type-selector-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.type-selector-section .form-group {
  margin: 0;
}

.type-selector-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.type-search-wrapper {
  position: relative;
}

.type-search-input {
  width: 100%;
  max-width: 500px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  background: white;
}

.type-search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.type-search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-width: 500px;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-top: 5px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.type-search-result {
  padding: 12px 15px;
  cursor: pointer;
  border-bottom: 1px solid #e0e0e0;
  transition: background 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-search-result:last-child {
  border-bottom: none;
}

.type-search-result:hover {
  background: #f8f9fa;
}

.type-search-result strong {
  color: #333;
  font-weight: 600;
}

.result-type-id {
  color: #666;
  font-size: 0.9em;
}

.type-search-no-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-width: 500px;
  padding: 12px 15px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-top: 5px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: #999;
  font-style: italic;
  z-index: 1000;
}
</style>

