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
      setDatasets(response.data);
      
      // Calculate stats
      const total = response.data.length;
      const published = response.data.filter(d => d.status === 'published').length;
      const draft = response.data.filter(d => d.status === 'draft').length;
      const withPII = response.data.filter(d => d.contains_pii).length;
      
      setStats({
        total,
        published,
        draft,
        violations: draft, // Simplified: draft status indicates violations
        pii: withPII,
      });
    } catch (error) {
      console.error('Failed to load datasets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock data for charts
  const trendData = [
    { month: 'Jan', datasets: 12, violations: 5 },
    { month: 'Feb', datasets: 19, violations: 3 },
    { month: 'Mar', datasets: 25, violations: 8 },
    { month: 'Apr', datasets: 32, violations: 4 },
    { month: 'May', datasets: 41, violations: 6 },
    { month: 'Jun', datasets: 48, violations: 2 },
  ];

  const classificationData = [
    { name: 'Public', value: 15, color: '#3b82f6' },
    { name: 'Internal', value: 32, color: '#8b5cf6' },
    { name: 'Confidential', value: 28, color: '#f59e0b' },
    { name: 'Restricted', value: 8, color: '#ef4444' },
  ];

  const policyData = [
    { policy: 'PII Encryption', violations: 8, passed: 42 },
    { policy: 'Retention', violations: 5, passed: 45 },
    { policy: 'Completeness', violations: 12, passed: 38 },
    { policy: 'Documentation', violations: 15, passed: 35 },
  ];

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
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
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
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                <XAxis 
                  dataKey="month" 
                  stroke="#6b7280"
                  style={{ fontSize: '0.75rem' }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '0.75rem' }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0f1419',
                    border: '1px solid rgba(139, 92, 246, 0.2)',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="datasets"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorDatasets)"
                />
                <Area
                  type="monotone"
                  dataKey="violations"
                  stroke="#ef4444"
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
                    background: '#0f1419',
                    border: '1px solid rgba(139, 92, 246, 0.2)',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
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
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                <XAxis 
                  dataKey="policy" 
                  stroke="#6b7280"
                  style={{ fontSize: '0.7rem' }}
                  angle={-15}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '0.75rem' }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0f1419',
                    border: '1px solid rgba(139, 92, 246, 0.2)',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                  }}
                />
                <Bar dataKey="violations" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="passed" fill="#10b981" radius={[4, 4, 0, 0]} />
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
