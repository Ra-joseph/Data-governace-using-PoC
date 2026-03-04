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
const {
  datasetAPI, subscriptionAPI, gitAPI, contractAPI, policyAPI,
  policyAuthoringAPI, policyDashboardAPI, policyReportsAPI,
  policyExchangeAPI, domainGovernanceAPI, policyExceptionsAPI, healthCheck
} = await import('../services/api')

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

  // ---- Dataset API additional tests ----

  describe('datasetAPI.update', () => {
    it('should update a dataset', async () => {
      mockPut.mockResolvedValue({ data: { id: 1, name: 'updated' } })
      const result = await datasetAPI.update(1, { name: 'updated' })
      expect(mockPut).toHaveBeenCalledWith('/api/v1/datasets/1', { name: 'updated' })
      expect(result.data.name).toBe('updated')
    })
  })

  describe('datasetAPI.delete', () => {
    it('should delete a dataset', async () => {
      mockDelete.mockResolvedValue({ data: { success: true } })
      const result = await datasetAPI.delete(1)
      expect(mockDelete).toHaveBeenCalledWith('/api/v1/datasets/1')
    })
  })

  describe('datasetAPI.importSchema', () => {
    it('should import schema from postgres', async () => {
      mockPost.mockResolvedValue({ data: { schema: [] } })
      await datasetAPI.importSchema({ table: 'customers' })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/datasets/import-schema', { table: 'customers' })
    })
  })

  describe('datasetAPI.listPostgresTables', () => {
    it('should list postgres tables', async () => {
      mockGet.mockResolvedValue({ data: [{ table_name: 'customers' }] })
      const result = await datasetAPI.listPostgresTables()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/datasets/postgres/tables', { params: { schema: 'public' } })
    })
  })

  // ---- Contract API tests ----

  describe('contractAPI', () => {
    it('should list contracts', async () => {
      mockGet.mockResolvedValue({ data: [{ id: 1, version: '1.0.0' }] })
      const result = await contractAPI.list()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/contracts/', { params: undefined })
    })

    it('should get a contract by ID', async () => {
      mockGet.mockResolvedValue({ data: { id: 1 } })
      await contractAPI.get(1)
      expect(mockGet).toHaveBeenCalledWith('/api/v1/contracts/1')
    })

    it('should validate a contract', async () => {
      const data = { contract_json: { dataset: { name: 'test' } } }
      mockPost.mockResolvedValue({ data: { status: 'passed' } })
      await contractAPI.validate(data)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/contracts/validate', data)
    })

    it('should approve a contract', async () => {
      mockPost.mockResolvedValue({ data: { approved: true } })
      await contractAPI.approve(1, { approved: true })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/contracts/1/approve', { approved: true })
    })

    it('should get contract diff', async () => {
      mockGet.mockResolvedValue({ data: { changes: [] } })
      await contractAPI.diff(1, 2)
      expect(mockGet).toHaveBeenCalledWith('/api/v1/contracts/1/diff/2')
    })
  })

  // ---- Policy API tests ----

  describe('policyAPI', () => {
    it('should list policies', async () => {
      mockGet.mockResolvedValue({ data: {} })
      await policyAPI.list()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policies/')
    })

    it('should get a policy by name', async () => {
      mockGet.mockResolvedValue({ data: { name: 'SD001' } })
      await policyAPI.get('SD001')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policies/SD001')
    })
  })

  // ---- Policy Authoring API tests ----

  describe('policyAuthoringAPI', () => {
    it('should create a policy', async () => {
      const data = { title: 'New Policy' }
      mockPost.mockResolvedValue({ data: { id: 1 } })
      await policyAuthoringAPI.create(data)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policies/authored/', data)
    })

    it('should submit a policy for approval', async () => {
      mockPost.mockResolvedValue({ data: { status: 'pending_approval' } })
      await policyAuthoringAPI.submit(1)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policies/authored/1/submit')
    })

    it('should approve a policy', async () => {
      mockPost.mockResolvedValue({ data: { status: 'approved' } })
      await policyAuthoringAPI.approve(1, { comments: 'LGTM' })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policies/authored/1/approve', { comments: 'LGTM' })
    })

    it('should reject a policy', async () => {
      mockPost.mockResolvedValue({ data: { status: 'rejected' } })
      await policyAuthoringAPI.reject(1, { reason: 'Needs work' })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policies/authored/1/reject', { reason: 'Needs work' })
    })

    it('should get policies by domain', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await policyAuthoringAPI.getByDomain('finance')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policies/authored/domains/finance/policies')
    })

    it('should get policy versions', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await policyAuthoringAPI.getVersions(1)
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policies/authored/1/versions')
    })

    it('should revise a policy', async () => {
      mockPost.mockResolvedValue({ data: { version: 2 } })
      await policyAuthoringAPI.revise(1)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policies/authored/1/revise')
    })

    it('should deprecate a policy', async () => {
      mockPost.mockResolvedValue({ data: { status: 'deprecated' } })
      await policyAuthoringAPI.deprecate(1, { reason: 'Replaced' })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policies/authored/1/deprecate', { reason: 'Replaced' })
    })

    it('should get policy YAML', async () => {
      mockGet.mockResolvedValue({ data: 'yaml: content' })
      await policyAuthoringAPI.getYaml(1)
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policies/authored/1/yaml')
    })
  })

  // ---- Policy Dashboard API tests ----

  describe('policyDashboardAPI', () => {
    it('should get dashboard stats', async () => {
      mockGet.mockResolvedValue({ data: { total: 10 } })
      await policyDashboardAPI.stats()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-dashboard/stats')
    })

    it('should get active policies', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await policyDashboardAPI.activePolicies()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-dashboard/active-policies', { params: {} })
    })

    it('should get active policies with domain filter', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await policyDashboardAPI.activePolicies('finance')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-dashboard/active-policies', { params: { domain: 'finance' } })
    })

    it('should validate combined', async () => {
      const data = { contract_json: {} }
      mockPost.mockResolvedValue({ data: { status: 'passed' } })
      await policyDashboardAPI.validateCombined(data)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policy-dashboard/validate-combined', data)
    })
  })

  // ---- Policy Reports API tests ----

  describe('policyReportsAPI', () => {
    it('should get impact report', async () => {
      mockGet.mockResolvedValue({ data: { affected: 5 } })
      await policyReportsAPI.impact('SD001')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-reports/impact/SD001')
    })

    it('should get compliance report', async () => {
      mockGet.mockResolvedValue({ data: { compliance: 95 } })
      await policyReportsAPI.compliance()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-reports/compliance')
    })

    it('should run bulk validation', async () => {
      mockPost.mockResolvedValue({ data: { validated: 10 } })
      await policyReportsAPI.bulkValidate(true)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policy-reports/bulk-validate?include_authored=true')
    })
  })

  // ---- Policy Exchange API tests ----

  describe('policyExchangeAPI', () => {
    it('should export a policy', async () => {
      mockGet.mockResolvedValue({ data: { yaml: 'content' } })
      await policyExchangeAPI.exportPolicy(1, 'yaml')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-exchange/export/1', { params: { format: 'yaml' } })
    })

    it('should import a bundle', async () => {
      const bundle = { policies: [] }
      mockPost.mockResolvedValue({ data: { imported: 0 } })
      await policyExchangeAPI.importBundle(bundle)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policy-exchange/import', bundle)
    })

    it('should list templates', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await policyExchangeAPI.listTemplates()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-exchange/templates', { params: undefined })
    })
  })

  // ---- Domain Governance API tests ----

  describe('domainGovernanceAPI', () => {
    it('should list domains', async () => {
      mockGet.mockResolvedValue({ data: ['finance', 'hr'] })
      await domainGovernanceAPI.listDomains()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/domain-governance/domains')
    })

    it('should get domain details', async () => {
      mockGet.mockResolvedValue({ data: { name: 'finance' } })
      await domainGovernanceAPI.getDomain('finance')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/domain-governance/domains/finance')
    })

    it('should get governance matrix', async () => {
      mockGet.mockResolvedValue({ data: { matrix: [] } })
      await domainGovernanceAPI.getMatrix()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/domain-governance/matrix')
    })

    it('should get analytics', async () => {
      mockGet.mockResolvedValue({ data: {} })
      await domainGovernanceAPI.getAnalytics()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/domain-governance/analytics')
    })
  })

  // ---- Policy Exceptions API tests ----

  describe('policyExceptionsAPI', () => {
    it('should detect failures', async () => {
      mockPost.mockResolvedValue({ data: { failures: [] } })
      await policyExceptionsAPI.detectFailures({ domain: 'finance' })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policy-exceptions/detect-failures', null, { params: { domain: 'finance' } })
    })

    it('should create an exception', async () => {
      const data = { policy_id: 'SD001', reason: 'Override' }
      mockPost.mockResolvedValue({ data: { id: 1 } })
      await policyExceptionsAPI.createException(data)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policy-exceptions/', data)
    })

    it('should approve an exception', async () => {
      mockPost.mockResolvedValue({ data: { status: 'approved' } })
      await policyExceptionsAPI.approve(1, { comments: 'OK' })
      expect(mockPost).toHaveBeenCalledWith('/api/v1/policy-exceptions/requests/1/approve', { comments: 'OK' })
    })

    it('should check deployment gate', async () => {
      mockGet.mockResolvedValue({ data: { allowed: true } })
      await policyExceptionsAPI.deploymentGate('finance')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/policy-exceptions/deployment-gate/finance')
    })
  })

  // ---- Git API additional tests ----

  describe('gitAPI additional', () => {
    it('should get diff between commits', async () => {
      mockGet.mockResolvedValue({ data: { diff: '' } })
      await gitAPI.diff('abc123', 'def456')
      expect(mockGet).toHaveBeenCalledWith('/api/v1/git/diff', { params: { commit1: 'abc123', commit2: 'def456' } })
    })

    it('should list contracts', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await gitAPI.contracts()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/git/contracts')
    })

    it('should list tags', async () => {
      mockGet.mockResolvedValue({ data: [] })
      await gitAPI.tags()
      expect(mockGet).toHaveBeenCalledWith('/api/v1/git/tags')
    })
  })

  // ---- Subscription API additional tests ----

  describe('subscriptionAPI additional', () => {
    it('should get a subscription by ID', async () => {
      mockGet.mockResolvedValue({ data: { id: 1 } })
      await subscriptionAPI.get(1)
      expect(mockGet).toHaveBeenCalledWith('/api/v1/subscriptions/1')
    })

    it('should create a subscription', async () => {
      const data = { dataset_id: 1, consumer_name: 'Team A' }
      mockPost.mockResolvedValue({ data: { id: 1 } })
      await subscriptionAPI.create(data)
      expect(mockPost).toHaveBeenCalledWith('/api/v1/subscriptions/', data)
    })

    it('should update a subscription', async () => {
      mockPut.mockResolvedValue({ data: { id: 1 } })
      await subscriptionAPI.update(1, { status: 'updated' })
      expect(mockPut).toHaveBeenCalledWith('/api/v1/subscriptions/1', { status: 'updated' })
    })
  })

  // ---- Health check ----

  describe('healthCheck', () => {
    it('should call health endpoint', async () => {
      mockGet.mockResolvedValue({ data: { status: 'ok' } })
      await healthCheck()
      expect(mockGet).toHaveBeenCalledWith('/health')
    })
  })
})
