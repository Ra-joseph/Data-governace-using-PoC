import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Globe, Shield, TrendingUp, Users, BarChart3, CheckCircle,
  XCircle, AlertTriangle, Activity, Layers
} from 'lucide-react';
import { domainGovernanceAPI } from '../../services/api';
import toast from 'react-hot-toast';

const CAT_COLORS = {
  data_quality: '#3b82f6',
  security: '#ef4444',
  privacy: '#f59e0b',
  compliance: '#10b981',
  lineage: '#8b5cf6',
  sla: '#0070AD',
};

export const DomainGovernance = () => {
  const [tab, setTab] = useState('overview');
  const [domains, setDomains] = useState(null);
  const [matrix, setMatrix] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [effectiveness, setEffectiveness] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [domRes, matRes, anaRes, effRes] = await Promise.all([
        domainGovernanceAPI.listDomains(),
        domainGovernanceAPI.getMatrix(),
        domainGovernanceAPI.getAnalytics(),
        domainGovernanceAPI.getEffectiveness(),
      ]);
      setDomains(domRes.data);
      setMatrix(matRes.data);
      setAnalytics(anaRes.data);
      setEffectiveness(effRes.data);
    } catch { toast.error('Failed to load governance data'); }
    finally { setLoading(false); }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>Loading governance data...</div>;
  }

  const tabs = [
    { key: 'overview', label: 'Domains', icon: Globe },
    { key: 'matrix', label: 'Coverage Matrix', icon: Layers },
    { key: 'analytics', label: 'Analytics', icon: BarChart3 },
    { key: 'health', label: 'Health Score', icon: Activity },
  ];

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      <div style={{ marginBottom: 'var(--space-xl)' }}>
        <h2 style={{ margin: 0 }}>Domain Governance</h2>
        <p style={{ margin: 0, marginTop: 'var(--space-xs)', color: 'var(--color-text-secondary)' }}>
          Cross-domain policy coverage, analytics, and governance health
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 'var(--space-xs)', marginBottom: 'var(--space-xl)', borderBottom: '1px solid var(--color-border)', paddingBottom: 'var(--space-xs)' }}>
        {tabs.map(t => {
          const active = tab === t.key;
          return (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 16px', fontSize: '0.8125rem', fontWeight: 600,
              background: active ? 'rgba(0,112,173,0.1)' : 'transparent',
              color: active ? '#0070AD' : 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
              border: 'none', borderBottom: active ? '2px solid #0070AD' : '2px solid transparent',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <t.icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      {/* Domains Overview */}
      {tab === 'overview' && domains && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--space-md)' }}>
          {domains.domains.map((d, i) => (
            <motion.div key={d.domain} className="card" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
                <h4 style={{ margin: 0, textTransform: 'capitalize' }}>{d.domain}</h4>
                <div style={{
                  width: 42, height: 42, borderRadius: '50%',
                  background: d.coverage_score >= 80 ? 'rgba(16,185,129,0.15)' : d.coverage_score >= 40 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.8rem', fontWeight: 700,
                  color: d.coverage_score >= 80 ? '#10b981' : d.coverage_score >= 40 ? '#f59e0b' : '#ef4444',
                }}>{d.coverage_score}%</div>
              </div>
              <div style={{ display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-sm)' }}>
                <div><div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{d.total_policies}</div><div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>Total</div></div>
                <div><div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#10b981' }}>{d.approved}</div><div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>Active</div></div>
                <div><div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f59e0b' }}>{d.pending}</div><div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>Pending</div></div>
              </div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {d.categories_covered.map(cat => (
                  <span key={cat} style={{
                    padding: '1px 6px', borderRadius: 9999, fontSize: '0.6rem', fontWeight: 600,
                    background: `${CAT_COLORS[cat] || '#9ca3af'}15`, color: CAT_COLORS[cat] || '#9ca3af',
                  }}>{cat}</span>
                ))}
              </div>
            </motion.div>
          ))}
          {domains.domains.length === 0 && (
            <p style={{ color: 'var(--color-text-muted)' }}>No domains found. Create policies with affected_domains to populate.</p>
          )}
        </div>
      )}

      {/* Coverage Matrix */}
      {tab === 'matrix' && matrix && (
        <div className="card" style={{ overflowX: 'auto' }}>
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Policy Coverage Matrix</h4>
          {matrix.matrix.length === 0 ? (
            <p style={{ color: 'var(--color-text-muted)' }}>No approved policies yet.</p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid var(--color-border)' }}>Domain</th>
                  {matrix.categories.map(c => (
                    <th key={c} style={{ textAlign: 'center', padding: '8px 6px', borderBottom: '1px solid var(--color-border)', fontSize: '0.7rem', color: CAT_COLORS[c] || '#9ca3af' }}>
                      {c.replace('_', ' ')}
                    </th>
                  ))}
                  <th style={{ textAlign: 'center', padding: '8px 12px', borderBottom: '1px solid var(--color-border)', fontWeight: 700 }}>Coverage</th>
                </tr>
              </thead>
              <tbody>
                {matrix.matrix.map(row => (
                  <tr key={row.domain}>
                    <td style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border)', fontWeight: 600, textTransform: 'capitalize' }}>{row.domain}</td>
                    {matrix.categories.map(c => (
                      <td key={c} style={{ textAlign: 'center', padding: '8px 6px', borderBottom: '1px solid var(--color-border)' }}>
                        {row[c] > 0 ? (
                          <CheckCircle size={16} style={{ color: '#10b981' }} />
                        ) : (
                          <XCircle size={16} style={{ color: 'rgba(239,68,68,0.3)' }} />
                        )}
                      </td>
                    ))}
                    <td style={{ textAlign: 'center', padding: '8px 12px', borderBottom: '1px solid var(--color-border)', fontWeight: 700, color: row.coverage_pct >= 80 ? '#10b981' : row.coverage_pct >= 40 ? '#f59e0b' : '#ef4444' }}>
                      {row.coverage_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Analytics */}
      {tab === 'analytics' && analytics && (
        <div>
          {/* Funnel */}
          <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
            <h4 style={{ marginBottom: 'var(--space-lg)' }}>Approval Funnel</h4>
            <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center' }}>
              {[
                { label: 'Drafted', value: analytics.approval_funnel.drafted, color: '#3b82f6' },
                { label: 'Submitted', value: analytics.approval_funnel.submitted, color: '#0070AD' },
                { label: 'Approved', value: analytics.approval_funnel.approved, color: '#10b981' },
                { label: 'Rejected', value: analytics.approval_funnel.rejected, color: '#ef4444' },
              ].map((step, i) => (
                <div key={step.label} style={{ textAlign: 'center', flex: 1 }}>
                  <div style={{ fontSize: '1.75rem', fontWeight: 700, color: step.color }}>{step.value}</div>
                  <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{step.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
            {/* Category Distribution */}
            <div className="card">
              <h4 style={{ marginBottom: 'var(--space-md)' }}>Category Distribution</h4>
              {Object.entries(analytics.category_distribution).map(([cat, count]) => (
                <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: CAT_COLORS[cat] || '#9ca3af' }} />
                    <span style={{ fontSize: '0.8125rem' }}>{cat.replace('_', ' ')}</span>
                  </div>
                  <span style={{ fontWeight: 700, color: CAT_COLORS[cat] || '#9ca3af' }}>{count}</span>
                </div>
              ))}
            </div>

            {/* Top Authors */}
            <div className="card">
              <h4 style={{ marginBottom: 'var(--space-md)' }}>Top Authors</h4>
              {analytics.top_authors.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>No policies authored yet.</p>
              ) : analytics.top_authors.map((a, i) => (
                <div key={a.author} style={{
                  display: 'flex', justifyContent: 'space-between', padding: '6px 10px',
                  background: i === 0 ? 'rgba(139,92,246,0.05)' : 'transparent',
                  borderRadius: 'var(--radius-sm)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Users size={14} style={{ color: 'var(--color-text-muted)' }} />
                    <span style={{ fontSize: '0.8125rem' }}>{a.author}</span>
                  </div>
                  <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{a.count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stats row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-md)' }}>
            {[
              { label: 'Avg Versions', value: analytics.avg_versions_per_policy },
              { label: 'Multi-Domain', value: analytics.multi_domain_policies },
              { label: 'Total Artifacts', value: analytics.total_artifacts },
              { label: 'Audit Events', value: analytics.total_audit_events },
            ].map(s => (
              <div key={s.label} className="card" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{s.value}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontWeight: 500 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Health Score */}
      {tab === 'health' && effectiveness && (
        <div>
          <div className="card" style={{ textAlign: 'center', marginBottom: 'var(--space-xl)' }}>
            <h4 style={{ marginBottom: 'var(--space-md)' }}>Governance Health Score</h4>
            <div style={{
              width: 120, height: 120, borderRadius: '50%', margin: '0 auto var(--space-md)',
              background: `conic-gradient(${effectiveness.health_score >= 80 ? '#10b981' : effectiveness.health_score >= 50 ? '#f59e0b' : '#ef4444'} ${effectiveness.health_score * 3.6}deg, var(--color-bg-tertiary) 0deg)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{
                width: 96, height: 96, borderRadius: '50%', background: 'var(--color-bg-primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.75rem', fontWeight: 700,
                color: effectiveness.health_score >= 80 ? '#10b981' : effectiveness.health_score >= 50 ? '#f59e0b' : '#ef4444',
              }}>
                {effectiveness.health_score}
              </div>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              Based on contract pass rate ({effectiveness.pass_rate_pct}%) and policy coverage ({effectiveness.policy_coverage_pct}%)
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)' }}>
            {[
              { label: 'Contracts', value: effectiveness.total_contracts, icon: Shield },
              { label: 'Validated', value: effectiveness.contracts_validated, icon: CheckCircle },
              { label: 'Violations Found', value: effectiveness.total_violations_detected, icon: AlertTriangle },
              { label: 'Active Policies', value: effectiveness.active_policies, icon: Layers },
            ].map(c => (
              <div key={c.label} className="card" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                <c.icon size={20} style={{ color: '#0070AD' }} />
                <div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{c.value}</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)' }}>{c.label}</div>
                </div>
              </div>
            ))}
          </div>

          {effectiveness.policy_summaries.length > 0 && (
            <div className="card">
              <h4 style={{ marginBottom: 'var(--space-md)' }}>Active Policy Details</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
                {effectiveness.policy_summaries.map(p => (
                  <div key={p.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 12px', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-sm)',
                  }}>
                    <div>
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{p.title}</span>
                      <div style={{ display: 'flex', gap: 6, marginTop: 2 }}>
                        <span style={{ fontSize: '0.6rem', fontWeight: 700, color: CAT_COLORS[p.category] || '#9ca3af', textTransform: 'uppercase' }}>{p.category}</span>
                        <span style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>v{p.version}</span>
                        <span style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>{p.domains.join(', ')}</span>
                      </div>
                    </div>
                    <span style={{
                      padding: '2px 8px', borderRadius: 9999, fontSize: '0.6rem', fontWeight: 700,
                      background: p.severity === 'CRITICAL' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)',
                      color: p.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b',
                    }}>{p.severity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
