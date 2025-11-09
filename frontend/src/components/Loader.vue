<template>
  <div class="loader" :class="loaderClasses">
    <div class="loader-spinner" :class="spinnerClasses"></div>
    <p v-if="message" class="loader-text">{{ message }}</p>
  </div>
</template>

<script>
export default {
  name: 'Loader',
  props: {
    message: {
      type: String,
      default: 'Loading...'
    },
    variant: {
      type: String,
      default: 'inline',
      validator: value => ['inline', 'overlay'].includes(value)
    },
    size: {
      type: String,
      default: 'normal',
      validator: value => ['small', 'normal'].includes(value)
    }
  },
  computed: {
    loaderClasses() {
      return {
        [`loader-${this.variant}`]: true,
        [`loader-${this.size}`]: this.size !== 'normal'
      }
    },
    spinnerClasses() {
      return {
        [`loader-spinner-${this.size}`]: true
      }
    }
  }
}
</script>

<style scoped>
.loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loader-inline {
  padding: 20px;
}

.loader-overlay {
  padding: 60px 20px;
  margin-top: 30px;
  background: #f8f9fa;
  border-radius: 8px;
  min-height: 200px;
}

.loader-small {
  padding: 10px;
  flex-direction: row;
  gap: 10px;
  justify-content: flex-start;
}

.loader-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e0e0e0;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.loader-spinner-small {
  width: 20px;
  height: 20px;
  border-width: 2px;
  margin-bottom: 0;
}

.loader-small .loader-spinner {
  margin-bottom: 0;
}

.loader-text {
  color: #667eea;
  font-size: 1.1em;
  font-weight: 500;
  margin: 0;
}

.loader-small .loader-text {
  font-size: 0.9em;
  font-style: italic;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>

