<template>
  <div class="system-detail-page">
    <h1>Eve Trade Helper</h1>
    <p class="subtitle">Détails du système</p>
    
    <Breadcrumb :items="breadcrumbItems" />
    
    <div class="card">
      <div v-if="loading" class="loading">
        Chargement des informations du système...
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="system" class="system-detail-container">
        <!-- Informations du système -->
        <div class="system-header">
          <h2>{{ system.name }}</h2>
          <div class="market-link">
            <router-link :to="`/markets/system/${systemId}`" class="market-button">
              📊 Voir le marché de ce système
            </router-link>
          </div>
          <div class="system-meta">
            <p class="system-id">ID: {{ system.system_id }}</p>
            <p class="security-status" :class="getSecurityClass(system.security_status)">
              <strong>Sécurité: {{ system.security_status.toFixed(1) }}</strong>
              <span v-if="system.security_class">{{ system.security_class }}</span>
            </p>
            <p v-if="system.constellation_id" class="constellation-link">
              Constellation ID: {{ system.constellation_id }}
            </p>
            <p class="planets-count">
              <strong>{{ system.planets?.length || 0 }}</strong> planète(s)
            </p>
            <div v-if="system.position" class="position">
              <small>
                Position: ({{ Math.round(system.position.x) }}, {{ Math.round(system.position.y) }}, {{ Math.round(system.position.z) }})
              </small>
            </div>
          </div>
        </div>

        <!-- Systèmes connectés -->
        <div class="connections-section">
          <h3>Systèmes connectés</h3>
          <div v-if="connectionsLoading" class="loading-small">
            Chargement des connexions...
          </div>
          <div v-else-if="connectionsError" class="error-small">
            {{ connectionsError }}
          </div>
          <div v-else-if="connections.length > 0" class="connections-grid">
            <router-link
              v-for="connection in connections"
              :key="connection.system_id"
              :to="`/systems/${connection.system_id}`"
              class="connection-card"
              :class="{
                'different-region': !connection.same_region,
                'different-constellation': !connection.same_constellation && connection.same_region
              }"
            >
              <h4>{{ connection.name }}</h4>
              <div class="connection-info">
                <p class="connection-id">ID: {{ connection.system_id }}</p>
                <p class="security-status" :class="getSecurityClass(connection.security_status)">
                  <strong>Sécurité: {{ connection.security_status.toFixed(1) }}</strong>
                  <span v-if="connection.security_class">{{ connection.security_class }}</span>
                </p>
                <div v-if="!connection.same_region" class="location-warning">
                  <span class="warning-badge different-region-badge">
                    Autre région{{ connection.region_name ? `: ${connection.region_name}` : '' }}
                  </span>
                  <span v-if="connection.constellation_name" class="constellation-info">
                    Constellation: {{ connection.constellation_name }}
                  </span>
                </div>
                <div v-else-if="!connection.same_constellation" class="location-warning">
                  <span class="warning-badge different-constellation-badge">
                    Autre constellation{{ connection.constellation_name ? `: ${connection.constellation_name}` : '' }}
                  </span>
                </div>
                <p class="stargate-info">
                  <small>Stargate ID: {{ connection.stargate_id }}</small>
                </p>
              </div>
            </router-link>
          </div>
          <div v-else class="no-connections">
            <p>Aucun système connecté trouvé.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Breadcrumb from '../components/Breadcrumb.vue'

export default {
  name: 'SystemDetail',
  components: {
    Breadcrumb
  },
  props: {
    systemId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      system: null,
      loading: false,
      error: '',
      connections: [],
      connectionsLoading: false,
      connectionsError: '',
      constellationName: '',
      constellationId: null,
      regionId: null,
      regionName: ''
    }
  },
  computed: {
    breadcrumbItems() {
      const items = [
        { label: 'Accueil', path: '/regions' },
        { label: 'Régions', path: '/regions' }
      ]
      
      if (this.regionName) {
        items.push({
          label: this.regionName,
          path: `/regions/${this.regionId}/constellations`
        })
      }
      
      if (this.constellationName) {
        items.push({
          label: this.constellationName,
          path: `/constellations/${this.constellationId}/systems`
        })
      }
      
      if (this.system) {
        items.push({
          label: this.system.name,
          path: `/systems/${this.systemId}`
        })
      }
      
      return items
    }
  },
  methods: {
    async fetchSystemDetails() {
      this.loading = true
      this.error = ''
      this.system = null
      
      try {
        // Récupérer directement les détails du système
        const systemResponse = await axios.get(
          `http://localhost:5000/api/v1/systems/${this.systemId}`
        )
        this.system = systemResponse.data.system
        
        if (this.system && this.system.constellation_id) {
          // Charger les informations de la constellation et de la région
          await this.fetchConstellationInfo(this.system.constellation_id)
        }
        
        // Charger les connexions
        this.fetchConnections()
      } catch (error) {
        this.error = 'Erreur: ' + (error.response?.data?.error || error.message)
        console.error('Erreur lors du chargement des détails du système:', error)
      } finally {
        this.loading = false
      }
    },
    async fetchConstellationInfo(constellationId) {
      try {
        // Récupérer directement les informations de la constellation avec sa région
        const response = await axios.get(
          `http://localhost:5000/api/v1/constellations/${constellationId}`
        )
        
        if (response.data.constellation) {
          this.constellationId = response.data.constellation.constellation_id
          this.constellationName = response.data.constellation.name
        }
        
        if (response.data.region) {
          this.regionId = response.data.region.region_id
          this.regionName = response.data.region.name
        }
      } catch (error) {
        console.error('Erreur lors de la récupération des informations:', error)
      }
    },
    async fetchConnections() {
      this.connectionsLoading = true
      this.connectionsError = ''
      this.connections = []
      
      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/systems/${this.systemId}/connections`
        )
        this.connections = response.data.connections || []
      } catch (error) {
        this.connectionsError = 'Erreur: ' + (error.response?.data?.error || error.message)
        console.error('Erreur lors du chargement des connexions:', error)
      } finally {
        this.connectionsLoading = false
      }
    },
    getSecurityClass(securityStatus) {
      if (securityStatus >= 0.5) return 'high-sec'
      if (securityStatus > 0.0) return 'low-sec'
      return 'null-sec'
    }
  },
  mounted() {
    this.fetchSystemDetails()
  },
  watch: {
    systemId() {
      this.fetchSystemDetails()
    }
  }
}
</script>

<style scoped>
.system-detail-page {
  min-height: 100vh;
  padding: 20px;
}

h1 {
  font-size: 2.5em;
  color: white;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
  text-align: center;
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2em;
  margin-bottom: 30px;
  text-align: center;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #667eea;
  font-size: 1.1em;
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

.system-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.system-header h2 {
  margin: 0 0 15px 0;
  color: #4299e1;
  font-size: 2em;
}

.market-link {
  margin-bottom: 15px;
}

.market-button {
  display: inline-block;
  padding: 10px 20px;
  background: #48bb78;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.2s, transform 0.2s;
}

.market-button:hover {
  background: #38a169;
  transform: translateY(-1px);
}

.system-meta {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.system-id {
  font-size: 0.9em;
  color: #666;
  margin: 0;
}

.security-status {
  padding: 10px 15px;
  border-radius: 6px;
  font-size: 1em;
  margin: 0;
}

.security-status.high-sec {
  background: #c6f6d5;
  color: #22543d;
}

.security-status.low-sec {
  background: #feebc8;
  color: #7c2d12;
}

.security-status.null-sec {
  background: #fed7d7;
  color: #742a2a;
}

.security-status strong {
  display: block;
  margin-bottom: 4px;
}

.constellation-link {
  margin: 0;
  color: #666;
  font-size: 0.95em;
}

.planets-count {
  margin: 0;
  color: #333;
  font-size: 1em;
}

.planets-count strong {
  color: #4299e1;
  font-size: 1.1em;
}

.position {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  color: #888;
  font-size: 0.9em;
}

.connections-section {
  margin-top: 30px;
}

.connections-section h3 {
  margin: 0 0 20px 0;
  color: #667eea;
  font-size: 1.5em;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
}

.loading-small {
  text-align: center;
  padding: 20px;
  color: #667eea;
}

.error-small {
  padding: 15px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  font-size: 0.95em;
}

.no-connections {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

.connections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.connection-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
}

.connection-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #4299e1;
}

.connection-card h4 {
  margin: 0 0 10px 0;
  color: #4299e1;
  font-size: 1.2em;
  border-bottom: 2px solid #4299e1;
  padding-bottom: 8px;
}

.connection-info {
  text-align: left;
}

.connection-id {
  font-size: 0.85em;
  color: #666;
  margin: 5px 0;
}

.stargate-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  color: #888;
  font-size: 0.85em;
}

.location-warning {
  margin: 10px 0;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.constellation-info {
  font-size: 0.85em;
  color: #666;
  font-style: italic;
  margin-top: 4px;
}

.warning-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 600;
}

.different-region-badge {
  background: #fed7d7;
  color: #742a2a;
}

.different-constellation-badge {
  background: #feebc8;
  color: #7c2d12;
}

.connection-card.different-region {
  border-left: 4px solid #f56565;
}

.connection-card.different-constellation {
  border-left: 4px solid #ed8936;
}
</style>

