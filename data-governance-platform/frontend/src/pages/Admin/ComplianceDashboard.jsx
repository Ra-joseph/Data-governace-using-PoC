import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Database,
  Users,
  Shield,
  Activity,
  BarChart3
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { datasetAPI, subscriptionAPI } from '../../services/api';

export function ComplianceDashboard() {
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [metrics, setMetrics] = useState({
    totalDatasets: 0,
    compliantDatasets: 0,
    totalViolations: 0,
    criticalViolations: 0,
    activeSubscriptions: 0,
    pendingApprovals: 0,
  });

  const [violationTrends, setViolationTrends] = useState([]);
  const [violationsByType, setViolationsByType] = useState([]);
  const [violationsByPolicy, setViolationsByPolicy] = useState([]);
  const [complianceByClassification, setComplianceByClassification] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load datasets
      const datasetsResponse = await datasetAPI.list({});
      const datasetsData = datasetsResponse.data;
      setDatasets(datasetsData);

      // Load subscriptions
      const subscriptionsResponse = await subscriptionAPI.list({});
      const subscriptionsData = subscriptionsResponse.data;
      setSubscriptions(subscriptionsData);

      // Calculate metrics
      const compliant = datasetsData.filter(
        (ds) => ds.contract?.validation_result?.status === 'passed'
      ).length;

      const allViolations = datasetsData
        .filter((ds) => ds.contract?.validation_result?.violations)
        .flatMap((ds) => ds.contract.validation_result.violations);

      const critical = allViolations.filter(
        (v) => v.type?.toLowerCase() === 'critical'
      ).length;

      setMetrics({
        totalDatasets: datasetsData.length,
        compliantDatasets: compliant,
        totalViolations: allViolations.length,
        criticalViolations: critical,
        activeSubscriptions: subscriptionsData.filter((s) => s.status === 'approved').length,
        pendingApprovals: subscriptionsData.filter((s) => s.status === 'pending').length,
      });

      // Process violation trends (mock data for demo)
      const trends = generateViolationTrends(datasetsData);
      setViolationTrends(trends);

      // Violations by type
      const byType = processViolationsByType(allViolations);
      setViolationsByType(byType);

      // Violations by policy
      const byPolicy = processViolationsByPolicy(allViolations);
      setViolationsByPolicy(byPolicy);

      // Compliance by classification
      const byClassification = processComplianceByClassification(datasetsData);
      setComplianceByClassification(byClassification);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const generateViolationTrends = (datasets) => {
    // Mock trend data (in production, this would come from historical data)
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    return months.map((month, index) => ({
      month,
      violations: Math.max(0, 50 - index * 5 + Math.floor(Math.random() * 10)),
      critical: Math.max(0, 15 - index * 2 + Math.floor(Math.random() * 3)),
    }));
  };

  const processViolationsByType = (violations) => {
    const counts = {
      critical: 0,
      warning: 0,
      info: 0,
    };

    violations.forEach((v) => {
      const type = v.type?.toLowerCase() || 'info';
      if (counts[type] !== undefined) {
        counts[type]++;
      }
    });

    return [
      { name: 'Critical', value: counts.critical, color: '#ef4444' },
      { name: 'Warning', value: counts.warning, color: '#f59e0b' },
      { name: 'Info', value: counts.info, color: '#3b82f6' },
    ];
  };

  const processViolationsByPolicy = (violations) => {
    const policyCounts = {};

    violations.forEach((v) => {
      const policy = v.policy?.split(':')[0] || 'Unknown';
      policyCounts[policy] = (policyCounts[policy] || 0) + 1;
    });

    return Object.entries(policyCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  };

  const processComplianceByClassification = (datasets) => {
    const classifications = ['public', 'internal', 'confidential', 'restricted'];
    return classifications.map((cls) => {
      const filtered = datasets.filter((ds) => ds.classification === cls);
      const compliant = filtered.filter(
        (ds) => ds.contract?.validation_result?.status === 'passed'
      ).length;
      return {
        classification: cls,
        compliant,
        nonCompliant: filtered.length - compliant,
        total: filtered.length,
      };
    });
  };

  const complianceRate = metrics.totalDatasets > 0
    ? ((metrics.compliantDatasets / metrics.totalDatasets) * 100).toFixed(1)
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-white">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Platform Compliance Dashboard
          </h1>
          <p className="text-gray-400">
            Monitor governance compliance and violation trends across the platform
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Compliance Rate */}
          <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 rounded-xl border border-green-500/30 p-6">
            <div className="flex items-center justify-between mb-4">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-400" />
                <span className="text-sm text-green-400">+5.2%</span>
              </div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{complianceRate}%</div>
            <p className="text-gray-400 text-sm">Compliance Rate</p>
            <p className="text-xs text-gray-500 mt-2">
              {metrics.compliantDatasets} of {metrics.totalDatasets} datasets
            </p>
          </div>

          {/* Total Violations */}
          <div className="bg-gradient-to-br from-red-500/10 to-red-600/10 rounded-xl border border-red-500/30 p-6">
            <div className="flex items-center justify-between mb-4">
              <AlertTriangle className="w-8 h-8 text-red-400" />
              <div className="flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-green-400" />
                <span className="text-sm text-green-400">-12.3%</span>
              </div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              {metrics.totalViolations}
            </div>
            <p className="text-gray-400 text-sm">Active Violations</p>
            <p className="text-xs text-gray-500 mt-2">
              {metrics.criticalViolations} critical
            </p>
          </div>

          {/* Active Subscriptions */}
          <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 rounded-xl border border-purple-500/30 p-6">
            <div className="flex items-center justify-between mb-4">
              <Users className="w-8 h-8 text-purple-400" />
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-400" />
                <span className="text-sm text-green-400">+18.5%</span>
              </div>
            </div>
            <div className="text-3xl font-bold text-white mb-1">
              {metrics.activeSubscriptions}
            </div>
            <p className="text-gray-400 text-sm">Active Subscriptions</p>
            <p className="text-xs text-gray-500 mt-2">
              {metrics.pendingApprovals} pending approval
            </p>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Violation Trends */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Violation Trends</h2>
              <Activity className="w-5 h-5 text-gray-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={violationTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="violations"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  name="Total Violations"
                />
                <Line
                  type="monotone"
                  dataKey="critical"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Critical"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Violations by Type */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Violations by Severity</h2>
              <AlertTriangle className="w-5 h-5 text-gray-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={violationsByType}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {violationsByType.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Top Violated Policies */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Top Violated Policies</h2>
              <Shield className="w-5 h-5 text-gray-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={violationsByPolicy} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" />
                <YAxis dataKey="name" type="category" stroke="#9ca3af" width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="count" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Compliance by Classification */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">
                Compliance by Classification
              </h2>
              <Database className="w-5 h-5 text-gray-500" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={complianceByClassification}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="classification" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="compliant" stackId="a" fill="#10b981" name="Compliant" />
                <Bar dataKey="nonCompliant" stackId="a" fill="#ef4444" name="Non-Compliant" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-gray-800 rounded-xl border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">Recent Activity</h2>
          </div>
          <div className="divide-y divide-gray-700">
            {datasets
              .filter((ds) => ds.contract?.validation_result?.status === 'failed')
              .slice(0, 5)
              .map((dataset) => (
                <div key={dataset.id} className="p-6 hover:bg-gray-750 transition-all">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        <h3 className="text-white font-medium">{dataset.name}</h3>
                        <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded">
                          {dataset.contract.validation_result.failures} violations
                        </span>
                      </div>
                      <p className="text-sm text-gray-400 ml-8">
                        {dataset.contract.validation_result.violations?.[0]?.message}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(dataset.updated_at || dataset.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
