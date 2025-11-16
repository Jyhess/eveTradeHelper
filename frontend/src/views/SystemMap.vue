<template>
  <div class="system-map-page">
    <div class="card">
      <div class="system-selector-section">
        <SystemSelector
          title="Select System"
          id-prefix="system-map"
          :region-id="regionId"
          :constellation-id="constellationId"
          :system-id="parseInt(systemId)"
          @update:region-id="regionId = $event"
          @update:constellation-id="constellationId = $event"
          @update:system-id="handleSystemChange"
          @region-change="handleRegionChange"
          @constellation-change="handleConstellationChange"
          @system-change="handleSystemChange"
        />
      </div>
      <Loader v-if="loading" message="Loading system map..." variant="overlay" />
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="mapData" class="map-container">
        <div class="map-header">
          <h2>System Map: {{ centerSystemName }}</h2>
          <div class="map-controls">
            <label for="maxJumps">Max Jumps:</label>
            <input
              id="maxJumps"
              v-model.number="localMaxJumps"
              type="number"
              min="1"
              max="10"
              @change="fetchMapData"
            />
            <router-link :to="`/systems/${systemId}`" class="system-detail-link">
              View System Details →
            </router-link>
          </div>
          <div class="map-stats">
            <p>
              <strong>{{ mapData.total_systems }}</strong> systems within
              <strong>{{ mapData.max_jumps }}</strong> jumps
            </p>
            <p>
              <strong>{{ mapData.total_connections }}</strong> connections
            </p>
          </div>
        </div>

        <div class="map-visualization">
          <div
            v-if="tooltipVisible && tooltipSystem"
            class="system-tooltip"
            :style="tooltipStyle"
          >
            <div class="tooltip-header">
              <strong>{{ tooltipSystem.name }}</strong>
            </div>
            <div class="tooltip-content">
              <div class="tooltip-row">
                <span class="tooltip-label">System ID:</span>
                <span class="tooltip-value">{{ tooltipSystem.system_id }}</span>
              </div>
              <div class="tooltip-row">
                <span class="tooltip-label">Security:</span>
                <span class="tooltip-value">{{ tooltipSystem.security_status.toFixed(1) }}</span>
              </div>
              <div class="tooltip-row">
                <span class="tooltip-label">Jumps:</span>
                <span class="tooltip-value">{{ tooltipSystem.jumps }}</span>
              </div>
              <div v-if="tooltipSystem.security_class" class="tooltip-row">
                <span class="tooltip-label">Class:</span>
                <span class="tooltip-value">{{ tooltipSystem.security_class }}</span>
              </div>
            </div>
            <div class="tooltip-footer">
              <span class="tooltip-hint">Click to view details</span>
            </div>
          </div>
          <svg ref="svgElement" class="map-svg" viewBox="0 0 1000 800">
            <!-- Draw connections first (behind nodes) -->
            <g class="connections">
              <line
                v-for="(connection, index) in mapData.connections"
                :key="`connection-${index}`"
                :x1="getSystemPosition(connection.from_system_id).x"
                :y1="getSystemPosition(connection.from_system_id).y"
                :x2="getSystemPosition(connection.to_system_id).x"
                :y2="getSystemPosition(connection.to_system_id).y"
                class="connection-line"
                :class="getConnectionClass(connection)"
              />
            </g>

            <!-- Draw systems (on top) -->
            <g class="systems">
              <g
                v-for="system in mapData.systems"
                :key="system.system_id"
                :transform="`translate(${getSystemPosition(system.system_id).x}, ${getSystemPosition(system.system_id).y})`"
                class="system-node"
                :class="getSystemNodeClass(system)"
                @mouseenter="showSystemTooltip(system)"
                @mouseleave="hideSystemTooltip"
                @click="goToSystemDetails(system.system_id)"
              >
                <circle
                  :r="getSystemRadius(system)"
                  class="system-circle"
                  :class="getSecurityClass(system.security_status)"
                />
                <text
                  class="system-label"
                  :y="getSystemRadius(system) + 15"
                  text-anchor="middle"
                >
                  {{ system.name }}
                </text>
                <text
                  class="system-jumps"
                  :y="getSystemRadius(system) + 30"
                  text-anchor="middle"
                >
                  ({{ system.jumps }} jump{{ system.jumps !== 1 ? 's' : '' }})
                </text>
              </g>
            </g>
          </svg>
        </div>

        <div class="map-legend">
          <h3>Legend</h3>
          <div class="legend-items">
            <div class="legend-item">
              <span class="legend-color sec-blue"></span>
              <span>High Security (>0.8)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color sec-green"></span>
              <span>Medium Security (0.5-0.8)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color sec-yellow"></span>
              <span>Low Security (0.4-0.5)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color sec-orange"></span>
              <span>Very Low Security (0.2-0.4)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color sec-red"></span>
              <span>Low Security (0.0-0.2)</span>
            </div>
            <div class="legend-item">
              <span class="legend-color sec-negative"></span>
              <span>Null Security (&lt;0.0)</span>
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
import SystemSelector from '../components/SystemSelector.vue'
import eventBus from '../utils/eventBus'
import {
  DEFAULT_MAX_JUMPS,
  SECURITY_COLORS,
  SECURITY_STROKE_COLORS,
  CONNECTION_COLORS
} from '../constants'

export default {
  name: 'SystemMap',
  components: {
    Loader,
    SystemSelector
  },
  props: {
    systemId: {
      type: [String, Number],
      required: true
    },
    maxJumps: {
      type: Number,
      default: DEFAULT_MAX_JUMPS
    }
  },
  data() {
    return {
      mapData: null,
      loading: false,
      error: '',
      centerSystemName: '',
      systemPositions: {},
      localMaxJumps: this.maxJumps || DEFAULT_MAX_JUMPS,
      regionId: null,
      constellationId: null,
      securityColorNegative: SECURITY_COLORS.NEGATIVE,
      securityColorRed: SECURITY_COLORS.RED,
      securityColorOrange: SECURITY_COLORS.ORANGE,
      securityColorYellow: SECURITY_COLORS.YELLOW,
      securityColorGreen: SECURITY_COLORS.GREEN,
      securityColorBlue: SECURITY_COLORS.BLUE,
      securityStrokeColorNegative: SECURITY_STROKE_COLORS.NEGATIVE,
      securityStrokeColorRed: SECURITY_STROKE_COLORS.RED,
      securityStrokeColorOrange: SECURITY_STROKE_COLORS.ORANGE,
      securityStrokeColorYellow: SECURITY_STROKE_COLORS.YELLOW,
      securityStrokeColorGreen: SECURITY_STROKE_COLORS.GREEN,
      securityStrokeColorBlue: SECURITY_STROKE_COLORS.BLUE,
      connectionColorNull: CONNECTION_COLORS.NULL,
      connectionColorLow: CONNECTION_COLORS.LOW,
      connectionColorVeryLow: CONNECTION_COLORS.VERY_LOW,
      connectionColorLowSec: CONNECTION_COLORS.LOW_SEC,
      connectionColorHighSec: CONNECTION_COLORS.HIGH_SEC,
      tooltipVisible: false,
      tooltipSystem: null,
      tooltipStyle: {}
    }
  },
  watch: {
    systemId() {
      this.fetchMapData()
    },
    maxJumps(newValue) {
      if (newValue) {
        this.localMaxJumps = newValue
        this.fetchMapData()
      }
    }
  },
  mounted() {
    this.fetchMapData()
  },
  methods: {
    async fetchMapData() {
      this.loading = true
      this.error = ''
      this.mapData = null
      this.systemPositions = {}

      try {
        const jumpsToUse = this.maxJumps || this.localMaxJumps
        const data = await api.systems.getSystemMap(this.systemId, jumpsToUse)
        this.mapData = data

        if (this.mapData.systems && this.mapData.systems.length > 0) {
          const centerSystem = this.mapData.systems.find(
            s => s.system_id === parseInt(this.systemId)
          )
          this.centerSystemName = centerSystem ? centerSystem.name : 'Unknown'

          if (centerSystem) {
            this.regionId = centerSystem.region_id || null
            this.constellationId = centerSystem.constellation_id || null
          }

          this.calculatePositions()

          eventBus.emit('breadcrumb-update', {
            systemName: this.centerSystemName,
            systemId: parseInt(this.systemId)
          })
        }
      } catch (error) {
        this.error = 'Error: ' + error.message
      } finally {
        this.loading = false
      }
    },
    calculatePositions() {
      if (!this.mapData || !this.mapData.systems) {
        return
      }

      const positions = {}
      const centerX = 500
      const centerY = 400
      const radiusStep = 150

      const systemsByJump = {}
      this.mapData.systems.forEach(system => {
        const jumps = system.jumps || 0
        if (!systemsByJump[jumps]) {
          systemsByJump[jumps] = []
        }
        systemsByJump[jumps].push(system)
      })

      Object.keys(systemsByJump)
        .map(Number)
        .sort((a, b) => a - b)
        .forEach(jumpLevel => {
          const systems = systemsByJump[jumpLevel]
          const angleStep = (2 * Math.PI) / systems.length

          systems.forEach((system, index) => {
            if (jumpLevel === 0) {
              positions[system.system_id] = { x: centerX, y: centerY }
            } else {
              const radius = radiusStep * jumpLevel
              const angle = angleStep * index
              positions[system.system_id] = {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle)
              }
            }
          })
        })

      this.systemPositions = positions
    },
    getSystemPosition(systemId) {
      return (
        this.systemPositions[systemId] || {
          x: 500,
          y: 400
        }
      )
    },
    getSystemRadius(system) {
      if (system.system_id === parseInt(this.systemId)) {
        return 20
      }
      return 12
    },
    getSystemNodeClass(system) {
      return {
        'center-system': system.system_id === parseInt(this.systemId)
      }
    },
    getConnectionClass(connection) {
      const fromSystem = this.mapData.systems.find(
        s => s.system_id === connection.from_system_id
      )
      const toSystem = this.mapData.systems.find(
        s => s.system_id === connection.to_system_id
      )

      if (!fromSystem || !toSystem) {
        return ''
      }

      const minSecurity = Math.min(
        fromSystem.security_status,
        toSystem.security_status
      )

      if (minSecurity < 0) return 'connection-null'
      if (minSecurity <= 0.2) return 'connection-low'
      if (minSecurity <= 0.4) return 'connection-very-low'
      if (minSecurity <= 0.5) return 'connection-low-sec'
      return 'connection-high-sec'
    },
    getSecurityClass(securityStatus) {
      if (securityStatus < 0) return 'sec-negative'
      if (securityStatus <= 0.2) return 'sec-red'
      if (securityStatus <= 0.4) return 'sec-orange'
      if (securityStatus <= 0.5) return 'sec-yellow'
      if (securityStatus <= 0.6) return 'sec-green'
      if (securityStatus <= 0.8) return 'sec-green'
      return 'sec-blue'
    },
    handleSystemChange(systemId) {
      if (systemId && systemId !== parseInt(this.systemId)) {
        this.$router.push(`/systems/${systemId}/map`)
      }
    },
    handleRegionChange(regionId) {
      this.regionId = regionId
      this.constellationId = null
    },
    handleConstellationChange(constellationId) {
      this.constellationId = constellationId
    },
    showSystemTooltip(system) {
      this.tooltipSystem = system
      this.tooltipVisible = true

      const svgElement = this.$refs.svgElement
      if (!svgElement) return

      const svgRect = svgElement.getBoundingClientRect()
      const position = this.getSystemPosition(system.system_id)
      const svgPoint = svgElement.createSVGPoint()
      svgPoint.x = position.x
      svgPoint.y = position.y

      const ctm = svgElement.getScreenCTM()
      if (ctm) {
        const screenPoint = svgPoint.matrixTransform(ctm)

        this.tooltipStyle = {
          left: `${screenPoint.x + svgRect.left + 20}px`,
          top: `${screenPoint.y + svgRect.top - 10}px`
        }
      }
    },
    hideSystemTooltip() {
      this.tooltipVisible = false
      this.tooltipSystem = null
    },
    goToSystemDetails(systemId) {
      this.$router.push(`/systems/${systemId}`)
    }
  }
}
</script>

<style scoped>
.system-map-page {
  min-height: 100vh;
  padding: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
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

.system-selector-section {
  margin-bottom: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.system-selector-section :deep(.system-selection-container) {
  margin-bottom: 0;
  padding: 0;
}

.system-selector-section :deep(.system-selection-container h3) {
  margin: 0 0 8px 0;
  font-size: 1em;
}

.system-selector-section :deep(.cascade-selectors) {
  gap: 10px;
}

.system-selector-section :deep(.form-group) {
  margin-bottom: 10px;
}

.system-selector-section :deep(.form-group label) {
  margin-bottom: 4px;
  font-size: 0.9em;
}

.map-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.map-header h2 {
  margin: 0 0 15px 0;
  color: #4299e1;
  font-size: 2em;
}

.map-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.map-controls label {
  font-weight: 500;
  color: #666;
}

.map-controls input[type='number'] {
  width: 80px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1em;
}

.system-detail-link {
  margin-left: auto;
  padding: 8px 16px;
  background: #48bb78;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.2s, transform 0.2s;
}

.system-detail-link:hover {
  background: #38a169;
  transform: translateY(-1px);
}

.map-stats {
  display: flex;
  gap: 20px;
  margin-top: 15px;
}

.map-stats p {
  margin: 0;
  color: #666;
  font-size: 0.95em;
}

.map-stats strong {
  color: #4299e1;
}

.map-visualization {
  margin: 30px 0;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  overflow: auto;
}

.map-svg {
  width: 100%;
  height: 600px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.connections {
  pointer-events: none;
}

.connection-line {
  stroke: #ccc;
  stroke-width: 1;
  opacity: 0.5;
}

.connection-line.connection-high-sec {
  stroke: v-bind('connectionColorHighSec');
  stroke-width: 2;
}

.connection-line.connection-low-sec {
  stroke: v-bind('connectionColorLowSec');
  stroke-width: 2;
}

.connection-line.connection-very-low {
  stroke: v-bind('connectionColorVeryLow');
  stroke-width: 2;
}

.connection-line.connection-low {
  stroke: v-bind('connectionColorLow');
  stroke-width: 2;
}

.connection-line.connection-null {
  stroke: v-bind('connectionColorNull');
  stroke-width: 2;
}

.systems {
  pointer-events: all;
}

.system-node {
  cursor: pointer;
}

.system-circle {
  transition: r 0.2s, filter 0.2s;
}

.system-node:hover .system-circle {
  filter: brightness(1.2) drop-shadow(0 0 4px rgba(66, 153, 225, 0.8));
}

.system-node.center-system {
  filter: drop-shadow(0 0 8px rgba(66, 153, 225, 0.6));
}

.system-circle {
  stroke: #333;
  stroke-width: 2;
  fill: white;
  cursor: pointer;
}

.system-circle.sec-negative {
  fill: v-bind('securityColorNegative');
  stroke: v-bind('securityStrokeColorNegative');
}

.system-circle.sec-red {
  fill: v-bind('securityColorRed');
  stroke: v-bind('securityStrokeColorRed');
}

.system-circle.sec-orange {
  fill: v-bind('securityColorOrange');
  stroke: v-bind('securityStrokeColorOrange');
}

.system-circle.sec-yellow {
  fill: v-bind('securityColorYellow');
  stroke: v-bind('securityStrokeColorYellow');
}

.system-circle.sec-green {
  fill: v-bind('securityColorGreen');
  stroke: v-bind('securityStrokeColorGreen');
}

.system-circle.sec-blue {
  fill: v-bind('securityColorBlue');
  stroke: v-bind('securityStrokeColorBlue');
}

.system-label {
  font-size: 12px;
  font-weight: 600;
  fill: #333;
  pointer-events: none;
}

.system-jumps {
  font-size: 10px;
  fill: #666;
  pointer-events: none;
}

.map-legend {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.map-legend h3 {
  margin: 0 0 15px 0;
  color: #667eea;
  font-size: 1.2em;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #333;
}

.legend-color.sec-negative {
  background: v-bind('securityColorNegative');
  border-color: v-bind('securityStrokeColorNegative');
}

.legend-color.sec-red {
  background: v-bind('securityColorRed');
  border-color: v-bind('securityStrokeColorRed');
}

.legend-color.sec-orange {
  background: v-bind('securityColorOrange');
  border-color: v-bind('securityStrokeColorOrange');
}

.legend-color.sec-yellow {
  background: v-bind('securityColorYellow');
  border-color: v-bind('securityStrokeColorYellow');
}

.legend-color.sec-green {
  background: v-bind('securityColorGreen');
  border-color: v-bind('securityStrokeColorGreen');
}

.legend-color.sec-blue {
  background: v-bind('securityColorBlue');
  border-color: v-bind('securityStrokeColorBlue');
}

.system-tooltip {
  position: fixed;
  background: #333;
  color: white;
  padding: 12px;
  border-radius: 6px;
  font-size: 0.9em;
  z-index: 1000;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  min-width: 200px;
  max-width: 300px;
}

.tooltip-header {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.tooltip-header strong {
  color: #4299e1;
  font-size: 1.1em;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.tooltip-label {
  color: #ccc;
  font-weight: 500;
}

.tooltip-value {
  color: white;
  font-weight: 600;
}

.tooltip-footer {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 0.85em;
  color: #aaa;
  font-style: italic;
}
</style>

