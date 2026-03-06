import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { datasetAPI } from '../services/api';
import { Shield, Database, Calendar, User, AlertTriangle } from 'lucide-react';
import { SkeletonLoader } from '../components/SkeletonLoader';
import './Dashboard.css';

export const DatasetDetail = () => {
  const { id } = useParams();
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDataset();
  }, [id]);

  const loadDataset = async () => {
    try {
      const response = await datasetAPI.get(id);
      setDataset(response.data);
    } catch (error) {
      console.error('Failed to load dataset:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="skeleton" style={{ height: 36, width: 240, borderRadius: '8px', marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 18, width: 320, borderRadius: '6px' }} />
        </div>
      </div>
      <div style={{ marginBottom: '1.5rem' }}>
        <SkeletonLoader type="stat" count={4} />
      </div>
      <SkeletonLoader type="row" count={6} />
    </div>
  );
  if (!dataset) return (
    <div className="page-container">
      <div className="error-state">
        <div className="error-state-icon">
          <AlertTriangle size={28} />
        </div>
        <h3>Dataset not found</h3>
        <p>The dataset you're looking for doesn't exist or may have been removed.</p>
      </div>
    </div>
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>{dataset.name}</h1>
          <p className="page-subtitle">{dataset.description}</p>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon metric-icon-accent"><Database size={24} /></div>
          <div className="metric-content">
            <h3 className="metric-value">{dataset.schema_definition?.length || 0}</h3>
            <p className="metric-label">Fields</p>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon metric-icon-success"><Shield size={24} /></div>
          <div className="metric-content">
            <h3 className="metric-value">{dataset.classification}</h3>
            <p className="metric-label">Classification</p>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon metric-icon-warning"><Calendar size={24} /></div>
          <div className="metric-content">
            <h3 className="metric-value">{new Date(dataset.created_at).toLocaleDateString()}</h3>
            <p className="metric-label">Created</p>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon metric-icon-info"><User size={24} /></div>
          <div className="metric-content">
            <h3 className="metric-value">{dataset.owner_name}</h3>
            <p className="metric-label">Owner</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Schema Definition</h3>
        <div style={{ overflowX: 'auto', marginTop: 'var(--space-lg)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-default)' }}>
                <th style={{ padding: 'var(--space-md)', textAlign: 'left' }}>Field Name</th>
                <th style={{ padding: 'var(--space-md)', textAlign: 'left' }}>Type</th>
                <th style={{ padding: 'var(--space-md)', textAlign: 'left' }}>Required</th>
                <th style={{ padding: 'var(--space-md)', textAlign: 'left' }}>PII</th>
                <th style={{ padding: 'var(--space-md)', textAlign: 'left' }}>Description</th>
              </tr>
            </thead>
            <tbody>
              {dataset.schema_definition?.map((field, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <td style={{ padding: 'var(--space-md)', fontFamily: 'var(--font-mono)' }}>{field.name}</td>
                  <td style={{ padding: 'var(--space-md)' }}><code>{field.type}</code></td>
                  <td style={{ padding: 'var(--space-md)' }}>{field.required ? '✓' : '—'}</td>
                  <td style={{ padding: 'var(--space-md)' }}>{field.pii ? <span className="badge badge-error">PII</span> : '—'}</td>
                  <td style={{ padding: 'var(--space-md)', color: 'var(--color-text-secondary)' }}>{field.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
