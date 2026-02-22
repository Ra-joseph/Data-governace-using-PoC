import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, Shield, Search, CheckCircle, XCircle,
  RefreshCw, ChevronDown, ChevronUp, ArrowRight, Zap,
  GitMerge, Trash2, AlertOctagon, Eye
} from 'lucide-react';
import toast from 'react-hot-toast';
import { policyConflictsAPI } from '../../services/api';

const TYPE_COLORS = {
  overlap: { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6', label: 'Overlap' },
  contradiction: { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', label: 'Contradiction' },
  severity_mismatch: { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', label: 'Severity Mismatch' },
  redundancy: { bg: 'rgba(139, 92, 246, 0.15)', border: '#8b5cf6', label: 'Redundancy' },
};

const STRATEGY_LABELS = {
  keep_both: { label: 'Keep Both', icon: CheckCircle, color: '#10b981' },
  merge: { label: 'Merge', icon: GitMerge, color: '#3b82f6' },
  deprecate_one: { label: 'Deprecate One', icon: Trash2, color: '#f59e0b' },
  escalate: { label: 'Escalate', icon: AlertOctagon, color: '#ef4444' },
};

export const PolicyConflicts = () => {
  const [tab, setTab] = useState('detect');
  const [conflicts, setConflicts] = useState([]);
  const [stats, setStats] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [resolveForm, setResolveForm] = useState({ strategy: 'keep_both', notes: '', resolved_by: 'governance-admin' });
  const [expandedId, setExpandedId] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    loadConflicts();
    loadStats();
  }, []);

  const loadConflicts = async () => {
    try {
      const params = {};
      if (filterType) params.conflict_type = filterType;
      if (filterStatus) params.status = filterStatus;
      const { data } = await policyConflictsAPI.list(params);
      setConflicts(data.conflicts || []);
    } catch { /* empty list on error */ }
  };

  const loadStats = async () => {
    try {
      const { data } = await policyConflictsAPI.stats();
      setStats(data);
    } catch { /* ignore */ }
  };

  const runDetection = async () => {
    setScanning(true);
    try {
      const { data } = await policyConflictsAPI.detect();
      toast.success(`Scan complete: ${data.total_conflicts_found} conflicts detected`);
      await loadConflicts();
      await loadStats();
    } catch {
      toast.error('Detection failed');
    } finally {
      setScanning(false);
    }
  };

  const viewDetail = async (id) => {
    try {
      const { data } = await policyConflictsAPI.get(id);
      setSelectedConflict(data);
    } catch {
      toast.error('Failed to load conflict details');
    }
  };

  const resolveConflict = async (id) => {
    try {
      await policyConflictsAPI.resolve(id, {
        strategy: resolveForm.strategy,
        resolution_notes: resolveForm.notes,
        resolved_by: resolveForm.resolved_by,
      });
      toast.success('Conflict resolved');
      setSelectedConflict(null);
      setResolveForm({ strategy: 'keep_both', notes: '', resolved_by: 'governance-admin' });
      await loadConflicts();
      await loadStats();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Resolution failed');
    }
  };

  const tabs = [
    { id: 'detect', label: 'Detect & Scan', icon: Search },
    { id: 'conflicts', label: 'Conflict List', icon: AlertTriangle },
    { id: 'stats', label: 'Statistics', icon: Zap },
  ];

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto' }}>
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <AlertTriangle size={28} style={{ color: '#f59e0b' }} />
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#e8eaed', margin: 0 }}>Policy Conflicts</h1>
            <p style={{ color: '#9ca3af', margin: 0, fontSize: '0.9rem' }}>Detect and resolve overlapping or contradictory policies</p>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: '0.5rem 1rem', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: tab === t.id ? 'rgba(139,92,246,0.2)' : 'transparent',
              color: tab === t.id ? '#a78bfa' : '#9ca3af',
              display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', fontWeight: 500,
            }}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {/* Detect Tab */}
      {tab === 'detect' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div style={{
            background: 'rgba(15, 20, 25, 0.6)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 12, padding: '2rem', textAlign: 'center',
          }}>
            <Shield size={48} style={{ color: '#8b5cf6', marginBottom: '1rem' }} />
            <h2 style={{ color: '#e8eaed', marginBottom: '0.5rem' }}>Conflict Detection Scanner</h2>
            <p style={{ color: '#9ca3af', marginBottom: '1.5rem', maxWidth: 500, margin: '0 auto 1.5rem' }}>
              Scans all approved policies for overlaps, contradictions, severity mismatches, and redundancies across domains.
            </p>
            <button
              onClick={runDetection}
              disabled={scanning}
              style={{
                padding: '0.75rem 2rem', borderRadius: 8, border: 'none', cursor: scanning ? 'not-allowed' : 'pointer',
                background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', color: '#fff',
                fontSize: '1rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                opacity: scanning ? 0.7 : 1,
              }}
            >
              <RefreshCw size={18} className={scanning ? 'spinning' : ''} />
              {scanning ? 'Scanning...' : 'Run Conflict Detection'}
            </button>

            {stats && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '2rem' }}>
                {[
                  { label: 'Total Conflicts', value: stats.total_conflicts, color: '#e8eaed' },
                  { label: 'Open', value: stats.open, color: '#f59e0b' },
                  { label: 'Resolved', value: stats.resolved, color: '#10b981' },
                  { label: 'Resolution Rate', value: `${stats.resolution_rate_pct}%`, color: '#3b82f6' },
                ].map((s, i) => (
                  <div key={i} style={{
                    background: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: '1rem',
                  }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: s.color }}>{s.value}</div>
                    <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{s.label}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Conflicts List Tab */}
      {tab === 'conflicts' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Filters */}
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
            <select
              value={filterType}
              onChange={e => { setFilterType(e.target.value); }}
              style={{ padding: '0.5rem', borderRadius: 6, background: '#1a1f2e', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)' }}
            >
              <option value="">All Types</option>
              {Object.entries(TYPE_COLORS).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={e => { setFilterStatus(e.target.value); }}
              style={{ padding: '0.5rem', borderRadius: 6, background: '#1a1f2e', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)' }}
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
            </select>
            <button onClick={loadConflicts} style={{
              padding: '0.5rem 1rem', borderRadius: 6, border: '1px solid rgba(139,92,246,0.3)',
              background: 'transparent', color: '#a78bfa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem',
            }}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>

          {conflicts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
              <AlertTriangle size={40} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
              <p>No conflicts found. Run a detection scan first.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <AnimatePresence>
                {conflicts.map(c => {
                  const typeInfo = TYPE_COLORS[c.type] || TYPE_COLORS.overlap;
                  const isExpanded = expandedId === c.id;
                  return (
                    <motion.div
                      key={c.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      style={{
                        background: typeInfo.bg, border: `1px solid ${typeInfo.border}33`,
                        borderRadius: 10, padding: '1rem', borderLeft: `4px solid ${typeInfo.border}`,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                        onClick={() => setExpandedId(isExpanded ? null : c.id)}>
                        <div>
                          <span style={{
                            display: 'inline-block', padding: '2px 8px', borderRadius: 4,
                            fontSize: '0.75rem', fontWeight: 600, background: `${typeInfo.border}22`, color: typeInfo.border,
                            marginBottom: '0.25rem',
                          }}>{typeInfo.label}</span>
                          <span style={{
                            display: 'inline-block', padding: '2px 8px', borderRadius: 4, marginLeft: '0.5rem',
                            fontSize: '0.75rem', fontWeight: 600,
                            background: c.status === 'open' ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)',
                            color: c.status === 'open' ? '#f59e0b' : '#10b981',
                          }}>{c.status}</span>
                          <p style={{ color: '#e8eaed', margin: '0.25rem 0 0', fontSize: '0.9rem' }}>{c.description}</p>
                        </div>
                        {isExpanded ? <ChevronUp size={18} style={{ color: '#9ca3af' }} /> : <ChevronDown size={18} style={{ color: '#9ca3af' }} />}
                      </div>

                      {isExpanded && (
                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} style={{ marginTop: '1rem' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1rem', alignItems: 'center' }}>
                            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '0.75rem' }}>
                              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>Policy A</div>
                              <div style={{ color: '#e8eaed', fontWeight: 600 }}>{c.policy_a.title}</div>
                              <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Severity: {c.policy_a.severity}</div>
                            </div>
                            <ArrowRight size={20} style={{ color: '#6b7280' }} />
                            <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '0.75rem' }}>
                              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>Policy B</div>
                              <div style={{ color: '#e8eaed', fontWeight: 600 }}>{c.policy_b.title}</div>
                              <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Severity: {c.policy_b.severity}</div>
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                            <button onClick={() => viewDetail(c.id)} style={{
                              padding: '0.4rem 0.75rem', borderRadius: 6, border: '1px solid rgba(139,92,246,0.3)',
                              background: 'transparent', color: '#a78bfa', cursor: 'pointer', fontSize: '0.8rem',
                              display: 'flex', alignItems: 'center', gap: '0.3rem',
                            }}>
                              <Eye size={14} /> View Detail
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </motion.div>
      )}

      {/* Stats Tab */}
      {tab === 'stats' && stats && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            {/* Type Distribution */}
            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>By Conflict Type</h3>
              {Object.entries(stats.by_type || {}).map(([type, count]) => {
                const info = TYPE_COLORS[type] || TYPE_COLORS.overlap;
                return (
                  <div key={type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ color: info.border, fontSize: '0.9rem' }}>{info.label}</span>
                    <span style={{ color: '#e8eaed', fontWeight: 600 }}>{count}</span>
                  </div>
                );
              })}
              {Object.keys(stats.by_type || {}).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No conflicts detected</p>}
            </div>

            {/* Domain Distribution */}
            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>By Domain</h3>
              {Object.entries(stats.by_domain || {}).map(([domain, count]) => (
                <div key={domain} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ color: '#9ca3af', fontSize: '0.9rem' }}>{domain}</span>
                  <span style={{ color: '#e8eaed', fontWeight: 600 }}>{count}</span>
                </div>
              ))}
              {Object.keys(stats.by_domain || {}).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No domains affected</p>}
            </div>

            {/* Resolution Strategies */}
            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Resolution Strategies Used</h3>
              {Object.entries(stats.resolution_strategies || {}).map(([strategy, count]) => {
                const info = STRATEGY_LABELS[strategy] || STRATEGY_LABELS.keep_both;
                return (
                  <div key={strategy} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ color: info.color, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <info.icon size={14} /> {info.label}
                    </span>
                    <span style={{ color: '#e8eaed', fontWeight: 600 }}>{count}</span>
                  </div>
                );
              })}
              {Object.keys(stats.resolution_strategies || {}).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No resolutions yet</p>}
            </div>

            {/* Severity Mismatches */}
            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Severity Mismatches</h3>
              {(stats.severity_mismatches || []).map((m, i) => (
                <div key={i} style={{ marginBottom: '0.75rem', padding: '0.5rem', background: 'rgba(245,158,11,0.08)', borderRadius: 6 }}>
                  <div style={{ color: '#e8eaed', fontSize: '0.85rem' }}>{m.policy_a} ({m.severity_a})</div>
                  <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>vs</div>
                  <div style={{ color: '#e8eaed', fontSize: '0.85rem' }}>{m.policy_b} ({m.severity_b})</div>
                </div>
              ))}
              {(stats.severity_mismatches || []).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No severity mismatches</p>}
            </div>
          </div>
        </motion.div>
      )}

      {/* Conflict Detail Modal */}
      {selectedConflict && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000,
        }} onClick={() => setSelectedConflict(null)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            style={{
              background: '#1a1f2e', borderRadius: 16, padding: '2rem', maxWidth: 600, width: '90%',
              border: '1px solid rgba(255,255,255,0.1)', maxHeight: '80vh', overflowY: 'auto',
            }}
            onClick={e => e.stopPropagation()}
          >
            <h2 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Conflict Detail #{selectedConflict.id}</h2>
            <p style={{ color: '#9ca3af', marginBottom: '1rem' }}>{selectedConflict.description}</p>

            {/* Recommendation */}
            {selectedConflict.recommendation && (
              <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
                <div style={{ color: '#a78bfa', fontWeight: 600, marginBottom: '0.25rem' }}>Recommendation: {selectedConflict.recommendation.strategy}</div>
                <p style={{ color: '#9ca3af', fontSize: '0.85rem', margin: '0.25rem 0' }}>{selectedConflict.recommendation.reason}</p>
                <p style={{ color: '#e8eaed', fontSize: '0.85rem', margin: '0.25rem 0' }}>{selectedConflict.recommendation.action}</p>
              </div>
            )}

            {/* Resolve Form */}
            {selectedConflict.status === 'open' && (
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1rem', marginTop: '1rem' }}>
                <h3 style={{ color: '#e8eaed', marginBottom: '0.75rem' }}>Resolve Conflict</h3>
                <div style={{ marginBottom: '0.75rem' }}>
                  <label style={{ color: '#9ca3af', fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>Strategy</label>
                  <select
                    value={resolveForm.strategy}
                    onChange={e => setResolveForm(f => ({ ...f, strategy: e.target.value }))}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)' }}
                  >
                    {Object.entries(STRATEGY_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v.label}</option>
                    ))}
                  </select>
                </div>
                <div style={{ marginBottom: '0.75rem' }}>
                  <label style={{ color: '#9ca3af', fontSize: '0.85rem', display: 'block', marginBottom: '0.25rem' }}>Resolution Notes</label>
                  <textarea
                    value={resolveForm.notes}
                    onChange={e => setResolveForm(f => ({ ...f, notes: e.target.value }))}
                    rows={3}
                    style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)', resize: 'vertical' }}
                    placeholder="Explain the resolution decision..."
                  />
                </div>
                <button
                  onClick={() => resolveConflict(selectedConflict.id)}
                  disabled={!resolveForm.notes.trim()}
                  style={{
                    padding: '0.5rem 1.5rem', borderRadius: 8, border: 'none',
                    background: resolveForm.notes.trim() ? 'linear-gradient(135deg, #10b981, #059669)' : '#374151',
                    color: '#fff', cursor: resolveForm.notes.trim() ? 'pointer' : 'not-allowed',
                    fontWeight: 600, fontSize: '0.9rem',
                  }}
                >
                  Resolve Conflict
                </button>
              </div>
            )}

            {selectedConflict.status === 'resolved' && selectedConflict.resolution && (
              <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 8, padding: '1rem' }}>
                <div style={{ color: '#10b981', fontWeight: 600 }}>Resolved: {selectedConflict.resolution.strategy}</div>
                <p style={{ color: '#9ca3af', fontSize: '0.85rem', margin: '0.25rem 0' }}>{selectedConflict.resolution.notes}</p>
                <p style={{ color: '#6b7280', fontSize: '0.8rem' }}>By {selectedConflict.resolution.resolved_by} at {selectedConflict.resolution.resolved_at}</p>
              </div>
            )}

            <button onClick={() => setSelectedConflict(null)} style={{
              marginTop: '1rem', padding: '0.4rem 1rem', borderRadius: 6,
              border: '1px solid rgba(255,255,255,0.2)', background: 'transparent',
              color: '#9ca3af', cursor: 'pointer',
            }}>Close</button>
          </motion.div>
        </div>
      )}
    </div>
  );
};
