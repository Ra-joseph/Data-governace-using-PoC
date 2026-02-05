import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  Database,
  Search,
  Filter,
  Shield,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  X
} from 'lucide-react';
import { datasetAPI, subscriptionAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

export function DataCatalogBrowser() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [filteredDatasets, setFilteredDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClassification, setSelectedClassification] = useState('all');
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [showSubscriptionForm, setShowSubscriptionForm] = useState(false);

  const [subscriptionForm, setSubscriptionForm] = useState({
    use_case: '',
    business_justification: '',
    sla_requirements: {
      max_latency_ms: 1000,
      min_availability_pct: 99.9,
      max_staleness_minutes: 60,
    },
    required_fields: [],
    access_duration_days: 365,
  });

  useEffect(() => {
    loadDatasets();
  }, []);

  useEffect(() => {
    filterDatasets();
  }, [datasets, searchTerm, selectedClassification]);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      // Load only published datasets
      const response = await datasetAPI.list({ status: 'published' });
      setDatasets(response.data);
    } catch (error) {
      toast.error('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const filterDatasets = () => {
    let filtered = datasets;

    if (searchTerm) {
      filtered = filtered.filter(
        (ds) =>
          ds.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          ds.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedClassification !== 'all') {
      filtered = filtered.filter((ds) => ds.classification === selectedClassification);
    }

    setFilteredDatasets(filtered);
  };

  const handleSubscribe = (dataset) => {
    setSelectedDataset(dataset);
    setSubscriptionForm({
      ...subscriptionForm,
      required_fields: dataset.schema?.map(col => col.name) || [],
    });
    setShowSubscriptionForm(true);
  };

  const submitSubscription = async () => {
    if (!subscriptionForm.use_case || !subscriptionForm.business_justification) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await subscriptionAPI.create({
        dataset_id: selectedDataset.id,
        consumer_name: user?.name,
        consumer_email: user?.email,
        consumer_organization: user?.organization || 'Demo Organization',
        ...subscriptionForm,
      });

      toast.success('Subscription request submitted successfully!');
      setShowSubscriptionForm(false);
      setSelectedDataset(null);
      setSubscriptionForm({
        use_case: '',
        business_justification: '',
        sla_requirements: {
          max_latency_ms: 1000,
          min_availability_pct: 99.9,
          max_staleness_minutes: 60,
        },
        required_fields: [],
        access_duration_days: 365,
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit subscription');
    }
  };

  const getClassificationColor = (classification) => {
    switch (classification) {
      case 'public':
        return 'text-green-400 bg-green-500/10';
      case 'internal':
        return 'text-blue-400 bg-blue-500/10';
      case 'confidential':
        return 'text-yellow-400 bg-yellow-500/10';
      case 'restricted':
        return 'text-red-400 bg-red-500/10';
      default:
        return 'text-gray-400 bg-gray-500/10';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-white">Loading catalog...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Data Catalog</h1>
          <p className="text-gray-400">
            Browse and subscribe to available datasets
          </p>
        </div>

        {/* Search and Filters */}
        <div className="flex gap-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search datasets..."
              className="w-full pl-12 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <select
            value={selectedClassification}
            onChange={(e) => setSelectedClassification(e.target.value)}
            className="px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
          >
            <option value="all">All Classifications</option>
            <option value="public">Public</option>
            <option value="internal">Internal</option>
            <option value="confidential">Confidential</option>
            <option value="restricted">Restricted</option>
          </select>
        </div>

        {/* Stats Bar */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 mb-8">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-400">
              <Database className="w-4 h-4" />
              <span>
                Showing {filteredDatasets.length} of {datasets.length} datasets
              </span>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-gray-400">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>
                  {datasets.filter(ds => ds.contract?.validation_result?.status === 'passed').length} Compliant
                </span>
              </div>
              <div className="flex items-center gap-2 text-gray-400">
                <Users className="w-4 h-4 text-purple-400" />
                <span>
                  {datasets.reduce((sum, ds) => sum + (ds.subscriber_count || 0), 0)} Active Subscriptions
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Dataset Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDatasets.map((dataset) => (
            <div
              key={dataset.id}
              className="bg-gray-800 rounded-xl border border-gray-700 hover:border-purple-500 transition-all overflow-hidden group"
            >
              <div className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-purple-400 transition-colors">
                      {dataset.name}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold capitalize ${getClassificationColor(
                          dataset.classification
                        )}`}
                      >
                        {dataset.classification}
                      </span>
                      {dataset.contains_pii && (
                        <span className="px-2 py-1 rounded text-xs font-semibold bg-yellow-500/10 text-yellow-400">
                          PII
                        </span>
                      )}
                    </div>
                  </div>
                  <Database className="w-8 h-8 text-gray-600 group-hover:text-purple-500 transition-colors" />
                </div>

                {/* Description */}
                <p className="text-sm text-gray-400 mb-4 line-clamp-3">
                  {dataset.description}
                </p>

                {/* Metadata */}
                <div className="space-y-2 mb-4 text-sm">
                  <div className="flex items-center gap-2 text-gray-500">
                    <Shield className="w-4 h-4" />
                    <span>{dataset.owner_name}</span>
                  </div>
                  {dataset.schema && (
                    <div className="flex items-center gap-2 text-gray-500">
                      <FileText className="w-4 h-4" />
                      <span>{dataset.schema.length} fields</span>
                    </div>
                  )}
                  {dataset.subscriber_count > 0 && (
                    <div className="flex items-center gap-2 text-gray-500">
                      <Users className="w-4 h-4" />
                      <span>{dataset.subscriber_count} subscribers</span>
                    </div>
                  )}
                </div>

                {/* Compliance Status */}
                {dataset.contract?.validation_result && (
                  <div className="mb-4">
                    {dataset.contract.validation_result.status === 'passed' ? (
                      <div className="flex items-center gap-2 text-green-400 text-sm">
                        <CheckCircle className="w-4 h-4" />
                        <span>Policy Compliant</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-yellow-400 text-sm">
                        <AlertCircle className="w-4 h-4" />
                        <span>
                          {dataset.contract.validation_result.failures} violation(s)
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Compliance Tags */}
                {dataset.compliance_tags && dataset.compliance_tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {dataset.compliance_tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Subscribe Button */}
                <button
                  onClick={() => handleSubscribe(dataset)}
                  className="w-full px-4 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all font-medium"
                >
                  Request Access
                </button>
              </div>
            </div>
          ))}
        </div>

        {filteredDatasets.length === 0 && (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-400 mb-2">
              No datasets found
            </h3>
            <p className="text-gray-500">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </div>

      {/* Subscription Form Modal */}
      {showSubscriptionForm && selectedDataset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-xl border border-gray-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  Request Access
                </h2>
                <p className="text-gray-400">
                  {selectedDataset.name}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowSubscriptionForm(false);
                  setSelectedDataset(null);
                }}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Use Case */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Use Case *
                </label>
                <input
                  type="text"
                  value={subscriptionForm.use_case}
                  onChange={(e) =>
                    setSubscriptionForm({ ...subscriptionForm, use_case: e.target.value })
                  }
                  placeholder="e.g., Customer Analytics Dashboard"
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Business Justification */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Business Justification *
                </label>
                <textarea
                  value={subscriptionForm.business_justification}
                  onChange={(e) =>
                    setSubscriptionForm({
                      ...subscriptionForm,
                      business_justification: e.target.value,
                    })
                  }
                  placeholder="Explain why you need access to this dataset..."
                  rows={4}
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* SLA Requirements */}
              <div className="bg-gray-900 rounded-lg p-4 space-y-4">
                <h3 className="text-sm font-semibold text-gray-300">
                  SLA Requirements
                </h3>

                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Max Latency (ms)
                  </label>
                  <input
                    type="number"
                    value={subscriptionForm.sla_requirements.max_latency_ms}
                    onChange={(e) =>
                      setSubscriptionForm({
                        ...subscriptionForm,
                        sla_requirements: {
                          ...subscriptionForm.sla_requirements,
                          max_latency_ms: parseInt(e.target.value),
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Min Availability (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={subscriptionForm.sla_requirements.min_availability_pct}
                    onChange={(e) =>
                      setSubscriptionForm({
                        ...subscriptionForm,
                        sla_requirements: {
                          ...subscriptionForm.sla_requirements,
                          min_availability_pct: parseFloat(e.target.value),
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-xs text-gray-500 mb-1">
                    Max Staleness (minutes)
                  </label>
                  <input
                    type="number"
                    value={subscriptionForm.sla_requirements.max_staleness_minutes}
                    onChange={(e) =>
                      setSubscriptionForm({
                        ...subscriptionForm,
                        sla_requirements: {
                          ...subscriptionForm.sla_requirements,
                          max_staleness_minutes: parseInt(e.target.value),
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              {/* Access Duration */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Access Duration (days)
                </label>
                <input
                  type="number"
                  value={subscriptionForm.access_duration_days}
                  onChange={(e) =>
                    setSubscriptionForm({
                      ...subscriptionForm,
                      access_duration_days: parseInt(e.target.value),
                    })
                  }
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Fields Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Required Fields ({subscriptionForm.required_fields.length} selected)
                </label>
                <div className="bg-gray-900 rounded-lg p-4 max-h-48 overflow-y-auto">
                  {selectedDataset.schema?.map((field) => (
                    <label
                      key={field.name}
                      className="flex items-center gap-2 py-2 text-sm text-gray-300 hover:text-white cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={subscriptionForm.required_fields.includes(field.name)}
                        onChange={(e) => {
                          const fields = e.target.checked
                            ? [...subscriptionForm.required_fields, field.name]
                            : subscriptionForm.required_fields.filter(f => f !== field.name);
                          setSubscriptionForm({
                            ...subscriptionForm,
                            required_fields: fields,
                          });
                        }}
                        className="rounded"
                      />
                      <span>{field.name}</span>
                      <span className="text-xs text-gray-500">({field.type})</span>
                      {field.pii && (
                        <span className="text-xs text-yellow-400">(PII)</span>
                      )}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-800 border-t border-gray-700 p-6 flex justify-end gap-4">
              <button
                onClick={() => {
                  setShowSubscriptionForm(false);
                  setSelectedDataset(null);
                }}
                className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={submitSubscription}
                className="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all"
              >
                Submit Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
