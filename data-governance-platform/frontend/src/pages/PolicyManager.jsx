import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight } from 'lucide-react';

export const PolicyManager = () => {
  const navigate = useNavigate();
  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Policy Manager</h1>
        <p className="page-subtitle">Create and manage data governance policies</p>
      </div>
      <div className="card" style={{ maxWidth: 560, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '3rem 2rem', gap: '1.25rem' }}>
        <div style={{ width: 56, height: 56, background: 'rgba(0,112,173,0.08)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-accent-primary)' }}>
          <Shield size={28} />
        </div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Policy Authoring</h2>
        <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          Full policy authoring, versioning, review, and lifecycle management is available in the Policy Authoring section.
        </p>
        <button
          onClick={() => navigate('/policy-authoring')}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.625rem 1.5rem',
            background: 'var(--color-accent-primary)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-md)',
            fontWeight: 600, fontSize: '0.9375rem', cursor: 'pointer',
            transition: 'all var(--transition-base)',
          }}
        >
          Go to Policy Authoring <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
};
