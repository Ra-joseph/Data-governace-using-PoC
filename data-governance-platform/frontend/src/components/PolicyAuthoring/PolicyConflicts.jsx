import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle, XCircle, RefreshCw, ChevronDown, ChevronUp, Zap,
  ShieldCheck, ShieldX, FileWarning, Send, Clock, Lock, Unlock
} from 'lucide-react';
import toast from 'react-hot-toast';
import { policyExceptionsAPI } from '../../services/api';

const SEVERITY_COLORS = {
  CRITICAL: { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444' },
  WARNING: { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
  INFO: { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6' },
};

const STATUS_BADGES = {
  pending_review: { bg: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', label: 'Pending Review' },
  approved: { bg: 'rgba(16, 185, 129, 0.2)', color: '#10b981', label: 'Approved' },
  rejected: { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', label: 'Rejected' },
};

export const PolicyConflicts = () => {
  const [tab, setTab] = useState('failures');
  const [failures, setFailures] = useState([]);
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [gateResult, setGateResult] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [gateDomain, setGateDomain] = useState('');

  // Exception request form
  const [showExceptionForm, setShowExceptionForm] = useState(null);
  const [exceptionForm, setExceptionForm] = useState({
    justification: '', business_impact: '', requested_by: 'domain-owner', requested_duration_days: 90,
  });

  // Board decision form
  const [showDecisionForm, setShowDecisionForm] = useState(null);
  const [decisionComments, setDecisionComments] = useState('');

  useEffect(() => {
    loadFailures();
    loadRequests();
    loadStats();
  }, []);

  const loadFailures = async () => {
    try {
      const { data } = await policyExceptionsAPI.listFailures();
      setFailures(data.failures || []);
    } catch { /* empty */ }
  };

  const loadRequests = async () => {
    try {
      const { data } = await policyExceptionsAPI.listRequests();
      setRequests(data.requests || []);
    } catch { /* empty */ }
  };

  const loadStats = async () => {
    try {
      const { data } = await policyExceptionsAPI.stats();
      setStats(data);
    } catch { /* empty */ }
  };

  const runScan = async () => {
    setScanning(true);
    try {
      const { data } = await policyExceptionsAPI.detectFailures();
      toast.success(`Scan complete: ${data.total_failures} failure(s) found across ${data.policies_scanned} policies`);
      await loadFailures();
      await loadStats();
    } catch {
      toast.error('Failure scan failed');
    } finally {
      setScanning(false);
    }
  };

  const raiseException = async (failure) => {
    try {
      await policyExceptionsAPI.createException({
        failure_id: failure.failure_id,
        domain: failure.domain,
        policy_id: failure.policy_id,
        policy_title: failure.policy_title,
        justification: exceptionForm.justification,
        business_impact: exceptionForm.business_impact,
        requested_by: exceptionForm.requested_by,
        requested_duration_days: exceptionForm.requested_duration_days,
      });
      toast.success('Exception request raised – awaiting board review');
      setShowExceptionForm(null);
      setExceptionForm({ justification: '', business_impact: '', requested_by: 'domain-owner', requested_duration_days: 90 });
      await loadFailures();
      await loadRequests();
      await loadStats();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create exception');
    }
  };

  const handleDecision = async (reqId, action) => {
    try {
      const method = action === 'approve' ? policyExceptionsAPI.approve : policyExceptionsAPI.reject;
      await method(reqId, { decided_by: 'advisory-board', comments: decisionComments });
      toast.success(`Exception ${action}d`);
      setShowDecisionForm(null);
      setDecisionComments('');
      await loadRequests();
      await loadFailures();
      await loadStats();
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to ${action}`);
    }
  };

  const checkGate = async () => {
    if (!gateDomain.trim()) return;
    try {
      const { data } = await policyExceptionsAPI.deploymentGate(gateDomain.trim());
      setGateResult(data);
    } catch {
      toast.error('Gate check failed');
    }
  };

  const tabs = [
    { id: 'failures', label: 'Policy Failures', icon: FileWarning },
    { id: 'requests', label: 'Exception Requests', icon: Send },
    { id: 'gate', label: 'Deployment Gate', icon: Lock },
    { id: 'stats', label: 'Overview', icon: Zap },
  ];

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto' }}>
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <ShieldX size={28} style={{ color: '#ef4444' }} />
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#e8eaed', margin: 0 }}>Policy Exceptions</h1>
            <p style={{ color: '#9ca3af', margin: 0, fontSize: '0.9rem' }}>
              Manage policy failures, raise exceptions, and control the deployment gate
            </p>
          </div>
          <button onClick={runScan} disabled={scanning} style={{
            marginLeft: 'auto', padding: '0.5rem 1.25rem', borderRadius: 8, border: 'none',
            background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', color: '#fff', cursor: scanning ? 'not-allowed' : 'pointer',
            fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.4rem', opacity: scanning ? 0.7 : 1,
          }}>
            <RefreshCw size={16} className={scanning ? 'spinning' : ''} />
            {scanning ? 'Scanning...' : 'Scan Policies'}
          </button>
        </div>
      </motion.div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: '0.5rem 1rem', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: tab === t.id ? 'rgba(139,92,246,0.2)' : 'transparent',
            color: tab === t.id ? '#a78bfa' : '#9ca3af',
            display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', fontWeight: 500,
          }}>
            <t.icon size={16} /> {t.label}
            {t.id === 'requests' && requests.filter(r => r.status === 'pending_review').length > 0 && (
              <span style={{
                background: '#f59e0b', color: '#000', borderRadius: '50%', width: 18, height: 18,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700,
              }}>
                {requests.filter(r => r.status === 'pending_review').length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Failures Tab ── */}
      {tab === 'failures' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {failures.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
              <ShieldCheck size={48} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
              <p>No policy failures detected. Run a scan to check.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {failures.map(f => {
                const sev = SEVERITY_COLORS[f.severity] || SEVERITY_COLORS.WARNING;
                const isExpanded = expandedId === f.failure_id;
                return (
                  <motion.div key={f.failure_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: sev.bg, border: `1px solid ${sev.border}33`, borderRadius: 10, padding: '1rem', borderLeft: `4px solid ${sev.border}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
                      onClick={() => setExpandedId(isExpanded ? null : f.failure_id)}>
                      <div>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
                          <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: '0.75rem', fontWeight: 600, background: `${sev.border}22`, color: sev.border }}>{f.severity}</span>
                          <span style={{ color: '#9ca3af', fontSize: '0.8rem' }}>{f.domain}</span>
                          {f.exception_status && (
                            <span style={{ background: STATUS_BADGES[f.exception_status]?.bg, color: STATUS_BADGES[f.exception_status]?.color, padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 600 }}>
                              {STATUS_BADGES[f.exception_status]?.label}
                            </span>
                          )}
                        </div>
                        <p style={{ color: '#e8eaed', margin: 0, fontSize: '0.95rem', fontWeight: 500 }}>{f.policy_title}</p>
                        <p style={{ color: '#9ca3af', margin: '0.15rem 0 0', fontSize: '0.8rem' }}>
                          {f.total_failing} contract(s) failing · {f.policy_category}
                        </p>
                      </div>
                      {isExpanded ? <ChevronUp size={18} style={{ color: '#9ca3af' }} /> : <ChevronDown size={18} style={{ color: '#9ca3af' }} />}
                    </div>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                          style={{ marginTop: '0.75rem' }}>
                          <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '0.75rem', marginBottom: '0.75rem' }}>
                            <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginBottom: '0.5rem' }}>Failing Contracts</div>
                            {(f.failing_contracts || []).map((c, i) => (
                              <div key={i} style={{ marginBottom: '0.5rem', padding: '0.4rem 0.6rem', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
                                <span style={{ color: '#e8eaed', fontSize: '0.85rem' }}>Contract #{c.contract_id}</span>
                                <span style={{ color: '#6b7280', fontSize: '0.8rem', marginLeft: '0.5rem' }}>{c.violation_count} violation(s)</span>
                                {(c.violations || []).map((v, j) => (
                                  <div key={j} style={{ color: '#9ca3af', fontSize: '0.75rem', marginLeft: '1rem' }}>
                                    {v.field}: {v.message}
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>

                          {(!f.exception_status || f.exception_status === 'rejected') && (
                            <button onClick={(e) => { e.stopPropagation(); setShowExceptionForm(f); }} style={{
                              padding: '0.4rem 1rem', borderRadius: 6, border: '1px solid rgba(245,158,11,0.4)',
                              background: 'rgba(245,158,11,0.1)', color: '#f59e0b', cursor: 'pointer', fontSize: '0.85rem',
                              display: 'flex', alignItems: 'center', gap: '0.4rem',
                            }}>
                              <Send size={14} /> {f.exception_status === 'rejected' ? 'Re-raise Exception' : 'Raise Exception'}
                            </button>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </div>
          )}
        </motion.div>
      )}

      {/* ── Requests Tab (Board Approval Queue) ── */}
      {tab === 'requests' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {requests.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
              <Clock size={48} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
              <p>No exception requests yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {requests.map(r => {
                const badge = STATUS_BADGES[r.status] || STATUS_BADGES.pending_review;
                return (
                  <div key={r.id} style={{
                    background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10,
                    padding: '1rem', borderLeft: `4px solid ${badge.color}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.25rem' }}>
                          <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: '0.75rem', fontWeight: 600, background: badge.bg, color: badge.color }}>{badge.label}</span>
                          <span style={{ color: '#6b7280', fontSize: '0.8rem' }}>#{r.id}</span>
                        </div>
                        <p style={{ color: '#e8eaed', margin: '0.25rem 0 0', fontWeight: 500 }}>{r.policy_title}</p>
                        <p style={{ color: '#9ca3af', fontSize: '0.85rem', margin: '0.15rem 0' }}>Domain: {r.domain} · Duration: {r.requested_duration_days} days</p>
                      </div>
                    </div>

                    <div style={{ marginTop: '0.75rem', background: 'rgba(0,0,0,0.2)', borderRadius: 8, padding: '0.75rem' }}>
                      <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Justification</div>
                      <p style={{ color: '#e8eaed', fontSize: '0.85rem', margin: '0.25rem 0' }}>{r.justification}</p>
                      <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.5rem' }}>Business Impact</div>
                      <p style={{ color: '#e8eaed', fontSize: '0.85rem', margin: '0.25rem 0' }}>{r.business_impact}</p>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.5rem' }}>
                        Requested by {r.requested_by} · {new Date(r.created_at).toLocaleString()}
                      </div>
                    </div>

                    {r.decision && (
                      <div style={{
                        marginTop: '0.5rem', padding: '0.5rem 0.75rem', borderRadius: 6,
                        background: r.status === 'approved' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                        border: `1px solid ${r.status === 'approved' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                      }}>
                        <div style={{ color: r.status === 'approved' ? '#10b981' : '#ef4444', fontWeight: 600, fontSize: '0.85rem' }}>
                          {r.decision.action === 'approved' ? 'Approved' : 'Rejected'} by {r.decision.decided_by}
                        </div>
                        <p style={{ color: '#9ca3af', fontSize: '0.8rem', margin: '0.15rem 0 0' }}>{r.decision.comments}</p>
                      </div>
                    )}

                    {r.status === 'pending_review' && (
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                        <button onClick={() => { setShowDecisionForm({ ...r, action: 'approve' }); setDecisionComments(''); }} style={{
                          padding: '0.4rem 1rem', borderRadius: 6, border: 'none',
                          background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', cursor: 'pointer',
                          fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.3rem',
                        }}>
                          <CheckCircle size={14} /> Approve
                        </button>
                        <button onClick={() => { setShowDecisionForm({ ...r, action: 'reject' }); setDecisionComments(''); }} style={{
                          padding: '0.4rem 1rem', borderRadius: 6, border: '1px solid rgba(239,68,68,0.4)',
                          background: 'transparent', color: '#ef4444', cursor: 'pointer',
                          fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.3rem',
                        }}>
                          <XCircle size={14} /> Reject
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </motion.div>
      )}

      {/* ── Deployment Gate Tab ── */}
      {tab === 'gate' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '2rem' }}>
            <h2 style={{ color: '#e8eaed', marginBottom: '0.5rem' }}>Deployment Gate Check</h2>
            <p style={{ color: '#9ca3af', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
              Enter a domain name to check whether it may deploy. A domain is allowed only if all
              policy failures have approved exceptions or have been fixed.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
              <input value={gateDomain} onChange={e => setGateDomain(e.target.value)}
                placeholder="e.g. finance" onKeyDown={e => e.key === 'Enter' && checkGate()}
                style={{ flex: 1, padding: '0.5rem 0.75rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)' }} />
              <button onClick={checkGate} style={{
                padding: '0.5rem 1.25rem', borderRadius: 6, border: 'none',
                background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', color: '#fff', cursor: 'pointer', fontWeight: 600,
              }}>Check Gate</button>
            </div>

            {gateResult && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div style={{
                  background: gateResult.allowed ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                  border: `2px solid ${gateResult.allowed ? '#10b981' : '#ef4444'}`,
                  borderRadius: 12, padding: '1.5rem', textAlign: 'center',
                }}>
                  {gateResult.allowed
                    ? <Unlock size={40} style={{ color: '#10b981', marginBottom: '0.5rem' }} />
                    : <Lock size={40} style={{ color: '#ef4444', marginBottom: '0.5rem' }} />}
                  <h3 style={{ color: gateResult.allowed ? '#10b981' : '#ef4444', margin: '0.25rem 0' }}>
                    {gateResult.allowed ? 'DEPLOY ALLOWED' : 'DEPLOY BLOCKED'}
                  </h3>
                  <p style={{ color: '#9ca3af', fontSize: '0.9rem' }}>{gateResult.reason}</p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginTop: '1rem' }}>
                  {[
                    { label: 'Total Failures', value: gateResult.total_failures, color: '#e8eaed' },
                    { label: 'Approved', value: gateResult.approved_exceptions, color: '#10b981' },
                    { label: 'Pending', value: gateResult.pending_exceptions, color: '#f59e0b' },
                    { label: 'Rejected', value: gateResult.rejected_exceptions, color: '#ef4444' },
                  ].map((s, i) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: '0.75rem', textAlign: 'center' }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: s.color }}>{s.value}</div>
                      <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                {gateResult.blockers?.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <h4 style={{ color: '#e8eaed', marginBottom: '0.5rem' }}>Blockers</h4>
                    {gateResult.blockers.map((b, i) => (
                      <div key={i} style={{
                        padding: '0.5rem 0.75rem', borderRadius: 6, marginBottom: '0.4rem',
                        background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)',
                      }}>
                        <span style={{ color: '#e8eaed', fontSize: '0.85rem', fontWeight: 500 }}>{b.policy_title}</span>
                        <span style={{ color: '#9ca3af', fontSize: '0.8rem', marginLeft: '0.5rem' }}>({b.severity})</span>
                        <p style={{ color: '#f87171', fontSize: '0.8rem', margin: '0.15rem 0 0' }}>{b.reason}</p>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </motion.div>
      )}

      {/* ── Stats Tab ── */}
      {tab === 'stats' && stats && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            {[
              { label: 'Total Failures', value: stats.total_failures, color: '#ef4444' },
              { label: 'Total Exceptions', value: stats.total_exceptions, color: '#f59e0b' },
              { label: 'Approval Rate', value: `${stats.approval_rate_pct}%`, color: '#10b981' },
            ].map((s, i) => (
              <div key={i} style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem', textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: '0.85rem', color: '#9ca3af' }}>{s.label}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Exception Status</h3>
              {[
                { label: 'Pending Review', value: stats.pending_review, color: '#f59e0b' },
                { label: 'Approved', value: stats.approved, color: '#10b981' },
                { label: 'Rejected', value: stats.rejected, color: '#ef4444' },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: item.color }}>{item.label}</span>
                  <span style={{ color: '#e8eaed', fontWeight: 600 }}>{item.value}</span>
                </div>
              ))}
            </div>

            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Failures by Domain</h3>
              {Object.entries(stats.failures_by_domain || {}).map(([domain, count]) => (
                <div key={domain} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: '#9ca3af' }}>{domain}</span>
                  <span style={{ color: '#e8eaed', fontWeight: 600 }}>{count}</span>
                </div>
              ))}
              {Object.keys(stats.failures_by_domain || {}).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>No failures</p>}
            </div>

            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Deployable Domains</h3>
              {(stats.domains_deployable || []).map(d => (
                <div key={d} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
                  <Unlock size={14} style={{ color: '#10b981' }} /> <span style={{ color: '#10b981' }}>{d}</span>
                </div>
              ))}
              {(stats.domains_deployable || []).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.85rem' }}>None</p>}
            </div>
            <div style={{ background: 'rgba(15,20,25,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '1.5rem' }}>
              <h3 style={{ color: '#e8eaed', marginBottom: '1rem' }}>Blocked Domains</h3>
              {(stats.domains_blocked || []).map(d => (
                <div key={d} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
                  <Lock size={14} style={{ color: '#ef4444' }} /> <span style={{ color: '#ef4444' }}>{d}</span>
                </div>
              ))}
              {(stats.domains_blocked || []).length === 0 && <p style={{ color: '#6b7280', fontSize: '0.85rem' }}>None</p>}
            </div>
          </div>
        </motion.div>
      )}

      {/* ── Exception Request Modal ── */}
      {showExceptionForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
          onClick={() => setShowExceptionForm(null)}>
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            style={{ background: '#1a1f2e', borderRadius: 16, padding: '2rem', maxWidth: 550, width: '90%', border: '1px solid rgba(255,255,255,0.1)' }}
            onClick={e => e.stopPropagation()}>
            <h2 style={{ color: '#e8eaed', marginBottom: '0.5rem' }}>Raise Exception Request</h2>
            <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginBottom: '1rem' }}>
              Policy: <strong style={{ color: '#e8eaed' }}>{showExceptionForm.policy_title}</strong> · Domain: {showExceptionForm.domain}
            </p>

            <label style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Business Justification *</label>
            <textarea value={exceptionForm.justification} onChange={e => setExceptionForm(f => ({ ...f, justification: e.target.value }))}
              rows={3} placeholder="Why does the domain need to deploy despite this failure?"
              style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)', resize: 'vertical', marginBottom: '0.75rem' }} />

            <label style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Business Impact *</label>
            <textarea value={exceptionForm.business_impact} onChange={e => setExceptionForm(f => ({ ...f, business_impact: e.target.value }))}
              rows={2} placeholder="What is the impact if deployment is blocked?"
              style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)', resize: 'vertical', marginBottom: '0.75rem' }} />

            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Requested By</label>
                <input value={exceptionForm.requested_by} onChange={e => setExceptionForm(f => ({ ...f, requested_by: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)' }} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Duration (days)</label>
                <input type="number" value={exceptionForm.requested_duration_days} onChange={e => setExceptionForm(f => ({ ...f, requested_duration_days: parseInt(e.target.value) || 90 }))}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)' }} />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={() => raiseException(showExceptionForm)}
                disabled={!exceptionForm.justification.trim() || !exceptionForm.business_impact.trim()}
                style={{
                  padding: '0.5rem 1.5rem', borderRadius: 8, border: 'none',
                  background: exceptionForm.justification.trim() && exceptionForm.business_impact.trim() ? 'linear-gradient(135deg, #f59e0b, #d97706)' : '#374151',
                  color: '#fff', cursor: exceptionForm.justification.trim() && exceptionForm.business_impact.trim() ? 'pointer' : 'not-allowed', fontWeight: 600,
                }}>
                Submit Exception Request
              </button>
              <button onClick={() => setShowExceptionForm(null)} style={{
                padding: '0.5rem 1rem', borderRadius: 6, border: '1px solid rgba(255,255,255,0.2)', background: 'transparent', color: '#9ca3af', cursor: 'pointer',
              }}>Cancel</button>
            </div>
          </motion.div>
        </div>
      )}

      {/* ── Board Decision Modal ── */}
      {showDecisionForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
          onClick={() => setShowDecisionForm(null)}>
          <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            style={{ background: '#1a1f2e', borderRadius: 16, padding: '2rem', maxWidth: 500, width: '90%', border: '1px solid rgba(255,255,255,0.1)' }}
            onClick={e => e.stopPropagation()}>
            <h2 style={{ color: '#e8eaed', marginBottom: '0.5rem' }}>
              {showDecisionForm.action === 'approve' ? 'Approve' : 'Reject'} Exception #{showDecisionForm.id}
            </h2>
            <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginBottom: '1rem' }}>{showDecisionForm.policy_title}</p>

            <label style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Board Comments *</label>
            <textarea value={decisionComments} onChange={e => setDecisionComments(e.target.value)}
              rows={3} placeholder="Provide reasoning for this decision..."
              style={{ width: '100%', padding: '0.5rem', borderRadius: 6, background: '#0f1419', color: '#e8eaed', border: '1px solid rgba(255,255,255,0.15)', resize: 'vertical', marginBottom: '1rem' }} />

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={() => handleDecision(showDecisionForm.id, showDecisionForm.action)}
                disabled={!decisionComments.trim()}
                style={{
                  padding: '0.5rem 1.5rem', borderRadius: 8, border: 'none',
                  background: !decisionComments.trim() ? '#374151' : showDecisionForm.action === 'approve' ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #ef4444, #dc2626)',
                  color: '#fff', cursor: decisionComments.trim() ? 'pointer' : 'not-allowed', fontWeight: 600,
                }}>
                Confirm {showDecisionForm.action === 'approve' ? 'Approval' : 'Rejection'}
              </button>
              <button onClick={() => setShowDecisionForm(null)} style={{
                padding: '0.5rem 1rem', borderRadius: 6, border: '1px solid rgba(255,255,255,0.2)', background: 'transparent', color: '#9ca3af', cursor: 'pointer',
              }}>Cancel</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};
