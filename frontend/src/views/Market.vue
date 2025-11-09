<template>
  <div class="market-page">
    <div class="card">
      <Loader v-if="loading" message="Loading market categories..." variant="overlay" />
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="treeData.length > 0" class="categories-container">
        <div class="region-selector-section">
          <div class="form-group">
            <label for="region-select">Region:</label>
            <select
              id="region-select"
              :value="currentRegionId"
              class="region-select"
              @change="onRegionChange"
            >
              <option value="">All regions</option>
              <option v-for="region in regions" :key="region.region_id" :value="region.region_id">
                {{ region.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="main-content">
          <div class="tree-container">
            <TreeNode
              v-for="rootNode in treeData"
              :key="rootNode.group_id"
              :node="rootNode"
              :level="0"
              :type-details="typeDetails"
              :region-id="regionId"
              :expanded-paths="expandedPaths"
              @node-selected="handleNodeSelected"
            />
          </div>

          <!-- Side panel -->
          <div v-if="selectedCategory || selectedTypeId" class="details-panel">
            <div class="panel-header">
              <h3>
                {{
                  selectedCategory
                    ? selectedCategory.name
                    : typeDetails[selectedTypeId]?.name ||
                      `Type
                ${selectedTypeId}`
                }}
              </h3>
              <button class="close-button" @click="closePanel">×</button>
            </div>
            <div class="panel-content">
              <!-- Display if it's a category -->
              <template v-if="selectedCategory">
                <div class="category-info">
                  <h4>Information</h4>
                  <p><strong>Category ID:</strong> {{ selectedCategory.group_id }}</p>
                </div>

                <div v-if="selectedCategory.description" class="description">
                  <h4>Description</h4>
                  <p v-html="processDescription(selectedCategory.description)"></p>
                </div>

                <div
                  v-if="selectedCategory.types && selectedCategory.types.length > 0"
                  class="types-section"
                >
                  <h4>{{ selectedCategory.types.length }} item type(s)</h4>
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
                      <Loader v-else message="Loading..." size="small" />
                    </div>
                  </div>
                </div>
              </template>

              <!-- Selected type details (if selected from tree or panel) -->
              <div v-if="selectedTypeId && typeDetails[selectedTypeId]" class="type-details">
                <h4>{{ typeDetails[selectedTypeId].name }}</h4>
                <div v-if="typeDetails[selectedTypeId].description" class="type-description">
                  <p v-html="processDescription(typeDetails[selectedTypeId].description)"></p>
                </div>

                <!-- Market orders (if on a region page) -->
                <div v-if="regionId" class="market-orders">
                  <h4>Market Orders ({{ regionName }})</h4>

                  <Loader v-if="marketOrdersLoading" message="Loading orders..." size="small" />
                  <div v-else-if="marketOrdersError" class="error-small">
                    {{ marketOrdersError }}
                  </div>
                  <div v-else-if="marketOrders">
                    <!-- Buy orders -->
                    <div
                      v-if="marketOrders.buy_orders && marketOrders.buy_orders.length > 0"
                      class="orders-section"
                    >
                      <h5>Buy Orders ({{ marketOrders.buy_orders.length }})</h5>
                      <div class="orders-list">
                        <div
                          v-for="order in marketOrders.buy_orders.slice(0, 10)"
                          :key="order.order_id"
                          class="order-item buy-order"
                        >
                          <div class="order-quantity">
                            Qty: {{ order.volume_remain || order.volume_total }}
                          </div>
                          <div class="order-price">{{ formatPrice(order.price) }} ISK</div>
                          <div class="order-location">
                            <span v-if="order.station_name && order.system_name">
                              {{ order.station_name }} ({{ order.system_name }})
                            </span>
                            <span v-else-if="order.system_name">
                              {{ order.system_name }}
                            </span>
                            <span v-else> System: {{ order.location_id }} </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Sell orders -->
                    <div
                      v-if="marketOrders.sell_orders && marketOrders.sell_orders.length > 0"
                      class="orders-section"
                    >
                      <h5>Sell Orders ({{ marketOrders.sell_orders.length }})</h5>
                      <div class="orders-list">
                        <div
                          v-for="order in marketOrders.sell_orders.slice(0, 10)"
                          :key="order.order_id"
                          class="order-item sell-order"
                        >
                          <div class="order-quantity">
                            Qty: {{ order.volume_remain || order.volume_total }}
                          </div>
                          <div class="order-price">{{ formatPrice(order.price) }} ISK</div>
                          <div class="order-location">
                            <span v-if="order.station_name && order.system_name">
                              {{ order.station_name }} ({{ order.system_name }})
                            </span>
                            <span v-else-if="order.system_name">
                              {{ order.system_name }}
                            </span>
                            <span v-else> System: {{ order.location_id }} </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div v-if="marketOrders.total === 0" class="no-orders">No orders available</div>
                  </div>
                  <div v-else class="no-region-warning">
                    Click on an item type to view orders
                  </div>
                </div>
                <div v-else-if="!regionId" class="no-region-warning">
                  Select a region to view market orders
                </div>
                <div v-else class="no-region-warning">Loading market orders...</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data">No categories found.</div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import TreeNode from '../components/TreeNode.vue'
import Loader from '../components/Loader.vue'
import eventBus from '../utils/eventBus'
import { formatPrice } from '../utils/numberFormatter'

export default {
  name: 'Market',
  components: {
    TreeNode,
    Loader
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
      regions: [],
      regionName: '',
      constellationName: '',
      systemName: '',
      selectedCategory: null,
      selectedTypeId: null,
      typeDetails: {},
      marketOrders: null,
      marketOrdersLoading: false,
      marketOrdersError: '',
      expandedPaths: new Set() // Paths (group_id) to expand to reach a type
    }
  },
  computed: {
    treeData() {
      return this.buildTree(this.categories)
    },
    currentRegionId() {
      return this.regionId ? parseInt(this.regionId) : null
    }
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
    },
    '$route.query.type_id'(newTypeId) {
      if (newTypeId && this.treeData.length > 0) {
        this.navigateToType(parseInt(newTypeId))
      }
    }
  },
  async mounted() {
    await this.fetchRegions()
    this.fetchCategories()
    // Setup description links after initial render
    this.$nextTick(() => {
      this.setupDescriptionLinks()
    })
  },
  updated() {
    // Setup click handlers for description links after DOM update
    this.$nextTick(() => {
      this.setupDescriptionLinks()
    })
  },
  methods: {
    async fetchCategories() {
      this.loading = true
      this.error = ''
      this.categories = []

      try {
        const data = await api.markets.getCategories()
        this.categories = data.categories || []
        this.total = data.total || 0

        console.log('Categories received:', this.categories.length)
        console.log('TreeData built:', this.treeData.length)

        // Retrieve names for breadcrumb if necessary
        if (this.regionId) {
          await this.fetchRegionName()
        } else {
          // Ensure regions are loaded even if no regionId
          if (this.regions.length === 0) {
            await this.fetchRegions()
          }
        }
        if (this.constellationId) {
          await this.fetchConstellationName()
        }
        if (this.systemId) {
          await this.fetchSystemName()
        }

        // Check if we should go directly to a type from URL
        await this.$nextTick()
        const typeIdFromQuery = this.$route.query.type_id
        if (typeIdFromQuery) {
          await this.navigateToType(parseInt(typeIdFromQuery))
        }
      } catch (error) {
        this.error = 'Error: ' + error.message
      } finally {
        this.loading = false
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

      // Third pass: add item types as child nodes
      const addTypesAsChildren = node => {
        if (node.types && node.types.length > 0) {
          node.types.forEach(typeId => {
            node.children.push({
              type_id: typeId,
              name: `Type ${typeId}`, // Will be replaced by real name once loaded
              is_type: true,
              children: []
            })
          })
        }
        // Apply recursively to children
        node.children.forEach(child => {
          if (!child.is_type) {
            addTypesAsChildren(child)
          }
        })
      }

      rootNodes.forEach(node => addTypesAsChildren(node))

      // Sort nodes and their children recursively
      const sortNodes = nodes => {
        nodes.sort((a, b) => {
          // Types after categories
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
    async fetchRegions() {
      try {
        const data = await api.regions.getRegions()
        this.regions = data.regions || []
        // Update region name if regionId is set
        if (this.regionId) {
          const region = this.regions.find(r => r.region_id === parseInt(this.regionId))
          if (region) {
            this.regionName = region.name
          }
        }
      } catch (error) {
        console.error('Error loading regions:', error)
      }
    },
    async fetchRegionName() {
      if (!this.regions || this.regions.length === 0) {
        await this.fetchRegions()
      }
      if (this.regionId) {
        const region = this.regions.find(r => r.region_id === parseInt(this.regionId))
        if (region) {
          this.regionName = region.name
          eventBus.emit('breadcrumb-update', {
            regionName: this.regionName,
            regionId: this.regionId
          })
        }
      }
    },
    onRegionChange(event) {
      const selectedRegionId = event.target.value
      if (selectedRegionId) {
        // Navigate to the selected region's market page
        this.$router.push(`/markets/region/${selectedRegionId}`)
      } else {
        // Navigate to the general market page (no region)
        this.$router.push('/markets')
      }
    },
    async fetchConstellationName() {
      try {
        if (!this.regionId) return
        const data = await api.regions.getConstellations(this.regionId)
        const constellation = data.constellations?.find(
          c => c.constellation_id === parseInt(this.constellationId)
        )
        if (constellation) {
          this.constellationName = constellation.name
          // Update breadcrumb
          eventBus.emit('breadcrumb-update', {
            constellationName: this.constellationName,
            constellationId: this.constellationId
          })
        }
      } catch (error) {
        console.error('Error retrieving constellation name:', error)
      }
    },
    async fetchSystemName() {
      try {
        const data = await api.systems.getSystem(this.systemId)
        if (data.system) {
          this.systemName = data.system.name
          // Update breadcrumb
          eventBus.emit('breadcrumb-update', {
            systemName: this.systemName,
            systemId: this.systemId
          })
        }
      } catch (error) {
        console.error('Error retrieving system name:', error)
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
      // If it's an item type, select the type
      if (node.is_type && node.type_id) {
        this.selectedTypeId = node.type_id
        this.selectedCategory = null
        this.marketOrders = null

        // Load type details
        if (!this.typeDetails[node.type_id]) {
          this.fetchTypeDetails(node.type_id)
        }

        // Load orders if we have a region
        if (this.regionId) {
          this.fetchMarketOrders(node.type_id)
        }
      } else {
        // It's a category
        this.selectedCategory = node
        this.selectedTypeId = null
        this.marketOrders = null

        // Load type details if available
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
        const data = await api.universe.getType(typeId)
        this.typeDetails[typeId] = data
      } catch (error) {
        console.error(`Error retrieving type ${typeId}:`, error)
        this.typeDetails[typeId] = { name: `Type ${typeId}`, description: '' }
      }
    },
    selectType(typeId) {
      this.selectedTypeId = typeId
      this.marketOrders = null
      this.marketOrdersError = ''

      // Load market orders if on a region page
      if (this.regionId) {
        this.fetchMarketOrders(typeId)
      }
    },
    async fetchMarketOrders(typeId) {
      if (!this.regionId) return

      this.marketOrdersLoading = true
      this.marketOrdersError = ''

      try {
        const data = await api.markets.getOrders(this.regionId, { type_id: typeId })
        this.marketOrders = data
      } catch (error) {
        this.marketOrdersError = 'Error: ' + error.message
      } finally {
        this.marketOrdersLoading = false
      }
    },
    closePanel() {
      this.selectedCategory = null
      this.selectedTypeId = null
      this.marketOrders = null
    },
    processDescription(description) {
      if (!description) return ''
      
      // Replace showinfo links with clickable links
      // Pattern: <a href=showinfo:1230>text</a>
      const showInfoPattern = /<a\s+href=showinfo:(\d+)>(.*?)<\/a>/gi
      
      const processed = description.replace(showInfoPattern, (match, typeId, linkText) => {
        // Return a clickable link with data attribute
        return `<a href="#" class="description-link" data-type-id="${typeId}">${linkText}</a>`
      })
      
      return processed
    },
    setupDescriptionLinks() {
      // Find all description links and add click handlers
      const links = this.$el.querySelectorAll('.description-link')
      links.forEach(link => {
        // Remove existing listener to avoid duplicates
        const newLink = link.cloneNode(true)
        link.parentNode.replaceChild(newLink, link)
        
        newLink.addEventListener('click', (e) => {
          e.preventDefault()
          const typeId = newLink.getAttribute('data-type-id')
          if (typeId) {
            this.navigateToType(parseInt(typeId))
          }
        })
      })
    },
    // Find a type in the tree and return the path (parent group_ids) to it
    findTypePath(tree, typeId, currentPath = []) {
      for (const node of tree) {
        // If it's the type we're looking for
        if (node.is_type && node.type_id === typeId) {
          return currentPath // Return path to parents (group_id only)
        }

        // Build new path with parent group_id (not types)
        let newPath = currentPath
        if (!node.is_type && node.group_id) {
          newPath = [...currentPath, node.group_id]
        }

        // If this node has children, search recursively
        if (node.children && node.children.length > 0) {
          const found = this.findTypePath(node.children, typeId, newPath)
          if (found !== null) {
            return found
          }
        }
      }
      return null
    },
    // Navigate to a specific type in the tree
    async navigateToType(typeId) {
      // Find path to this type
      const path = this.findTypePath(this.treeData, typeId)

      if (path) {
        // Expand all parents in the path
        this.expandedPaths = new Set(path)

        // Wait a tick for TreeNode components to update
        await this.$nextTick()

        // Select type
        this.selectedTypeId = typeId
        this.selectedCategory = null
        this.marketOrders = null

        // Load type details
        if (!this.typeDetails[typeId]) {
          await this.fetchTypeDetails(typeId)
        }

        // Load market orders if we have a region
        if (this.regionId) {
          await this.fetchMarketOrders(typeId)
        }

        // Scroll to element if possible (optional)
        await this.$nextTick()
        this.scrollToSelectedType()
      } else {
        console.warn(`Type ${typeId} not found in tree`)
      }
    },
    scrollToSelectedType() {
      // Find selected element in DOM and scroll to it
      // This function can be improved if necessary
      const selectedElements = document.querySelectorAll('.type-node')
      selectedElements.forEach(el => {
        if (
          el.textContent &&
          this.typeDetails[this.selectedTypeId] &&
          el.textContent.includes(this.typeDetails[this.selectedTypeId].name)
        ) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      })
    },
    formatPrice
  }
}
</script>

<style scoped>
.market-page {
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

.region-selector-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.region-selector-section .form-group {
  margin: 0;
}

.region-selector-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.region-select {
  width: 100%;
  max-width: 400px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  background: white;
  cursor: pointer;
}

.region-select:hover {
  border-color: #667eea;
}

.region-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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

.category-info {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.category-info h4 {
  margin: 0 0 10px 0;
  color: #667eea;
  font-size: 1.1em;
}

.category-info p {
  margin: 0;
  color: #555;
  line-height: 1.6;
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
  transition:
    background 0.2s,
    border-color 0.2s;
}

.type-item:hover {
  background: #f8f9fa;
  border-color: #667eea;
}

.type-name {
  color: #667eea;
  font-weight: 500;
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
  flex-direction: row;
  align-items: center;
  gap: 15px;
}

.order-item.buy-order {
  background: #e6f7ff;
  border-color: #4299e1;
}

.order-item.sell-order {
  background: #fff4e6;
  border-color: #faad14;
}

.order-quantity {
  font-size: 0.9em;
  color: #666;
  min-width: 120px;
  flex-shrink: 0;
}

.order-price {
  font-weight: 600;
  color: #333;
  font-size: 1em;
  min-width: 150px;
  flex-shrink: 0;
  text-align: right;
}

.order-location {
  font-size: 0.9em;
  color: #666;
  flex: 1;
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
