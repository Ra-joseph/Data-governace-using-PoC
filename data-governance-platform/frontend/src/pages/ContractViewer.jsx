import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, GitBranch, Clock, ChevronLeft, AlertTriangle } from 'lucide-react';
import { gitAPI } from '../services/api';
import { SkeletonLoader } from '../components/SkeletonLoader';
import { EmptyState } from '../components/EmptyState';
import toast from 'react-hot-toast';

export const ContractViewer = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadContracts();
  }, []);

  const loadContracts = async () => {
    try {
      setLoading(true);
      const response = await gitAPI.contracts();
      const contractList = response.data.contracts || [];
      setContracts(contractList);
      if (id) {
        const found = contractList.find(c => c.name === id || String(c.id) === id);
        if (found) setSelectedContract(found);
      } else if (contractList.length > 0) {
        setSelectedContract(contractList[0]);
      }
    } catch (error) {
      toast.error('Failed to load contracts');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.375rem',
            background: 'none', border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-md)', padding: '0.375rem 0.75rem',
            color: 'var(--color-text-secondary)', cursor: 'pointer', fontSize: '0.875rem',
          }}
        >
          <ChevronLeft size={16} /> Back
        </button>
        <div>
          <h1>Contract Viewer</h1>
          <p className="page-subtitle">Browse and inspect versioned data contracts</p>
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          <div style={{ width: 240, flexShrink: 0 }}>
            <SkeletonLoader type="row" count={4} />
          </div>
          <div style={{ flex: 1 }}>
            <SkeletonLoader type="chart" />
          </div>
        </div>
      ) : contracts.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No contracts yet"
          description="Data contracts are generated automatically when subscriptions are approved. Approve a subscription to generate your first contract."
        />
      ) : (
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
          {/* Contract list sidebar */}
          <div style={{
            width: 240, flexShrink: 0,
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border-default)',
            borderRadius: 'var(--radius-lg)',
            overflow: 'hidden',
          }}>
            <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--color-border-default)', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-text-primary)' }}>
              Contracts ({contracts.length})
            </div>
            {contracts.map((contract, i) => (
              <button
                key={i}
                onClick={() => setSelectedContract(contract)}
                style={{
                  width: '100%', textAlign: 'left',
                  padding: '0.75rem 1rem',
                  background: selectedContract === contract ? 'rgba(0,112,173,0.08)' : 'transparent',
                  border: 'none',
                  borderBottom: '1px solid var(--color-border-subtle)',
                  color: selectedContract === contract ? 'var(--color-accent-primary)' : 'var(--color-text-secondary)',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: selectedContract === contract ? 600 : 400,
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                }}
              >
                <FileText size={14} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={contract.name}>
                  {contract.name}
                </span>
              </button>
            ))}
          </div>

          {/* Contract detail */}
          {selectedContract ? (
            <div style={{ flex: 1, background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--color-border-default)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <GitBranch size={18} style={{ color: 'var(--color-accent-primary)' }} />
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{selectedContract.name}</span>
                {selectedContract.last_modified && (
                  <span style={{ marginLeft: 'auto', fontSize: '0.8125rem', color: 'var(--color-text-tertiary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Clock size={12} />
                    {new Date(selectedContract.last_modified).toLocaleDateString()}
                  </span>
                )}
              </div>
              <div style={{ padding: '1.5rem' }}>
                {selectedContract.content ? (
                  <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border-default)', borderRadius: 'var(--radius-md)', padding: '1rem', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: 'var(--color-text-primary)' }}>
                    {typeof selectedContract.content === 'string' ? selectedContract.content : JSON.stringify(selectedContract.content, null, 2)}
                  </pre>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
                    <FileText size={32} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
                    <p>Contract content not available</p>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
