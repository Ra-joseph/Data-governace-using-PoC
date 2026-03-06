import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  Database,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Plus
} from 'lucide-react';
import { datasetAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { SkeletonLoader } from '../../components/SkeletonLoader';

export function OwnerDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    withViolations: 0,
    active: 0,
    subscribers: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // Load datasets owned by current user
      const response = await datasetAPI.list({
        owner_email: user?.email,
      });
      const datasetsData = response.data;
      setDatasets(datasetsData);

      // Calculate stats
      const withViolations = datasetsData.filter(
        ds => ds.contract?.validation_result?.status === 'failed'
      ).length;

      const allViolations = datasetsData
        .filter(ds => ds.contract?.validation_result?.violations)
        .flatMap(ds =>
          ds.contract.validation_result.violations.map(v => ({
            ...v,
            dataset: ds.name,
            datasetId: ds.id,
          }))
        );

      setViolations(allViolations);
      setStats({
        total: datasetsData.length,
        withViolations,
        active: datasetsData.filter(ds => ds.status === 'published').length,
        subscribers: datasetsData.reduce((sum, ds) => sum + (ds.subscriber_count || 0), 0),
      });
    } catch (err) {
      toast.error('Failed to load datasets');
      setError('Failed to load your datasets. Please refresh to try again.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityStyle = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return { color: 'var(--color-error)', backgroundColor: 'rgba(220, 38, 38, 0.1)' };
      case 'warning':
        return { color: 'var(--color-warning)', backgroundColor: 'rgba(217, 119, 6, 0.1)' };
      default:
        return { color: 'var(--color-accent-primary)', backgroundColor: 'rgba(0, 112, 173, 0.1)' };
    }
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case 'published':
        return { color: 'var(--color-success)', backgroundColor: 'rgba(22, 163, 74, 0.1)' };
      case 'draft':
        return { color: 'var(--color-text-tertiary)', backgroundColor: 'var(--color-bg-tertiary)' };
      default:
        return { color: 'var(--color-warning)', backgroundColor: 'rgba(217, 119, 6, 0.1)' };
    }
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-primary)',
        padding: 'var(--space-2xl)',
      }}>
        <div style={{ maxWidth: '80rem', margin: '0 auto' }}>
          <div style={{ marginBottom: 'var(--space-2xl)' }}>
            <div className="skeleton" style={{ height: 36, width: 280, borderRadius: 'var(--radius-md)', marginBottom: '0.5rem' }} />
            <div className="skeleton" style={{ height: 18, width: 340, borderRadius: 'var(--radius-sm)' }} />
          </div>
          <div style={{ marginBottom: 'var(--space-2xl)' }}>
            <SkeletonLoader type="stat" count={4} />
          </div>
          <SkeletonLoader type="row" count={5} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-primary)',
        padding: 'var(--space-2xl)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <div style={{
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border-default)',
          borderRadius: 'var(--radius-xl)',
          padding: '3rem 2rem',
          textAlign: 'center',
          maxWidth: 400,
        }}>
          <div style={{
            width: 56, height: 56,
            background: 'rgba(220,38,38,0.08)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1rem',
            color: 'var(--color-error)',
          }}>
            <AlertTriangle size={28} />
          </div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--color-text-primary)' }}>
            Unable to load datasets
          </h3>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1.5rem' }}>{error}</p>
          <button
            onClick={() => { setError(null); setLoading(true); loadData(); }}
            style={{
              padding: '0.625rem 1.5rem',
              background: 'var(--color-accent-primary)',
              color: '#fff', border: 'none',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600, cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-primary)',
      padding: 'var(--space-2xl)',
    }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto' }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--space-2xl)',
        }}>
          <div>
            <h1 style={{
              fontSize: '1.875rem',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-sm)',
              fontFamily: 'var(--font-display)',
            }}>
              Data Owner Dashboard
            </h1>
            <p style={{ color: 'var(--color-text-tertiary)' }}>
              Manage your datasets and track governance compliance
            </p>
          </div>

          <button
            onClick={() => navigate('/owner/register')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'var(--color-accent-primary)',
              color: '#FFFFFF',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-sm)',
              fontWeight: 500,
              fontSize: '0.875rem',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#005a8a'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--color-accent-primary)'}
          >
            <Plus style={{ width: '1.25rem', height: '1.25rem' }} />
            Register Dataset
          </button>
        </div>

        {/* Stats Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 'var(--space-lg)',
          marginBottom: 'var(--space-2xl)',
        }}>
          <div style={{
            backgroundColor: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
            padding: 'var(--space-lg)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--space-md)',
            }}>
              <Database style={{ width: '2rem', height: '2rem', color: 'var(--color-accent-primary)' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.total}</span>
            </div>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>Total Datasets</p>
          </div>

          <div style={{
            backgroundColor: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
            padding: 'var(--space-lg)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--space-md)',
            }}>
              <AlertTriangle style={{ width: '2rem', height: '2rem', color: 'var(--color-error)' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.withViolations}</span>
            </div>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>With Violations</p>
          </div>

          <div style={{
            backgroundColor: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
            padding: 'var(--space-lg)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--space-md)',
            }}>
              <CheckCircle style={{ width: '2rem', height: '2rem', color: 'var(--color-success)' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.active}</span>
            </div>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>Active Datasets</p>
          </div>

          <div style={{
            backgroundColor: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
            padding: 'var(--space-lg)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--space-md)',
            }}>
              <Users style={{ width: '2rem', height: '2rem', color: 'var(--color-accent-primary)' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.subscribers}</span>
            </div>
            <p style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>Total Subscribers</p>
          </div>
        </div>

        {/* Violations Alert */}
        {violations.length > 0 && (
          <div style={{
            backgroundColor: 'rgba(220, 38, 38, 0.08)',
            border: '1px solid rgba(220, 38, 38, 0.25)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-lg)',
            marginBottom: 'var(--space-2xl)',
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-md)' }}>
              <AlertTriangle style={{
                width: '1.5rem',
                height: '1.5rem',
                color: 'var(--color-error)',
                flexShrink: 0,
                marginTop: '0.25rem',
              }} />
              <div style={{ flex: 1 }}>
                <h3 style={{
                  fontSize: '1.125rem',
                  fontWeight: 600,
                  color: 'var(--color-error)',
                  marginBottom: 'var(--space-sm)',
                }}>
                  Active Policy Violations
                </h3>
                <p style={{
                  color: 'var(--color-text-secondary)',
                  marginBottom: 'var(--space-md)',
                }}>
                  You have {violations.length} policy violation(s) across your datasets that need attention.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {violations.slice(0, 5).map((violation, index) => (
                    <div
                      key={index}
                      style={{
                        backgroundColor: 'var(--color-bg-secondary)',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--space-md)',
                        cursor: 'pointer',
                        border: '1px solid var(--color-border-default)',
                        transition: 'background-color 0.2s',
                      }}
                      onClick={() => navigate(`/owner/datasets/${violation.datasetId}`)}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--color-bg-secondary)'}
                    >
                      <div style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                        marginBottom: 'var(--space-sm)',
                      }}>
                        <div>
                          <span style={{
                            fontSize: '0.75rem',
                            color: 'var(--color-text-muted)',
                          }}>Dataset:</span>
                          <span style={{
                            color: 'var(--color-text-primary)',
                            fontWeight: 500,
                            marginLeft: 'var(--space-sm)',
                          }}>
                            {violation.dataset}
                          </span>
                        </div>
                        <span
                          style={{
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            ...getSeverityStyle(violation.type),
                          }}
                        >
                          {violation.type?.toUpperCase()}
                        </span>
                      </div>
                      <p style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-secondary)',
                        marginBottom: 'var(--space-sm)',
                      }}>{violation.policy}</p>
                      <p style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-tertiary)',
                      }}>{violation.message}</p>
                      {violation.remediation && (
                        <div style={{
                          marginTop: '0.75rem',
                          paddingTop: '0.75rem',
                          borderTop: '1px solid var(--color-border-default)',
                        }}>
                          <p style={{
                            fontSize: '0.75rem',
                            color: 'var(--color-text-muted)',
                            marginBottom: '0.25rem',
                          }}>How to fix:</p>
                          <p style={{
                            fontSize: '0.75rem',
                            color: 'var(--color-text-tertiary)',
                          }}>{violation.remediation}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {violations.length > 5 && (
                  <button
                    onClick={() => navigate('/owner/violations')}
                    style={{
                      marginTop: 'var(--space-md)',
                      fontSize: '0.875rem',
                      color: 'var(--color-error)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                  >
                    View all {violations.length} violations →
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Datasets List */}
        <div style={{
          backgroundColor: 'var(--color-bg-secondary)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-default)',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <div style={{
            padding: 'var(--space-lg)',
            borderBottom: '1px solid var(--color-border-default)',
          }}>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              fontFamily: 'var(--font-display)',
            }}>Your Datasets</h2>
          </div>

          <div>
            {datasets.length === 0 ? (
              <div style={{
                padding: '3rem',
                textAlign: 'center',
              }}>
                <Database style={{
                  width: '4rem',
                  height: '4rem',
                  color: 'var(--color-text-muted)',
                  margin: '0 auto 1rem',
                  display: 'block',
                }} />
                <h3 style={{
                  fontSize: '1.125rem',
                  fontWeight: 600,
                  color: 'var(--color-text-tertiary)',
                  marginBottom: 'var(--space-sm)',
                }}>
                  No datasets yet
                </h3>
                <p style={{
                  color: 'var(--color-text-muted)',
                  marginBottom: 'var(--space-lg)',
                }}>
                  Start by registering your first dataset
                </p>
                <button
                  onClick={() => navigate('/owner/register')}
                  style={{
                    padding: '0.75rem 1.5rem',
                    backgroundColor: 'var(--color-accent-primary)',
                    color: '#FFFFFF',
                    borderRadius: 'var(--radius-md)',
                    border: 'none',
                    cursor: 'pointer',
                    fontWeight: 500,
                    transition: 'background-color 0.2s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#005a8a'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--color-accent-primary)'}
                >
                  Register Dataset
                </button>
              </div>
            ) : (
              datasets.map((dataset, index) => (
                <div
                  key={dataset.id}
                  style={{
                    padding: 'var(--space-lg)',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    borderTop: index > 0 ? '1px solid var(--color-border-default)' : 'none',
                  }}
                  onClick={() => navigate(`/owner/datasets/${dataset.id}`)}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--color-bg-tertiary)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    marginBottom: '0.75rem',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        marginBottom: 'var(--space-sm)',
                      }}>
                        <h3 style={{
                          fontSize: '1.125rem',
                          fontWeight: 600,
                          color: 'var(--color-text-primary)',
                        }}>
                          {dataset.name}
                        </h3>
                        <span
                          style={{
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            ...getStatusStyle(dataset.status),
                          }}
                        >
                          {dataset.status}
                        </span>
                        {dataset.contract?.validation_result?.status === 'failed' && (
                          <span style={{
                            padding: '0.25rem 0.75rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            backgroundColor: 'rgba(220, 38, 38, 0.1)',
                            color: 'var(--color-error)',
                          }}>
                            Has Violations
                          </span>
                        )}
                      </div>
                      <p style={{
                        color: 'var(--color-text-tertiary)',
                        fontSize: '0.875rem',
                        marginBottom: '0.75rem',
                      }}>
                        {dataset.description}
                      </p>

                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--color-text-muted)',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                          <Database style={{ width: '1rem', height: '1rem' }} />
                          <span>{dataset.source_system}</span>
                        </div>
                        {dataset.classification && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                            <span style={{ textTransform: 'capitalize' }}>{dataset.classification}</span>
                          </div>
                        )}
                        {dataset.subscriber_count > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                            <Users style={{ width: '1rem', height: '1rem' }} />
                            <span>{dataset.subscriber_count} subscribers</span>
                          </div>
                        )}
                        {dataset.created_at && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                            <Clock style={{ width: '1rem', height: '1rem' }} />
                            <span>{new Date(dataset.created_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {dataset.contract?.validation_result && (
                      <div style={{ textAlign: 'right' }}>
                        {dataset.contract.validation_result.status === 'passed' ? (
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 'var(--space-sm)',
                            color: 'var(--color-success)',
                          }}>
                            <CheckCircle style={{ width: '1.25rem', height: '1.25rem' }} />
                            <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>Compliant</span>
                          </div>
                        ) : (
                          <div style={{ color: 'var(--color-error)' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                              {dataset.contract.validation_result.failures || 0}
                            </div>
                            <div style={{ fontSize: '0.75rem' }}>violations</div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
