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

        <div class="tree-container">
          <TreeNode
            v-for="rootNode in treeData"
            :key="rootNode.group_id"
            :node="rootNode"
            :level="0"
          />
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
      systemName: ''
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

.tree-container {
  margin-top: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
  max-height: 80vh;
  overflow-y: auto;
}
</style>