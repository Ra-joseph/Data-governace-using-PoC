import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Dataset APIs
export const datasetAPI = {
  list: (params) => api.get('/api/v1/datasets/', { params }),
  get: (id) => api.get(`/api/v1/datasets/${id}`),
  create: (data) => api.post('/api/v1/datasets/', data),
  update: (id, data) => api.put(`/api/v1/datasets/${id}`, data),
  delete: (id) => api.delete(`/api/v1/datasets/${id}`),
  importSchema: (data) => api.post('/api/v1/datasets/import-schema', data),
  listPostgresTables: (schema = 'public') => 
    api.get('/api/v1/datasets/postgres/tables', { params: { schema } }),
};

// Contract APIs
export const contractAPI = {
  list: (params) => api.get('/api/v1/contracts/', { params }),
  get: (id) => api.get(`/api/v1/contracts/${id}`),
  validate: (data) => api.post('/api/v1/contracts/validate', data),
  approve: (id, data) => api.post(`/api/v1/contracts/${id}/approve`, data),
  diff: (id, otherId) => api.get(`/api/v1/contracts/${id}/diff/${otherId}`),
};

// Subscription APIs
export const subscriptionAPI = {
  list: (params) => api.get('/api/v1/subscriptions/', { params }),
  get: (id) => api.get(`/api/v1/subscriptions/${id}`),
  create: (data) => api.post('/api/v1/subscriptions/', data),
  update: (id, data) => api.put(`/api/v1/subscriptions/${id}`, data),
  approve: (id, data) => api.post(`/api/v1/subscriptions/${id}/approve`, data),
};

// Policy APIs
export const policyAPI = {
  list: () => api.get('/api/v1/policies/'),
  get: (name) => api.get(`/api/v1/policies/${name}`),
};

// Git APIs
export const gitAPI = {
  history: (filename) => 
    api.get('/api/v1/git/history', { params: { filename } }),
  diff: (commit1, commit2) => 
    api.get('/api/v1/git/diff', { params: { commit1, commit2 } }),
  contracts: () => api.get('/api/v1/git/contracts'),
  tags: () => api.get('/api/v1/git/tags'),
};

// Health check
export const healthCheck = () => api.get('/health');

export default api;
