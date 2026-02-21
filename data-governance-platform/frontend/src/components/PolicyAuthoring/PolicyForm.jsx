import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, Shield } from 'lucide-react';
import { policyAuthoringAPI } from '../../services/api';
import toast from 'react-hot-toast';

const STEPS = ['Basic Info', 'Rules & Severity', 'Remediation', 'Review'];

const CATEGORIES = [
  { value: 'data_quality', label: 'Data Quality', desc: 'Rules for completeness, accuracy, freshness' },
  { value: 'security', label: 'Security', desc: 'Encryption, access control, masking' },
  { value: 'privacy', label: 'Privacy', desc: 'PII handling, consent, anonymisation' },
  { value: 'compliance', label: 'Compliance', desc: 'GDPR, HIPAA, SOC2, CCPA' },
  { value: 'lineage', label: 'Lineage', desc: 'Data flow tracking and provenance' },
  { value: 'sla', label: 'SLA', desc: 'Availability, latency, freshness SLAs' },
];

const SEVERITIES = [
  { value: 'CRITICAL', label: 'Critical', color: '#ef4444', desc: 'Must fix before approval' },
  { value: 'WARNING', label: 'Warning', color: '#f59e0b', desc: 'Should fix; blocks recommended' },
  { value: 'INFO', label: 'Info', color: '#10b981', desc: 'Advisory; does not block' },
];

const SCANNER_HINTS = [
  { value: 'auto', label: 'Auto-detect', desc: 'Let the system choose the best scanner' },
  { value: 'rule_based', label: 'Rule-based', desc: 'Deterministic YAML rule engine' },
  { value: 'ai_semantic', label: 'AI Semantic', desc: 'LLM-powered semantic analysis' },
];

export const PolicyForm = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    policy_category: '',
    affected_domains: ['ALL'],
    severity: 'WARNING',
    scanner_hint: 'auto',
    remediation_guide: '',
    effective_date: '',
    authored_by: 'Data Governance Expert',
  });

  const [domainInput, setDomainInput] = useState('');

  const update = (field, value) => setForm(prev => ({ ...prev, [field]: value }));

  const addDomain = () => {
    const d = domainInput.trim();
    if (d && !form.affected_domains.includes(d)) {
      // Remove "ALL" if adding a specific domain
      const domains = form.affected_domains.filter(x => x !== 'ALL');
      update('affected_domains', [...domains, d]);
      setDomainInput('');
    }
  };

  const removeDomain = (domain) => {
    const remaining = form.affected_domains.filter(x => x !== domain);
    update('affected_domains', remaining.length === 0 ? ['ALL'] : remaining);
  };

  const canProceed = () => {
    if (step === 0) return form.title.trim() && form.description.trim() && form.policy_category;
    if (step === 1) return form.severity;
    if (step === 2) return form.remediation_guide.trim().length >= 10;
    return true;
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      const payload = { ...form };
      if (!payload.effective_date) delete payload.effective_date;
      const response = await policyAuthoringAPI.create(payload);
      toast.success('Policy draft created successfully!');
      navigate(`/policy-authoring/${response.data.id}`);
    } catch (error) {
      const msg = error.response?.data?.detail || 'Failed to create policy';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const inputStyle = { width: '100%', padding: 'var(--space-sm) var(--space-md)' };
  const labelStyle = { display: 'block', marginBottom: 'var(--space-xs)', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-text-secondary)' };

  return (
    <div style={{ padding: 'var(--space-xl)', maxWidth: 800, margin: '0 auto' }}>
      <button
        onClick={() => navigate('/policy-authoring')}
        style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', background: 'none', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-lg)', fontSize: '0.875rem' }}
      >
        <ArrowLeft size={16} /> Back to Policies
      </button>

      <h2 style={{ marginBottom: 'var(--space-xs)' }}>Author New Policy</h2>
      <p style={{ marginBottom: 'var(--space-xl)' }}>Write governance rules in plain English. The platform will convert them to enforceable YAML.</p>

      {/* Step indicator */}
      <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-xl)' }}>
        {STEPS.map((s, i) => (
          <div key={s} style={{ flex: 1, textAlign: 'center' }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%', margin: '0 auto var(--space-xs)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8125rem', fontWeight: 700,
              background: i <= step ? 'linear-gradient(135deg, #0070AD, #12ABDB)' : 'var(--color-bg-tertiary)',
              color: i <= step ? 'white' : 'var(--color-text-muted)',
              transition: 'all 0.3s',
            }}>
              {i < step ? <Check size={16} /> : i + 1}
            </div>
            <span style={{ fontSize: '0.75rem', color: i <= step ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}>{s}</span>
          </div>
        ))}
      </div>

      <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="card" style={{ padding: 'var(--space-xl)' }}>
        {/* Step 0: Basic Info */}
        {step === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
            <div>
              <label style={labelStyle}>Policy Title *</label>
              <input style={inputStyle} placeholder="e.g. All PII fields must be encrypted at rest" value={form.title} onChange={e => update('title', e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Description (Plain English) *</label>
              <textarea style={{ ...inputStyle, minHeight: 120, resize: 'vertical' }} placeholder="Describe the governance rule in plain English. Be specific about what must be enforced, when, and why." value={form.description} onChange={e => update('description', e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Category *</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--space-sm)' }}>
                {CATEGORIES.map(cat => (
                  <div key={cat.value} onClick={() => update('policy_category', cat.value)} style={{
                    padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                    border: form.policy_category === cat.value ? '2px solid #0070AD' : '1px solid var(--color-border-default)',
                    background: form.policy_category === cat.value ? 'rgba(0,112,173,0.08)' : 'var(--color-bg-secondary)',
                    transition: 'all 0.2s',
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{cat.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginTop: 2 }}>{cat.desc}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <label style={labelStyle}>Author</label>
              <input style={inputStyle} value={form.authored_by} onChange={e => update('authored_by', e.target.value)} />
            </div>
          </div>
        )}

        {/* Step 1: Rules & Severity */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
            <div>
              <label style={labelStyle}>Severity *</label>
              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                {SEVERITIES.map(sev => (
                  <div key={sev.value} onClick={() => update('severity', sev.value)} style={{
                    flex: 1, padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', cursor: 'pointer', textAlign: 'center',
                    border: form.severity === sev.value ? `2px solid ${sev.color}` : '1px solid var(--color-border-default)',
                    background: form.severity === sev.value ? `${sev.color}15` : 'var(--color-bg-secondary)',
                  }}>
                    <div style={{ fontWeight: 700, color: sev.color }}>{sev.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginTop: 2 }}>{sev.desc}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <label style={labelStyle}>Scanner Hint</label>
              <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
                {SCANNER_HINTS.map(sh => (
                  <div key={sh.value} onClick={() => update('scanner_hint', sh.value)} style={{
                    flex: 1, padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', cursor: 'pointer', textAlign: 'center',
                    border: form.scanner_hint === sh.value ? '2px solid #0070AD' : '1px solid var(--color-border-default)',
                    background: form.scanner_hint === sh.value ? 'rgba(0,112,173,0.08)' : 'var(--color-bg-secondary)',
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{sh.label}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginTop: 2 }}>{sh.desc}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <label style={labelStyle}>Affected Domains</label>
              <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-sm)' }}>
                <input
                  style={{ ...inputStyle, flex: 1 }}
                  placeholder="Add a domain (e.g., finance, marketing) or leave ALL"
                  value={domainInput}
                  onChange={e => setDomainInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addDomain())}
                />
                <button onClick={addDomain} style={{ padding: 'var(--space-sm) var(--space-md)', background: 'var(--color-bg-tertiary)', color: 'var(--color-text-primary)', borderRadius: 'var(--radius-md)' }}>Add</button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)' }}>
                {form.affected_domains.map(d => (
                  <span key={d} style={{
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    padding: '2px 10px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600,
                    background: 'rgba(0,112,173,0.1)', color: '#0070AD', border: '1px solid rgba(0,112,173,0.2)',
                  }}>
                    {d}
                    <span onClick={() => removeDomain(d)} style={{ cursor: 'pointer', fontWeight: 400, marginLeft: 2 }}>x</span>
                  </span>
                ))}
              </div>
            </div>
            <div>
              <label style={labelStyle}>Effective Date (optional)</label>
              <input type="date" style={inputStyle} value={form.effective_date} onChange={e => update('effective_date', e.target.value)} />
            </div>
          </div>
        )}

        {/* Step 2: Remediation */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
            <div>
              <label style={labelStyle}>Remediation Guide * (min 10 characters)</label>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-tertiary)', marginBottom: 'var(--space-sm)' }}>
                Describe the steps a data owner should take to resolve a violation of this policy.
              </p>
              <textarea
                style={{ ...inputStyle, minHeight: 200, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: '0.8125rem' }}
                placeholder={"Step 1: Identify affected fields\nStep 2: Apply encryption using approved methods\nStep 3: Update the data contract\nStep 4: Revalidate through the policy engine"}
                value={form.remediation_guide}
                onChange={e => update('remediation_guide', e.target.value)}
              />
              <div style={{ marginTop: 'var(--space-xs)', fontSize: '0.75rem', color: form.remediation_guide.trim().length >= 10 ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
                {form.remediation_guide.trim().length} / 10 min characters
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Review */}
        {step === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <h3 style={{ marginBottom: 'var(--space-sm)' }}>Review Policy Before Creating</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
              <div>
                <span style={labelStyle}>Title</span>
                <p style={{ color: 'var(--color-text-primary)' }}>{form.title}</p>
              </div>
              <div>
                <span style={labelStyle}>Category</span>
                <p style={{ color: 'var(--color-text-primary)' }}>{CATEGORIES.find(c => c.value === form.policy_category)?.label}</p>
              </div>
              <div>
                <span style={labelStyle}>Severity</span>
                <p style={{ color: SEVERITIES.find(s => s.value === form.severity)?.color, fontWeight: 600 }}>{form.severity}</p>
              </div>
              <div>
                <span style={labelStyle}>Scanner</span>
                <p style={{ color: 'var(--color-text-primary)' }}>{SCANNER_HINTS.find(s => s.value === form.scanner_hint)?.label}</p>
              </div>
              <div>
                <span style={labelStyle}>Domains</span>
                <p style={{ color: 'var(--color-text-primary)' }}>{form.affected_domains.join(', ')}</p>
              </div>
              <div>
                <span style={labelStyle}>Author</span>
                <p style={{ color: 'var(--color-text-primary)' }}>{form.authored_by}</p>
              </div>
            </div>
            <div>
              <span style={labelStyle}>Description</span>
              <div style={{ padding: 'var(--space-md)', background: 'var(--color-bg-tertiary)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', lineHeight: 1.6 }}>{form.description}</div>
            </div>
            <div>
              <span style={labelStyle}>Remediation Guide</span>
              <pre style={{ padding: 'var(--space-md)', whiteSpace: 'pre-wrap' }}>{form.remediation_guide}</pre>
            </div>
          </div>
        )}
      </motion.div>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-lg)' }}>
        <button
          onClick={() => step > 0 && setStep(step - 1)}
          disabled={step === 0}
          style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', padding: 'var(--space-sm) var(--space-lg)', background: 'var(--color-bg-tertiary)', color: 'var(--color-text-primary)', borderRadius: 'var(--radius-md)' }}
        >
          <ArrowLeft size={16} /> Previous
        </button>
        {step < STEPS.length - 1 ? (
          <button
            onClick={() => canProceed() && setStep(step + 1)}
            disabled={!canProceed()}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', padding: 'var(--space-sm) var(--space-lg)', background: canProceed() ? 'linear-gradient(135deg, #0070AD, #12ABDB)' : 'var(--color-bg-tertiary)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600 }}
          >
            Next <ArrowRight size={16} />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', padding: 'var(--space-sm) var(--space-lg)', background: 'linear-gradient(135deg, #0070AD, #12ABDB)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600 }}
          >
            <Shield size={16} /> {submitting ? 'Creating...' : 'Create Policy Draft'}
          </button>
        )}
      </div>
    </div>
  );
};
