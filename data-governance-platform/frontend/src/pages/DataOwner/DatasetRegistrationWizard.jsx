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

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Register New Dataset
          </h1>
          <p className="text-gray-400">
            Follow the steps to register your dataset with the governance platform
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;

              return (
                <div key={index} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${
                        isCompleted
                          ? 'bg-green-500 border-green-500'
                          : isActive
                          ? 'bg-purple-500 border-purple-500'
                          : 'bg-gray-800 border-gray-700'
                      }`}
                    >
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div className="mt-2 text-center">
                      <p
                        className={`text-sm font-semibold ${
                          isActive ? 'text-white' : 'text-gray-500'
                        }`}
                      >
                        {step.title}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        {step.description}
                      </p>
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`h-0.5 flex-1 mx-4 ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-800'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-8">
          {/* Step 0: Basic Information */}
          {currentStep === 0 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Dataset Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., customer_accounts"
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe the purpose and contents of this dataset"
                  rows={4}
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Source System *
                </label>
                <input
                  type="text"
                  value={formData.source_system}
                  onChange={(e) => setFormData({ ...formData, source_system: e.target.value })}
                  placeholder="e.g., PostgreSQL Production DB"
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Owner Name
                  </label>
                  <input
                    type="text"
                    value={formData.owner_name}
                    onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Owner Email
                  </label>
                  <input
                    type="email"
                    value={formData.owner_email}
                    onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 1: Schema Definition */}
          {currentStep === 1 && (
            <div className="space-y-6">
              {/* Import Mode Selection */}
              <div className="bg-gray-900 rounded-lg p-4 mb-6">
                <p className="text-sm font-medium text-gray-300 mb-3">
                  Choose how to define your schema:
                </p>
                <div className="flex gap-4">
                  <button
                    onClick={() => setImportMode('manual')}
                    className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                      importMode === 'manual'
                        ? 'border-purple-500 bg-purple-500/10 text-white'
                        : 'border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    Manual Entry
                  </button>
                  <button
                    onClick={() => {
                      setImportMode('postgres');
                      loadPostgresTables();
                    }}
                    className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                      importMode === 'postgres'
                        ? 'border-purple-500 bg-purple-500/10 text-white'
                        : 'border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    Import from PostgreSQL
                  </button>
                </div>
              </div>

              {/* PostgreSQL Import */}
              {importMode === 'postgres' && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-400">
                    Select a table to import:
                  </p>
                  {availableTables.map((table) => (
                    <button
                      key={table}
                      onClick={() => importFromPostgres(table)}
                      className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-left text-white hover:border-purple-500 transition-all"
                    >
                      <Database className="w-4 h-4 inline mr-2" />
                      {table}
                    </button>
                  ))}
                </div>
              )}

              {/* Manual Schema Entry */}
              {importMode === 'manual' && (
                <div className="space-y-4">
                  {formData.schema.map((field, index) => (
                    <div
                      key={index}
                      className="bg-gray-900 rounded-lg p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium text-gray-300">
                          Field {index + 1}
                        </h4>
                        <button
                          onClick={() => removeSchemaField(index)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            Field Name
                          </label>
                          <input
                            type="text"
                            value={field.name}
                            onChange={(e) =>
                              updateSchemaField(index, 'name', e.target.value)
                            }
                            placeholder="e.g., customer_id"
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            Data Type
                          </label>
                          <select
                            value={field.type}
                            onChange={(e) =>
                              updateSchemaField(index, 'type', e.target.value)
                            }
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
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
                        <label className="block text-xs text-gray-500 mb-1">
                          Description
                        </label>
                        <input
                          type="text"
                          value={field.description}
                          onChange={(e) =>
                            updateSchemaField(index, 'description', e.target.value)
                          }
                          placeholder="Describe this field"
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                        />
                      </div>

                      <div className="flex items-center gap-6">
                        <label className="flex items-center text-sm text-gray-300">
                          <input
                            type="checkbox"
                            checked={field.nullable}
                            onChange={(e) =>
                              updateSchemaField(index, 'nullable', e.target.checked)
                            }
                            className="mr-2"
                          />
                          Nullable
                        </label>

                        <label className="flex items-center text-sm text-gray-300">
                          <input
                            type="checkbox"
                            checked={field.pii}
                            onChange={(e) => {
                              updateSchemaField(index, 'pii', e.target.checked);
                              if (e.target.checked) {
                                setFormData(prev => ({ ...prev, contains_pii: true }));
                              }
                            }}
                            className="mr-2"
                          />
                          Contains PII
                        </label>
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={addSchemaField}
                    className="w-full px-4 py-3 bg-purple-500/10 border-2 border-dashed border-purple-500 rounded-lg text-purple-400 hover:bg-purple-500/20 transition-all"
                  >
                    + Add Field
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Governance & Compliance */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Data Classification *
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {classifications.map((cls) => (
                    <button
                      key={cls}
                      onClick={() => setFormData({ ...formData, classification: cls })}
                      className={`px-4 py-3 rounded-lg border-2 capitalize transition-all ${
                        formData.classification === cls
                          ? 'border-purple-500 bg-purple-500/10 text-white'
                          : 'border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      {cls}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Compliance Tags
                </label>
                <div className="flex flex-wrap gap-2">
                  {complianceTags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => {
                        const tags = formData.compliance_tags.includes(tag)
                          ? formData.compliance_tags.filter(t => t !== tag)
                          : [...formData.compliance_tags, tag];
                        setFormData({ ...formData, compliance_tags: tags });
                      }}
                      className={`px-4 py-2 rounded-lg border transition-all ${
                        formData.compliance_tags.includes(tag)
                          ? 'border-purple-500 bg-purple-500/10 text-white'
                          : 'border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Retention Period (days) *
                </label>
                <input
                  type="number"
                  value={formData.retention_period_days}
                  onChange={(e) =>
                    setFormData({ ...formData, retention_period_days: parseInt(e.target.value) })
                  }
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
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
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              {formData.contains_pii && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Data Residency
                    <span className="text-xs text-gray-500 ml-2">
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
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              )}
            </div>
          )}

          {/* Step 3: Review & Submit */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-blue-400 mb-1">
                    Review Before Submitting
                  </h4>
                  <p className="text-sm text-gray-400">
                    Please review your dataset information. Once submitted, a data contract will be
                    generated and validated against governance policies.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-300 mb-3">
                    Basic Information
                  </h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Name:</dt>
                      <dd className="text-white font-medium">{formData.name}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Source:</dt>
                      <dd className="text-white">{formData.source_system}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Owner:</dt>
                      <dd className="text-white">{formData.owner_name}</dd>
                    </div>
                  </dl>
                </div>

                <div className="bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-300 mb-3">
                    Schema
                  </h4>
                  <p className="text-sm text-gray-400">
                    {formData.schema.length} fields defined
                    {formData.contains_pii && (
                      <span className="ml-2 text-yellow-400">
                        (Contains PII)
                      </span>
                    )}
                  </p>
                </div>

                <div className="bg-gray-900 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-300 mb-3">
                    Governance
                  </h4>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Classification:</dt>
                      <dd className="text-white capitalize">{formData.classification}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Retention:</dt>
                      <dd className="text-white">{formData.retention_period_days} days</dd>
                    </div>
                    {formData.compliance_tags.length > 0 && (
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Compliance:</dt>
                        <dd className="text-white">{formData.compliance_tags.join(', ')}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <ChevronLeft className="w-5 h-5" />
            Previous
          </button>

          {currentStep < steps.length - 1 ? (
            <button
              onClick={() => setCurrentStep(currentStep + 1)}
              disabled={!canProceed()}
              className="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              Next
              <ChevronRight className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading || !canProceed()}
              className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? 'Submitting...' : 'Submit Dataset'}
              <CheckCircle className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
