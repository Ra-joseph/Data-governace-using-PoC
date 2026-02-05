import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Search, 
  Filter, 
  Database, 
  Shield, 
  AlertCircle,
  CheckCircle2,
  Plus
} from 'lucide-react';
import { datasetAPI } from '../services/api';
import toast from 'react-hot-toast';
import './DatasetCatalog.css';

export const DatasetCatalog = () => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadDatasets();
  }, [filter]);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await datasetAPI.list(params);
      setDatasets(response.data);
    } catch (error) {
      toast.error('Failed to load datasets');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDatasets = datasets.filter(dataset =>
    dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dataset.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    const badges = {
      published: { icon: CheckCircle2, className: 'badge-success', label: 'Published' },
      draft: { icon: AlertCircle, className: 'badge-warning', label: 'Draft' },
      deprecated: { icon: AlertCircle, className: 'badge-error', label: 'Deprecated' },
    };
    
    const badge = badges[status] || badges.draft;
    const Icon = badge.icon;
    
    return (
      <span className={`badge ${badge.className}`}>
        <Icon size={12} />
        {badge.label}
      </span>
    );
  };

  const getClassificationBadge = (classification) => {
    const classes = {
      public: 'badge-info',
      internal: 'badge-neutral',
      confidential: 'badge-warning',
      restricted: 'badge-error',
    };
    
    return (
      <span className={`badge ${classes[classification] || 'badge-neutral'}`}>
        <Shield size={12} />
        {classification}
      </span>
    );
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Dataset Catalog</h1>
          <p className="page-subtitle">
            Browse and manage your organization's data assets
          </p>
        </div>
        <div className="header-actions">
          <Link to="/import" className="btn-primary">
            <Plus size={18} />
            Register Dataset
          </Link>
        </div>
      </div>

      <div className="catalog-toolbar">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search datasets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <Filter size={18} />
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All Datasets</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading datasets...</p>
        </div>
      ) : (
        <div className="dataset-grid">
          {filteredDatasets.map((dataset, index) => (
            <motion.div
              key={dataset.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Link to={`/datasets/${dataset.id}`} className="dataset-card">
                <div className="dataset-header">
                  <div className="dataset-icon">
                    <Database size={24} />
                  </div>
                  <div className="dataset-badges">
                    {getStatusBadge(dataset.status)}
                    {dataset.contains_pii && (
                      <span className="badge badge-error">
                        <AlertCircle size={12} />
                        PII
                      </span>
                    )}
                  </div>
                </div>

                <h3 className="dataset-title">{dataset.name}</h3>
                <p className="dataset-description">
                  {dataset.description || 'No description available'}
                </p>

                <div className="dataset-meta">
                  {getClassificationBadge(dataset.classification)}
                  <span className="meta-text">
                    {dataset.schema_definition?.length || 0} fields
                  </span>
                  <span className="meta-text">
                    {new Date(dataset.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="dataset-footer">
                  <div className="owner-info">
                    <div className="avatar">{dataset.owner_name?.[0] || 'U'}</div>
                    <span>{dataset.owner_name}</span>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      {!loading && filteredDatasets.length === 0 && (
        <div className="empty-state">
          <Database size={48} strokeWidth={1.5} />
          <h3>No datasets found</h3>
          <p>
            {searchTerm
              ? 'Try adjusting your search criteria'
              : 'Get started by registering your first dataset'}
          </p>
          <Link to="/import" className="btn-primary">
            <Plus size={18} />
            Register Dataset
          </Link>
        </div>
      )}
    </div>
  );
};
