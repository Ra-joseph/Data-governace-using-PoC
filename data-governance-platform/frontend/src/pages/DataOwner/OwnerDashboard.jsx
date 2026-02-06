import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Database,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Plus
} from 'lucide-react';
import { datasetAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

export function OwnerDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    withViolations: 0,
    active: 0,
    subscribers: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // Load datasets owned by current user
      const response = await datasetAPI.list({
        owner_email: user?.email,
      });
      const datasetsData = response.data;
      setDatasets(datasetsData);

      // Calculate stats
      const withViolations = datasetsData.filter(
        ds => ds.contract?.validation_result?.status === 'failed'
      ).length;

      const allViolations = datasetsData
        .filter(ds => ds.contract?.validation_result?.violations)
        .flatMap(ds =>
          ds.contract.validation_result.violations.map(v => ({
            ...v,
            dataset: ds.name,
            datasetId: ds.id,
          }))
        );

      setViolations(allViolations);
      setStats({
        total: datasetsData.length,
        withViolations,
        active: datasetsData.filter(ds => ds.status === 'published').length,
        subscribers: datasetsData.reduce((sum, ds) => sum + (ds.subscriber_count || 0), 0),
      });
    } catch (error) {
      toast.error('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-400 bg-red-500/10';
      case 'warning':
        return 'text-yellow-400 bg-yellow-500/10';
      default:
        return 'text-blue-400 bg-blue-500/10';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'published':
        return 'text-green-400 bg-green-500/10';
      case 'draft':
        return 'text-gray-400 bg-gray-500/10';
      default:
        return 'text-yellow-400 bg-yellow-500/10';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Data Owner Dashboard
            </h1>
            <p className="text-gray-400">
              Manage your datasets and track governance compliance
            </p>
          </div>

          <button
            onClick={() => navigate('/owner/register')}
            className="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Register Dataset
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <Database className="w-8 h-8 text-blue-400" />
              <span className="text-3xl font-bold text-white">{stats.total}</span>
            </div>
            <p className="text-gray-400 text-sm">Total Datasets</p>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <AlertTriangle className="w-8 h-8 text-red-400" />
              <span className="text-3xl font-bold text-white">{stats.withViolations}</span>
            </div>
            <p className="text-gray-400 text-sm">With Violations</p>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <span className="text-3xl font-bold text-white">{stats.active}</span>
            </div>
            <p className="text-gray-400 text-sm">Active Datasets</p>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <Users className="w-8 h-8 text-purple-400" />
              <span className="text-3xl font-bold text-white">{stats.subscribers}</span>
            </div>
            <p className="text-gray-400 text-sm">Total Subscribers</p>
          </div>
        </div>

        {/* Violations Alert */}
        {violations.length > 0 && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-8">
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-400 mb-2">
                  Active Policy Violations
                </h3>
                <p className="text-gray-300 mb-4">
                  You have {violations.length} policy violation(s) across your datasets that need attention.
                </p>

                <div className="space-y-3">
                  {violations.slice(0, 5).map((violation, index) => (
                    <div
                      key={index}
                      className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-all cursor-pointer"
                      onClick={() => navigate(`/owner/datasets/${violation.datasetId}`)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <span className="text-xs text-gray-500">Dataset:</span>
                          <span className="text-white font-medium ml-2">
                            {violation.dataset}
                          </span>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${getSeverityColor(
                            violation.type
                          )}`}
                        >
                          {violation.type?.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300 mb-2">{violation.policy}</p>
                      <p className="text-sm text-gray-400">{violation.message}</p>
                      {violation.remediation && (
                        <div className="mt-3 pt-3 border-t border-gray-700">
                          <p className="text-xs text-gray-500 mb-1">How to fix:</p>
                          <p className="text-xs text-gray-400">{violation.remediation}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {violations.length > 5 && (
                  <button
                    onClick={() => navigate('/owner/violations')}
                    className="mt-4 text-sm text-red-400 hover:text-red-300"
                  >
                    View all {violations.length} violations →
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Datasets List */}
        <div className="bg-gray-800 rounded-xl border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">Your Datasets</h2>
          </div>

          <div className="divide-y divide-gray-700">
            {datasets.length === 0 ? (
              <div className="p-12 text-center">
                <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-400 mb-2">
                  No datasets yet
                </h3>
                <p className="text-gray-500 mb-6">
                  Start by registering your first dataset
                </p>
                <button
                  onClick={() => navigate('/owner/register')}
                  className="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all"
                >
                  Register Dataset
                </button>
              </div>
            ) : (
              datasets.map((dataset) => (
                <div
                  key={dataset.id}
                  className="p-6 hover:bg-gray-750 transition-all cursor-pointer"
                  onClick={() => navigate(`/owner/datasets/${dataset.id}`)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {dataset.name}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                            dataset.status
                          )}`}
                        >
                          {dataset.status}
                        </span>
                        {dataset.contract?.validation_result?.status === 'failed' && (
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400">
                            Has Violations
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm mb-3">
                        {dataset.description}
                      </p>

                      <div className="flex items-center gap-6 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4" />
                          <span>{dataset.source_system}</span>
                        </div>
                        {dataset.classification && (
                          <div className="flex items-center gap-2">
                            <span className="capitalize">{dataset.classification}</span>
                          </div>
                        )}
                        {dataset.subscriber_count > 0 && (
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            <span>{dataset.subscriber_count} subscribers</span>
                          </div>
                        )}
                        {dataset.created_at && (
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            <span>{new Date(dataset.created_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {dataset.contract?.validation_result && (
                      <div className="text-right">
                        {dataset.contract.validation_result.status === 'passed' ? (
                          <div className="flex items-center gap-2 text-green-400">
                            <CheckCircle className="w-5 h-5" />
                            <span className="text-sm font-medium">Compliant</span>
                          </div>
                        ) : (
                          <div className="text-red-400">
                            <div className="text-2xl font-bold">
                              {dataset.contract.validation_result.failures || 0}
                            </div>
                            <div className="text-xs">violations</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
