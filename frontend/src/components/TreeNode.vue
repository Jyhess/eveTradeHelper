<template>
  <div class="tree-node-item">
    <div class="tree-node-header" :style="indentStyle" :class="{ 'has-children': hasChildren, 'expanded': expanded }">
      <span v-if="hasChildren" class="expand-icon" @click.stop="toggleExpand">
        {{ expanded ? '▼' : '▶' }}
      </span>
      <span v-else class="expand-icon-spacer"></span>
      <span class="node-name" :class="{ 'type-node': isType }" @click="selectNode">
        <span v-if="isType && typeDetailsForNode && typeDetailsForNode.name">{{ typeDetailsForNode.name }}</span>
        <span v-else>{{ node.name }}</span>
      </span>
      <span class="node-badge">{{ badgeValue }}</span>
      <router-link 
        v-if="!isType && regionId" 
        :to="dealsLink" 
        class="deals-link"
        @click.stop
        title="Trouver les bonnes affaires dans ce groupe"
      >
        💰
      </router-link>
    </div>
    <div v-if="expanded && hasChildren" class="tree-children">
      <TreeNode v-for="child in node.children" :key="child.is_type ? `type_${child.type_id}` : child.group_id"
        :node="child" :level="level + 1" :type-details="typeDetails" :region-id="regionId" @node-selected="$emit('node-selected', $event)" />
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
    },
    typeDetails: {
      type: Object,
      default: () => ({})
    },
    regionId: {
      type: [String, Number],
      default: null
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
    isType() {
      return this.node.is_type === true
    },
    indentStyle() {
      return {
        paddingLeft: `${this.level * 30 + 10}px`
      }
    },
    badgeValue() {
      // Les types n'ont pas de badge
      if (this.isType) {
        return ''
      }
      // Si la catégorie a des enfants, afficher le nombre d'enfants
      // Sinon, afficher le nombre de types d'items
      if (this.hasChildren) {
        return this.node.children.length
      }
      return this.node.types?.length || 0
    },
    typeDetailsForNode() {
      if (this.isType && this.node.type_id && this.typeDetails) {
        return this.typeDetails[this.node.type_id] || null
      }
      return null
    },
    dealsLink() {
      if (!this.regionId || !this.node.group_id) {
        return '/deals'
      }
      return {
        path: '/deals',
        query: {
          region_id: this.regionId,
          group_id: this.node.group_id
        }
      }
    }
  },
  methods: {
    toggleExpand() {
      if (this.hasChildren) {
        this.expanded = !this.expanded
      }
    },
    selectNode() {
      // Émettre l'événement pour sélectionner ce nœud (catégorie ou type d'item)
      if (this.isType) {
        this.$emit('node-selected', {
          type_id: this.node.type_id,
          name: this.node.name,
          is_type: true
        })
      } else {
        this.$emit('node-selected', {
          group_id: this.node.group_id,
          name: this.node.name,
          description: this.node.description,
          types: this.node.types || []
        })
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

.node-name.type-node {
  color: #4299e1;
  font-style: italic;
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

.deals-link {
  margin-left: 10px;
  padding: 4px 8px;
  background: #667eea;
  color: white;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9em;
  transition: background 0.2s;
  display: inline-block;
}

.deals-link:hover {
  background: #5568d3;
}

.tree-children {
  margin-top: 5px;
  margin-left: 0;
}
</style>
