import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Download, Upload, BookTemplate, Copy, CheckCircle, AlertTriangle,
  XCircle, Package, Tag, ArrowRight, Sparkles
} from 'lucide-react';
import { policyExchangeAPI } from '../../services/api';
import toast from 'react-hot-toast';

const TAG_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#0070AD'];

export const PolicyExchange = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState('templates');
  const [templates, setTemplates] = useState([]);
  const [importText, setImportText] = useState('');
  const [importResult, setImportResult] = useState(null);
  const [exportResult, setExportResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const resp = await policyExchangeAPI.listTemplates({});
      setTemplates(resp.data.templates);
    } catch {
      toast.error('Failed to load templates');
    }
  };

  const instantiate = async (templateId) => {
    try {
      const resp = await policyExchangeAPI.instantiateTemplate(templateId, 'Data Governance Expert');
      toast.success(`Created draft: ${resp.data.created_policy.title}`);
      navigate(`/policy-authoring/${resp.data.created_policy.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create from template');
    }
  };

  const handleImport = async () => {
    setImportResult(null);
    let parsed;
    try {
      parsed = JSON.parse(importText);
    } catch {
      toast.error('Invalid JSON — paste a valid policy bundle');
      return;
    }

    // Wrap single policy in bundle format
    const policies = Array.isArray(parsed.policies) ? parsed.policies : Array.isArray(parsed) ? parsed : [parsed];

    try {
      setLoading(true);
      const resp = await policyExchangeAPI.importBundle({
        bundle_name: parsed.bundle_name || 'Manual Import',
        imported_by: 'Data Governance Admin',
        policies,
      });
      setImportResult(resp.data);
      if (resp.data.created > 0) toast.success(`Imported ${resp.data.created} policies`);
      if (resp.data.skipped > 0) toast.error(`Skipped ${resp.data.skipped} duplicates`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExportAll = async () => {
    try {
      setLoading(true);
      const resp = await policyExchangeAPI.exportBundle({ status: 'approved' });
      setExportResult(resp.data);
      toast.success(`Exported ${resp.data.total_policies} policies`);
    } catch {
      toast.error('Export failed');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { key: 'templates', label: 'Templates', icon: BookTemplate },
    { key: 'import', label: 'Import', icon: Upload },
    { key: 'export', label: 'Export', icon: Download },
  ];

  return (
    <div style={{ padding: 'var(--space-xl)' }}>
      <div style={{ marginBottom: 'var(--space-xl)' }}>
        <h2 style={{ margin: 0 }}>Policy Exchange</h2>
        <p style={{ margin: 0, marginTop: 'var(--space-xs)', color: 'var(--color-text-secondary)' }}>
          Templates, import/export for cross-team policy sharing
        </p>
      </div>

      {/* Tab Bar */}
      <div style={{ display: 'flex', gap: 'var(--space-xs)', marginBottom: 'var(--space-xl)', borderBottom: '1px solid var(--color-border)', paddingBottom: 'var(--space-xs)' }}>
        {tabs.map(t => {
          const active = tab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              style={{
                padding: '8px 16px', fontSize: '0.8125rem', fontWeight: 600,
                background: active ? 'rgba(0,112,173,0.1)' : 'transparent',
                color: active ? '#0070AD' : 'var(--color-text-secondary)',
                borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
                border: 'none', borderBottom: active ? '2px solid #0070AD' : '2px solid transparent',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              <t.icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      {/* Templates Tab */}
      {tab === 'templates' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--space-md)' }}>
          {templates.map((tmpl, i) => (
            <motion.div
              key={tmpl.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card"
              style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '0.95rem' }}>{tmpl.name}</h4>
                  <span style={{
                    fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                    color: '#0070AD', background: 'rgba(0,112,173,0.1)',
                    padding: '1px 6px', borderRadius: 4, marginTop: 4, display: 'inline-block',
                  }}>{tmpl.category}</span>
                </div>
                <Sparkles size={18} style={{ color: '#f59e0b', flexShrink: 0 }} />
              </div>
              <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--color-text-secondary)', flex: 1 }}>
                {tmpl.description}
              </p>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {tmpl.tags.map((tag, ti) => (
                  <span key={tag} style={{
                    padding: '1px 6px', borderRadius: 9999, fontSize: '0.6rem', fontWeight: 600,
                    background: `${TAG_COLORS[ti % TAG_COLORS.length]}15`,
                    color: TAG_COLORS[ti % TAG_COLORS.length],
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
              <button
                onClick={() => instantiate(tmpl.id)}
                style={{
                  padding: '6px 12px', fontSize: '0.8125rem', fontWeight: 600,
                  background: 'rgba(16,185,129,0.1)', color: '#10b981',
                  borderRadius: 'var(--radius-md)', border: '1px solid rgba(16,185,129,0.2)',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4,
                }}
              >
                <Copy size={14} /> Use Template
              </button>
            </motion.div>
          ))}
        </div>
      )}

      {/* Import Tab */}
      {tab === 'import' && (
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-md)' }}>
            <Upload size={16} style={{ marginRight: 6, verticalAlign: -3 }} />
            Import Policy Bundle
          </h4>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-md)' }}>
            Paste a JSON policy bundle. Each policy becomes a new draft.
          </p>
          <textarea
            value={importText}
            onChange={e => setImportText(e.target.value)}
            placeholder={'[\n  {\n    "title": "My Policy",\n    "description": "Description...",\n    "policy_category": "security",\n    "severity": "CRITICAL"\n  }\n]'}
            style={{
              width: '100%', minHeight: 180, padding: 'var(--space-md)',
              background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)', fontSize: '0.8125rem',
              fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)', resize: 'vertical',
            }}
          />
          <button
            onClick={handleImport}
            disabled={!importText.trim() || loading}
            style={{
              marginTop: 'var(--space-md)', padding: '8px 20px', fontSize: '0.875rem', fontWeight: 600,
              background: importText.trim() ? 'rgba(0,112,173,0.15)' : 'var(--color-bg-tertiary)',
              color: importText.trim() ? '#0070AD' : 'var(--color-text-muted)',
              borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,112,173,0.2)',
              cursor: importText.trim() ? 'pointer' : 'not-allowed',
            }}
          >
            {loading ? 'Importing...' : 'Import Policies'}
          </button>

          <AnimatePresence>
            {importResult && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                style={{ marginTop: 'var(--space-lg)', overflow: 'hidden' }}
              >
                <div style={{ display: 'flex', gap: 'var(--space-lg)', marginBottom: 'var(--space-md)' }}>
                  <span style={{ color: '#10b981', fontWeight: 600 }}>
                    <CheckCircle size={14} style={{ verticalAlign: -2 }} /> {importResult.created} created
                  </span>
                  <span style={{ color: '#f59e0b', fontWeight: 600 }}>
                    <AlertTriangle size={14} style={{ verticalAlign: -2 }} /> {importResult.skipped} skipped
                  </span>
                  <span style={{ color: '#ef4444', fontWeight: 600 }}>
                    <XCircle size={14} style={{ verticalAlign: -2 }} /> {importResult.errors} errors
                  </span>
                </div>
                {importResult.created_policies?.map(p => (
                  <div key={p.id} style={{
                    padding: '6px 10px', background: 'rgba(16,185,129,0.05)', borderRadius: 'var(--radius-sm)',
                    marginBottom: 4, fontSize: '0.8125rem', display: 'flex', justifyContent: 'space-between',
                  }}>
                    <span>{p.title}</span>
                    <button onClick={() => navigate(`/policy-authoring/${p.id}`)} style={{
                      background: 'none', border: 'none', color: '#0070AD', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600,
                    }}>
                      View <ArrowRight size={12} style={{ verticalAlign: -2 }} />
                    </button>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Export Tab */}
      {tab === 'export' && (
        <div className="card">
          <h4 style={{ marginBottom: 'var(--space-md)' }}>
            <Download size={16} style={{ marginRight: 6, verticalAlign: -3 }} />
            Export Policy Bundle
          </h4>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-md)' }}>
            Export all approved policies as a portable JSON bundle for sharing or backup.
          </p>
          <button
            onClick={handleExportAll}
            disabled={loading}
            style={{
              padding: '8px 20px', fontSize: '0.875rem', fontWeight: 600,
              background: 'rgba(0,112,173,0.15)', color: '#0070AD',
              borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,112,173,0.2)',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            <Package size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
            {loading ? 'Exporting...' : 'Export Approved Policies'}
          </button>

          {exportResult && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ marginTop: 'var(--space-lg)' }}
            >
              <div style={{ fontSize: '0.8125rem', marginBottom: 'var(--space-sm)', fontWeight: 600 }}>
                Exported {exportResult.total_policies} policies
              </div>
              <textarea
                readOnly
                value={JSON.stringify(exportResult, null, 2)}
                style={{
                  width: '100%', minHeight: 250, padding: 'var(--space-md)',
                  background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)', fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)', resize: 'vertical',
                }}
              />
              <button
                onClick={() => { navigator.clipboard.writeText(JSON.stringify(exportResult, null, 2)); toast.success('Copied to clipboard'); }}
                style={{
                  marginTop: 'var(--space-sm)', padding: '6px 14px', fontSize: '0.8125rem', fontWeight: 600,
                  background: 'rgba(139,92,246,0.1)', color: '#8b5cf6',
                  borderRadius: 'var(--radius-md)', border: '1px solid rgba(139,92,246,0.2)',
                  cursor: 'pointer',
                }}
              >
                <Copy size={14} style={{ marginRight: 4, verticalAlign: -2 }} /> Copy to Clipboard
              </button>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
};
