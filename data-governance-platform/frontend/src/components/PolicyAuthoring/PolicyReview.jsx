import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle, XCircle, Clock, Eye, Shield
} from 'lucide-react';
import { policyAuthoringAPI } from '../../services/api';
import toast from 'react-hot-toast';

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

export const PolicyReview = () => {
  const navigate = useNavigate();
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [approverName, setApproverName] = useState('Data Governance Approver');
  const [rejectComment, setRejectComment] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [processing, setProcessing] = useState(false);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const response = await policyAuthoringAPI.list({ status: 'pending_approval' });
      setPolicies(response.data.policies);
    } catch (error) {
      toast.error('Failed to load pending policies');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadDetail = async (id) => {
    try {
      const response = await policyAuthoringAPI.get(id);
      setSelectedPolicy(response.data);
    } catch (error) {
      toast.error('Failed to load policy details');
    }
  };

  const handleApprove = async () => {
    if (!selectedPolicy) return;
    try {
      setProcessing(true);
      await policyAuthoringAPI.approve(selectedPolicy.id, { approver_name: approverName });
      toast.success('Policy approved!');
      setSelectedPolicy(null);
      loadPolicies();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve policy');
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedPolicy || rejectComment.length < 10) return;
    try {
      setProcessing(true);
      await policyAuthoringAPI.reject(selectedPolicy.id, {
        approver_name: approverName,
        comment: rejectComment,
      });
      toast.success('Policy rejected');
      setSelectedPolicy(null);
      setShowRejectModal(false);
      setRejectComment('');
      loadPolicies();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject policy');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      <div style={{ marginBottom: 'var(--space-xl)' }}>
        <h2 style={{ margin: 0 }}>Policy Review Queue</h2>
        <p style={{ margin: 0, marginTop: 'var(--space-xs)' }}>{policies.length} policies awaiting approval</p>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-xs)', marginBottom: 'var(--space-lg)' }}>
        <label style={{ fontSize: '0.8125rem', color: 'var(--color-text-tertiary)', marginRight: 'var(--space-xs)' }}>Approver:</label>
        <input
          value={approverName}
          onChange={(e) => setApproverName(e.target.value)}
          style={{ width: 250, padding: '4px 8px', fontSize: '0.8125rem' }}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-3xl)', color: 'var(--color-text-tertiary)' }}>Loading...</div>
      ) : policies.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-3xl)' }}>
          <CheckCircle size={48} style={{ color: 'var(--color-success)', marginBottom: 'var(--space-md)' }} />
          <h3>All caught up!</h3>
          <p>No policies pending approval.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: selectedPolicy ? '1fr 2fr' : '1fr', gap: 'var(--space-lg)' }}>
          {/* Policy List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {policies.map((policy, index) => {
              const sevColor = SEVERITY_COLORS[policy.severity] || '#9ca3af';
              return (
                <motion.div
                  key={policy.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="card"
                  onClick={() => loadDetail(policy.id)}
                  style={{
                    cursor: 'pointer', padding: 'var(--space-md)',
                    border: selectedPolicy?.id === policy.id ? '2px solid #0070AD' : undefined,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xs)' }}>
                    <h5 style={{ margin: 0, fontSize: '0.875rem' }}>{policy.title}</h5>
                    <span style={{
                      padding: '2px 6px', borderRadius: 9999, fontSize: '0.65rem', fontWeight: 700,
                      background: `${sevColor}15`, color: sevColor, border: `1px solid ${sevColor}30`,
                      textTransform: 'uppercase',
                    }}>{policy.severity}</span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                    {CATEGORY_LABELS[policy.policy_category] || policy.policy_category} — by {policy.authored_by}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* Detail Panel */}
          {selectedPolicy && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-lg)' }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{selectedPolicy.title}</h3>
                    <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-xs)', flexWrap: 'wrap' }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600,
                        background: `${SEVERITY_COLORS[selectedPolicy.severity] || '#9ca3af'}15`,
                        color: SEVERITY_COLORS[selectedPolicy.severity] || '#9ca3af',
                        textTransform: 'uppercase',
                      }}>{selectedPolicy.severity}</span>
                      <span style={{
                        padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600,
                        background: 'rgba(0,112,173,0.1)', color: '#0070AD',
                      }}>{CATEGORY_LABELS[selectedPolicy.policy_category]}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                    <button
                      onClick={handleApprove}
                      disabled={processing}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 4,
                        padding: 'var(--space-sm) var(--space-md)',
                        background: 'rgba(16,185,129,0.1)', color: '#10b981',
                        borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: '0.8125rem',
                        border: '1px solid rgba(16,185,129,0.2)',
                      }}
                    >
                      <CheckCircle size={14} /> Approve
                    </button>
                    <button
                      onClick={() => setShowRejectModal(true)}
                      disabled={processing}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 4,
                        padding: 'var(--space-sm) var(--space-md)',
                        background: 'rgba(239,68,68,0.1)', color: '#ef4444',
                        borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: '0.8125rem',
                        border: '1px solid rgba(239,68,68,0.2)',
                      }}
                    >
                      <XCircle size={14} /> Reject
                    </button>
                  </div>
                </div>

                <h5 style={{ marginBottom: 'var(--space-sm)' }}>Description</h5>
                <div style={{
                  padding: 'var(--space-md)', background: 'var(--color-bg-tertiary)',
                  borderRadius: 'var(--radius-md)', fontSize: '0.875rem', lineHeight: 1.7,
                  whiteSpace: 'pre-wrap', marginBottom: 'var(--space-lg)',
                }}>
                  {selectedPolicy.description}
                </div>

                {selectedPolicy.remediation_guide && (
                  <>
                    <h5 style={{ marginBottom: 'var(--space-sm)' }}>Remediation Guide</h5>
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8125rem', lineHeight: 1.6, marginBottom: 'var(--space-lg)' }}>
                      {selectedPolicy.remediation_guide}
                    </pre>
                  </>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>Author</span>
                    <p style={{ margin: 0, fontSize: '0.875rem' }}>{selectedPolicy.authored_by}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>Domains</span>
                    <p style={{ margin: 0, fontSize: '0.875rem' }}>{(selectedPolicy.affected_domains || []).join(', ')}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>Scanner</span>
                    <p style={{ margin: 0, fontSize: '0.875rem' }}>{selectedPolicy.scanner_hint}</p>
                  </div>
                  {selectedPolicy.effective_date && (
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>Effective Date</span>
                      <p style={{ margin: 0, fontSize: '0.875rem' }}>{selectedPolicy.effective_date}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Reject Modal */}
              {showRejectModal && (
                <div className="card" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
                  <h4 style={{ color: '#ef4444', marginBottom: 'var(--space-md)' }}>Reject Policy</h4>
                  <p style={{ fontSize: '0.8125rem', marginBottom: 'var(--space-sm)' }}>
                    Provide a reason for rejection (minimum 10 characters):
                  </p>
                  <textarea
                    value={rejectComment}
                    onChange={(e) => setRejectComment(e.target.value)}
                    placeholder="Explain why this policy is being rejected..."
                    style={{ width: '100%', minHeight: 100, resize: 'vertical', marginBottom: 'var(--space-md)' }}
                  />
                  <div style={{ display: 'flex', gap: 'var(--space-sm)', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => { setShowRejectModal(false); setRejectComment(''); }}
                      style={{ padding: 'var(--space-sm) var(--space-md)', background: 'var(--color-bg-tertiary)', color: 'var(--color-text-primary)', borderRadius: 'var(--radius-md)' }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={rejectComment.length < 10 || processing}
                      style={{
                        padding: 'var(--space-sm) var(--space-md)',
                        background: rejectComment.length >= 10 ? 'rgba(239,68,68,0.2)' : 'var(--color-bg-tertiary)',
                        color: rejectComment.length >= 10 ? '#ef4444' : 'var(--color-text-muted)',
                        borderRadius: 'var(--radius-md)', fontWeight: 600,
                      }}
                    >
                      Confirm Rejection
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
};
