import { create } from 'zustand';

export const useDatasetStore = create((set) => ({
  datasets: [],
  currentDataset: null,
  loading: false,
  error: null,
  
  setDatasets: (datasets) => set({ datasets }),
  setCurrentDataset: (dataset) => set({ currentDataset: dataset }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  addDataset: (dataset) => set((state) => ({ 
    datasets: [...state.datasets, dataset] 
  })),
  
  updateDataset: (id, updates) => set((state) => ({
    datasets: state.datasets.map((d) => 
      d.id === id ? { ...d, ...updates } : d
    ),
  })),
  
  removeDataset: (id) => set((state) => ({
    datasets: state.datasets.filter((d) => d.id !== id),
  })),
}));

export const useContractStore = create((set) => ({
  contracts: [],
  currentContract: null,
  validationResult: null,
  loading: false,
  error: null,
  
  setContracts: (contracts) => set({ contracts }),
  setCurrentContract: (contract) => set({ currentContract: contract }),
  setValidationResult: (result) => set({ validationResult: result }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

export const useSubscriptionStore = create((set) => ({
  subscriptions: [],
  currentSubscription: null,
  loading: false,
  error: null,
  
  setSubscriptions: (subscriptions) => set({ subscriptions }),
  setCurrentSubscription: (subscription) => set({ currentSubscription: subscription }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  approveSubscription: (id) => set((state) => ({
    subscriptions: state.subscriptions.map((s) =>
      s.id === id ? { ...s, status: 'approved' } : s
    ),
  })),
  
  rejectSubscription: (id) => set((state) => ({
    subscriptions: state.subscriptions.map((s) =>
      s.id === id ? { ...s, status: 'rejected' } : s
    ),
  })),
}));

export const usePolicyStore = create((set) => ({
  policies: {},
  loading: false,
  error: null,
  
  setPolicies: (policies) => set({ policies }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

export const useGitStore = create((set) => ({
  history: [],
  contracts: [],
  currentDiff: null,
  loading: false,
  error: null,
  
  setHistory: (history) => set({ history }),
  setContracts: (contracts) => set({ contracts }),
  setCurrentDiff: (diff) => set({ currentDiff: diff }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
