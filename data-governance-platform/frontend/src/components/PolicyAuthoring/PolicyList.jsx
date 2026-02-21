import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Search, Filter, FileText, AlertTriangle, Info, ShieldAlert } from 'lucide-react';
import { policyAuthoringAPI } from '../../services/api';
import toast from 'react-hot-toast';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.2)' },
  WARNING: { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.2)' },
  INFO: { color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.2)' },
};

const STATUS_CONFIG = {
  draft: { color: '#9ca3af', bg: 'rgba(156,163,175,0.1)', border: 'rgba(156,163,175,0.2)', label: 'Draft' },
  pending_approval: { color: '#0070AD', bg: 'rgba(0,112,173,0.1)', border: 'rgba(0,112,173,0.2)', label: 'Pending' },
  approved: { color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.2)', label: 'Approved' },
  rejected: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.2)', label: 'Rejected' },
  deprecated: { color: '#6b7280', bg: 'rgba(107,114,128,0.1)', border: 'rgba(107,114,128,0.2)', label: 'Deprecated' },
};

const CATEGORY_LABELS = {
  data_quality: 'Data Quality',
  security: 'Security',
  privacy: 'Privacy',
  compliance: 'Compliance',
  lineage: 'Lineage',
  sla: 'SLA',
};

export const PolicyList = () => {
  const navigate = useNavigate();
  const [policies, setPolicies] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      const response = await policyAuthoringAPI.list(params);
      setPolicies(response.data.policies);
      setTotal(response.data.total);
    } catch (error) {
      toast.error('Failed to load policies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, [statusFilter, categoryFilter]);

  const filteredPolicies = policies.filter(p =>
    p.title.toLowerCase().includes(search.toLowerCase()) ||
    p.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xl)' }}>
        <div>
          <h2 style={{ margin: 0 }}>Policy Authoring</h2>
          <p style={{ margin: 0, marginTop: 'var(--space-xs)' }}>{total} policies total</p>
        </div>
        <button
          onClick={() => navigate('/policy-authoring/new')}
          style={{
            display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
            padding: 'var(--space-sm) var(--space-lg)',
            background: 'linear-gradient(135deg, #0070AD, #12ABDB)',
            color: 'white', borderRadius: 'var(--radius-md)',
            fontSize: '0.9375rem', fontWeight: 600,
          }}
        >
          <Plus size={18} /> New Policy
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input
            type="text"
            placeholder="Search policies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: 36 }}
          />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={{ minWidth: 150 }}>
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="pending_approval">Pending Approval</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} style={{ minWidth: 150 }}>
          <option value="">All Categories</option>
          {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* Policy Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-3xl)', color: 'var(--color-text-tertiary)' }}>Loading...</div>
      ) : filteredPolicies.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-3xl)' }}>
          <FileText size={48} style={{ color: 'var(--color-text-muted)', marginBottom: 'var(--space-md)' }} />
          <h3 style={{ color: 'var(--color-text-secondary)' }}>No policies found</h3>
          <p>Create your first governance policy to get started.</p>
          <button
            onClick={() => navigate('/policy-authoring/new')}
            style={{
              marginTop: 'var(--space-md)',
              padding: 'var(--space-sm) var(--space-lg)',
              background: 'linear-gradient(135deg, #0070AD, #12ABDB)',
              color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600,
            }}
          >
            <Plus size={16} style={{ verticalAlign: 'middle', marginRight: 4 }} /> Create Policy
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
          {filteredPolicies.map((policy, index) => {
            const sev = SEVERITY_CONFIG[policy.severity] || SEVERITY_CONFIG.INFO;
            const st = STATUS_CONFIG[policy.status] || STATUS_CONFIG.draft;
            return (
              <motion.div
                key={policy.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="card"
                onClick={() => navigate(`/policy-authoring/${policy.id}`)}
                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 'var(--space-lg)', padding: 'var(--space-md) var(--space-lg)' }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-xs)' }}>
                    <h4 style={{ margin: 0, fontSize: '1rem' }}>{policy.title}</h4>
                    <span style={{
                      padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600,
                      background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`, textTransform: 'uppercase',
                    }}>{policy.severity}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--color-text-tertiary)' }}>
                    {policy.description.length > 120 ? policy.description.slice(0, 120) + '...' : policy.description}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', flexShrink: 0 }}>
                  <span style={{
                    padding: '4px 12px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
                    background: 'rgba(0,112,173,0.1)', color: '#0070AD', border: '1px solid rgba(0,112,173,0.2)',
                  }}>{CATEGORY_LABELS[policy.policy_category] || policy.policy_category}</span>
                  <span style={{
                    padding: '4px 12px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
                    background: st.bg, color: st.color, border: `1px solid ${st.border}`,
                  }}>{st.label}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>v{policy.version}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};
