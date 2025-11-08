import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  regionsApi,
  constellationsApi,
  systemsApi,
  marketsApi,
  universeApi
} from '@/services/api'

// Use vi.hoisted to create mocks that can be accessed both in the mock factory and in tests
const { mockGet } = vi.hoisted(() => {
  const mockGet = vi.fn()
  return { mockGet }
})

vi.mock('axios', () => {
  const mockApiClient = {
    get: mockGet,
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() }
    }
  }

  return {
    default: {
      create: () => mockApiClient
    }
  }
})

describe('API Services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('regionsApi', () => {
    it('should get regions successfully', async () => {
      const mockData = [{ id: 10000001, name: 'Test Region' }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await regionsApi.getRegions()
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/regions')
    })

    it('should handle errors when getting regions', async () => {
      const mockError = {
        response: { data: { error: 'Network error' } },
        message: 'Network error'
      }
      mockGet.mockRejectedValue(mockError)

      await expect(regionsApi.getRegions()).rejects.toThrow('Network error')
    })

    it('should get constellations for a region', async () => {
      const mockData = [{ id: 20000001, name: 'Test Constellation' }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await regionsApi.getConstellations(10000001)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/regions/10000001/constellations')
    })

    it('should get adjacent regions', async () => {
      const mockData = [{ id: 10000002, name: 'Adjacent Region' }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await regionsApi.getAdjacentRegions(10000001)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/regions/10000001/adjacent')
    })
  })

  describe('constellationsApi', () => {
    it('should get constellation by id', async () => {
      const mockData = { id: 20000001, name: 'Test Constellation' }
      mockGet.mockResolvedValue({ data: mockData })

      const result = await constellationsApi.getConstellation(20000001)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/constellations/20000001')
    })

    it('should get systems for a constellation', async () => {
      const mockData = [{ id: 30000001, name: 'Test System' }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await constellationsApi.getSystems(20000001)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/constellations/20000001/systems')
    })
  })

  describe('systemsApi', () => {
    it('should get system by id', async () => {
      const mockData = { id: 30000001, name: 'Test System' }
      mockGet.mockResolvedValue({ data: mockData })

      const result = await systemsApi.getSystem(30000001)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/systems/30000001')
    })

    it('should get connections for a system', async () => {
      const mockData = [{ id: 30000002, name: 'Connected System' }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await systemsApi.getConnections(30000001)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/systems/30000001/connections')
    })
  })

  describe('marketsApi', () => {
    it('should get market categories', async () => {
      const mockData = [{ id: 1, name: 'Category 1' }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await marketsApi.getCategories()
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/markets/categories')
    })

    it('should get orders for a region', async () => {
      const mockData = [{ order_id: 1, type_id: 123 }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await marketsApi.getOrders(10000001, { type_id: 123 })
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/markets/regions/10000001/orders', {
        params: { type_id: 123 }
      })
    })

    it('should search for deals', async () => {
      const mockData = [{ deal_id: 1, profit: 1000000 }]
      mockGet.mockResolvedValue({ data: mockData })

      const result = await marketsApi.searchDeals({ min_profit: 1000000 })
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/markets/deals', {
        params: { min_profit: 1000000 }
      })
    })
  })

  describe('universeApi', () => {
    it('should get type by id', async () => {
      const mockData = { id: 123, name: 'Test Type' }
      mockGet.mockResolvedValue({ data: mockData })

      const result = await universeApi.getType(123)
      expect(result).toEqual(mockData)
      expect(mockGet).toHaveBeenCalledWith('/universe/types/123')
    })
  })
})
