import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Database, 
  FileCheck, 
  AlertTriangle, 
  TrendingUp,
  Shield,
  Users,
  Activity
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend 
} from 'recharts';
import { datasetAPI } from '../services/api';
import { SkeletonLoader } from '../components/SkeletonLoader';
import './Dashboard.css';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export const Dashboard = () => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    published: 0,
    draft: 0,
    violations: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await datasetAPI.list();
      const data = response.data;
      setDatasets(data);

      // Calculate stats from real data
      const total = data.length;
      const published = data.filter(d => d.status === 'published').length;
      const draft = data.filter(d => d.status === 'draft').length;
      const withPII = data.filter(d => d.contains_pii).length;

      // Count datasets that have contract violations (failed or warning status)
      const violations = data.filter(d =>
        d.contract && ['failed', 'warning'].includes(d.contract.validation_result?.status)
      ).length;

      setStats({ total, published, draft, violations, pii: withPII });
    } catch (error) {
      console.error('Failed to load datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Derive classification distribution from real dataset data
  const classificationColors = {
    public: '#0070AD',
    internal: '#12ABDB',
    confidential: '#d97706',
    restricted: '#dc2626',
  };

  const classificationData = Object.entries(
    datasets.reduce((acc, d) => {
      const cls = d.classification || 'internal';
      acc[cls] = (acc[cls] || 0) + 1;
      return acc;
    }, {})
  ).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    color: classificationColors[name] || '#8A8A8A',
  }));

  // Derive policy compliance counts from contract validation results
  const policyViolationMap = {};
  datasets.forEach(d => {
    const violations = d.contract?.validation_result?.violations || [];
    violations.forEach(v => {
      const key = v.policy ? v.policy.split(':')[0].trim() : 'Unknown';
      policyViolationMap[key] = (policyViolationMap[key] || 0) + 1;
    });
  });

  const policyData = Object.entries(policyViolationMap)
    .slice(0, 5)
    .map(([policy, count]) => ({
      policy,
      violations: count,
      passed: Math.max(0, datasets.length - count),
    }));

  // Build monthly registration trend from real dataset created_at dates
  const now = new Date();
  const trendData = Array.from({ length: 6 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1);
    const label = d.toLocaleString('default', { month: 'short' });
    const count = datasets.filter(ds => {
      const created = new Date(ds.created_at);
      return created.getFullYear() === d.getFullYear() && created.getMonth() === d.getMonth();
    }).length;
    const viol = datasets.filter(ds => {
      const created = new Date(ds.created_at);
      return (
        created.getFullYear() === d.getFullYear() &&
        created.getMonth() === d.getMonth() &&
        ds.contract &&
        ['failed', 'warning'].includes(ds.contract.validation_result?.status)
      );
    }).length;
    return { month: label, datasets: count, violations: viol };
  });

  const metricCards = [
    {
      title: 'Total Datasets',
      value: stats.total,
      icon: Database,
      color: 'accent',
      trend: '+12%',
    },
    {
      title: 'Published',
      value: stats.published,
      icon: FileCheck,
      color: 'success',
      trend: '+8%',
    },
    {
      title: 'Active Violations',
      value: stats.violations,
      icon: AlertTriangle,
      color: 'warning',
      trend: '-23%',
    },
    {
      title: 'Contains PII',
      value: stats.pii || 0,
      icon: Shield,
      color: 'error',
      trend: '+5%',
    },
  ];

  if (loading) {
    return (
      <div className="page-container">
        <div className="page-header">
          <div className="skeleton" style={{ height: 36, width: 200, borderRadius: '8px', marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 18, width: 300, borderRadius: '6px' }} />
        </div>
        <div style={{ marginBottom: '2rem' }}>
          <SkeletonLoader type="stat" count={4} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
          <SkeletonLoader type="chart" />
          <SkeletonLoader type="chart" />
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Governance Dashboard</h1>
          <p className="page-subtitle">
            Real-time insights into your data governance posture
          </p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary">
            <Activity size={18} />
            View Reports
          </button>
        </div>
      </div>

      <motion.div
        className="metrics-grid"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {metricCards.map((metric, index) => (
          <motion.div key={index} variants={item} className="metric-card">
            <div className="metric-header">
              <div className={`metric-icon metric-icon-${metric.color}`}>
                <metric.icon size={24} />
              </div>
              <span className={`metric-trend trend-${metric.color}`}>
                {metric.trend}
              </span>
            </div>
            <div className="metric-content">
              <h3 className="metric-value">{metric.value}</h3>
              <p className="metric-label">{metric.title}</p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      <div className="charts-grid">
        <motion.div 
          className="chart-card chart-card-large"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="chart-header">
            <h3>Dataset Growth & Violations</h3>
            <p>Monthly trend over the last 6 months</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorDatasets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0070AD" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#0070AD" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 112, 173, 0.1)" />
                <XAxis
                  dataKey="month"
                  stroke="#B0ADA6"
                  style={{ fontSize: '0.75rem' }}
                />
                <YAxis
                  stroke="#B0ADA6"
                  style={{ fontSize: '0.75rem' }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E5E2DB',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    color: '#1A1A1A',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="datasets"
                  stroke="#0070AD"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorDatasets)"
                />
                <Area
                  type="monotone"
                  dataKey="violations"
                  stroke="#dc2626"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorViolations)"
                />
                <Legend />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div 
          className="chart-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="chart-header">
            <h3>Data Classification</h3>
            <p>Distribution by sensitivity level</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={classificationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {classificationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E5E2DB',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    color: '#1A1A1A',
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div 
          className="chart-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <div className="chart-header">
            <h3>Policy Compliance</h3>
            <p>Violations vs passed checks</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={policyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 112, 173, 0.1)" />
                <XAxis
                  dataKey="policy"
                  stroke="#B0ADA6"
                  style={{ fontSize: '0.7rem' }}
                  angle={-15}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  stroke="#B0ADA6"
                  style={{ fontSize: '0.75rem' }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E5E2DB',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    color: '#1A1A1A',
                  }}
                />
                <Bar dataKey="violations" fill="#dc2626" radius={[4, 4, 0, 0]} />
                <Bar dataKey="passed" fill="#16a34a" radius={[4, 4, 0, 0]} />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      <motion.div 
        className="activity-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <div className="section-header">
          <h3>Recent Activity</h3>
          <button className="btn-text">View All</button>
        </div>
        <div className="activity-list">
          {datasets.slice(0, 5).map((dataset, index) => (
            <div key={dataset.id} className="activity-item">
              <div className={`activity-icon ${dataset.status === 'published' ? 'success' : 'warning'}`}>
                <Database size={18} />
              </div>
              <div className="activity-content">
                <p className="activity-title">{dataset.name}</p>
                <p className="activity-meta">
                  {dataset.status === 'published' ? 'Published' : 'Draft'} • 
                  {dataset.contains_pii && ' Contains PII •'}
                  {' '}{dataset.classification}
                </p>
              </div>
              <span className="activity-time">
                {new Date(dataset.created_at).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};
