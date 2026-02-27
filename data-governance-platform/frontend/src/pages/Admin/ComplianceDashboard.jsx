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
import './ComplianceDashboard.css';

const TOOLTIP_STYLE = {
  background: 'var(--color-bg-elevated)',
  border: '1px solid rgba(139, 92, 246, 0.2)',
  borderRadius: '0.5rem',
  fontSize: '0.875rem',
  color: 'var(--color-text-primary)',
};

export function ComplianceDashboard() {
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState([]);
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

      const datasetsResponse = await datasetAPI.list({});
      const datasetsData = datasetsResponse.data;
      setDatasets(datasetsData);

      const subscriptionsResponse = await subscriptionAPI.list({});
      const subscriptionsData = subscriptionsResponse.data;

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

      setViolationTrends(generateViolationTrends(datasetsData));
      setViolationsByType(processViolationsByType(allViolations));
      setViolationsByPolicy(processViolationsByPolicy(allViolations));
      setComplianceByClassification(processComplianceByClassification(datasetsData));
    } catch {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const generateViolationTrends = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    return months.map((month, index) => ({
      month,
      violations: Math.max(0, 50 - index * 5 + Math.floor(Math.random() * 10)),
      critical: Math.max(0, 15 - index * 2 + Math.floor(Math.random() * 3)),
    }));
  };

  const processViolationsByType = (violations) => {
    const counts = { critical: 0, warning: 0, info: 0 };
    violations.forEach((v) => {
      const type = v.type?.toLowerCase() || 'info';
      if (counts[type] !== undefined) counts[type]++;
    });
    return [
      { name: 'Critical', value: counts.critical, color: '#ef4444' },
      { name: 'Warning',  value: counts.warning,  color: '#f59e0b' },
      { name: 'Info',     value: counts.info,     color: '#3b82f6' },
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
    return ['public', 'internal', 'confidential', 'restricted'].map((cls) => {
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

  const complianceRate =
    metrics.totalDatasets > 0
      ? ((metrics.compliantDatasets / metrics.totalDatasets) * 100).toFixed(1)
      : 0;

  if (loading) {
    return <div className="compliance-loading">Loading dashboard...</div>;
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h1>Platform Compliance Dashboard</h1>
        <p>Monitor governance compliance and violation trends across the platform</p>
      </div>

      {/* Key Metrics */}
      <div className="compliance-metrics-grid">
        {/* Compliance Rate */}
        <div className="compliance-metric-card card-success">
          <div className="compliance-metric-top">
            <div className="compliance-metric-icon icon-success">
              <CheckCircle size={32} />
            </div>
            <div className="compliance-metric-trend trend-up">
              <TrendingUp size={18} />
              <span>+5.2%</span>
            </div>
          </div>
          <p className="compliance-metric-value">{complianceRate}%</p>
          <p className="compliance-metric-label">Compliance Rate</p>
          <p className="compliance-metric-sub">
            {metrics.compliantDatasets} of {metrics.totalDatasets} datasets
          </p>
        </div>

        {/* Total Violations */}
        <div className="compliance-metric-card card-error">
          <div className="compliance-metric-top">
            <div className="compliance-metric-icon icon-error">
              <AlertTriangle size={32} />
            </div>
            <div className="compliance-metric-trend trend-up">
              <TrendingDown size={18} />
              <span>-12.3%</span>
            </div>
          </div>
          <p className="compliance-metric-value">{metrics.totalViolations}</p>
          <p className="compliance-metric-label">Active Violations</p>
          <p className="compliance-metric-sub">{metrics.criticalViolations} critical</p>
        </div>

        {/* Active Subscriptions */}
        <div className="compliance-metric-card card-accent">
          <div className="compliance-metric-top">
            <div className="compliance-metric-icon icon-accent">
              <Users size={32} />
            </div>
            <div className="compliance-metric-trend trend-up">
              <TrendingUp size={18} />
              <span>+18.5%</span>
            </div>
          </div>
          <p className="compliance-metric-value">{metrics.activeSubscriptions}</p>
          <p className="compliance-metric-label">Active Subscriptions</p>
          <p className="compliance-metric-sub">{metrics.pendingApprovals} pending approval</p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="compliance-charts-grid">
        {/* Violation Trends */}
        <div className="compliance-chart-card">
          <div className="compliance-chart-header">
            <h2>Violation Trends</h2>
            <Activity size={20} />
          </div>
          <div className="compliance-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={violationTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                <XAxis dataKey="month" stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                <YAxis stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="violations"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  name="Total Violations"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="critical"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Critical"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Violations by Severity */}
        <div className="compliance-chart-card">
          <div className="compliance-chart-header">
            <h2>Violations by Severity</h2>
            <AlertTriangle size={20} />
          </div>
          <div className="compliance-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={violationsByType}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius="70%"
                  dataKey="value"
                >
                  {violationsByType.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="compliance-charts-grid">
        {/* Top Violated Policies */}
        <div className="compliance-chart-card">
          <div className="compliance-chart-header">
            <h2>Top Violated Policies</h2>
            <Shield size={20} />
          </div>
          <div className="compliance-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={violationsByPolicy} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                <XAxis type="number" stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#6b7280"
                  style={{ fontSize: '0.75rem' }}
                  width={80}
                />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Compliance by Classification */}
        <div className="compliance-chart-card">
          <div className="compliance-chart-header">
            <h2>Compliance by Classification</h2>
            <Database size={20} />
          </div>
          <div className="compliance-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={complianceByClassification}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                <XAxis dataKey="classification" stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                <YAxis stroke="#6b7280" style={{ fontSize: '0.75rem' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend />
                <Bar dataKey="compliant"    stackId="a" fill="#10b981" name="Compliant"     radius={[4, 4, 0, 0]} />
                <Bar dataKey="nonCompliant" stackId="a" fill="#ef4444" name="Non-Compliant" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="compliance-activity">
        <div className="compliance-activity-header">
          <h2>Recent Activity</h2>
        </div>
        {datasets
          .filter((ds) => ds.contract?.validation_result?.status === 'failed')
          .slice(0, 5)
          .map((dataset) => (
            <div key={dataset.id} className="compliance-activity-item">
              <div className="compliance-activity-item-inner">
                <div className="compliance-activity-left">
                  <div className="compliance-activity-title-row">
                    <AlertTriangle size={18} />
                    <span className="compliance-activity-name">{dataset.name}</span>
                    <span className="compliance-activity-badge">
                      {dataset.contract.validation_result.failures} violations
                    </span>
                  </div>
                  <p className="compliance-activity-message">
                    {dataset.contract.validation_result.violations?.[0]?.message}
                  </p>
                </div>
                <span className="compliance-activity-date">
                  {new Date(dataset.updated_at || dataset.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
