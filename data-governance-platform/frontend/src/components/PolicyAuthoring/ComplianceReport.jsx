import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Shield, FileText, CheckCircle, XCircle, AlertTriangle,
  BarChart3, RefreshCw, Layers, TrendingUp, Database
} from 'lucide-react';
import { policyReportsAPI, policyDashboardAPI } from '../../services/api';
import toast from 'react-hot-toast';

const CLS_COLORS = {
  public: '#10b981',
  internal: '#3b82f6',
  confidential: '#f59e0b',
  restricted: '#ef4444',
  unknown: '#9ca3af',
};

export const ComplianceReport = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    try {
      setLoading(true);
      const resp = await policyReportsAPI.compliance();
      setReport(resp.data);
    } catch {
      toast.error('Failed to load compliance report');
    } finally {
      setLoading(false);
    }
  };

  const runBulkValidation = async () => {
    setValidating(true);
    setBulkResult(null);
    try {
      const resp = await policyReportsAPI.bulkValidate(true);
      setBulkResult(resp.data);
      toast.success(`Validated ${resp.data.validated} contracts`);
      loadReport();
    } catch {
      toast.error('Bulk validation failed');
    } finally {
      setValidating(false);
    }
  };

  if (loading || !report) {
    return (
      <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
        Loading compliance report...
      </div>
    );
  }

  const { total_contracts, contracts_passing, contracts_warning, contracts_failing, contracts_unvalidated } = report;

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-xl)' }}>
        <div>
          <h2 style={{ margin: 0 }}>Compliance Report</h2>
          <p style={{ margin: 0, marginTop: 'var(--space-xs)', color: 'var(--color-text-secondary)' }}>
            Policy compliance analysis across all contracts and datasets
          </p>
        </div>
        <button
          onClick={runBulkValidation}
          disabled={validating}
          style={{
            padding: '8px 16px', fontSize: '0.8125rem', fontWeight: 600,
            background: validating ? 'var(--color-bg-tertiary)' : 'rgba(0,112,173,0.1)',
            color: validating ? 'var(--color-text-muted)' : '#0070AD',
            borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,112,173,0.2)',
            cursor: validating ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          <RefreshCw size={14} className={validating ? 'spin' : ''} />
          {validating ? 'Validating...' : 'Re-validate All'}
        </button>
      </div>

      {/* Top KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
        {[
          { label: 'Total Contracts', value: total_contracts, icon: FileText, color: '#0070AD' },
          { label: 'Datasets', value: report.total_datasets, icon: Database, color: '#8b5cf6' },
          { label: 'Active Policies', value: report.total_policies_active, icon: Shield, color: '#10b981' },
          { label: 'Authored Policies', value: report.total_policies_authored, icon: Layers, color: '#3b82f6' },
          { label: 'Pass Rate', value: `${report.pass_rate_pct}%`, icon: TrendingUp, color: report.pass_rate_pct >= 80 ? '#10b981' : report.pass_rate_pct >= 50 ? '#f59e0b' : '#ef4444' },
        ].map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="card"
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}
          >
            <div style={{
              width: 40, height: 40, borderRadius: 'var(--radius-lg)',
              background: `${card.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <card.icon size={20} style={{ color: card.color }} />
            </div>
            <div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{card.value}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-tertiary)', fontWeight: 500 }}>{card.label}</div>
            </div>
          </motion.div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
        {/* Contract Validation Status */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Contract Validation Status</h4>
          <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'center', marginBottom: 'var(--space-lg)' }}>
            {[
              { label: 'Passing', count: contracts_passing, color: '#10b981', icon: CheckCircle },
              { label: 'Warning', count: contracts_warning, color: '#f59e0b', icon: AlertTriangle },
              { label: 'Failing', count: contracts_failing, color: '#ef4444', icon: XCircle },
              { label: 'Unvalidated', count: contracts_unvalidated, color: '#9ca3af', icon: FileText },
            ].map(s => (
              <div key={s.label} style={{ textAlign: 'center', flex: 1 }}>
                <div style={{
                  width: 52, height: 52, borderRadius: '50%', margin: '0 auto 8px',
                  background: `${s.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <s.icon size={24} style={{ color: s.color }} />
                </div>
                <div style={{ fontSize: '1.3rem', fontWeight: 700, color: s.color }}>{s.count}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>{s.label}</div>
              </div>
            ))}
          </div>
          {/* Progress bar */}
          {total_contracts > 0 && (
            <div style={{ height: 10, borderRadius: 5, background: 'var(--color-bg-tertiary)', overflow: 'hidden', display: 'flex' }}>
              {[
                { pct: (contracts_passing / total_contracts) * 100, color: '#10b981' },
                { pct: (contracts_warning / total_contracts) * 100, color: '#f59e0b' },
                { pct: (contracts_failing / total_contracts) * 100, color: '#ef4444' },
                { pct: (contracts_unvalidated / total_contracts) * 100, color: '#9ca3af' },
              ].map((seg, i) => (
                <motion.div
                  key={i}
                  initial={{ width: 0 }}
                  animate={{ width: `${seg.pct}%` }}
                  transition={{ duration: 0.8, delay: 0.3 + i * 0.1 }}
                  style={{ height: '100%', background: seg.color }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Classification Breakdown */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Data Classification</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
            {Object.entries(report.classification_breakdown || {}).map(([cls, count]) => {
              const total = total_contracts || 1;
              const pct = Math.round((count / total) * 100);
              const color = CLS_COLORS[cls] || '#9ca3af';
              return (
                <div key={cls}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem', marginBottom: 4 }}>
                    <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>{cls}</span>
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
            {Object.keys(report.classification_breakdown || {}).length === 0 && (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>No classification data available.</p>
            )}
          </div>
        </div>
      </div>

      {/* Severity Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Violation Severity</h4>
          <div style={{ display: 'flex', gap: 'var(--space-lg)', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#ef4444' }}>
                {report.severity_summary?.critical || 0}
              </div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>CRITICAL</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f59e0b' }}>
                {report.severity_summary?.warning || 0}
              </div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>WARNING</div>
            </div>
          </div>
        </div>

        {/* Policy Coverage */}
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-lg)' }}>Policy Coverage</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)' }}>
            {report.policy_coverage?.map((cov, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 10px', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-sm)',
              }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>{cov.category}</span>
                <span style={{
                  padding: '1px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 700,
                  background: 'rgba(0,112,173,0.1)', color: '#0070AD',
                }}>
                  {cov.policy_count} {cov.policy_count === 1 ? 'policy' : 'policies'}
                </span>
              </div>
            ))}
            {(report.policy_coverage || []).length === 0 && (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>No policies loaded.</p>
            )}
          </div>
        </div>
      </div>

      {/* Bulk Validation Results */}
      {bulkResult && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <h4 style={{ marginBottom: 'var(--space-md)' }}>Bulk Validation Results</h4>
          <div style={{ display: 'flex', gap: 'var(--space-lg)', marginBottom: 'var(--space-md)' }}>
            <span style={{ fontSize: '0.875rem' }}>
              <strong>{bulkResult.validated}</strong> validated
            </span>
            <span style={{ color: '#10b981', fontSize: '0.875rem' }}>
              <strong>{bulkResult.passed}</strong> passed
            </span>
            <span style={{ color: '#f59e0b', fontSize: '0.875rem' }}>
              <strong>{bulkResult.warnings}</strong> warnings
            </span>
            <span style={{ color: '#ef4444', fontSize: '0.875rem' }}>
              <strong>{bulkResult.failed}</strong> failed
            </span>
            {bulkResult.errors > 0 && (
              <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
                <strong>{bulkResult.errors}</strong> errors
              </span>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xs)', maxHeight: 200, overflow: 'auto' }}>
            {bulkResult.results.map((r, i) => {
              const color = r.status === 'passed' ? '#10b981' : r.status === 'warning' ? '#f59e0b' : r.status === 'failed' ? '#ef4444' : '#9ca3af';
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between',
                  padding: '4px 10px', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8125rem',
                }}>
                  <span>Contract #{r.contract_id}</span>
                  <span style={{ fontWeight: 600, color, textTransform: 'uppercase', fontSize: '0.7rem' }}>{r.status}</span>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
};
