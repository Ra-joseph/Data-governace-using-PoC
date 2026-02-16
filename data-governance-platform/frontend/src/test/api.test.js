/**
 * Unit tests for API service
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { api } from '../services/api'

// Mock axios
vi.mock('axios')

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getDatasets', () => {
    it('should fetch datasets successfully', async () => {
      const mockDatasets = [
        { id: 1, name: 'test_dataset', status: 'published' }
      ]
      axios.get.mockResolvedValue({ data: mockDatasets })

      const result = await api.getDatasets()

      expect(axios.get).toHaveBeenCalledWith('/datasets/')
      expect(result).toEqual(mockDatasets)
    })

    it('should handle errors when fetching datasets', async () => {
      const mockError = new Error('Network error')
      axios.get.mockRejectedValue(mockError)

      await expect(api.getDatasets()).rejects.toThrow('Network error')
    })
  })

  describe('getDataset', () => {
    it('should fetch a single dataset by ID', async () => {
      const mockDataset = { id: 1, name: 'test_dataset' }
      axios.get.mockResolvedValue({ data: mockDataset })

      const result = await api.getDataset(1)

      expect(axios.get).toHaveBeenCalledWith('/datasets/1')
      expect(result).toEqual(mockDataset)
    })
  })

  describe('createDataset', () => {
    it('should create a new dataset', async () => {
      const newDataset = {
        name: 'new_dataset',
        description: 'Test dataset',
        owner_name: 'Test Owner',
        owner_email: 'test@example.com'
      }
      const mockResponse = { id: 1, ...newDataset }
      axios.post.mockResolvedValue({ data: mockResponse })

      const result = await api.createDataset(newDataset)

      expect(axios.post).toHaveBeenCalledWith('/datasets/', newDataset)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSubscriptions', () => {
    it('should fetch subscriptions', async () => {
      const mockSubscriptions = [
        { id: 1, consumer_name: 'Analytics Team', status: 'pending' }
      ]
      axios.get.mockResolvedValue({ data: mockSubscriptions })

      const result = await api.getSubscriptions()

      expect(axios.get).toHaveBeenCalledWith('/subscriptions/')
      expect(result).toEqual(mockSubscriptions)
    })
  })

  describe('approveSubscription', () => {
    it('should approve a subscription', async () => {
      const approvalData = {
        status: 'approved',
        approved_fields: ['id', 'name']
      }
      const mockResponse = { id: 1, status: 'approved' }
      axios.post.mockResolvedValue({ data: mockResponse })

      const result = await api.approveSubscription(1, approvalData)

      expect(axios.post).toHaveBeenCalledWith('/subscriptions/1/approve', approvalData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getGitHistory', () => {
    it('should fetch git commit history', async () => {
      const mockHistory = {
        history: [
          { commit: 'abc123', message: 'Initial commit' }
        ],
        count: 1
      }
      axios.get.mockResolvedValue({ data: mockHistory })

      const result = await api.getGitHistory()

      expect(axios.get).toHaveBeenCalledWith('/git/history')
      expect(result).toEqual(mockHistory)
    })
  })
})
