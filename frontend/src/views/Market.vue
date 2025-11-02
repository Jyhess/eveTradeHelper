<template>
  <div class="market-page">
    <h1>Eve Trade Helper</h1>
    <p class="subtitle">Marché - Catégories</p>

    <Breadcrumb :items="breadcrumbItems" />

    <div class="card">
      <div v-if="loading" class="loading">
        Chargement des catégories du marché...
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="treeData.length > 0" class="categories-container">
        <div class="stats">
          <p><strong>{{ total }}</strong> catégorie(s) de marché</p>
        </div>

        <div class="main-content">
          <div class="tree-container">
            <TreeNode
              v-for="rootNode in treeData"
              :key="rootNode.group_id"
              :node="rootNode"
              :level="0"
              :type-details="typeDetails"
              @node-selected="handleNodeSelected"
            />
          </div>

          <!-- Panneau latéral -->
          <div v-if="selectedCategory || selectedTypeId" class="details-panel">
            <div class="panel-header">
              <h3>{{ selectedCategory ? selectedCategory.name : (typeDetails[selectedTypeId]?.name || `Type ${selectedTypeId}`) }}</h3>
              <button class="close-button" @click="closePanel">×</button>
            </div>
            <div class="panel-content">
              <!-- Affichage si c'est une catégorie -->
              <template v-if="selectedCategory">
                <div v-if="selectedCategory.description" class="description">
                  <h4>Description</h4>
                  <p>{{ selectedCategory.description }}</p>
                </div>

                <div v-if="selectedCategory.types && selectedCategory.types.length > 0" class="types-section">
                  <h4>{{ selectedCategory.types.length }} type(s) d'item</h4>
                  <div class="types-list">
                    <div
                      v-for="typeId in selectedCategory.types"
                      :key="typeId"
                      class="type-item"
                      @click="selectType(typeId)"
                    >
                      Type ID: {{ typeId }}
                      <span v-if="typeDetails[typeId]" class="type-name">
                        - {{ typeDetails[typeId].name }}
                      </span>
                      <span v-else class="loading-small">Chargement...</span>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Détails du type sélectionné (si sélectionné depuis l'arbre ou le panneau) -->
              <div v-if="selectedTypeId && typeDetails[selectedTypeId]" class="type-details">
                <h4>{{ typeDetails[selectedTypeId].name }}</h4>
                <div v-if="typeDetails[selectedTypeId].description" class="type-description">
                  <p>{{ typeDetails[selectedTypeId].description }}</p>
                </div>

                <!-- Ordres de marché (si on est sur une page de région) -->
                <div v-if="regionId" class="market-orders">
                  <h4>Offres de marché ({{ regionName }})</h4>
                  
                  <div v-if="marketOrdersLoading" class="loading-small">
                    Chargement des offres...
                  </div>
                  <div v-else-if="marketOrdersError" class="error-small">
                    {{ marketOrdersError }}
                  </div>
                  <div v-else>
                    <!-- Ordres d'achat -->
                    <div v-if="marketOrders.buy_orders && marketOrders.buy_orders.length > 0" class="orders-section">
                      <h5>Ordres d'achat ({{ marketOrders.buy_orders.length }})</h5>
                      <div class="orders-list">
                        <div
                          v-for="order in marketOrders.buy_orders.slice(0, 10)"
                          :key="order.order_id"
                          class="order-item buy-order"
                        >
                          <div class="order-price">{{ formatPrice(order.price) }} ISK</div>
                          <div class="order-quantity">Qté: {{ order.volume_remain || order.volume_total }}</div>
                          <div class="order-location">Système: {{ order.location_id }}</div>
                        </div>
                      </div>
                    </div>

                    <!-- Ordres de vente -->
                    <div v-if="marketOrders.sell_orders && marketOrders.sell_orders.length > 0" class="orders-section">
                      <h5>Ordres de vente ({{ marketOrders.sell_orders.length }})</h5>
                      <div class="orders-list">
                        <div
                          v-for="order in marketOrders.sell_orders.slice(0, 10)"
                          :key="order.order_id"
                          class="order-item sell-order"
                        >
                          <div class="order-price">{{ formatPrice(order.price) }} ISK</div>
                          <div class="order-quantity">Qté: {{ order.volume_remain || order.volume_total }}</div>
                          <div class="order-location">Système: {{ order.location_id }}</div>
                        </div>
                      </div>
                    </div>

                    <div v-if="marketOrders.total === 0" class="no-orders">
                      Aucune offre disponible
                    </div>
                  </div>
                </div>
                <div v-else-if="!regionId" class="no-region-warning">
                  Sélectionnez une région pour voir les offres de marché
                </div>
                <div v-else-if="regionId && !marketOrders" class="no-region-warning">
                  Cliquez sur un type d'item pour voir les offres
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">
        Aucune catégorie trouvée.
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import Breadcrumb from '../components/Breadcrumb.vue'
import TreeNode from '../components/TreeNode.vue'

export default {
  name: 'Market',
  components: {
    Breadcrumb,
    TreeNode
  },
  props: {
    regionId: {
      type: [String, Number],
      default: null
    },
    constellationId: {
      type: [String, Number],
      default: null
    },
    systemId: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      categories: [],
      total: 0,
      loading: false,
      error: '',
      regionName: '',
      constellationName: '',
      systemName: '',
      selectedCategory: null,
      selectedTypeId: null,
      typeDetails: {},
      marketOrders: null,
      marketOrdersLoading: false,
      marketOrdersError: ''
    }
  },
  computed: {
    breadcrumbItems() {
      const items = [
        { label: 'Accueil', path: '/regions' },
        { label: 'Régions', path: '/regions' }
      ]

      if (this.regionId && this.regionName) {
        items.push({
          label: this.regionName,
          path: `/regions/${this.regionId}/constellations`
        })
      }

      if (this.constellationId && this.constellationName) {
        items.push({
          label: this.constellationName,
          path: `/constellations/${this.constellationId}/systems`
        })
      }

      if (this.systemId && this.systemName) {
        items.push({
          label: this.systemName,
          path: `/systems/${this.systemId}`
        })
      }

      items.push({
        label: 'Marché',
        path: this.getMarketPath()
      })

      return items
    },
    treeData() {
      return this.buildTree(this.categories)
    }
  },
  methods: {
    async fetchCategories() {
      this.loading = true
      this.error = ''
      this.categories = []

      try {
        const response = await axios.get('http://localhost:5000/api/v1/markets/categories')
        this.categories = response.data.categories || []
        this.total = response.data.total || 0

        console.log('Catégories reçues:', this.categories.length)
        console.log('TreeData construit:', this.treeData.length)

        // Récupérer les noms pour le breadcrumb si nécessaire
        if (this.regionId) {
          await this.fetchRegionName()
        }
        if (this.constellationId) {
          await this.fetchConstellationName()
        }
        if (this.systemId) {
          await this.fetchSystemName()
        }
      } catch (error) {
        this.error = 'Erreur: ' + (error.response?.data?.detail || error.message)
        console.error('Erreur lors du chargement des catégories:', error)
      } finally {
        this.loading = false
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

      // Troisième passe : ajouter les types d'items comme nœuds enfants
      const addTypesAsChildren = (node) => {
        if (node.types && node.types.length > 0) {
          node.types.forEach(typeId => {
            node.children.push({
              type_id: typeId,
              name: `Type ${typeId}`, // Sera remplacé par le vrai nom une fois chargé
              is_type: true,
              children: []
            })
          })
        }
        // Appliquer récursivement aux enfants
        node.children.forEach(child => {
          if (!child.is_type) {
            addTypesAsChildren(child)
          }
        })
      }

      rootNodes.forEach(node => addTypesAsChildren(node))

      // Trier les nœuds et leurs enfants récursivement
      const sortNodes = (nodes) => {
        nodes.sort((a, b) => {
          // Les types après les catégories
          if (a.is_type && !b.is_type) return 1
          if (!a.is_type && b.is_type) return -1
          return a.name.localeCompare(b.name)
        })
        nodes.forEach(node => {
          if (node.children.length > 0) {
            sortNodes(node.children)
          }
        })
      }

      sortNodes(rootNodes)

      return rootNodes
    },
    async fetchRegionName() {
      try {
        const response = await axios.get('http://localhost:5000/api/v1/regions')
        const region = response.data.regions?.find(r => r.region_id === parseInt(this.regionId))
        if (region) {
          this.regionName = region.name
        }
      } catch (error) {
        console.error('Erreur lors de la récupération du nom de la région:', error)
      }
    },
    async fetchConstellationName() {
      try {
        if (!this.regionId) return
        const response = await axios.get(
          `http://localhost:5000/api/v1/regions/${this.regionId}/constellations`
        )
        const constellation = response.data.constellations?.find(
          c => c.constellation_id === parseInt(this.constellationId)
        )
        if (constellation) {
          this.constellationName = constellation.name
        }
      } catch (error) {
        console.error('Erreur lors de la récupération du nom de la constellation:', error)
      }
    },
    async fetchSystemName() {
      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/systems/${this.systemId}`
        )
        if (response.data.system) {
          this.systemName = response.data.system.name
        }
      } catch (error) {
        console.error('Erreur lors de la récupération du nom du système:', error)
      }
    },
    getMarketPath() {
      if (this.systemId) {
        return `/markets/system/${this.systemId}`
      } else if (this.constellationId) {
        return `/markets/constellation/${this.constellationId}`
      } else if (this.regionId) {
        return `/markets/region/${this.regionId}`
      }
      return '/markets'
    },
    handleNodeSelected(node) {
      // Si c'est un type d'item, sélectionner le type
      if (node.is_type && node.type_id) {
        this.selectedTypeId = node.type_id
        this.selectedCategory = null
        this.marketOrders = null
        
        // Charger les détails du type
        if (!this.typeDetails[node.type_id]) {
          this.fetchTypeDetails(node.type_id)
        }
        
        // Charger les ordres si on a une région
        if (this.regionId) {
          this.fetchMarketOrders(node.type_id)
        }
      } else {
        // C'est une catégorie
        this.selectedCategory = node
        this.selectedTypeId = null
        this.marketOrders = null

        // Charger les détails des types si disponibles
        if (node.types && node.types.length > 0) {
          node.types.forEach(typeId => {
            if (!this.typeDetails[typeId]) {
              this.fetchTypeDetails(typeId)
            }
          })
        }
      }
    },
    async fetchTypeDetails(typeId) {
      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/universe/types/${typeId}`
        )
        this.typeDetails[typeId] = response.data
      } catch (error) {
        console.error(`Erreur lors de la récupération du type ${typeId}:`, error)
        this.typeDetails[typeId] = { name: `Type ${typeId}`, description: '' }
      }
    },
    selectType(typeId) {
      this.selectedTypeId = typeId
      this.marketOrders = null
      this.marketOrdersError = ''

      // Charger les ordres de marché si on est sur une page de région
      if (this.regionId) {
        this.fetchMarketOrders(typeId)
      }
    },
    async fetchMarketOrders(typeId) {
      if (!this.regionId) return

      this.marketOrdersLoading = true
      this.marketOrdersError = ''

      try {
        const response = await axios.get(
          `http://localhost:5000/api/v1/markets/regions/${this.regionId}/orders`,
          { params: { type_id: typeId } }
        )
        this.marketOrders = response.data
      } catch (error) {
        this.marketOrdersError = 'Erreur: ' + (error.response?.data?.detail || error.message)
        console.error('Erreur lors de la récupération des ordres:', error)
      } finally {
        this.marketOrdersLoading = false
      }
    },
    closePanel() {
      this.selectedCategory = null
      this.selectedTypeId = null
      this.marketOrders = null
    },
    formatPrice(price) {
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(price)
    }
  },
  mounted() {
    this.fetchCategories()
  },
  watch: {
    regionId() {
      this.fetchCategories()
    },
    constellationId() {
      this.fetchCategories()
    },
    systemId() {
      this.fetchCategories()
    }
  }
}
</script>

<style scoped>
.market-page {
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

.stats {
  margin: 20px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
}

.stats p {
  margin: 0;
  font-size: 1.1em;
  color: #667eea;
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #999;
  font-style: italic;
}

.main-content {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.tree-container {
  flex: 0 0 33.333%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
  max-height: 80vh;
  overflow-y: auto;
}

.details-panel {
  flex: 0 0 66.666%;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
}

.panel-header h3 {
  margin: 0;
  color: #667eea;
  font-size: 1.2em;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5em;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.close-button:hover {
  background: #e0e0e0;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.description {
  margin-bottom: 20px;
}

.description h4,
.types-section h4,
.type-details h4,
.market-orders h4 {
  margin: 0 0 10px 0;
  color: #667eea;
  font-size: 1.1em;
}

.description p,
.type-description p {
  margin: 0;
  color: #555;
  line-height: 1.6;
}

.types-section {
  margin-bottom: 20px;
}

.types-list {
  max-height: 300px;
  overflow-y: auto;
}

.type-item {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.type-item:hover {
  background: #f8f9fa;
  border-color: #667eea;
}

.type-name {
  color: #667eea;
  font-weight: 500;
}

.loading-small {
  color: #999;
  font-size: 0.9em;
  font-style: italic;
}

.type-details {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid #e0e0e0;
}

.market-orders {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid #e0e0e0;
}

.orders-section {
  margin-bottom: 20px;
}

.orders-section h5 {
  margin: 0 0 10px 0;
  color: #4299e1;
  font-size: 1em;
}

.orders-list {
  max-height: 300px;
  overflow-y: auto;
}

.order-item {
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-item.buy-order {
  background: #e6f7ff;
  border-color: #4299e1;
}

.order-item.sell-order {
  background: #fff4e6;
  border-color: #faad14;
}

.order-price {
  font-weight: 600;
  color: #333;
}

.order-quantity,
.order-location {
  font-size: 0.9em;
  color: #666;
}

.no-orders,
.no-region-warning {
  padding: 20px;
  text-align: center;
  color: #999;
  font-style: italic;
}

.error-small {
  padding: 10px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 4px;
  color: #c33;
  font-size: 0.9em;
}
</style>