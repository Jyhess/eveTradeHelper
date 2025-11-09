<template>
  <div class="tree-select" :class="{ 'is-open': isOpen, 'is-disabled': disabled }">
    <div class="tree-select-trigger" :class="{ 'has-value': selectedNode }" @click="toggleDropdown">
      <span v-if="selectedNode" class="selected-text">{{ selectedNode.name }}</span>
      <span v-else class="placeholder">{{ placeholder }}</span>
      <span class="arrow-icon">{{ isOpen ? '▲' : '▼' }}</span>
    </div>

    <div v-if="isOpen" class="tree-select-dropdown">
      <div v-if="searchable" class="tree-select-search">
        <input
          v-model="searchText"
          type="text"
          placeholder="Search..."
          class="search-input"
          @click.stop
        />
      </div>

      <div class="tree-select-options" @click.stop>
        <TreeSelectNode
          v-for="node in filteredTree"
          :key="node.group_id"
          :node="node"
          :level="0"
          :selected-id="selectedNodeId"
          @node-selected="handleNodeSelect"
        />
        <div v-if="filteredTree.length === 0" class="no-results">No results found</div>
      </div>
    </div>
  </div>
</template>

<script>
import TreeSelectNode from './TreeSelectNode.vue'

export default {
  name: 'TreeSelect',
  components: {
    TreeSelectNode
  },
  props: {
    tree: {
      type: Array,
      default: () => []
    },
    value: {
      type: [Number, String],
      default: null
    },
    placeholder: {
      type: String,
      default: 'Select...'
    },
    disabled: {
      type: Boolean,
      default: false
    },
    searchable: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      isOpen: false,
      searchText: ''
    }
  },
  computed: {
    selectedNodeId() {
      return this.value
    },
    selectedNode() {
      if (!this.value) return null
      return this.findNodeInTree(this.tree, this.value)
    },
    filteredTree() {
      if (!this.searchText.trim()) {
        return this.tree
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

      return filterTree(this.tree)
    }
  },
  mounted() {
    // Close dropdown if clicking outside
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    toggleDropdown() {
      if (!this.disabled) {
        this.isOpen = !this.isOpen
        if (this.isOpen) {
          this.searchText = ''
          // Scroll to selected node after dropdown opens
          this.$nextTick(() => {
            this.scrollToSelectedNode()
          })
        }
      }
    },
    scrollToSelectedNode() {
      if (!this.selectedNodeId) return

      // Find the selected node element
      const selectedElement = this.$el.querySelector(
        `.tree-select-option.is-selected`
      )
      if (selectedElement) {
        const optionsContainer = this.$el.querySelector('.tree-select-options')
        if (optionsContainer) {
          // Scroll to center the selected element
          const containerRect = optionsContainer.getBoundingClientRect()
          const elementRect = selectedElement.getBoundingClientRect()
          const scrollTop =
            optionsContainer.scrollTop +
            elementRect.top -
            containerRect.top -
            containerRect.height / 2 +
            elementRect.height / 2
          optionsContainer.scrollTop = Math.max(0, scrollTop)
        }
      }
    },
    handleNodeSelect(node) {
      this.$emit('input', node.group_id)
      this.$emit('change', node)
      this.isOpen = false
      this.searchText = ''
    },
    findNodeInTree(tree, groupId) {
      for (const node of tree) {
        if (node.group_id === groupId) {
          return node
        }
        if (node.children && node.children.length > 0) {
          const found = this.findNodeInTree(node.children, groupId)
          if (found) return found
        }
      }
      return null
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
.tree-select {
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
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
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

.tree-select.is-open .arrow-icon {
  transform: rotate(180deg);
}

.tree-select.is-disabled .tree-select-trigger {
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
