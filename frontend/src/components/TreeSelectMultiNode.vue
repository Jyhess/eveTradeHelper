<template>
  <div class="tree-select-node">
    <div
      class="tree-select-option"
      :class="{
        'is-selected': isSelected,
        'has-children': hasChildren
      }"
      :style="indentStyle"
    >
      <span v-if="hasChildren" class="expand-icon" @click.stop="toggleExpand">
        {{ expanded ? '▼' : '▶' }}
      </span>
      <span v-else class="expand-icon-spacer"></span>
      <label class="checkbox-label">
        <input
          type="checkbox"
          :checked="isSelected"
          @change="handleToggle"
          @click.stop
        />
        <span class="option-name">{{ node.name }}</span>
      </label>
    </div>

    <div v-if="expanded && hasChildren" class="tree-select-children">
      <TreeSelectMultiNode
        v-for="child in filteredChildren"
        :key="child.group_id"
        :node="child"
        :level="level + 1"
        :selected-ids="selectedIds"
        @node-toggle="$emit('node-toggle', $event)"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'TreeSelectMultiNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    },
    selectedIds: {
      type: Array,
      default: () => []
    }
  },
  emits: ['node-toggle'],
  data() {
    return {
      expanded: false
    }
  },
  computed: {
    hasChildren() {
      if (!this.node.children) return false
      return this.filteredChildren.length > 0
    },
    filteredChildren() {
      if (!this.node.children) return []
      return this.node.children.filter(child => child.group_id && !child.is_type)
    },
    isSelected() {
      return this.selectedIds.includes(this.node.group_id)
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
    handleToggle() {
      if (this.node.group_id) {
        this.$emit('node-toggle', this.node.group_id)
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
  transition: background-color 0.2s;
}

.tree-select-option:hover {
  background-color: #f8f9fa;
}

.tree-select-option.is-selected {
  background-color: #e3f2fd;
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
  cursor: pointer;
}

.expand-icon-spacer {
  display: inline-block;
  width: 16px;
  margin-right: 8px;
  flex-shrink: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  flex: 1;
  cursor: pointer;
  gap: 8px;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #667eea;
}

.option-name {
  flex: 1;
  color: #333;
  font-size: 0.95em;
}

.tree-select-option.is-selected .option-name {
  color: #667eea;
  font-weight: 600;
}

.tree-select-children {
  margin-left: 0;
}
</style>

