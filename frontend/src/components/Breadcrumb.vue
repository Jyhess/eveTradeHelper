<template>
  <nav class="breadcrumb" v-if="items.length > 0">
    <ol class="breadcrumb-list">
      <li 
        v-for="(item, index) in items" 
        :key="index"
        class="breadcrumb-item"
        :class="{ 'active': index === items.length - 1 }"
      >
        <router-link v-if="item.path && index < items.length - 1" :to="item.path" class="breadcrumb-link">
          {{ item.label || item.name }}
        </router-link>
        <span v-else class="breadcrumb-current">{{ item.label || item.name }}</span>
        <span v-if="index < items.length - 1" class="breadcrumb-separator">/</span>
      </li>
    </ol>
  </nav>
</template>

<script>
export default {
  name: 'Breadcrumb',
  props: {
    items: {
      type: Array,
      required: true,
      default: () => []
    }
  }
}
</script>

<style scoped>
.breadcrumb {
  margin: 0;
  padding: 0;
  background: transparent;
}

.breadcrumb-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
}

.breadcrumb-link {
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s;
  font-size: 0.95em;
}

.breadcrumb-link:hover {
  color: #5568d3;
  text-decoration: underline;
}

.breadcrumb-current {
  color: #333;
  font-weight: 600;
  font-size: 0.95em;
}

.breadcrumb-separator {
  color: #999;
  margin: 0 10px;
  font-size: 0.9em;
}

.breadcrumb-item.active .breadcrumb-separator {
  display: none;
}
</style>

