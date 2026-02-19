/**
 * Unit tests for API service
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock axios before importing modules that use it
const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()

const mockAxiosInstance = {
  get: mockGet,
  post: mockPost,
  put: mockPut,
  delete: mockDelete,
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
}

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
  },
}))

// Import after mocking
const { datasetAPI, subscriptionAPI, gitAPI } = await import('../services/api')

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('datasetAPI.list', () => {
    it('should fetch datasets successfully', async () => {
      const mockDatasets = [
        { id: 1, name: 'test_dataset', status: 'published' }
      ]
      mockGet.mockResolvedValue({ data: mockDatasets })

      const result = await datasetAPI.list()

      expect(mockGet).toHaveBeenCalledWith('/api/v1/datasets/', { params: undefined })
      expect(result.data).toEqual(mockDatasets)
    })

    it('should handle errors when fetching datasets', async () => {
      const mockError = new Error('Network error')
      mockGet.mockRejectedValue(mockError)

      await expect(datasetAPI.list()).rejects.toThrow('Network error')
    })
  })

  describe('datasetAPI.get', () => {
    it('should fetch a single dataset by ID', async () => {
      const mockDataset = { id: 1, name: 'test_dataset' }
      mockGet.mockResolvedValue({ data: mockDataset })

      const result = await datasetAPI.get(1)

      expect(mockGet).toHaveBeenCalledWith('/api/v1/datasets/1')
      expect(result.data).toEqual(mockDataset)
    })
  })

  describe('datasetAPI.create', () => {
    it('should create a new dataset', async () => {
      const newDataset = {
        name: 'new_dataset',
        description: 'Test dataset',
        owner_name: 'Test Owner',
        owner_email: 'test@example.com'
      }
      const mockResponse = { id: 1, ...newDataset }
      mockPost.mockResolvedValue({ data: mockResponse })

      const result = await datasetAPI.create(newDataset)

      expect(mockPost).toHaveBeenCalledWith('/api/v1/datasets/', newDataset)
      expect(result.data).toEqual(mockResponse)
    })
  })

  describe('subscriptionAPI.list', () => {
    it('should fetch subscriptions', async () => {
      const mockSubscriptions = [
        { id: 1, consumer_name: 'Analytics Team', status: 'pending' }
      ]
      mockGet.mockResolvedValue({ data: mockSubscriptions })

      const result = await subscriptionAPI.list()

      expect(mockGet).toHaveBeenCalledWith('/api/v1/subscriptions/', { params: undefined })
      expect(result.data).toEqual(mockSubscriptions)
    })
  })

  describe('subscriptionAPI.approve', () => {
    it('should approve a subscription', async () => {
      const approvalData = {
        status: 'approved',
        approved_fields: ['id', 'name']
      }
      const mockResponse = { id: 1, status: 'approved' }
      mockPost.mockResolvedValue({ data: mockResponse })

      const result = await subscriptionAPI.approve(1, approvalData)

      expect(mockPost).toHaveBeenCalledWith('/api/v1/subscriptions/1/approve', approvalData)
      expect(result.data).toEqual(mockResponse)
    })
  })

  describe('gitAPI.history', () => {
    it('should fetch git commit history', async () => {
      const mockHistory = {
        history: [
          { commit: 'abc123', message: 'Initial commit' }
        ],
        count: 1
      }
      mockGet.mockResolvedValue({ data: mockHistory })

      const result = await gitAPI.history()

      expect(mockGet).toHaveBeenCalledWith('/api/v1/git/history', { params: { filename: undefined } })
      expect(result.data).toEqual(mockHistory)
    })
  })
})
