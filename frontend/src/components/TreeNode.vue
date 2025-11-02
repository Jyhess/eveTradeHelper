<template>
  <div class="tree-node-item">
    <div class="tree-node-header" :style="indentStyle" :class="{ 'has-children': hasChildren, 'expanded': expanded }"
      @click="toggleExpand">
      <span v-if="hasChildren" class="expand-icon">
        {{ expanded ? '▼' : '▶' }}
      </span>
      <span v-else class="expand-icon-spacer"></span>
      <span class="node-name">{{ node.name }}</span>
      <span class="node-badge">{{ badgeValue }}</span>
    </div>
    <div v-if="expanded && hasChildren" class="tree-children">
      <TreeNode v-for="child in node.children" :key="child.group_id" :node="child" :level="level + 1" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'TreeNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      expanded: false // Par défaut, tous les nœuds sont repliés
    }
  },
  computed: {
    hasChildren() {
      return this.node.children && this.node.children.length > 0
    },
    indentStyle() {
      return {
        paddingLeft: `${this.level * 30 + 10}px`
      }
    },
    badgeValue() {
      // Si la catégorie a des enfants, afficher le nombre d'enfants
      // Sinon, afficher le nombre de types d'items
      if (this.hasChildren) {
        return this.node.children.length
      }
      return this.node.types?.length || 0
    }
  },
  methods: {
    toggleExpand() {
      if (this.hasChildren) {
        this.expanded = !this.expanded
      }
    }
  }
}
</script>

<style scoped>
.tree-node-item {
  margin-bottom: 2px;
}

.tree-node-header {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  user-select: none;
}

.tree-node-header:hover {
  background: #f8f9fa;
  border-color: #48bb78;
}

.tree-node-header.has-children {
  font-weight: 600;
}

.tree-node-header.expanded {
  background: #f0f9ff;
  border-color: #4299e1;
}

.expand-icon {
  display: inline-block;
  width: 20px;
  text-align: center;
  color: #667eea;
  font-size: 0.85em;
  margin-right: 8px;
}

.expand-icon-spacer {
  display: inline-block;
  width: 20px;
  margin-right: 8px;
}

.node-name {
  flex: 1;
  color: #333;
  font-size: 1em;
}

.node-badge {
  background: #48bb78;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
  margin-left: 10px;
}

.tree-children {
  margin-top: 5px;
  margin-left: 0;
}
</style>
