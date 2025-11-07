import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5001/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

const extractErrorMessage = (error) => {
  if (error.response?.data?.error) {
    return error.response.data.error
  }
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }
  return error.message || 'Une erreur est survenue'
}

export const regionsApi = {
  async getRegions() {
    try {
      const response = await apiClient.get('/regions')
      return response.data
    } catch (error) {
      console.error('Erreur lors de la récupération des régions:', error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getConstellations(regionId) {
    try {
      const response = await apiClient.get(`/regions/${regionId}/constellations`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération des constellations pour la région ${regionId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getAdjacentRegions(regionId) {
    try {
      const response = await apiClient.get(`/regions/${regionId}/adjacent`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération des régions adjacentes pour la région ${regionId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  }
}

export const constellationsApi = {
  async getConstellation(constellationId) {
    try {
      const response = await apiClient.get(`/constellations/${constellationId}`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération de la constellation ${constellationId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getSystems(constellationId) {
    try {
      const response = await apiClient.get(`/constellations/${constellationId}/systems`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération des systèmes pour la constellation ${constellationId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  }
}

export const systemsApi = {
  async getSystem(systemId) {
    try {
      const response = await apiClient.get(`/systems/${systemId}`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération du système ${systemId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getConnections(systemId) {
    try {
      const response = await apiClient.get(`/systems/${systemId}/connections`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération des connexions pour le système ${systemId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  }
}

export const marketsApi = {
  async getCategories() {
    try {
      const response = await apiClient.get('/markets/categories')
      return response.data
    } catch (error) {
      console.error('Erreur lors de la récupération des catégories de marché:', error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getOrders(regionId, params = {}) {
    try {
      const response = await apiClient.get(`/markets/regions/${regionId}/orders`, { params })
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération des ordres pour la région ${regionId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async searchDeals(params) {
    try {
      const response = await apiClient.get('/markets/deals', { params })
      return response.data
    } catch (error) {
      console.error('Erreur lors de la recherche de bonnes affaires:', error)
      throw new Error(extractErrorMessage(error))
    }
  }
}

export const universeApi = {
  async getType(typeId) {
    try {
      const response = await apiClient.get(`/universe/types/${typeId}`)
      return response.data
    } catch (error) {
      console.error(`Erreur lors de la récupération du type ${typeId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  }
}

export default {
  regions: regionsApi,
  constellations: constellationsApi,
  systems: systemsApi,
  markets: marketsApi,
  universe: universeApi
}
