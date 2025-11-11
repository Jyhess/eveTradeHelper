<template>
  <div class="deal-item">
    <div class="deal-header">
      <h3>{{ deal.type_name || `Type ${deal.type_id}` }}</h3>
      <div class="deal-header-right">
        <button
          class="refresh-deal-button"
          :disabled="refreshing"
          :title="refreshing ? 'Refreshing...' : 'Refresh this deal (force cache update)'"
          @click="refreshDeal"
        >
          <span v-if="refreshing">⟳</span>
          <span v-else>↻</span>
        </button>
        <span
          v-if="dealRegionName && dealRegionName !== currentRegionName"
          class="region-badge"
        >
          {{ dealRegionName }}
        </span>
        <div class="profit-badge" :class="profitBadgeClass">
          {{ deal.profit_percent || 0 }}% profit
        </div>
      </div>
    </div>
    <div class="deal-details">
      <!-- Line 1: Financial calculation -->
      <div class="detail-line financial-line">
        <span class="detail-label">Finance:</span>
        <span class="detail-content">
          <span class="volume">{{ formatNumber(deal.tradable_volume) }}</span>
          <span class="operator">×</span>
          <span class="price">{{ formatPrice(deal.buy_price) }} ISK</span>
          <span class="equals">=</span>
          <span class="total-buy">{{ formatPrice(deal.total_buy_cost) }} ISK</span>
          <span class="arrow">→</span>
          <span class="price">{{ formatPrice(deal.sell_price) }} ISK</span>
          <span class="equals">=</span>
          <span class="total-sell">{{ formatPrice(deal.total_sell_revenue) }} ISK</span>
          <span class="arrow">=></span>
          <span class="profit-total"
            >{{ formatPrice(deal.profit_isk) }} ISK ({{ deal.profit_percent || 0 }}%)</span
          >
        </span>
      </div>

      <!-- Line 2: Transport -->
      <div class="detail-line transport-line">
        <span class="detail-label">Transport:</span>
        <span class="detail-content">
          <span class="volume">{{ formatNumber(deal.tradable_volume) }}</span>
          <span class="operator">×</span>
          <span class="volume-unit">{{ formatVolume(deal.item_volume) }} m³</span>
          <span class="equals">=</span>
          <span class="total-volume"
            >{{ formatVolume(deal.total_transport_volume) }} m³</span
          >
          <span class="separator">•</span>
          <span class="jumps-label">Jumps:</span>
          <span class="jumps-value">
            <span v-if="deal.jumps !== null && deal.jumps !== undefined">{{
              formatNumber(deal.jumps)
            }}</span>
            <span v-else>Unknown</span>
          </span>
          <span class="separator">•</span>
          <span class="time-label">Time:</span>
          <span class="time-value">
            <span
              v-if="
                deal.estimated_time_minutes !== null &&
                deal.estimated_time_minutes !== undefined
              "
            >
              {{ formatTime(deal.estimated_time_minutes) }}
            </span>
            <span v-else>Unknown</span>
          </span>
        </span>
      </div>

      <!-- Line 3: Route -->
      <div
        v-if="deal.route_details && deal.route_details.length > 0"
        class="detail-line route-line"
      >
        <span class="detail-label">Route:</span>
        <span class="detail-content route-content">
          <span class="route-start-container">
            <router-link
              v-if="deal.route_details[0].system_id"
              :to="`/systems/${deal.route_details[0].system_id}`"
              class="route-system-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ deal.route_details[0].name }}
            </router-link>
            <span v-else class="route-start">{{ deal.route_details[0].name }}</span>
            <router-link
              v-if="deal.route_details[0].system_id && deal.buy_region_id"
              :to="`/markets/region/${deal.buy_region_id}?type_id=${deal.type_id}`"
              class="market-icon-link"
              target="_blank"
              rel="noopener noreferrer"
              title="View market for this system"
            >
              📊
            </router-link>
            <span
              v-if="isSystemNotInCurrentRegion(deal.buy_system_id, deal.buy_region_id)"
              class="region-indicator"
            >
              (
              <router-link
                v-if="deal.buy_region_id"
                :to="`/markets/region/${deal.buy_region_id}?type_id=${deal.type_id}`"
                class="region-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ getRegionName(deal.buy_region_id) }}
              </router-link>
              <span v-else>{{ getRegionName(deal.buy_region_id) }}</span>
              )
            </span>
          </span>
          <span class="route-separator">[</span>
          <div class="route-systems-inline">
            <div
              v-for="(system, index) in deal.route_details"
              :key="system.system_id"
              class="route-system-inline"
            >
              <router-link
                v-if="system.system_id"
                :to="`/systems/${system.system_id}`"
                class="danger-indicator-link"
                target="_blank"
                rel="noopener noreferrer"
                :title="`${system.name}\nSecurity: ${system.security_status.toFixed(1)}\nClick to view system details`"
              >
                <div
                  class="danger-indicator-small"
                  :class="getDangerClass(system.security_status)"
                >
                  <span class="tooltip-text-small"
                    >{{ system.name }}<br />Security:
                    {{ system.security_status.toFixed(1) }}</span
                  >
                </div>
              </router-link>
              <div
                v-else
                class="danger-indicator-small"
                :class="getDangerClass(system.security_status)"
                :title="`${system.name}\nSecurity: ${system.security_status.toFixed(1)}`"
              >
                <span class="tooltip-text-small"
                  >{{ system.name }}<br />Security:
                  {{ system.security_status.toFixed(1) }}</span
                >
              </div>
              <span v-if="index < deal.route_details.length - 1" class="route-arrow-small"
                >→</span
              >
            </div>
          </div>
          <span class="route-separator">]</span>
          <span class="route-end-container">
            <router-link
              v-if="deal.route_details[deal.route_details.length - 1].system_id"
              :to="`/systems/${deal.route_details[deal.route_details.length - 1].system_id}`"
              class="route-system-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ deal.route_details[deal.route_details.length - 1].name }}
            </router-link>
            <span v-else class="route-end">{{
              deal.route_details[deal.route_details.length - 1].name
            }}</span>
            <router-link
              v-if="deal.route_details[deal.route_details.length - 1].system_id && deal.sell_region_id"
              :to="`/markets/region/${deal.sell_region_id}?type_id=${deal.type_id}`"
              class="market-icon-link"
              target="_blank"
              rel="noopener noreferrer"
              title="View market for this system"
            >
              📊
            </router-link>
            <span
              v-if="isSystemNotInCurrentRegion(deal.sell_system_id, deal.sell_region_id)"
              class="region-indicator"
            >
              (
              <router-link
                v-if="deal.sell_region_id"
                :to="`/markets/region/${deal.sell_region_id}?type_id=${deal.type_id}`"
                class="region-link"
                target="_blank"
                rel="noopener noreferrer"
              >
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
          <router-link
            :to="`/markets/region/${dealRegionId}?type_id=${deal.type_id}`"
            class="market-link-inline"
            target="_blank"
            rel="noopener noreferrer"
          >
            📊 Market Details
          </router-link>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { formatPrice, formatVolume, formatNumber } from '../utils/numberFormatter'
import api from '../services/api'

export default {
  name: 'DealItem',
  props: {
    deal: {
      type: Object,
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
    currentRegionId: {
      type: Number,
      default: null
    },
    currentRegionName: {
      type: String,
      default: ''
    },
    minProfitIsk: {
      type: Number,
      default: null
    },
    maxTransportVolume: {
      type: Number,
      default: null
    },
    maxBuyCost: {
      type: Number,
      default: null
    }
  },
  emits: ['deal-updated', 'deal-removed'],
  data() {
    return {
      refreshing: false
    }
  },
  computed: {
    dealRegionId() {
      return this.deal.buy_region_id || this.deal.sell_region_id || this.currentRegionId
    },
    dealRegionName() {
      const regionId = this.deal.buy_region_id || this.deal.sell_region_id
      if (!regionId || regionId === this.currentRegionId) {
        return null
      }
      const region = this.regions.find(r => r.region_id === regionId)
      if (region) {
        return region.name
      }
      const adjacentRegion = this.adjacentRegions.find(r => r.region_id === regionId)
      if (adjacentRegion) {
        return adjacentRegion.name
      }
      return `Region ${regionId}`
    },
    profitBadgeClass() {
      const profitPercent = this.deal.profit_percent || 0
      if (profitPercent >= 20) return 'profit-excellent'
      if (profitPercent >= 10) return 'profit-good'
      if (profitPercent >= 5) return 'profit-medium'
      return 'profit-low'
    }
  },
  methods: {
    formatPrice,
    formatVolume,
    formatNumber,
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
    getDangerClass(securityStatus) {
      if (securityStatus < 0) return 'danger-negative'
      if (securityStatus <= 0.2) return 'danger-red'
      if (securityStatus <= 0.4) return 'danger-orange'
      if (securityStatus <= 0.5) return 'danger-yellow'
      if (securityStatus <= 0.6) return 'danger-green'
      if (securityStatus <= 0.8) return 'danger-green'
      return 'danger-blue'
    },
    isSystemNotInCurrentRegion(systemId, regionId) {
      if (!this.currentRegionId || !regionId) {
        return false
      }
      return regionId !== this.currentRegionId
    },
    getRegionName(regionId) {
      if (!regionId) {
        return 'Unknown region'
      }
      const region = this.regions.find(r => r.region_id === regionId)
      if (region) {
        return region.name
      }
      const adjacentRegion = this.adjacentRegions.find(r => r.region_id === regionId)
      if (adjacentRegion) {
        return adjacentRegion.name
      }
      return `Region ${regionId}`
    },
    async refreshDeal() {
      if (this.refreshing) {
        return
      }

      if (!this.deal.buy_region_id || !this.deal.sell_region_id) {
        console.warn('Cannot refresh deal: missing region IDs')
        return
      }

      this.refreshing = true
      try {
        const data = {
          type_id: this.deal.type_id,
          buy_region_id: this.deal.buy_region_id,
          sell_region_id: this.deal.sell_region_id,
          min_profit_isk: this.minProfitIsk !== null && this.minProfitIsk !== undefined
            ? this.minProfitIsk
            : this.deal.profit_isk || 100000.0
        }

        if (this.maxTransportVolume !== null && this.maxTransportVolume !== undefined) {
          data.max_transport_volume = this.maxTransportVolume
        }
        if (this.maxBuyCost !== null && this.maxBuyCost !== undefined) {
          data.max_buy_cost = this.maxBuyCost
        }

        const response = await api.markets.refreshDeal(data)
        const refreshedDeal = response.deal

        if (refreshedDeal) {
          // Emit event to update the deal in the parent list
          this.$emit('deal-updated', {
            oldDeal: this.deal,
            newDeal: refreshedDeal
          })
        } else {
          // Deal no longer profitable, remove it
          this.$emit('deal-removed', this.deal)
        }
      } catch (error) {
        console.error('Error refreshing deal:', error)
         
        window.alert('Error refreshing deal: ' + error.message)
      } finally {
        this.refreshing = false
      }
    }
  }
}
</script>

<style scoped>
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

.refresh-deal-button {
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 8px;
  transition: background 0.2s, opacity 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
}

.refresh-deal-button:hover:not(:disabled) {
  background: #5568d3;
}

.refresh-deal-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-deal-button span {
  display: inline-block;
}

.refresh-deal-button:disabled span {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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

.market-icon-link {
  display: inline-block;
  font-size: 0.9em;
  text-decoration: none;
  margin-left: 4px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.market-icon-link:hover {
  opacity: 1;
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

.danger-indicator-link {
  display: inline-block;
  text-decoration: none;
  cursor: pointer;
}

.danger-indicator-small {
  position: relative;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.2s;
}

.danger-indicator-small:hover {
  transform: scale(1.3);
}

.danger-indicator-link:hover .danger-indicator-small {
  transform: scale(1.3);
  box-shadow: 0 0 4px rgba(102, 126, 234, 0.5);
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
  transition:
    opacity 0.3s,
    visibility 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  line-height: 1.4;
}

.danger-indicator-small:hover .tooltip-text-small {
  visibility: visible;
  opacity: 1;
}

.danger-indicator-small .tooltip-text-small::after {
  content: '';
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

.danger-negative {
  background: #000000;
}

.danger-red {
  background: #f56565;
}

.danger-orange {
  background: #ed8936;
}

.danger-yellow {
  background: #f6e05e;
}

.danger-green {
  background: #48bb78;
}

.danger-blue {
  background: #4299e1;
}

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
</style>

