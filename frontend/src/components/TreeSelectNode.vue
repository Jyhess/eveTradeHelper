<template>
  <div class="tree-select-node">
    <div 
      class="tree-select-option" 
      :class="{ 
        'is-selected': isSelected,
        'has-children': hasChildren 
      }"
      :style="indentStyle"
      @click.stop="handleClick"
    >
      <span v-if="hasChildren" class="expand-icon" @click.stop="toggleExpand">
        {{ expanded ? '▼' : '▶' }}
      </span>
      <span v-else class="expand-icon-spacer"></span>
      <span class="option-name">{{ node.name }}</span>
      <span v-if="isSelected" class="check-icon">✓</span>
    </div>
    
    <div v-if="expanded && hasChildren" class="tree-select-children">
      <TreeSelectNode
        v-for="child in filteredChildren"
        :key="child.group_id || child.type_id"
        :node="child"
        :level="level + 1"
        :selected-id="selectedId"
        @node-selected="$emit('node-selected', $event)"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'TreeSelectNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    },
    selectedId: {
      type: [Number, String],
      default: null
    }
  },
  data() {
    return {
      expanded: this.level < 2 // Expanded par défaut pour les 2 premiers niveaux
    }
  },
  computed: {
    hasChildren() {
      if (!this.node.children) return false
      // Filtrer pour ne garder que les groupes (pas les types)
      return this.filteredChildren.length > 0
    },
    filteredChildren() {
      if (!this.node.children) return []
      // Ne garder que les enfants qui sont des groupes (ont un group_id)
      return this.node.children.filter(child => child.group_id && !child.is_type)
    },
    isSelected() {
      return this.node.group_id === this.selectedId
    },
    indentStyle() {
      return {
        paddingLeft: `${this.level * 20 + 10}px`
      }
    }
  },
  methods: {
    toggleExpand() {
      if (this.hasChildren) {
        this.expanded = !this.expanded
      }
    },
    handleClick() {
      // Sélectionner le nœud s'il a un group_id (c'est un groupe)
      if (this.node.group_id) {
        this.$emit('node-selected', this.node)
      }
    }
  }
}
</script>

<style scoped>
.tree-select-node {
  user-select: none;
}

.tree-select-option {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.tree-select-option:hover {
  background-color: #f8f9fa;
}

.tree-select-option.is-selected {
  background-color: #e3f2fd;
  color: #667eea;
  font-weight: 600;
}

.tree-select-option.has-children {
  font-weight: 500;
}

.expand-icon {
  display: inline-block;
  width: 16px;
  text-align: center;
  color: #667eea;
  font-size: 0.75em;
  margin-right: 8px;
  flex-shrink: 0;
}

.expand-icon-spacer {
  display: inline-block;
  width: 16px;
  margin-right: 8px;
  flex-shrink: 0;
}

.option-name {
  flex: 1;
  color: #333;
  font-size: 0.95em;
}

.tree-select-option.is-selected .option-name {
  color: #667eea;
}

.check-icon {
  color: #667eea;
  font-weight: bold;
  margin-left: 8px;
  font-size: 1.1em;
}

.tree-select-children {
  margin-left: 0;
}
</style>
