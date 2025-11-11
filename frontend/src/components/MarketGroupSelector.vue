<template>
  <div class="form-group">
    <label :for="id">Market Group:</label>
    <Loader v-if="loadingGroups" message="Loading groups..." size="small" />
    <TreeSelect
      v-else
      :id="id"
      :tree="marketGroupsTree"
      :value="selectedGroupId"
      placeholder="Select a group..."
      :disabled="disabled || loadingGroups"
      @input="handleGroupSelect"
      @change="handleGroupChange"
    />
  </div>
</template>

<script>
import api from '../services/api'
import TreeSelect from './TreeSelect.vue'
import Loader from './Loader.vue'

export default {
  name: 'MarketGroupSelector',
  components: {
    TreeSelect,
    Loader
  },
  props: {
    id: {
      type: String,
      default: 'group-select'
    },
    selectedGroupId: {
      type: [Number, String],
      default: null
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:selected-group-id', 'group-select', 'group-change', 'error'],
  data() {
    return {
      marketGroups: [],
      marketGroupsTree: [],
      loadingGroups: false
    }
  },
  watch: {
    selectedGroupId(newValue) {
      if (newValue && this.marketGroupsTree.length > 0) {
        this.updateGroupName(newValue)
      }
    }
  },
  mounted() {
    this.fetchMarketGroups()
  },
  methods: {
    async fetchMarketGroups() {
      this.loadingGroups = true

      try {
        const data = await api.markets.getCategories()
        const categories = data.categories || []

        this.marketGroupsTree = this.buildTree(categories)

        this.marketGroups = categories.map(cat => ({
          group_id: cat.group_id,
          name: cat.name
        }))

        if (this.selectedGroupId) {
          this.updateGroupName(this.selectedGroupId)
        }
      } catch (error) {
        this.$emit('error', 'Error loading market groups: ' + error.message)
      } finally {
        this.loadingGroups = false
      }
    },
    buildTree(categories) {
      if (!categories || categories.length === 0) {
        return []
      }

      const categoryMap = new Map()
      const rootNodes = []

      categories.forEach(category => {
        categoryMap.set(category.group_id, {
          ...category,
          children: []
        })
      })

      categories.forEach(category => {
        const node = categoryMap.get(category.group_id)

        if (category.parent_group_id && categoryMap.has(category.parent_group_id)) {
          const parent = categoryMap.get(category.parent_group_id)
          parent.children.push(node)
        } else {
          rootNodes.push(node)
        }
      })

      const sortNodes = nodes => {
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
      this.$emit('update:selected-group-id', groupId)
      this.$emit('group-select', groupId)
    },
    handleGroupChange(group) {
      if (group) {
        this.$emit('group-change', group)
      }
    },
    findGroupInTree(tree, groupId) {
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
    updateGroupName(groupId) {
      const group = this.findGroupInTree(this.marketGroupsTree, groupId)
      if (group) {
        this.$emit('group-change', group)
      } else {
        const flatGroup = this.marketGroups.find(g => g.group_id === groupId)
        if (flatGroup) {
          this.$emit('group-change', flatGroup)
        }
      }
    }
  }
}
</script>

<style scoped>
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #667eea;
}
</style>

