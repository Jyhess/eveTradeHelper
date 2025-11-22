<template>
  <div class="form-group">
    <label :for="id">Market Group{{ multiple ? 's' : '' }}:</label>
    <Loader v-if="loadingGroups" message="Loading groups..." size="small" />
    <TreeSelect
      v-else-if="!multiple"
      :id="id"
      :tree="marketGroupsTree"
      :value="selectedGroupId"
      placeholder="Select a group..."
      :disabled="disabled || loadingGroups"
      @input="handleGroupSelect"
      @change="handleGroupChange"
    />
    <div v-else class="multi-select-container">
      <div v-if="selectedGroupIds.length > 0" class="selected-count">
        {{ selectedGroupIds.length }} group{{ selectedGroupIds.length > 1 ? 's' : '' }} selected
      </div>
      <div class="tree-select-multi" :class="{ 'is-open': isOpen, 'is-disabled': disabled || loadingGroups }">
        <div class="tree-select-trigger" @click="toggleDropdown">
          <span v-if="selectedGroupIds.length > 0" class="selected-text">
            {{ getSelectedGroupsText() }}
          </span>
          <span v-else class="placeholder">Select groups...</span>
          <span class="arrow-icon">{{ isOpen ? '▲' : '▼' }}</span>
        </div>
        <div v-if="isOpen" class="tree-select-dropdown">
          <div class="tree-select-search">
            <input
              v-model="searchText"
              type="text"
              placeholder="Search..."
              class="search-input"
              @click.stop
            />
          </div>
          <div class="tree-select-options" @click.stop>
            <TreeSelectMultiNode
              v-for="node in filteredTree"
              :key="node.group_id"
              :node="node"
              :level="0"
              :selected-ids="selectedGroupIds"
              @node-toggle="handleNodeToggle"
            />
            <div v-if="filteredTree.length === 0" class="no-results">No results found</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import TreeSelect from './TreeSelect.vue'
import Loader from './Loader.vue'
import TreeSelectMultiNode from './TreeSelectMultiNode.vue'

export default {
  name: 'MarketGroupSelector',
  components: {
    TreeSelect,
    Loader,
    TreeSelectMultiNode
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
    selectedGroupIds: {
      type: Array,
      default: () => []
    },
    multiple: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:selected-group-id', 'update:selected-group-ids', 'group-select', 'group-change', 'error'],
  data() {
    return {
      marketGroups: [],
      marketGroupsTree: [],
      loadingGroups: false,
      isOpen: false,
      searchText: ''
    }
  },
  computed: {
    filteredTree() {
      if (!this.searchText.trim()) {
        return this.marketGroupsTree
      }

      const searchLower = this.searchText.toLowerCase()
      const filterTree = nodes => {
        const result = []
        for (const node of nodes) {
          const matches = node.name.toLowerCase().includes(searchLower)
          const children = node.children ? filterTree(node.children) : []

          if (matches || children.length > 0) {
            result.push({
              ...node,
              children: children
            })
          }
        }
        return result
      }

      return filterTree(this.marketGroupsTree)
    }
  },
  watch: {
    selectedGroupId(newValue) {
      if (newValue && this.marketGroupsTree.length > 0 && !this.multiple) {
        this.updateGroupName(newValue)
      }
    }
  },
  mounted() {
    this.fetchMarketGroups()
    if (this.multiple) {
      document.addEventListener('click', this.handleClickOutside)
    }
  },
  beforeUnmount() {
    if (this.multiple) {
      document.removeEventListener('click', this.handleClickOutside)
    }
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
    },
    toggleDropdown() {
      if (!this.disabled && !this.loadingGroups) {
        this.isOpen = !this.isOpen
        if (this.isOpen) {
          this.searchText = ''
        }
      }
    },
    handleNodeToggle(groupId) {
      const currentIds = [...this.selectedGroupIds]
      const index = currentIds.indexOf(groupId)
      
      if (index > -1) {
        currentIds.splice(index, 1)
      } else {
        currentIds.push(groupId)
      }
      
      this.$emit('update:selected-group-ids', currentIds)
      
      const group = this.findGroupInTree(this.marketGroupsTree, groupId)
      if (group) {
        this.$emit('group-change', group)
      }
    },
    getSelectedGroupsText() {
      if (this.selectedGroupIds.length === 0) {
        return ''
      }
      if (this.selectedGroupIds.length === 1) {
        const group = this.findGroupInTree(this.marketGroupsTree, this.selectedGroupIds[0])
        return group ? group.name : `Group ${this.selectedGroupIds[0]}`
      }
      return `${this.selectedGroupIds.length} groups selected`
    },
    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.isOpen = false
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

.multi-select-container {
  position: relative;
}

.selected-count {
  font-size: 0.85em;
  color: #667eea;
  margin-bottom: 4px;
  font-weight: 500;
}

.tree-select-multi {
  position: relative;
  width: 100%;
}

.tree-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  min-height: 42px;
}

.tree-select-trigger:hover:not(.is-disabled) {
  border-color: #667eea;
}

.tree-select-trigger.has-value .selected-text {
  color: #333;
  font-weight: 500;
}

.placeholder {
  color: #999;
}

.arrow-icon {
  color: #666;
  font-size: 0.8em;
  transition: transform 0.2s;
}

.tree-select-multi.is-open .arrow-icon {
  transform: rotate(180deg);
}

.tree-select-multi.is-disabled .tree-select-trigger {
  background: #f0f0f0;
  cursor: not-allowed;
  color: #999;
}

.tree-select-dropdown {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 400px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tree-select-search {
  padding: 10px;
  border-bottom: 1px solid #e0e0e0;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 0.95em;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.tree-select-options {
  overflow-y: auto;
  padding: 5px 0;
  max-height: 350px;
}

.no-results {
  padding: 20px;
  text-align: center;
  color: #999;
  font-style: italic;
}
</style>

