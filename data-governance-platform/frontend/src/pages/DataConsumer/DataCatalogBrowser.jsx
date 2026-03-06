import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  Database,
  Search,
  Filter,
  Shield,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  X
} from 'lucide-react';
import { datasetAPI, subscriptionAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const classificationColors = {
  public: { color: '#16a34a', background: 'rgba(22,163,74,0.08)' },
  internal: { color: '#0070AD', background: 'rgba(0,112,173,0.08)' },
  confidential: { color: '#d97706', background: 'rgba(217,119,6,0.08)' },
  restricted: { color: '#dc2626', background: 'rgba(220,38,38,0.08)' },
};

export function DataCatalogBrowser() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [filteredDatasets, setFilteredDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClassification, setSelectedClassification] = useState('all');
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [showSubscriptionForm, setShowSubscriptionForm] = useState(false);
  const [hoveredCardId, setHoveredCardId] = useState(null);
  const [hoveredButton, setHoveredButton] = useState(null);
  const [hoveredCancelBtn, setHoveredCancelBtn] = useState(false);
  const [hoveredSubmitBtn, setHoveredSubmitBtn] = useState(false);
  const [hoveredCloseBtn, setHoveredCloseBtn] = useState(false);

  const [subscriptionForm, setSubscriptionForm] = useState({
    use_case: '',
    business_justification: '',
    sla_requirements: {
      max_latency_ms: 1000,
      min_availability_pct: 99.9,
      max_staleness_minutes: 60,
    },
    required_fields: [],
    access_duration_days: 365,
  });

  useEffect(() => {
    loadDatasets();
  }, []);

  useEffect(() => {
    filterDatasets();
  }, [datasets, searchTerm, selectedClassification]);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      // Load only published datasets
      const response = await datasetAPI.list({ status: 'published' });
      setDatasets(response.data);
    } catch (error) {
      toast.error('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const filterDatasets = () => {
    let filtered = datasets;

    if (searchTerm) {
      filtered = filtered.filter(
        (ds) =>
          ds.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          ds.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedClassification !== 'all') {
      filtered = filtered.filter((ds) => ds.classification === selectedClassification);
    }

    setFilteredDatasets(filtered);
  };

  const handleSubscribe = (dataset) => {
    setSelectedDataset(dataset);
    setSubscriptionForm({
      ...subscriptionForm,
      required_fields: dataset.schema?.map(col => col.name) || [],
    });
    setShowSubscriptionForm(true);
  };

  const submitSubscription = async () => {
    if (!subscriptionForm.use_case || !subscriptionForm.business_justification) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await subscriptionAPI.create({
        dataset_id: selectedDataset.id,
        consumer_name: user?.name,
        consumer_email: user?.email,
        consumer_organization: user?.organization || 'Demo Organization',
        ...subscriptionForm,
      });

      toast.success('Subscription request submitted successfully!');
      setShowSubscriptionForm(false);
      setSelectedDataset(null);
      setSubscriptionForm({
        use_case: '',
        business_justification: '',
        sla_requirements: {
          max_latency_ms: 1000,
          min_availability_pct: 99.9,
          max_staleness_minutes: 60,
        },
        required_fields: [],
        access_duration_days: 365,
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit subscription');
    }
  };

  const getClassificationStyle = (classification) => {
    const colors = classificationColors[classification] || { color: '#8A8A8A', background: 'rgba(138,138,138,0.08)' };
    return {
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '12px',
      fontWeight: 600,
      textTransform: 'capitalize',
      color: colors.color,
      backgroundColor: colors.background,
    };
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    backgroundColor: '#FAF9F6',
    border: '1px solid #E5E2DB',
    borderRadius: '8px',
    color: '#1A1A1A',
    fontSize: '14px',
    outline: 'none',
  };

  const slaInputStyle = {
    width: '100%',
    padding: '8px 12px',
    backgroundColor: '#FFFFFF',
    border: '1px solid #E5E2DB',
    borderRadius: '4px',
    color: '#1A1A1A',
    fontSize: '13px',
    outline: 'none',
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#FAF9F6',
      }}>
        <div style={{ color: '#1A1A1A' }}>Loading catalog...</div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#FAF9F6',
      padding: '32px',
    }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{
            fontSize: '1.875rem',
            fontWeight: 700,
            color: '#1A1A1A',
            marginBottom: '8px',
          }}>
            Data Catalog
          </h1>
          <p style={{ color: '#5A5A5A' }}>
            Browse and subscribe to available datasets
          </p>
        </div>

        {/* Search and Filters */}
        <div style={{ display: 'flex', gap: '16px', marginBottom: '32px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <Search style={{
              position: 'absolute',
              left: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '20px',
              height: '20px',
              color: '#8A8A8A',
            }} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search datasets..."
              style={{
                ...inputStyle,
                paddingLeft: '48px',
                backgroundColor: '#FFFFFF',
              }}
            />
          </div>

          <select
            value={selectedClassification}
            onChange={(e) => setSelectedClassification(e.target.value)}
            style={{
              padding: '12px 16px',
              backgroundColor: '#FFFFFF',
              border: '1px solid #E5E2DB',
              borderRadius: '8px',
              color: '#1A1A1A',
              fontSize: '14px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Classifications</option>
            <option value="public">Public</option>
            <option value="internal">Internal</option>
            <option value="confidential">Confidential</option>
            <option value="restricted">Restricted</option>
          </select>
        </div>

        {/* Stats Bar */}
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '8px',
          border: '1px solid #E5E2DB',
          padding: '16px',
          marginBottom: '32px',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '14px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#5A5A5A' }}>
              <Database style={{ width: '16px', height: '16px' }} />
              <span>
                Showing {filteredDatasets.length} of {datasets.length} datasets
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#5A5A5A' }}>
                <CheckCircle style={{ width: '16px', height: '16px', color: '#16a34a' }} />
                <span>
                  {datasets.filter(ds => ds.contract?.validation_result?.status === 'passed').length} Compliant
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#5A5A5A' }}>
                <Users style={{ width: '16px', height: '16px', color: '#0070AD' }} />
                <span>
                  {datasets.reduce((sum, ds) => sum + (ds.subscriber_count || 0), 0)} Active Subscriptions
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Dataset Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
          gap: '24px',
        }}>
          {filteredDatasets.map((dataset) => {
            const isHovered = hoveredCardId === dataset.id;
            return (
              <div
                key={dataset.id}
                onMouseEnter={() => setHoveredCardId(dataset.id)}
                onMouseLeave={() => setHoveredCardId(null)}
                style={{
                  backgroundColor: '#FFFFFF',
                  borderRadius: '12px',
                  border: `1px solid ${isHovered ? '#0070AD' : '#E5E2DB'}`,
                  overflow: 'hidden',
                  transition: 'border-color 0.2s ease',
                }}
              >
                <div style={{ padding: '24px' }}>
                  {/* Header */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    marginBottom: '16px',
                  }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{
                        fontSize: '1.125rem',
                        fontWeight: 600,
                        color: isHovered ? '#0070AD' : '#1A1A1A',
                        marginBottom: '4px',
                        transition: 'color 0.2s ease',
                      }}>
                        {dataset.name}
                      </h3>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={getClassificationStyle(dataset.classification)}>
                          {dataset.classification}
                        </span>
                        {dataset.contains_pii && (
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 600,
                            backgroundColor: 'rgba(217,119,6,0.08)',
                            color: '#d97706',
                          }}>
                            PII
                          </span>
                        )}
                      </div>
                    </div>
                    <Database style={{
                      width: '32px',
                      height: '32px',
                      color: isHovered ? '#0070AD' : '#B0ADA6',
                      transition: 'color 0.2s ease',
                    }} />
                  </div>

                  {/* Description */}
                  <p style={{
                    fontSize: '14px',
                    color: '#5A5A5A',
                    marginBottom: '16px',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}>
                    {dataset.description}
                  </p>

                  {/* Metadata */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px', fontSize: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8A8A8A' }}>
                      <Shield style={{ width: '16px', height: '16px' }} />
                      <span>{dataset.owner_name}</span>
                    </div>
                    {dataset.schema && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8A8A8A' }}>
                        <FileText style={{ width: '16px', height: '16px' }} />
                        <span>{dataset.schema.length} fields</span>
                      </div>
                    )}
                    {dataset.subscriber_count > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#8A8A8A' }}>
                        <Users style={{ width: '16px', height: '16px' }} />
                        <span>{dataset.subscriber_count} subscribers</span>
                      </div>
                    )}
                  </div>

                  {/* Compliance Status */}
                  {dataset.contract?.validation_result && (
                    <div style={{ marginBottom: '16px' }}>
                      {dataset.contract.validation_result.status === 'passed' ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#16a34a', fontSize: '14px' }}>
                          <CheckCircle style={{ width: '16px', height: '16px' }} />
                          <span>Policy Compliant</span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#d97706', fontSize: '14px' }}>
                          <AlertCircle style={{ width: '16px', height: '16px' }} />
                          <span>
                            {dataset.contract.validation_result.failures} violation(s)
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Compliance Tags */}
                  {dataset.compliance_tags && dataset.compliance_tags.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
                      {dataset.compliance_tags.map((tag) => (
                        <span
                          key={tag}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#F4F3EE',
                            color: '#5A5A5A',
                            borderRadius: '4px',
                            fontSize: '12px',
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Subscribe Button */}
                  <button
                    onClick={() => handleSubscribe(dataset)}
                    onMouseEnter={() => setHoveredButton(dataset.id)}
                    onMouseLeave={() => setHoveredButton(null)}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      backgroundColor: hoveredButton === dataset.id ? '#005a8a' : '#0070AD',
                      color: '#FFFFFF',
                      borderRadius: '8px',
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: 500,
                      fontSize: '14px',
                      transition: 'background-color 0.2s ease',
                    }}
                  >
                    Request Access
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {filteredDatasets.length === 0 && (
          <div style={{ textAlign: 'center', padding: '48px 0' }}>
            <Database style={{ width: '64px', height: '64px', color: '#B0ADA6', margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#5A5A5A', marginBottom: '8px' }}>
              No datasets found
            </h3>
            <p style={{ color: '#8A8A8A' }}>
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </div>

      {/* Subscription Form Modal */}
      {showSubscriptionForm && selectedDataset && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
          zIndex: 50,
        }}>
          <div style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E5E2DB',
            maxWidth: '672px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            {/* Modal Header */}
            <div style={{
              position: 'sticky',
              top: 0,
              backgroundColor: '#FFFFFF',
              borderBottom: '1px solid #E5E2DB',
              padding: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1A1A1A', marginBottom: '4px' }}>
                  Request Access
                </h2>
                <p style={{ color: '#5A5A5A' }}>
                  {selectedDataset.name}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowSubscriptionForm(false);
                  setSelectedDataset(null);
                }}
                onMouseEnter={() => setHoveredCloseBtn(true)}
                onMouseLeave={() => setHoveredCloseBtn(false)}
                style={{
                  color: hoveredCloseBtn ? '#1A1A1A' : '#5A5A5A',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'color 0.2s ease',
                }}
              >
                <X style={{ width: '24px', height: '24px' }} />
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Use Case */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, color: '#1A1A1A', marginBottom: '8px' }}>
                  Use Case *
                </label>
                <input
                  type="text"
                  value={subscriptionForm.use_case}
                  onChange={(e) =>
                    setSubscriptionForm({ ...subscriptionForm, use_case: e.target.value })
                  }
                  placeholder="e.g., Customer Analytics Dashboard"
                  style={inputStyle}
                />
              </div>

              {/* Business Justification */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, color: '#1A1A1A', marginBottom: '8px' }}>
                  Business Justification *
                </label>
                <textarea
                  value={subscriptionForm.business_justification}
                  onChange={(e) =>
                    setSubscriptionForm({
                      ...subscriptionForm,
                      business_justification: e.target.value,
                    })
                  }
                  placeholder="Explain why you need access to this dataset..."
                  rows={4}
                  style={{
                    ...inputStyle,
                    resize: 'vertical',
                  }}
                />
              </div>

              {/* SLA Requirements */}
              <div style={{
                backgroundColor: '#F4F3EE',
                borderRadius: '8px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}>
                <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#1A1A1A' }}>
                  SLA Requirements
                </h3>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8A8A8A', marginBottom: '4px' }}>
                    Max Latency (ms)
                  </label>
                  <input
                    type="number"
                    value={subscriptionForm.sla_requirements.max_latency_ms}
                    onChange={(e) =>
                      setSubscriptionForm({
                        ...subscriptionForm,
                        sla_requirements: {
                          ...subscriptionForm.sla_requirements,
                          max_latency_ms: parseInt(e.target.value),
                        },
                      })
                    }
                    style={slaInputStyle}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8A8A8A', marginBottom: '4px' }}>
                    Min Availability (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={subscriptionForm.sla_requirements.min_availability_pct}
                    onChange={(e) =>
                      setSubscriptionForm({
                        ...subscriptionForm,
                        sla_requirements: {
                          ...subscriptionForm.sla_requirements,
                          min_availability_pct: parseFloat(e.target.value),
                        },
                      })
                    }
                    style={slaInputStyle}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: '#8A8A8A', marginBottom: '4px' }}>
                    Max Staleness (minutes)
                  </label>
                  <input
                    type="number"
                    value={subscriptionForm.sla_requirements.max_staleness_minutes}
                    onChange={(e) =>
                      setSubscriptionForm({
                        ...subscriptionForm,
                        sla_requirements: {
                          ...subscriptionForm.sla_requirements,
                          max_staleness_minutes: parseInt(e.target.value),
                        },
                      })
                    }
                    style={slaInputStyle}
                  />
                </div>
              </div>

              {/* Access Duration */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, color: '#1A1A1A', marginBottom: '8px' }}>
                  Access Duration (days)
                </label>
                <input
                  type="number"
                  value={subscriptionForm.access_duration_days}
                  onChange={(e) =>
                    setSubscriptionForm({
                      ...subscriptionForm,
                      access_duration_days: parseInt(e.target.value),
                    })
                  }
                  style={inputStyle}
                />
              </div>

              {/* Fields Selection */}
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 500, color: '#1A1A1A', marginBottom: '8px' }}>
                  Required Fields ({subscriptionForm.required_fields.length} selected)
                </label>
                <div style={{
                  backgroundColor: '#FAF9F6',
                  borderRadius: '8px',
                  padding: '16px',
                  maxHeight: '192px',
                  overflowY: 'auto',
                  border: '1px solid #E5E2DB',
                }}>
                  {selectedDataset.schema?.map((field) => (
                    <label
                      key={field.name}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '8px 0',
                        fontSize: '14px',
                        color: '#1A1A1A',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={subscriptionForm.required_fields.includes(field.name)}
                        onChange={(e) => {
                          const fields = e.target.checked
                            ? [...subscriptionForm.required_fields, field.name]
                            : subscriptionForm.required_fields.filter(f => f !== field.name);
                          setSubscriptionForm({
                            ...subscriptionForm,
                            required_fields: fields,
                          });
                        }}
                      />
                      <span>{field.name}</span>
                      <span style={{ fontSize: '12px', color: '#8A8A8A' }}>({field.type})</span>
                      {field.pii && (
                        <span style={{ fontSize: '12px', color: '#d97706' }}>(PII)</span>
                      )}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{
              position: 'sticky',
              bottom: 0,
              backgroundColor: '#FFFFFF',
              borderTop: '1px solid #E5E2DB',
              padding: '24px',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '16px',
            }}>
              <button
                onClick={() => {
                  setShowSubscriptionForm(false);
                  setSelectedDataset(null);
                }}
                onMouseEnter={() => setHoveredCancelBtn(true)}
                onMouseLeave={() => setHoveredCancelBtn(false)}
                style={{
                  padding: '12px 24px',
                  backgroundColor: hoveredCancelBtn ? '#EEEEE8' : '#F4F3EE',
                  color: '#1A1A1A',
                  borderRadius: '8px',
                  border: '1px solid #E5E2DB',
                  cursor: 'pointer',
                  fontWeight: 500,
                  fontSize: '14px',
                  transition: 'background-color 0.2s ease',
                }}
              >
                Cancel
              </button>
              <button
                onClick={submitSubscription}
                onMouseEnter={() => setHoveredSubmitBtn(true)}
                onMouseLeave={() => setHoveredSubmitBtn(false)}
                style={{
                  padding: '12px 24px',
                  backgroundColor: hoveredSubmitBtn ? '#005a8a' : '#0070AD',
                  color: '#FFFFFF',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 500,
                  fontSize: '14px',
                  transition: 'background-color 0.2s ease',
                }}
              >
                Submit Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
