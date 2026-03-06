import { useNavigate } from 'react-router-dom';
import { Database, ArrowRight } from 'lucide-react';

export const SchemaImport = () => {
  const navigate = useNavigate();
  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Schema Import</h1>
        <p className="page-subtitle">Import schemas from PostgreSQL into the platform</p>
      </div>
      <div className="card" style={{ maxWidth: 560, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '3rem 2rem', gap: '1.25rem' }}>
        <div style={{ width: 56, height: 56, background: 'rgba(0,112,173,0.08)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-accent-primary)' }}>
          <Database size={28} />
        </div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Import Schema from PostgreSQL</h2>
        <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          Schema import is available during dataset registration. Use the Dataset Registration Wizard to connect to PostgreSQL and import your table schema automatically.
        </p>
        <button
          onClick={() => navigate('/owner/register')}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.625rem 1.5rem',
            background: 'var(--color-accent-primary)', color: '#fff',
            border: 'none', borderRadius: 'var(--radius-md)',
            fontWeight: 600, fontSize: '0.9375rem', cursor: 'pointer',
            transition: 'all var(--transition-base)',
          }}
        >
          Open Registration Wizard <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
};
