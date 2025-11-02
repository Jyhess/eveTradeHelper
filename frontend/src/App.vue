<template>
  <div id="app">
    <div class="container">
      <h1>{{ title }}</h1>
      <p class="subtitle">Frontend Vue.js + Backend Python</p>
      <div class="card">
        <button @click="fetchHello" class="btn">Appeler le Backend</button>
        <div v-if="message" class="message">{{ message }}</div>
        <div v-if="loading" class="loading">Chargement...</div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      title: 'Hello World',
      message: '',
      loading: false
    }
  },
  methods: {
    async fetchHello() {
      this.loading = true
      this.message = ''
      try {
        const response = await axios.get('http://localhost:5000/api/hello')
        this.message = response.data.message
      } catch (error) {
        this.message = 'Erreur: ' + error.message
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

body {
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  font-size: 3em;
  color: white;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2em;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 30px;
  font-size: 1.1em;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn:active {
  transform: translateY(0);
}

.message {
  margin-top: 20px;
  padding: 15px;
  background: #f0f0f0;
  border-radius: 6px;
  color: #333;
  font-size: 1.1em;
}

.loading {
  margin-top: 20px;
  color: #667eea;
  font-style: italic;
}
</style>

