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
  margin-bottom: 20px;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
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
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  transition: color 0.2s;
  font-size: 0.95em;
}

.breadcrumb-link:hover {
  color: white;
  text-decoration: underline;
}

.breadcrumb-current {
  color: white;
  font-weight: 600;
  font-size: 0.95em;
}

.breadcrumb-separator {
  color: rgba(255, 255, 255, 0.6);
  margin: 0 10px;
  font-size: 0.9em;
}

.breadcrumb-item.active .breadcrumb-separator {
  display: none;
}
</style>

