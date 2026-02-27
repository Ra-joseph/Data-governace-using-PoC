import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield, FileText, CheckCircle, XCircle, AlertTriangle,
  Clock, PenTool, Activity, BarChart3, Users
} from 'lucide-react';
import { policyDashboardAPI, policyAuthoringAPI } from '../../services/api';
import toast from 'react-hot-toast';

const CATEGORY_LABELS = {
  data_quality: 'Data Quality',
  security: 'Security',
  privacy: 'Privacy',
  compliance: 'Compliance',
  lineage: 'Lineage',
  sla: 'SLA',
};

const CATEGORY_COLORS = {
  data_quality: '#3b82f6',
  security: '#ef4444',
  privacy: '#f59e0b',
  compliance: '#10b981',
  lineage: '#8b5cf6',
  sla: '#0070AD',
};

const STATUS_COLORS = {
  draft: '#9ca3af',
  pending_approval: '#0070AD',
  approved: '#10b981',
  rejected: '#ef4444',
  deprecated: '#6b7280',
};

const STATUS_LABELS = {
  draft: 'Draft',
  pending_approval: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  deprecated: 'Deprecated',
};

export const PolicyDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await policyDashboardAPI.stats();
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) {
    return (
      <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
        Loading dashboard...
      </div>
    );
  }

  const approved = stats.by_status?.approved || 0;
  const pending = stats.by_status?.pending_approval || 0;
  const draft = stats.by_status?.draft || 0;
  const rejected = stats.by_status?.rejected || 0;

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      <div style={{ marginBottom: 'var(--space-xl)' }}>
        <h2 style={{ margin: 0 }}>Policy Governance Dashboard</h2>
        <p style={{ margin: 0, marginTop: 'var(--space-xs)' }}>Overview of authored governance policies and enforcement status</p>
      </div>

      {/* Top Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
        {[
          { label: 'Total Policies', value: stats.total_policies, icon: FileText, color: '#0070AD' },
          { label: 'Approved & Active', value: approved, icon: CheckCircle, color: '#10b981' },
          { label: 'Pending Review', value: pending, icon: Clock, color: '#f59e0b' },
          { label: 'Generated Artifacts', value: stats.total_artifacts, icon: Shield, color: '#8b5cf6' },
          { label: 'Audit Actions', value: stats.total_approval_actions, icon: Activity, color: '#3b82f6' },
        ].map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="card"
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}
          >
            <div style={{
              width: 44, height: 44, borderRadius: 'var(--radius-lg)',
              background: `${card.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <card.icon size={22} style={{ color: card.color }} />
            </div>
            <div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>{card.value}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', fontWeight: 500 }}>{card.label}</div>
            </div>
          </motion.div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
        {/* Status Breakdown */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Policy Status Breakdown</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {Object.entries(stats.by_status || {}).map(([status, count]) => {
              const total = stats.total_policies || 1;
              const pct = Math.round((count / total) * 100);
              const color = STATUS_COLORS[status] || '#9ca3af';
              return (
                <div key={status}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: 4 }}>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{STATUS_LABELS[status] || status}</span>
                    <span style={{ fontWeight: 600 }}>{count} ({pct}%)</span>
                  </div>
                  <div style={{ height: 8, borderRadius: 4, background: 'var(--color-bg-tertiary)', overflow: 'hidden' }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.8, delay: 0.2 }}
                      style={{ height: '100%', borderRadius: 4, background: color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Policies by Category</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {Object.entries(stats.by_category || {}).map(([cat, count]) => {
              const color = CATEGORY_COLORS[cat] || '#0070AD';
              return (
                <div key={cat} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: 'var(--space-sm) var(--space-md)',
                  background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
                    <span style={{ fontSize: '0.875rem' }}>{CATEGORY_LABELS[cat] || cat}</span>
                  </div>
                  <span style={{ fontWeight: 700, fontSize: '1rem', color }}>{count}</span>
                </div>
              );
            })}
            {Object.keys(stats.by_category || {}).length === 0 && (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>No policies authored yet.</p>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
        {/* Severity Breakdown */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Severity Distribution</h4>
          <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
            {[
              { key: 'CRITICAL', color: '#ef4444', icon: XCircle },
              { key: 'WARNING', color: '#f59e0b', icon: AlertTriangle },
              { key: 'INFO', color: '#10b981', icon: CheckCircle },
            ].map(sev => (
              <div key={sev.key} style={{ textAlign: 'center', flex: 1 }}>
                <div style={{
                  width: 64, height: 64, borderRadius: '50%', margin: '0 auto var(--space-sm)',
                  background: `${sev.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <sev.icon size={28} style={{ color: sev.color }} />
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: sev.color }}>
                  {stats.by_severity?.[sev.key] || 0}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', fontWeight: 600, textTransform: 'uppercase' }}>
                  {sev.key}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scanner Breakdown */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Scanner Distribution</h4>
          <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
            {[
              { key: 'rule_based', label: 'Rule-Based', color: '#0070AD', desc: 'Deterministic YAML rules' },
              { key: 'ai_semantic', label: 'AI Semantic', color: '#8b5cf6', desc: 'LLM-powered analysis' },
            ].map(scanner => (
              <div key={scanner.key} style={{ textAlign: 'center', flex: 1, padding: 'var(--space-md)', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: scanner.color }}>
                  {stats.scanner_breakdown?.[scanner.key] || 0}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{scanner.label}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 2 }}>{scanner.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Approval Activity */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-lg)' }}>
          <h4 style={{ margin: 0 }}>Recent Approval Activity</h4>
          <button
            onClick={() => navigate('/policy-review')}
            style={{
              padding: '4px 12px', fontSize: '0.8125rem', fontWeight: 600,
              background: 'rgba(0,112,173,0.1)', color: '#0070AD',
              borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,112,173,0.2)',
            }}
          >
            Review Queue
          </button>
        </div>
        {stats.recent_approvals?.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>No approval activity yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            {stats.recent_approvals?.map(log => {
              const actionColor = log.action === 'approved' ? '#10b981' : log.action === 'rejected' ? '#ef4444' : '#0070AD';
              return (
                <div key={log.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: 'var(--space-sm) var(--space-md)',
                  background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-sm)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                    <Users size={14} style={{ color: 'var(--color-text-muted)' }} />
                    <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>{log.actor_name}</span>
                    <span style={{
                      padding: '1px 6px', borderRadius: 9999, fontSize: '0.65rem', fontWeight: 700,
                      background: `${actionColor}15`, color: actionColor, textTransform: 'uppercase',
                    }}>{log.action}</span>
                    {log.comment && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                        "{log.comment.slice(0, 40)}{log.comment.length > 40 ? '...' : ''}"
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
