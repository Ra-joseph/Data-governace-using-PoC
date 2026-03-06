import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Database,
  FileText,
  Shield,
  CheckCircle,
  ChevronRight,
  ChevronLeft,
  AlertCircle
} from 'lucide-react';
import { datasetAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const inputStyle = {
  width: '100%',
  padding: '0.75rem 1rem',
  background: 'var(--color-bg-tertiary)',
  border: '1px solid var(--color-border-default)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--color-text-primary)',
  fontSize: '0.9375rem',
  outline: 'none',
};

const labelStyle = {
  display: 'block',
  fontSize: '0.875rem',
  fontWeight: 500,
  color: 'var(--color-text-secondary)',
  marginBottom: '0.5rem',
};

const smallLabelStyle = {
  display: 'block',
  fontSize: '0.75rem',
  color: 'var(--color-text-tertiary)',
  marginBottom: '0.25rem',
};

const sectionCardStyle = {
  background: 'var(--color-bg-tertiary)',
  borderRadius: 'var(--radius-lg)',
  padding: '1rem',
};

export function DatasetRegistrationWizard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [importMode, setImportMode] = useState('manual'); // 'manual' or 'postgres'
  const [availableTables, setAvailableTables] = useState([]);

  const [formData, setFormData] = useState({
    // Basic Info
    name: '',
    description: '',
    source_system: '',
    owner_name: user?.name || '',
    owner_email: user?.email || '',

    // Classification
    classification: 'internal',
    contains_pii: false,
    compliance_tags: [],

    // Schema
    schema: [],

    // Governance
    retention_period_days: 365,
    use_cases: [],
    data_residency: '',
  });

  const steps = [
    {
      title: 'Basic Information',
      description: 'Dataset name and description',
      icon: Database,
    },
    {
      title: 'Schema Definition',
      description: 'Define dataset schema',
      icon: FileText,
    },
    {
      title: 'Governance & Compliance',
      description: 'Set governance policies',
      icon: Shield,
    },
    {
      title: 'Review & Submit',
      description: 'Review and submit dataset',
      icon: CheckCircle,
    },
  ];

  const classifications = ['public', 'internal', 'confidential', 'restricted'];
  const complianceTags = ['GDPR', 'CCPA', 'HIPAA', 'SOC2', 'PCI-DSS'];
  const dataTypes = ['string', 'integer', 'float', 'boolean', 'date', 'timestamp', 'json'];

  const loadPostgresTables = async () => {
    try {
      const response = await datasetAPI.listPostgresTables();
      setAvailableTables(response.data);
    } catch (error) {
      toast.error('Failed to load PostgreSQL tables');
    }
  };

  const importFromPostgres = async (tableName) => {
    try {
      const response = await datasetAPI.importSchema({
        source_type: 'postgresql',
        table_name: tableName,
        schema: 'public',
      });

      const importedData = response.data;
      setFormData(prev => ({
        ...prev,
        name: importedData.name || tableName,
        description: importedData.description || '',
        schema: importedData.schema || [],
        contains_pii: importedData.schema?.some(col => col.pii) || false,
      }));

      toast.success(`Schema imported from ${tableName}`);
      setCurrentStep(2); // Skip to governance step
    } catch (error) {
      toast.error('Failed to import schema');
    }
  };

  const addSchemaField = () => {
    setFormData(prev => ({
      ...prev,
      schema: [
        ...prev.schema,
        {
          name: '',
          type: 'string',
          nullable: true,
          description: '',
          pii: false,
        }
      ]
    }));
  };

  const updateSchemaField = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      schema: prev.schema.map((col, i) =>
        i === index ? { ...col, [field]: value } : col
      )
    }));
  };

  const removeSchemaField = (index) => {
    setFormData(prev => ({
      ...prev,
      schema: prev.schema.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await datasetAPI.create(formData);
      toast.success('Dataset registered successfully!');
      navigate(`/owner/datasets/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to register dataset');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return formData.name && formData.description && formData.source_system;
      case 1:
        return formData.schema.length > 0;
      case 2:
        return formData.retention_period_days > 0;
      default:
        return true;
    }
  };

  const getStepCircleStyle = (isCompleted, isActive) => {
    if (isCompleted) {
      return {
        width: '3rem',
        height: '3rem',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '2px solid #16a34a',
        background: '#16a34a',
        color: 'white',
        transition: 'all 0.2s ease',
      };
    }
    if (isActive) {
      return {
        width: '3rem',
        height: '3rem',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '2px solid #0070AD',
        background: '#0070AD',
        color: 'white',
        transition: 'all 0.2s ease',
      };
    }
    return {
      width: '3rem',
      height: '3rem',
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      border: '2px solid var(--color-border-default)',
      background: 'var(--color-bg-elevated)',
      color: 'var(--color-text-tertiary)',
      transition: 'all 0.2s ease',
    };
  };

  const getSelectedButtonStyle = (isSelected) => {
    if (isSelected) {
      return {
        padding: '0.75rem 1rem',
        borderRadius: 'var(--radius-md)',
        border: '2px solid var(--color-accent-primary)',
        background: 'rgba(0, 112, 173, 0.1)',
        color: 'var(--color-text-primary)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        textTransform: 'capitalize',
      };
    }
    return {
      padding: '0.75rem 1rem',
      borderRadius: 'var(--radius-md)',
      border: '2px solid var(--color-border-default)',
      background: 'transparent',
      color: 'var(--color-text-secondary)',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      textTransform: 'capitalize',
    };
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--color-bg-primary)',
      padding: 'var(--space-xl) var(--space-md)',
    }}>
      <div style={{ maxWidth: '64rem', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: 'var(--space-xl)' }}>
          <h1 style={{
            fontSize: '1.875rem',
            fontWeight: 700,
            color: 'var(--color-text-primary)',
            fontFamily: 'var(--font-display)',
            marginBottom: '0.5rem',
          }}>
            Register New Dataset
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Follow the steps to register your dataset with the governance platform
          </p>
        </div>

        {/* Progress Steps */}
        <div style={{ marginBottom: '3rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;

              return (
                <div key={index} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                    <div style={getStepCircleStyle(isCompleted, isActive)}>
                      <Icon style={{ width: '1.5rem', height: '1.5rem' }} />
                    </div>
                    <div style={{ marginTop: '0.5rem', textAlign: 'center' }}>
                      <p style={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                      }}>
                        {step.title}
                      </p>
                      <p style={{
                        fontSize: '0.75rem',
                        color: 'var(--color-text-muted)',
                        marginTop: '0.25rem',
                      }}>
                        {step.description}
                      </p>
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div style={{
                      height: '2px',
                      flex: 1,
                      margin: '0 1rem',
                      background: isCompleted ? '#16a34a' : 'var(--color-border-default)',
                    }} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div style={{
          background: 'var(--color-bg-secondary)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--color-border-default)',
          padding: 'var(--space-xl)',
          boxShadow: 'var(--shadow-sm)',
        }}>
          {/* Step 0: Basic Information */}
          {currentStep === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <label style={labelStyle}>
                  Dataset Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., customer_accounts"
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the purpose and contents of this dataset"
                  rows={4}
                  style={{ ...inputStyle, resize: 'vertical' }}
                />
              </div>

              <div>
                <label style={labelStyle}>
                  Source System *
                </label>
                <input
                  type="text"
                  value={formData.source_system}
                  onChange={(e) => setFormData({ ...formData, source_system: e.target.value })}
                  placeholder="e.g., PostgreSQL Production DB"
                  style={inputStyle}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div>
                  <label style={labelStyle}>
                    Owner Name
                  </label>
                  <input
                    type="text"
                    value={formData.owner_name}
                    onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                    style={inputStyle}
                  />
                </div>

                <div>
                  <label style={labelStyle}>
                    Owner Email
                  </label>
                  <input
                    type="email"
                    value={formData.owner_email}
                    onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                    style={inputStyle}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 1: Schema Definition */}
          {currentStep === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Import Mode Selection */}
              <div style={{
                ...sectionCardStyle,
                marginBottom: '0.5rem',
              }}>
                <p style={{
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: 'var(--color-text-secondary)',
                  marginBottom: '0.75rem',
                }}>
                  Choose how to define your schema:
                </p>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    onClick={() => setImportMode('manual')}
                    style={{
                      ...getSelectedButtonStyle(importMode === 'manual'),
                      flex: 1,
                    }}
                  >
                    Manual Entry
                  </button>
                  <button
                    onClick={() => {
                      setImportMode('postgres');
                      loadPostgresTables();
                    }}
                    style={{
                      ...getSelectedButtonStyle(importMode === 'postgres'),
                      flex: 1,
                    }}
                  >
                    Import from PostgreSQL
                  </button>
                </div>
              </div>

              {/* PostgreSQL Import */}
              {importMode === 'postgres' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    Select a table to import:
                  </p>
                  {availableTables.map((table) => (
                    <button
                      key={table}
                      onClick={() => importFromPostgres(table)}
                      style={{
                        width: '100%',
                        padding: '0.75rem 1rem',
                        background: 'var(--color-bg-tertiary)',
                        border: '1px solid var(--color-border-default)',
                        borderRadius: 'var(--radius-md)',
                        textAlign: 'left',
                        color: 'var(--color-text-primary)',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      <Database style={{ width: '1rem', height: '1rem', display: 'inline', marginRight: '0.5rem' }} />
                      {table}
                    </button>
                  ))}
                </div>
              )}

              {/* Manual Schema Entry */}
              {importMode === 'manual' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {formData.schema.map((field, index) => (
                    <div
                      key={index}
                      style={{
                        ...sectionCardStyle,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.75rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <h4 style={{
                          fontSize: '0.875rem',
                          fontWeight: 500,
                          color: 'var(--color-text-secondary)',
                        }}>
                          Field {index + 1}
                        </h4>
                        <button
                          onClick={() => removeSchemaField(index)}
                          style={{
                            color: 'var(--color-error)',
                            fontSize: '0.875rem',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                          }}
                        >
                          Remove
                        </button>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div>
                          <label style={smallLabelStyle}>
                            Field Name
                          </label>
                          <input
                            type="text"
                            value={field.name}
                            onChange={(e) =>
                              updateSchemaField(index, 'name', e.target.value)
                            }
                            placeholder="e.g., customer_id"
                            style={{ ...inputStyle, fontSize: '0.875rem' }}
                          />
                        </div>

                        <div>
                          <label style={smallLabelStyle}>
                            Data Type
                          </label>
                          <select
                            value={field.type}
                            onChange={(e) =>
                              updateSchemaField(index, 'type', e.target.value)
                            }
                            style={{ ...inputStyle, fontSize: '0.875rem' }}
                          >
                            {dataTypes.map((type) => (
                              <option key={type} value={type}>
                                {type}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div>
                        <label style={smallLabelStyle}>
                          Description
                        </label>
                        <input
                          type="text"
                          value={field.description}
                          onChange={(e) =>
                            updateSchemaField(index, 'description', e.target.value)
                          }
                          placeholder="Describe this field"
                          style={{ ...inputStyle, fontSize: '0.875rem' }}
                        />
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <label style={{
                          display: 'flex',
                          alignItems: 'center',
                          fontSize: '0.875rem',
                          color: 'var(--color-text-secondary)',
                          cursor: 'pointer',
                        }}>
                          <input
                            type="checkbox"
                            checked={field.nullable}
                            onChange={(e) =>
                              updateSchemaField(index, 'nullable', e.target.checked)
                            }
                            style={{ marginRight: '0.5rem' }}
                          />
                          Nullable
                        </label>

                        <label style={{
                          display: 'flex',
                          alignItems: 'center',
                          fontSize: '0.875rem',
                          color: 'var(--color-text-secondary)',
                          cursor: 'pointer',
                        }}>
                          <input
                            type="checkbox"
                            checked={field.pii}
                            onChange={(e) => {
                              updateSchemaField(index, 'pii', e.target.checked);
                              if (e.target.checked) {
                                setFormData(prev => ({ ...prev, contains_pii: true }));
                              }
                            }}
                            style={{ marginRight: '0.5rem' }}
                          />
                          Contains PII
                        </label>
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={addSchemaField}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      background: 'rgba(0, 112, 173, 0.08)',
                      border: '2px dashed var(--color-accent-primary)',
                      borderRadius: 'var(--radius-md)',
                      color: 'var(--color-accent-primary)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontSize: '0.9375rem',
                    }}
                  >
                    + Add Field
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Governance & Compliance */}
          {currentStep === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <label style={labelStyle}>
                  Data Classification *
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  {classifications.map((cls) => (
                    <button
                      key={cls}
                      onClick={() => setFormData({ ...formData, classification: cls })}
                      style={getSelectedButtonStyle(formData.classification === cls)}
                    >
                      {cls}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label style={labelStyle}>
                  Compliance Tags
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {complianceTags.map((tag) => {
                    const isSelected = formData.compliance_tags.includes(tag);
                    return (
                      <button
                        key={tag}
                        onClick={() => {
                          const tags = formData.compliance_tags.includes(tag)
                            ? formData.compliance_tags.filter(t => t !== tag)
                            : [...formData.compliance_tags, tag];
                          setFormData({ ...formData, compliance_tags: tags });
                        }}
                        style={{
                          padding: '0.5rem 1rem',
                          borderRadius: 'var(--radius-md)',
                          border: isSelected
                            ? '1px solid var(--color-accent-primary)'
                            : '1px solid var(--color-border-default)',
                          background: isSelected ? 'rgba(0, 112, 173, 0.1)' : 'transparent',
                          color: isSelected ? 'var(--color-accent-primary)' : 'var(--color-text-secondary)',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label style={labelStyle}>
                  Retention Period (days) *
                </label>
                <input
                  type="number"
                  value={formData.retention_period_days}
                  onChange={(e) =>
                    setFormData({ ...formData, retention_period_days: parseInt(e.target.value) })
                  }
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>
                  Use Cases (one per line)
                </label>
                <textarea
                  value={formData.use_cases.join('\n')}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      use_cases: e.target.value.split('\n').filter(uc => uc.trim())
                    })
                  }
                  placeholder="Enter approved use cases for this dataset"
                  rows={4}
                  style={{ ...inputStyle, resize: 'vertical' }}
                />
              </div>

              {formData.contains_pii && (
                <div>
                  <label style={labelStyle}>
                    Data Residency
                    <span style={{
                      fontSize: '0.75rem',
                      color: 'var(--color-text-tertiary)',
                      marginLeft: '0.5rem',
                    }}>
                      (Required for PII data)
                    </span>
                  </label>
                  <input
                    type="text"
                    value={formData.data_residency}
                    onChange={(e) =>
                      setFormData({ ...formData, data_residency: e.target.value })
                    }
                    placeholder="e.g., US-EAST, EU-WEST"
                    style={inputStyle}
                  />
                </div>
              )}
            </div>
          )}

          {/* Step 3: Review & Submit */}
          {currentStep === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{
                background: 'rgba(0, 112, 173, 0.08)',
                border: '1px solid rgba(0, 112, 173, 0.25)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
              }}>
                <AlertCircle style={{
                  width: '1.25rem',
                  height: '1.25rem',
                  color: 'var(--color-accent-primary)',
                  flexShrink: 0,
                  marginTop: '0.125rem',
                }} />
                <div>
                  <h4 style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: 'var(--color-accent-primary)',
                    marginBottom: '0.25rem',
                  }}>
                    Review Before Submitting
                  </h4>
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    Please review your dataset information. Once submitted, a data contract will be
                    generated and validated against governance policies.
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={sectionCardStyle}>
                  <h4 style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                    marginBottom: '0.75rem',
                  }}>
                    Basic Information
                  </h4>
                  <dl style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <dt style={{ color: 'var(--color-text-tertiary)' }}>Name:</dt>
                      <dd style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>{formData.name}</dd>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <dt style={{ color: 'var(--color-text-tertiary)' }}>Source:</dt>
                      <dd style={{ color: 'var(--color-text-primary)' }}>{formData.source_system}</dd>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <dt style={{ color: 'var(--color-text-tertiary)' }}>Owner:</dt>
                      <dd style={{ color: 'var(--color-text-primary)' }}>{formData.owner_name}</dd>
                    </div>
                  </dl>
                </div>

                <div style={sectionCardStyle}>
                  <h4 style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                    marginBottom: '0.75rem',
                  }}>
                    Schema
                  </h4>
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    {formData.schema.length} fields defined
                    {formData.contains_pii && (
                      <span style={{ marginLeft: '0.5rem', color: 'var(--color-warning)' }}>
                        (Contains PII)
                      </span>
                    )}
                  </p>
                </div>

                <div style={sectionCardStyle}>
                  <h4 style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: 'var(--color-text-secondary)',
                    marginBottom: '0.75rem',
                  }}>
                    Governance
                  </h4>
                  <dl style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.875rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <dt style={{ color: 'var(--color-text-tertiary)' }}>Classification:</dt>
                      <dd style={{ color: 'var(--color-text-primary)', textTransform: 'capitalize' }}>{formData.classification}</dd>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <dt style={{ color: 'var(--color-text-tertiary)' }}>Retention:</dt>
                      <dd style={{ color: 'var(--color-text-primary)' }}>{formData.retention_period_days} days</dd>
                    </div>
                    {formData.compliance_tags.length > 0 && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <dt style={{ color: 'var(--color-text-tertiary)' }}>Compliance:</dt>
                        <dd style={{ color: 'var(--color-text-primary)' }}>{formData.compliance_tags.join(', ')}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'var(--space-xl)' }}>
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'var(--color-bg-elevated)',
              color: 'var(--color-text-primary)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border-default)',
              cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
              opacity: currentStep === 0 ? 0.5 : 1,
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontWeight: 500,
            }}
          >
            <ChevronLeft style={{ width: '1.25rem', height: '1.25rem' }} />
            Previous
          </button>

          {currentStep < steps.length - 1 ? (
            <button
              onClick={() => setCurrentStep(currentStep + 1)}
              disabled={!canProceed()}
              style={{
                padding: '0.75rem 1.5rem',
                background: canProceed() ? 'var(--color-accent-primary)' : 'var(--color-bg-elevated)',
                color: canProceed() ? '#FFFFFF' : 'var(--color-text-muted)',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                cursor: canProceed() ? 'pointer' : 'not-allowed',
                opacity: canProceed() ? 1 : 0.5,
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 500,
              }}
            >
              Next
              <ChevronRight style={{ width: '1.25rem', height: '1.25rem' }} />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading || !canProceed()}
              style={{
                padding: '0.75rem 1.5rem',
                background: (!loading && canProceed()) ? 'var(--color-success)' : 'var(--color-bg-elevated)',
                color: (!loading && canProceed()) ? '#FFFFFF' : 'var(--color-text-muted)',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                cursor: (loading || !canProceed()) ? 'not-allowed' : 'pointer',
                opacity: (loading || !canProceed()) ? 0.5 : 1,
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 500,
              }}
            >
              {loading ? 'Submitting...' : 'Submit Dataset'}
              <CheckCircle style={{ width: '1.25rem', height: '1.25rem' }} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
