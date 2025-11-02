<template>
  <div class="deals-page">
    <div class="card">
      <div class="search-section">
        <div class="form-group">
          <label for="region-select">Région:</label>
          <select id="region-select" v-model="selectedRegionId" @change="onRegionChange">
            <option value="">Sélectionner une région...</option>
            <option v-for="region in regions" :key="region.region_id" :value="region.region_id">
              {{ region.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="group-select">Groupe de marché:</label>
          <div v-if="loadingGroups" class="loading-small">Chargement des groupes...</div>
          <TreeSelect
            v-else
            :tree="marketGroupsTree"
            :value="selectedGroupId"
            placeholder="Sélectionner un groupe..."
            :disabled="!selectedRegionId || loadingGroups"
            @input="handleGroupSelect"
            @change="handleGroupChange"
          />
        </div>

        <div class="form-group">
          <label for="threshold-input">Seuil de bénéfice (%):</label>
          <input 
            id="threshold-input" 
            type="number" 
            v-model.number="profitThreshold" 
            min="0" 
            max="100" 
            step="0.1"
            :disabled="!selectedGroupId"
          />
        </div>

        <button 
          class="search-button" 
          @click="searchDeals" 
          :disabled="!selectedRegionId || !selectedGroupId || searching"
        >
          {{ searching ? 'Recherche en cours...' : 'Rechercher les bonnes affaires' }}
        </button>
      </div>

      <div v-if="error" class="error">
        {{ error }}
      </div>

      <div v-if="searchResults" class="results-section">
        <div class="results-header">
          <h2>Résultats</h2>
          <div class="results-stats">
            <p>
              <strong>{{ searchResults.deals.length }}</strong> bonne(s) affaire(s) trouvée(s)
              sur <strong>{{ searchResults.total_types }}</strong> type(s) analysé(s)
            </p>
            <p>
              Total bénéfice potentiel: <strong>{{ formatPrice(searchResults.total_profit_isk || 0) }} ISK</strong>
            </p>
            <p>
              Seuil: <strong>{{ searchResults.profit_threshold }}%</strong> | 
              Région: <strong>{{ regionName }}</strong> |
              Groupe: <strong>{{ groupName }}</strong>
            </p>
          </div>
        </div>

        <div v-if="searchResults.deals.length === 0" class="no-results">
          <p>Aucune bonne affaire trouvée avec le seuil de {{ searchResults.profit_threshold }}%</p>
          <p>Essayez de réduire le seuil ou de sélectionner un autre groupe.</p>
        </div>

        <div v-else class="deals-list">
          <div class="sort-controls">
            <label>Trier par:</label>
            <select v-model="sortBy" class="sort-select">
              <option value="profit">Bénéfice (%)</option>
              <option value="jumps">Nombre de sauts</option>
              <option value="profit_isk">Bénéfice (ISK)</option>
            </select>
          </div>
          <div v-for="deal in sortedDeals" :key="deal.type_id" class="deal-item">
            <div class="deal-header">
              <h3>{{ deal.type_name }}</h3>
              <div class="profit-badge" :class="getProfitBadgeClass(deal.profit_percent)">
                {{ deal.profit_percent }}% de bénéfice
              </div>
            </div>
            <div class="deal-details">
              <div class="price-info">
                <div class="price-item">
                  <span class="price-label">Meilleur prix d'achat:</span>
                  <span class="price-value buy-price">{{ formatPrice(deal.best_buy_price) }} ISK</span>
                </div>
                <div class="price-item">
                  <span class="price-label">Meilleur prix de vente:</span>
                  <span class="price-value sell-price">{{ formatPrice(deal.best_sell_price) }} ISK</span>
                </div>
                <div class="price-item profit-item">
                  <span class="price-label">Bénéfice:</span>
                  <span class="price-value profit-value">{{ formatPrice(deal.profit_isk) }} ISK</span>
                </div>
              </div>
              <div class="order-stats">
                <span>{{ deal.buy_order_count }} ordre(s) d'achat</span>
                <span>•</span>
                <span>{{ deal.sell_order_count }} ordre(s) de vente</span>
                <span v-if="deal.tradable_volume">
                  • <span class="volume-info">Vol: {{ deal.tradable_volume.toLocaleString('fr-FR') }}</span>
                </span>
                <span v-if="deal.jumps !== null && deal.jumps !== undefined">
                  • <span class="jumps-info">{{ deal.jumps }} saut(s)</span>
                </span>
                <span v-else-if="deal.jumps === null || deal.jumps === undefined">
                  • <span class="jumps-info unknown">Sauts inconnus</span>
                </span>
              </div>
              
              <!-- Affichage de la route avec niveaux de danger -->
              <div v-if="deal.route_details && deal.route_details.length > 0" class="route-display">
                <span class="route-label">Route:</span>
                <div class="route-jumps">
                  <div 
                    v-for="(system, index) in deal.route_details" 
                    :key="system.system_id"
                    class="route-jump"
                  >
                    <div 
                      class="danger-indicator"
                      :class="getDangerClass(system.security_status)"
                      :title="`${system.name}\nSécurité: ${system.security_status.toFixed(1)}`"
                    >
                      <span class="tooltip-text">{{ system.name }}<br>Sécurité: {{ system.security_status.toFixed(1) }}</span>
                    </div>
                    <span v-if="index < deal.route_details.length - 1" class="route-arrow">→</span>
                  </div>
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
import axios from 'axios'
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
      profitThreshold: 5.0,
      searching: false,
      searchResults: null,
      error: '',
      sortBy: 'profit'
    }
  },
  computed: {
    sortedDeals() {
      if (!this.searchResults || !this.searchResults.deals) {
        return []
      }
      const deals = [...this.searchResults.deals]
      
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
    }
  },
  async mounted() {
    await this.fetchRegions()
    // Si on a un regionId dans les props (depuis une route), le charger
    const routeRegionId = this.$route.params.regionId || this.$route.query.region_id
    if (routeRegionId) {
      this.selectedRegionId = parseInt(routeRegionId)
      await this.onRegionChange()
      
      // Si on a un group_id dans les query params, le sélectionner
      const groupId = this.$route.query.group_id
      if (groupId) {
        await this.$nextTick() // Attendre que les groupes soient chargés
        this.selectedGroupId = parseInt(groupId)
        const group = this.marketGroups.find(g => g.group_id === this.selectedGroupId)
        if (group) {
          this.groupName = group.name
        }
      }
    }
  },
  methods: {
    async fetchRegions() {
      try {
        const response = await axios.get('http://localhost:5000/api/v1/regions')
        this.regions = response.data.regions || []
        // Trouver le nom de la région si selectedRegionId est déjà défini
        if (this.selectedRegionId) {
          const region = this.regions.find(r => r.region_id === this.selectedRegionId)
          if (region) {
            this.regionName = region.name
          }
        }
      } catch (error) {
        this.error = 'Erreur lors du chargement des régions: ' + (error.response?.data?.detail || error.message)
        console.error('Erreur lors du chargement des régions:', error)
      }
    },
    async onRegionChange() {
      if (!this.selectedRegionId) {
        this.marketGroups = []
        this.selectedGroupId = null
        this.regionName = ''
        return
      }

      const region = this.regions.find(r => r.region_id === this.selectedRegionId)
      if (region) {
        this.regionName = region.name
        // Mettre à jour le breadcrumb
        eventBus.emit('breadcrumb-update', {
          regionName: this.regionName,
          regionId: this.selectedRegionId
        })
      }

      await this.fetchMarketGroups()
    },
    async fetchMarketGroups() {
      if (!this.selectedRegionId) return

      this.loadingGroups = true
      this.error = ''
      this.marketGroups = []
      this.marketGroupsTree = []

      try {
        const response = await axios.get('http://localhost:5000/api/v1/markets/categories')
        const categories = response.data.categories || []
        
        // Construire l'arbre hiérarchique
        this.marketGroupsTree = this.buildTree(categories)
        
        // Conserver aussi la liste plate pour compatibilité
        this.marketGroups = categories.map(cat => ({
          group_id: cat.group_id,
          name: cat.name
        }))

        // Trouver le nom du groupe si selectedGroupId est déjà défini
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
        this.error = 'Erreur lors du chargement des groupes de marché: ' + (error.response?.data?.detail || error.message)
        console.error('Erreur lors du chargement des groupes:', error)
      } finally {
        this.loadingGroups = false
      }
    },
    buildTree(categories) {
      if (!categories || categories.length === 0) {
        return []
      }

      // Créer un map pour accès rapide
      const categoryMap = new Map()
      const rootNodes = []

      // Première passe : créer tous les nœuds
      categories.forEach(category => {
        categoryMap.set(category.group_id, {
          ...category,
          children: []
        })
      })

      // Deuxième passe : construire l'arbre
      categories.forEach(category => {
        const node = categoryMap.get(category.group_id)

        if (category.parent_group_id && categoryMap.has(category.parent_group_id)) {
          // Ajouter ce nœud comme enfant de son parent
          const parent = categoryMap.get(category.parent_group_id)
          parent.children.push(node)
        } else {
          // C'est un nœud racine
          rootNodes.push(node)
        }
      })

      // Trier les nœuds et leurs enfants récursivement
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
    },
    handleGroupChange(group) {
      if (group) {
        this.groupName = group.name
      }
    },
    findGroupInTree(tree, groupId) {
      // Recherche récursive dans l'arbre
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
        this.error = 'Veuillez sélectionner une région et un groupe de marché'
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
        const response = await axios.get('http://localhost:5000/api/v1/markets/deals', {
          params: {
            region_id: this.selectedRegionId,
            group_id: this.selectedGroupId,
            profit_threshold: this.profitThreshold
          }
        })
        this.searchResults = response.data
      } catch (error) {
        this.error = 'Erreur lors de la recherche: ' + (error.response?.data?.detail || error.message)
        console.error('Erreur lors de la recherche de bonnes affaires:', error)
      } finally {
        this.searching = false
      }
    },
    formatPrice(price) {
      if (price >= 1000) {
        return Math.round(price).toLocaleString('fr-FR')
      }
      return price.toFixed(2).replace('.', ',')
    },
    getProfitBadgeClass(profitPercent) {
      if (profitPercent >= 20) return 'profit-excellent'
      if (profitPercent >= 10) return 'profit-good'
      if (profitPercent >= 5) return 'profit-medium'
      return 'profit-low'
    },
    getDangerClass(securityStatus) {
      if (securityStatus >= 0.5) return 'danger-high-sec'
      if (securityStatus > 0.0) return 'danger-low-sec'
      return 'danger-null-sec'
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
}

.deal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.3em;
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

.route-display {
  margin-top: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.route-label {
  font-weight: 600;
  color: #667eea;
  font-size: 0.9em;
}

.route-jumps {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}

.route-jump {
  display: flex;
  align-items: center;
  gap: 5px;
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

.danger-high-sec {
  background: #48bb78; /* Vert pour high-sec */
}

.danger-low-sec {
  background: #ed8936; /* Orange pour low-sec */
}

.danger-null-sec {
  background: #f56565; /* Rouge pour null-sec */
}

.route-arrow {
  color: #999;
  font-size: 0.9em;
  margin: 0 3px;
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
