import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Send, CheckCircle, XCircle, FileText,
  Clock, User, Shield, Code, History
} from 'lucide-react';
import { policyAuthoringAPI } from '../../services/api';
import toast from 'react-hot-toast';

const STATUS_CONFIG = {
  draft: { color: '#9ca3af', label: 'Draft', icon: FileText },
  pending_approval: { color: '#0070AD', label: 'Pending Approval', icon: Clock },
  approved: { color: '#10b981', label: 'Approved', icon: CheckCircle },
  rejected: { color: '#ef4444', label: 'Rejected', icon: XCircle },
  deprecated: { color: '#6b7280', label: 'Deprecated', icon: History },
};

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  WARNING: '#f59e0b',
  INFO: '#10b981',
};

const CATEGORY_LABELS = {
  data_quality: 'Data Quality',
  security: 'Security',
  privacy: 'Privacy',
  compliance: 'Compliance',
  lineage: 'Lineage',
  sla: 'SLA',
};

export const PolicyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');
  const [yamlContent, setYamlContent] = useState(null);

  const loadPolicy = async () => {
    try {
      setLoading(true);
      const response = await policyAuthoringAPI.get(id);
      setPolicy(response.data);
    } catch (error) {
      toast.error('Failed to load policy');
      navigate('/policy-authoring');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicy();
  }, [id]);

  const handleSubmit = async () => {
    try {
      await policyAuthoringAPI.submit(id);
      toast.success('Policy submitted for approval');
      loadPolicy();
    } catch (error) {
      const msg = error.response?.data?.detail || 'Failed to submit policy';
      toast.error(msg);
    }
  };

  const handleLoadYaml = async () => {
    try {
      const response = await policyAuthoringAPI.getYaml(id);
      setYamlContent(response.data);
      setTab('yaml');
    } catch (error) {
      toast.error('No YAML artifact available. Policy must be approved first.');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
        Loading policy...
      </div>
    );
  }

  if (!policy) return null;

  const st = STATUS_CONFIG[policy.status] || STATUS_CONFIG.draft;
  const StatusIcon = st.icon;
  const sevColor = SEVERITY_COLORS[policy.severity] || '#9ca3af';

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      <button
        onClick={() => navigate('/policy-authoring')}
        style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', background: 'none', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-lg)', fontSize: '0.875rem' }}
      >
        <ArrowLeft size={16} /> Back to Policies
      </button>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-xl)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: 'var(--space-xs)' }}>
            <h2 style={{ margin: 0 }}>{policy.title}</h2>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>v{policy.version}</span>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              padding: '4px 12px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
              background: `${st.color}15`, color: st.color, border: `1px solid ${st.color}30`,
            }}>
              <StatusIcon size={12} /> {st.label}
            </span>
            <span style={{
              padding: '4px 12px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
              background: `${sevColor}15`, color: sevColor, border: `1px solid ${sevColor}30`,
              textTransform: 'uppercase',
            }}>{policy.severity}</span>
            <span style={{
              padding: '4px 12px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
              background: 'rgba(0,112,173,0.1)', color: '#0070AD', border: '1px solid rgba(0,112,173,0.2)',
            }}>{CATEGORY_LABELS[policy.policy_category] || policy.policy_category}</span>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          {policy.status === 'draft' && (
            <button
              onClick={handleSubmit}
              style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-xs)',
                padding: 'var(--space-sm) var(--space-lg)',
                background: 'linear-gradient(135deg, #0070AD, #12ABDB)',
                color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600,
              }}
            >
              <Send size={16} /> Submit for Approval
            </button>
          )}
          {policy.status === 'approved' && (
            <button
              onClick={handleLoadYaml}
              style={{
                display: 'flex', alignItems: 'center', gap: 'var(--space-xs)',
                padding: 'var(--space-sm) var(--space-lg)',
                background: 'var(--color-bg-tertiary)', color: 'var(--color-text-primary)',
                borderRadius: 'var(--radius-md)', fontWeight: 600,
              }}
            >
              <Code size={16} /> View YAML
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 'var(--space-lg)', borderBottom: '1px solid var(--color-border-default)' }}>
        {['overview', 'versions', 'audit', ...(yamlContent ? ['yaml'] : [])].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: 'var(--space-sm) var(--space-lg)', background: 'none',
              color: tab === t ? '#0070AD' : 'var(--color-text-tertiary)',
              fontWeight: tab === t ? 600 : 400, fontSize: '0.875rem',
              borderBottom: tab === t ? '2px solid #0070AD' : '2px solid transparent',
              textTransform: 'capitalize',
            }}
          >{t}</button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div key={tab} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {tab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 'var(--space-lg)' }}>
            <div>
              <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                <h4 style={{ marginBottom: 'var(--space-md)' }}>Policy Description</h4>
                <div style={{ fontSize: '0.9375rem', lineHeight: 1.8, color: 'var(--color-text-secondary)', whiteSpace: 'pre-wrap' }}>
                  {policy.description}
                </div>
              </div>
              {policy.remediation_guide && (
                <div className="card">
                  <h4 style={{ marginBottom: 'var(--space-md)' }}>Remediation Guide</h4>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8125rem', lineHeight: 1.6 }}>{policy.remediation_guide}</pre>
                </div>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
              <div className="card">
                <h5 style={{ marginBottom: 'var(--space-md)' }}>Metadata</h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--color-text-tertiary)' }}>UID</span>
                    <code style={{ fontSize: '0.7rem' }}>{policy.policy_uid?.slice(0, 8)}...</code>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--color-text-tertiary)' }}>Author</span>
                    <span>{policy.authored_by}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--color-text-tertiary)' }}>Scanner</span>
                    <span>{policy.scanner_hint}</span>
                  </div>
                  {policy.effective_date && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                      <span style={{ color: 'var(--color-text-tertiary)' }}>Effective</span>
                      <span>{policy.effective_date}</span>
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
                    <span style={{ color: 'var(--color-text-tertiary)' }}>Created</span>
                    <span>{policy.created_at ? new Date(policy.created_at).toLocaleDateString() : '—'}</span>
                  </div>
                </div>
              </div>
              <div className="card">
                <h5 style={{ marginBottom: 'var(--space-md)' }}>Affected Domains</h5>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)' }}>
                  {(Array.isArray(policy.affected_domains) ? policy.affected_domains : []).map(d => (
                    <span key={d} style={{
                      padding: '2px 10px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
                      background: 'rgba(0,112,173,0.1)', color: '#0070AD', border: '1px solid rgba(0,112,173,0.2)',
                    }}>{d}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {tab === 'versions' && (
          <div className="card">
            <h4 style={{ marginBottom: 'var(--space-md)' }}>Version History</h4>
            {policy.versions?.length === 0 ? (
              <p style={{ color: 'var(--color-text-tertiary)' }}>No version snapshots yet. Versions are created when a policy is approved or rejected.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {policy.versions?.map(v => (
                  <div key={v.id} style={{
                    padding: 'var(--space-md)', background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>v{v.version} — {v.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                        {v.status} by {v.approved_by || v.authored_by} on {v.created_at ? new Date(v.created_at).toLocaleString() : '—'}
                      </div>
                    </div>
                    <span style={{
                      padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600,
                      color: v.status === 'approved' ? '#10b981' : '#ef4444',
                      background: v.status === 'approved' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                      textTransform: 'uppercase',
                    }}>{v.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'audit' && (
          <div className="card">
            <h4 style={{ marginBottom: 'var(--space-md)' }}>Approval Audit Log</h4>
            {policy.approval_logs?.length === 0 ? (
              <p style={{ color: 'var(--color-text-tertiary)' }}>No audit entries yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {policy.approval_logs?.map(log => (
                  <div key={log.id} style={{
                    padding: 'var(--space-md)', background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                        <User size={14} style={{ color: 'var(--color-text-muted)' }} />
                        <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{log.actor_name}</span>
                        <span style={{
                          padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600,
                          background: log.action === 'approved' ? 'rgba(16,185,129,0.1)' : log.action === 'rejected' ? 'rgba(239,68,68,0.1)' : 'rgba(0,112,173,0.1)',
                          color: log.action === 'approved' ? '#10b981' : log.action === 'rejected' ? '#ef4444' : '#0070AD',
                          textTransform: 'uppercase',
                        }}>{log.action}</span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : '—'}
                      </span>
                    </div>
                    {log.comment && (
                      <div style={{ marginTop: 'var(--space-sm)', fontSize: '0.8125rem', color: 'var(--color-text-secondary)', paddingLeft: 28 }}>
                        {log.comment}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'yaml' && yamlContent && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)' }}>
            <div className="card">
              <h4 style={{ marginBottom: 'var(--space-md)' }}>YAML</h4>
              <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8125rem', lineHeight: 1.6, maxHeight: 600, overflowY: 'auto' }}>
                {yamlContent.yaml_content}
              </pre>
            </div>
            <div className="card">
              <h4 style={{ marginBottom: 'var(--space-md)' }}>JSON</h4>
              <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8125rem', lineHeight: 1.6, maxHeight: 600, overflowY: 'auto' }}>
                {yamlContent.json_content}
              </pre>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};
