/**
 * Unit tests for Zustand stores
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { act } from '@testing-library/react'
import {
  useDatasetStore,
  useContractStore,
  useSubscriptionStore,
  usePolicyStore,
  useGitStore,
} from '../stores/index'

describe('useDatasetStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useDatasetStore.setState({
      datasets: [],
      currentDataset: null,
      loading: false,
      error: null,
    })
  })

  it('should have correct initial state', () => {
    const state = useDatasetStore.getState()
    expect(state.datasets).toEqual([])
    expect(state.currentDataset).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('should set datasets', () => {
    const datasets = [{ id: 1, name: 'ds1' }, { id: 2, name: 'ds2' }]
    act(() => {
      useDatasetStore.getState().setDatasets(datasets)
    })
    expect(useDatasetStore.getState().datasets).toEqual(datasets)
  })

  it('should add a dataset', () => {
    const initial = { id: 1, name: 'ds1' }
    const added = { id: 2, name: 'ds2' }
    act(() => {
      useDatasetStore.getState().setDatasets([initial])
      useDatasetStore.getState().addDataset(added)
    })
    expect(useDatasetStore.getState().datasets).toHaveLength(2)
    expect(useDatasetStore.getState().datasets[1]).toEqual(added)
  })

  it('should update a dataset by ID', () => {
    act(() => {
      useDatasetStore.getState().setDatasets([
        { id: 1, name: 'old_name', status: 'draft' },
      ])
      useDatasetStore.getState().updateDataset(1, { name: 'new_name' })
    })
    expect(useDatasetStore.getState().datasets[0].name).toBe('new_name')
    expect(useDatasetStore.getState().datasets[0].status).toBe('draft')
  })

  it('should not change datasets when updating non-existent ID', () => {
    act(() => {
      useDatasetStore.getState().setDatasets([{ id: 1, name: 'ds1' }])
      useDatasetStore.getState().updateDataset(999, { name: 'nope' })
    })
    expect(useDatasetStore.getState().datasets).toHaveLength(1)
    expect(useDatasetStore.getState().datasets[0].name).toBe('ds1')
  })

  it('should remove a dataset by ID', () => {
    act(() => {
      useDatasetStore.getState().setDatasets([
        { id: 1, name: 'ds1' },
        { id: 2, name: 'ds2' },
      ])
      useDatasetStore.getState().removeDataset(1)
    })
    expect(useDatasetStore.getState().datasets).toHaveLength(1)
    expect(useDatasetStore.getState().datasets[0].id).toBe(2)
  })

  it('should not change datasets when removing non-existent ID', () => {
    act(() => {
      useDatasetStore.getState().setDatasets([{ id: 1, name: 'ds1' }])
      useDatasetStore.getState().removeDataset(999)
    })
    expect(useDatasetStore.getState().datasets).toHaveLength(1)
  })

  it('should set loading state', () => {
    act(() => {
      useDatasetStore.getState().setLoading(true)
    })
    expect(useDatasetStore.getState().loading).toBe(true)

    act(() => {
      useDatasetStore.getState().setLoading(false)
    })
    expect(useDatasetStore.getState().loading).toBe(false)
  })

  it('should set error state', () => {
    act(() => {
      useDatasetStore.getState().setError('Something went wrong')
    })
    expect(useDatasetStore.getState().error).toBe('Something went wrong')

    act(() => {
      useDatasetStore.getState().setError(null)
    })
    expect(useDatasetStore.getState().error).toBeNull()
  })

  it('should set current dataset', () => {
    const dataset = { id: 1, name: 'selected' }
    act(() => {
      useDatasetStore.getState().setCurrentDataset(dataset)
    })
    expect(useDatasetStore.getState().currentDataset).toEqual(dataset)
  })
})

describe('useContractStore', () => {
  beforeEach(() => {
    useContractStore.setState({
      contracts: [],
      currentContract: null,
      validationResult: null,
      loading: false,
      error: null,
    })
  })

  it('should have correct initial state', () => {
    const state = useContractStore.getState()
    expect(state.contracts).toEqual([])
    expect(state.currentContract).toBeNull()
    expect(state.validationResult).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('should set contracts', () => {
    const contracts = [{ id: 1, version: '1.0.0' }]
    act(() => {
      useContractStore.getState().setContracts(contracts)
    })
    expect(useContractStore.getState().contracts).toEqual(contracts)
  })

  it('should set validation result', () => {
    const result = { status: 'passed', violations: [] }
    act(() => {
      useContractStore.getState().setValidationResult(result)
    })
    expect(useContractStore.getState().validationResult).toEqual(result)
  })

  it('should set current contract', () => {
    const contract = { id: 1, version: '1.0.0' }
    act(() => {
      useContractStore.getState().setCurrentContract(contract)
    })
    expect(useContractStore.getState().currentContract).toEqual(contract)
  })

  it('should set loading and error states', () => {
    act(() => {
      useContractStore.getState().setLoading(true)
      useContractStore.getState().setError('Contract error')
    })
    expect(useContractStore.getState().loading).toBe(true)
    expect(useContractStore.getState().error).toBe('Contract error')
  })
})

describe('useSubscriptionStore', () => {
  beforeEach(() => {
    useSubscriptionStore.setState({
      subscriptions: [],
      currentSubscription: null,
      loading: false,
      error: null,
    })
  })

  it('should have correct initial state', () => {
    const state = useSubscriptionStore.getState()
    expect(state.subscriptions).toEqual([])
    expect(state.currentSubscription).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('should set subscriptions', () => {
    const subs = [{ id: 1, status: 'pending' }]
    act(() => {
      useSubscriptionStore.getState().setSubscriptions(subs)
    })
    expect(useSubscriptionStore.getState().subscriptions).toEqual(subs)
  })

  it('should approve a subscription by ID', () => {
    act(() => {
      useSubscriptionStore.getState().setSubscriptions([
        { id: 1, status: 'pending' },
        { id: 2, status: 'pending' },
      ])
      useSubscriptionStore.getState().approveSubscription(1)
    })
    expect(useSubscriptionStore.getState().subscriptions[0].status).toBe('approved')
    expect(useSubscriptionStore.getState().subscriptions[1].status).toBe('pending')
  })

  it('should not change state when approving non-existent ID', () => {
    act(() => {
      useSubscriptionStore.getState().setSubscriptions([{ id: 1, status: 'pending' }])
      useSubscriptionStore.getState().approveSubscription(999)
    })
    expect(useSubscriptionStore.getState().subscriptions[0].status).toBe('pending')
  })

  it('should reject a subscription by ID', () => {
    act(() => {
      useSubscriptionStore.getState().setSubscriptions([
        { id: 1, status: 'pending' },
      ])
      useSubscriptionStore.getState().rejectSubscription(1)
    })
    expect(useSubscriptionStore.getState().subscriptions[0].status).toBe('rejected')
  })

  it('should set current subscription', () => {
    const sub = { id: 1, consumer_name: 'Team A' }
    act(() => {
      useSubscriptionStore.getState().setCurrentSubscription(sub)
    })
    expect(useSubscriptionStore.getState().currentSubscription).toEqual(sub)
  })
})

describe('usePolicyStore', () => {
  beforeEach(() => {
    usePolicyStore.setState({
      policies: {},
      loading: false,
      error: null,
    })
  })

  it('should have correct initial state', () => {
    const state = usePolicyStore.getState()
    expect(state.policies).toEqual({})
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('should set policies', () => {
    const policies = {
      sensitive_data: [{ id: 'SD001', name: 'pii_encryption' }],
      quality: [{ id: 'DQ001', name: 'completeness' }],
    }
    act(() => {
      usePolicyStore.getState().setPolicies(policies)
    })
    expect(usePolicyStore.getState().policies).toEqual(policies)
  })

  it('should set loading and error', () => {
    act(() => {
      usePolicyStore.getState().setLoading(true)
      usePolicyStore.getState().setError('Policy load error')
    })
    expect(usePolicyStore.getState().loading).toBe(true)
    expect(usePolicyStore.getState().error).toBe('Policy load error')
  })
})

describe('useGitStore', () => {
  beforeEach(() => {
    useGitStore.setState({
      history: [],
      contracts: [],
      currentDiff: null,
      loading: false,
      error: null,
    })
  })

  it('should have correct initial state', () => {
    const state = useGitStore.getState()
    expect(state.history).toEqual([])
    expect(state.contracts).toEqual([])
    expect(state.currentDiff).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('should set history', () => {
    const history = [{ commit: 'abc123', message: 'Initial commit' }]
    act(() => {
      useGitStore.getState().setHistory(history)
    })
    expect(useGitStore.getState().history).toEqual(history)
  })

  it('should set contracts', () => {
    const contracts = [{ filename: 'test_v1.0.0.yaml', size: 1024 }]
    act(() => {
      useGitStore.getState().setContracts(contracts)
    })
    expect(useGitStore.getState().contracts).toEqual(contracts)
  })

  it('should set current diff', () => {
    const diff = { lines_added: 5, lines_removed: 2, content: '+new\n-old' }
    act(() => {
      useGitStore.getState().setCurrentDiff(diff)
    })
    expect(useGitStore.getState().currentDiff).toEqual(diff)
  })

  it('should set loading and error', () => {
    act(() => {
      useGitStore.getState().setLoading(true)
      useGitStore.getState().setError('Git error')
    })
    expect(useGitStore.getState().loading).toBe(true)
    expect(useGitStore.getState().error).toBe('Git error')
  })
})
