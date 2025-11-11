import axios from 'axios'
import { API_BASE_URL } from '@/constants'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

const extractErrorMessage = error => {
  if (error.response?.data?.error) {
    return error.response.data.error
  }
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }
  return error.message || 'An error occurred'
}

export const regionsApi = {
  async getRegions() {
    try {
      const response = await apiClient.get('/regions')
      return response.data
    } catch (error) {
      console.error('Error retrieving regions:', error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getConstellations(regionId) {
    try {
      const response = await apiClient.get(`/regions/${regionId}/constellations`)
      return response.data
    } catch (error) {
      console.error(`Error retrieving constellations for region ${regionId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getAdjacentRegions(regionId) {
    try {
      const response = await apiClient.get(`/regions/${regionId}/adjacent`)
      return response.data
    } catch (error) {
      console.error(`Error retrieving adjacent regions for region ${regionId}:`, error)
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
      console.error(`Error retrieving constellation ${constellationId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getSystems(constellationId) {
    try {
      const response = await apiClient.get(`/constellations/${constellationId}/systems`)
      return response.data
    } catch (error) {
      console.error(`Error retrieving systems for constellation ${constellationId}:`, error)
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
      console.error(`Error retrieving system ${systemId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getConnections(systemId) {
    try {
      const response = await apiClient.get(`/systems/${systemId}/connections`)
      return response.data
    } catch (error) {
      console.error(`Error retrieving connections for system ${systemId}:`, error)
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
      console.error('Error retrieving market categories:', error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async getOrders(regionId, params = {}) {
    try {
      const response = await apiClient.get(`/markets/regions/${regionId}/orders`, { params })
      return response.data
    } catch (error) {
      console.error(`Error retrieving orders for region ${regionId}:`, error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async searchDeals(params) {
    try {
      const response = await apiClient.get('/markets/deals', { params })
      return response.data
    } catch (error) {
      console.error('Error searching for deals:', error)
      throw new Error(extractErrorMessage(error))
    }
  },

  async searchSystemToSystemDeals(params) {
    try {
      const response = await apiClient.get('/markets/system-to-system-deals', { params })
      return response.data
    } catch (error) {
      console.error('Error searching for system-to-system deals:', error)
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
      console.error(`Error retrieving type ${typeId}:`, error)
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
