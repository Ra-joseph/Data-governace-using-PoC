import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock, CheckCircle, XCircle, AlertTriangle, Send, Edit3,
  Archive, GitBranch, ChevronDown, ChevronRight, ArrowLeft, RefreshCw
} from 'lucide-react';
import { policyAuthoringAPI } from '../../services/api';
import toast from 'react-hot-toast';

const EVENT_CONFIG = {
  created:    { icon: Edit3,       color: '#3b82f6', label: 'Created' },
  submitted:  { icon: Send,        color: '#0070AD', label: 'Submitted' },
  approved:   { icon: CheckCircle, color: '#10b981', label: 'Approved' },
  rejected:   { icon: XCircle,     color: '#ef4444', label: 'Rejected' },
  revised:    { icon: RefreshCw,   color: '#f59e0b', label: 'Revised' },
  deprecated: { icon: Archive,     color: '#6b7280', label: 'Deprecated' },
};

export const PolicyTimeline = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [timeline, setTimeline] = useState(null);
  const [versions, setVersions] = useState(null);
  const [expandedVersion, setExpandedVersion] = useState(null);
  const [diffData, setDiffData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [timelineRes, versionsRes] = await Promise.all([
        policyAuthoringAPI.getTimeline(id),
        policyAuthoringAPI.getVersions(id),
      ]);
      setTimeline(timelineRes.data);
      setVersions(versionsRes.data);
    } catch (error) {
      toast.error('Failed to load policy history');
    } finally {
      setLoading(false);
    }
  };

  const loadDiff = async (version) => {
    if (diffData[version]) {
      setExpandedVersion(expandedVersion === version ? null : version);
      return;
    }
    try {
      const res = await policyAuthoringAPI.getVersionDiff(id, version);
      setDiffData(prev => ({ ...prev, [version]: res.data }));
      setExpandedVersion(version);
    } catch {
      toast.error('Failed to load version diff');
    }
  };

  const handleRevise = async () => {
    try {
      await policyAuthoringAPI.revise(id);
      toast.success('New revision created');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create revision');
    }
  };

  const handleDeprecate = async () => {
    try {
      await policyAuthoringAPI.deprecate(id, { approver_name: 'Data Governance Admin' });
      toast.success('Policy deprecated');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to deprecate policy');
    }
  };

  if (loading || !timeline) {
    return (
      <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
        Loading policy history...
      </div>
    );
  }

  return (
    <div style={{ padding: 'var(--space-xl)', maxWidth: 960, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)' }}>
        <button onClick={() => navigate(`/policy-authoring/${id}`)} style={{
          background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-secondary)',
          display: 'flex', alignItems: 'center', gap: 4,
        }}>
          <ArrowLeft size={18} /> Back
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-xl)' }}>
        <div>
          <h2 style={{ margin: 0 }}>{timeline.title}</h2>
          <div style={{ display: 'flex', gap: 'var(--space-sm)', alignItems: 'center', marginTop: 'var(--space-xs)' }}>
            <span style={{
              padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 700,
              textTransform: 'uppercase',
              background: (EVENT_CONFIG[timeline.current_status]?.color || '#9ca3af') + '20',
              color: EVENT_CONFIG[timeline.current_status]?.color || '#9ca3af',
            }}>{timeline.current_status}</span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
              v{timeline.current_version} &middot; {timeline.total_events} events
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          {(timeline.current_status === 'approved' || timeline.current_status === 'rejected') && (
            <button onClick={handleRevise} style={{
              padding: '6px 14px', fontSize: '0.8125rem', fontWeight: 600,
              background: 'rgba(245,158,11,0.1)', color: '#f59e0b',
              borderRadius: 'var(--radius-md)', border: '1px solid rgba(245,158,11,0.2)',
              cursor: 'pointer',
            }}>
              <RefreshCw size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
              Revise
            </button>
          )}
          {timeline.current_status === 'approved' && (
            <button onClick={handleDeprecate} style={{
              padding: '6px 14px', fontSize: '0.8125rem', fontWeight: 600,
              background: 'rgba(107,114,128,0.1)', color: '#6b7280',
              borderRadius: 'var(--radius-md)', border: '1px solid rgba(107,114,128,0.2)',
              cursor: 'pointer',
            }}>
              <Archive size={14} style={{ marginRight: 4, verticalAlign: -2 }} />
              Deprecate
            </button>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <h4 style={{ marginBottom: 'var(--space-lg)' }}>
          <Clock size={16} style={{ marginRight: 6, verticalAlign: -3 }} />
          Audit Timeline
        </h4>
        <div style={{ position: 'relative', paddingLeft: 32 }}>
          {/* Vertical line */}
          <div style={{
            position: 'absolute', left: 11, top: 6, bottom: 6, width: 2,
            background: 'var(--color-border)',
          }} />

          {timeline.events.map((event, i) => {
            const cfg = EVENT_CONFIG[event.type] || EVENT_CONFIG.created;
            const Icon = cfg.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                style={{ position: 'relative', marginBottom: 'var(--space-lg)' }}
              >
                <div style={{
                  position: 'absolute', left: -32, top: 0,
                  width: 24, height: 24, borderRadius: '50%',
                  background: `${cfg.color}20`, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  border: `2px solid ${cfg.color}`,
                  zIndex: 1,
                }}>
                  <Icon size={12} style={{ color: cfg.color }} />
                </div>

                <div style={{ paddingLeft: 'var(--space-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontWeight: 600, fontSize: '0.875rem', color: cfg.color }}>{cfg.label}</span>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginLeft: 8 }}>
                        by {event.actor}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'}
                    </span>
                  </div>
                  {event.detail && (
                    <p style={{ margin: '4px 0 0', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                      {event.detail}
                    </p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Version History with Diffs */}
      {versions && versions.versions.length > 0 && (
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>
            <GitBranch size={16} style={{ marginRight: 6, verticalAlign: -3 }} />
            Version History ({versions.total_versions} versions)
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {versions.versions.map(v => {
              const isExpanded = expandedVersion === v.version;
              const diff = diffData[v.version];
              const statusColor = v.status === 'approved' ? '#10b981' : v.status === 'rejected' ? '#ef4444' : '#9ca3af';
              return (
                <div key={v.version}>
                  <div
                    onClick={() => loadDiff(v.version)}
                    style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: 'var(--space-sm) var(--space-md)',
                      background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)',
                      cursor: 'pointer', transition: 'background 0.15s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>v{v.version}</span>
                      <span style={{
                        padding: '1px 6px', borderRadius: 9999, fontSize: '0.65rem', fontWeight: 700,
                        background: `${statusColor}15`, color: statusColor, textTransform: 'uppercase',
                      }}>{v.status}</span>
                      {v.approved_by && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          by {v.approved_by}
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                      {v.has_artifact && (
                        <span style={{
                          padding: '1px 6px', borderRadius: 4, fontSize: '0.6rem', fontWeight: 700,
                          background: 'rgba(139,92,246,0.1)', color: '#8b5cf6',
                        }}>YAML</span>
                      )}
                      <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {v.created_at ? new Date(v.created_at).toLocaleDateString() : '—'}
                      </span>
                    </div>
                  </div>

                  <AnimatePresence>
                    {isExpanded && diff && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{
                          padding: 'var(--space-md)',
                          borderLeft: '2px solid var(--color-border)',
                          marginLeft: 'var(--space-lg)',
                          marginTop: 4,
                        }}>
                          {diff.changes.length === 0 ? (
                            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem', margin: 0 }}>
                              Initial version — no previous version to compare.
                            </p>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
                              <p style={{ margin: '0 0 8px', fontSize: '0.8125rem', fontWeight: 600 }}>
                                {diff.changes.length} field(s) changed from v{diff.compared_to || 0}
                              </p>
                              {diff.changes.map((c, ci) => (
                                <div key={ci} style={{
                                  padding: '6px 10px', borderRadius: 'var(--radius-sm)',
                                  background: 'var(--color-bg-secondary)', fontSize: '0.8125rem',
                                }}>
                                  <span style={{ fontWeight: 600, color: '#0070AD' }}>{c.field}</span>
                                  {c.old_value != null && (
                                    <span style={{ color: '#ef4444', margin: '0 6px' }}>
                                      - {typeof c.old_value === 'object' ? JSON.stringify(c.old_value) : String(c.old_value)}
                                    </span>
                                  )}
                                  <span style={{ color: '#10b981' }}>
                                    + {typeof c.new_value === 'object' ? JSON.stringify(c.new_value) : String(c.new_value)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
