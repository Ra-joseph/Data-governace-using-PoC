import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  User,
  Calendar,
  Shield,
  TrendingUp,
  Eye,
  X
} from 'lucide-react';
import { subscriptionAPI, contractAPI } from '../../services/api';

const statusStyles = {
  pending: { color: '#d97706', background: 'rgba(217,119,6,0.08)' },
  approved: { color: '#16a34a', background: 'rgba(22,163,74,0.08)' },
  rejected: { color: '#dc2626', background: 'rgba(220,38,38,0.08)' },
};

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

export function ApprovalQueue() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewDecision, setReviewDecision] = useState({
    status: 'approved',
    reviewer_notes: '',
    approved_fields: [],
    access_credentials: {
      connection_string: '',
      username: '',
      api_key: '',
    },
  });

  useEffect(() => {
    loadSubscriptions();
  }, [filter]);

  const loadSubscriptions = async () => {
    try {
      setLoading(true);
      const response = await subscriptionAPI.list({ status: filter });
      setSubscriptions(response.data);
    } catch (error) {
      toast.error('Failed to load subscriptions');
    } finally {
      setLoading(false);
    }
  };

  const openReviewModal = (subscription) => {
    setSelectedSubscription(subscription);
    setReviewDecision({
      status: 'approved',
      reviewer_notes: '',
      approved_fields: subscription.required_fields || [],
      access_credentials: {
        connection_string: '',
        username: `${subscription.consumer_email.split('@')[0]}_access`,
        api_key: `demo_api_key_${Date.now()}`,
      },
    });
    setShowReviewModal(true);
  };

  const submitReview = async () => {
    if (!reviewDecision.reviewer_notes) {
      toast.error('Please provide reviewer notes');
      return;
    }

    try {
      await subscriptionAPI.approve(selectedSubscription.id, reviewDecision);
      toast.success(
        `Subscription ${reviewDecision.status === 'approved' ? 'approved' : 'rejected'} successfully!`
      );
      setShowReviewModal(false);
      setSelectedSubscription(null);
      loadSubscriptions();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit review');
    }
  };

  const getStatusBadgeStyle = (status) => {
    const base = statusStyles[status] || { color: 'var(--color-text-tertiary)', background: 'var(--color-bg-tertiary)' };
    return {
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: 600,
      textTransform: 'capitalize',
      color: base.color,
      background: base.background,
    };
  };

  const stats = {
    pending: subscriptions.filter((s) => s.status === 'pending').length,
    approved: subscriptions.filter((s) => s.status === 'approved').length,
    rejected: subscriptions.filter((s) => s.status === 'rejected').length,
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--color-bg-primary)',
      }}>
        <div style={{ color: 'var(--color-text-primary)' }}>Loading approvals...</div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--color-bg-primary)',
      padding: '2rem',
    }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{
            fontSize: '1.875rem',
            fontWeight: 700,
            color: 'var(--color-text-primary)',
            marginBottom: '0.5rem',
          }}>
            Data Steward Approval Queue
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            Review and approve data access requests
          </p>
        </div>

        {/* Stats Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1.5rem',
          marginBottom: '2rem',
        }}>
          <div style={{
            background: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--color-border-default)',
            padding: '1.5rem',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
            }}>
              <Clock style={{ width: '2rem', height: '2rem', color: '#d97706' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.pending}</span>
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>Pending Reviews</p>
          </div>

          <div style={{
            background: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--color-border-default)',
            padding: '1.5rem',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
            }}>
              <CheckCircle style={{ width: '2rem', height: '2rem', color: '#16a34a' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.approved}</span>
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>Approved</p>
          </div>

          <div style={{
            background: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--color-border-default)',
            padding: '1.5rem',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
            }}>
              <XCircle style={{ width: '2rem', height: '2rem', color: '#dc2626' }} />
              <span style={{
                fontSize: '1.875rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
              }}>{stats.rejected}</span>
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>Rejected</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          {['pending', 'approved', 'rejected'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              style={{
                padding: '0.75rem 1.5rem',
                borderRadius: 'var(--radius-md)',
                fontWeight: 500,
                textTransform: 'capitalize',
                transition: 'all 0.2s',
                border: 'none',
                cursor: 'pointer',
                ...(filter === status
                  ? {
                      background: '#0070AD',
                      color: '#FFFFFF',
                    }
                  : {
                      background: 'var(--color-bg-secondary)',
                      color: 'var(--color-text-secondary)',
                      border: '1px solid var(--color-border-default)',
                    }),
              }}
            >
              {status}
              {stats[status] > 0 && (
                <span style={{
                  marginLeft: '0.5rem',
                  padding: '0.125rem 0.5rem',
                  background: 'var(--color-bg-tertiary)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                }}>
                  {stats[status]}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Subscriptions List */}
        <div style={{
          background: 'var(--color-bg-secondary)',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--color-border-default)',
        }}>
          {subscriptions.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <Clock style={{
                width: '4rem',
                height: '4rem',
                color: 'var(--color-text-muted)',
                margin: '0 auto 1rem',
              }} />
              <h3 style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                marginBottom: '0.5rem',
              }}>
                No subscriptions found
              </h3>
              <p style={{ color: 'var(--color-text-tertiary)' }}>
                No {filter} subscription requests at the moment
              </p>
            </div>
          ) : (
            <div>
              {subscriptions.map((subscription, index) => (
                <div
                  key={subscription.id}
                  style={{
                    padding: '1.5rem',
                    transition: 'all 0.2s',
                    ...(index < subscriptions.length - 1
                      ? { borderBottom: '1px solid var(--color-border-default)' }
                      : {}),
                  }}
                >
                  {/* Header */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    marginBottom: '1rem',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        marginBottom: '0.5rem',
                      }}>
                        <h3 style={{
                          fontSize: '1.125rem',
                          fontWeight: 600,
                          color: 'var(--color-text-primary)',
                        }}>
                          {subscription.dataset?.name || 'Unknown Dataset'}
                        </h3>
                        <span style={getStatusBadgeStyle(subscription.status)}>
                          {subscription.status}
                        </span>
                      </div>

                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--color-text-secondary)',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <User style={{ width: '1rem', height: '1rem' }} />
                          <span>{subscription.consumer_name}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Calendar style={{ width: '1rem', height: '1rem' }} />
                          <span>
                            {new Date(subscription.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {subscription.access_duration_days && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Clock style={{ width: '1rem', height: '1rem' }} />
                            <span>{subscription.access_duration_days} days</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {subscription.status === 'pending' && (
                      <button
                        onClick={() => openReviewModal(subscription)}
                        style={{
                          padding: '0.5rem 1rem',
                          background: '#0070AD',
                          color: '#FFFFFF',
                          borderRadius: 'var(--radius-md)',
                          border: 'none',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          fontWeight: 500,
                        }}
                      >
                        <Eye style={{ width: '1rem', height: '1rem' }} />
                        Review
                      </button>
                    )}
                  </div>

                  {/* Details Grid */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: '1rem',
                    marginBottom: '1rem',
                  }}>
                    {/* Use Case */}
                    <div style={{
                      background: 'var(--color-bg-tertiary)',
                      borderRadius: 'var(--radius-md)',
                      padding: '1rem',
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.5rem',
                      }}>
                        <FileText style={{ width: '1rem', height: '1rem' }} />
                        <span>Use Case</span>
                      </div>
                      <p style={{
                        color: 'var(--color-text-primary)',
                        fontSize: '0.875rem',
                      }}>{subscription.use_case}</p>
                    </div>

                    {/* Business Justification */}
                    <div style={{
                      background: 'var(--color-bg-tertiary)',
                      borderRadius: 'var(--radius-md)',
                      padding: '1rem',
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.5rem',
                      }}>
                        <Shield style={{ width: '1rem', height: '1rem' }} />
                        <span>Business Justification</span>
                      </div>
                      <p style={{
                        color: 'var(--color-text-primary)',
                        fontSize: '0.875rem',
                      }}>
                        {subscription.business_justification}
                      </p>
                    </div>
                  </div>

                  {/* SLA Requirements */}
                  {subscription.sla_requirements && (
                    <div style={{
                      background: 'var(--color-bg-tertiary)',
                      borderRadius: 'var(--radius-md)',
                      padding: '1rem',
                      marginBottom: '1rem',
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.75rem',
                      }}>
                        <TrendingUp style={{ width: '1rem', height: '1rem' }} />
                        <span>SLA Requirements</span>
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '1rem',
                        fontSize: '0.875rem',
                      }}>
                        <div>
                          <p style={{ color: 'var(--color-text-tertiary)', marginBottom: '0.25rem' }}>Max Latency</p>
                          <p style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
                            {subscription.sla_requirements.max_latency_ms}ms
                          </p>
                        </div>
                        <div>
                          <p style={{ color: 'var(--color-text-tertiary)', marginBottom: '0.25rem' }}>Min Availability</p>
                          <p style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
                            {subscription.sla_requirements.min_availability_pct}%
                          </p>
                        </div>
                        <div>
                          <p style={{ color: 'var(--color-text-tertiary)', marginBottom: '0.25rem' }}>Max Staleness</p>
                          <p style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
                            {subscription.sla_requirements.max_staleness_minutes}min
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Required Fields */}
                  {subscription.required_fields && subscription.required_fields.length > 0 && (
                    <div style={{
                      background: 'var(--color-bg-tertiary)',
                      borderRadius: 'var(--radius-md)',
                      padding: '1rem',
                    }}>
                      <p style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.5rem',
                      }}>Required Fields:</p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {subscription.required_fields.map((field) => (
                          <span
                            key={field}
                            style={{
                              padding: '0.25rem 0.75rem',
                              background: 'var(--color-bg-elevated)',
                              color: 'var(--color-text-secondary)',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '0.75rem',
                            }}
                          >
                            {field}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Review Notes (if approved/rejected) */}
                  {subscription.reviewer_notes && (
                    <div style={{
                      marginTop: '1rem',
                      paddingTop: '1rem',
                      borderTop: '1px solid var(--color-border-default)',
                    }}>
                      <p style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.5rem',
                      }}>Reviewer Notes:</p>
                      <p style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-secondary)',
                      }}>{subscription.reviewer_notes}</p>
                      {subscription.reviewed_by && (
                        <p style={{
                          fontSize: '0.75rem',
                          color: 'var(--color-text-tertiary)',
                          marginTop: '0.5rem',
                        }}>
                          Reviewed by {subscription.reviewed_by} on{' '}
                          {new Date(subscription.reviewed_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Review Modal */}
      {showReviewModal && selectedSubscription && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem',
          zIndex: 50,
        }}>
          <div style={{
            background: 'var(--color-bg-secondary)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--color-border-default)',
            maxWidth: '48rem',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
          }}>
            {/* Modal Header */}
            <div style={{
              position: 'sticky',
              top: 0,
              background: 'var(--color-bg-secondary)',
              borderBottom: '1px solid var(--color-border-default)',
              padding: '1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <h2 style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: 'var(--color-text-primary)',
                  marginBottom: '0.25rem',
                }}>
                  Review Subscription Request
                </h2>
                <p style={{ color: 'var(--color-text-secondary)' }}>
                  {selectedSubscription.dataset?.name} - {selectedSubscription.consumer_name}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowReviewModal(false);
                  setSelectedSubscription(null);
                }}
                style={{
                  color: 'var(--color-text-secondary)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <X style={{ width: '1.5rem', height: '1.5rem' }} />
              </button>
            </div>

            {/* Modal Content */}
            <div style={{
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
            }}>
              {/* Decision */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: 'var(--color-text-secondary)',
                  marginBottom: '0.75rem',
                }}>
                  Decision *
                </label>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    onClick={() =>
                      setReviewDecision({ ...reviewDecision, status: 'approved' })
                    }
                    style={{
                      flex: 1,
                      padding: '1rem 1.5rem',
                      borderRadius: 'var(--radius-md)',
                      transition: 'all 0.2s',
                      cursor: 'pointer',
                      textAlign: 'center',
                      background: reviewDecision.status === 'approved'
                        ? 'rgba(22,163,74,0.08)'
                        : 'var(--color-bg-primary)',
                      border: reviewDecision.status === 'approved'
                        ? '2px solid #16a34a'
                        : '2px solid var(--color-border-default)',
                      color: reviewDecision.status === 'approved'
                        ? '#16a34a'
                        : 'var(--color-text-secondary)',
                    }}
                  >
                    <CheckCircle style={{ width: '1.5rem', height: '1.5rem', margin: '0 auto 0.5rem' }} />
                    <div style={{ fontWeight: 600 }}>Approve</div>
                  </button>

                  <button
                    onClick={() =>
                      setReviewDecision({ ...reviewDecision, status: 'rejected' })
                    }
                    style={{
                      flex: 1,
                      padding: '1rem 1.5rem',
                      borderRadius: 'var(--radius-md)',
                      transition: 'all 0.2s',
                      cursor: 'pointer',
                      textAlign: 'center',
                      background: reviewDecision.status === 'rejected'
                        ? 'rgba(220,38,38,0.08)'
                        : 'var(--color-bg-primary)',
                      border: reviewDecision.status === 'rejected'
                        ? '2px solid #dc2626'
                        : '2px solid var(--color-border-default)',
                      color: reviewDecision.status === 'rejected'
                        ? '#dc2626'
                        : 'var(--color-text-secondary)',
                    }}
                  >
                    <XCircle style={{ width: '1.5rem', height: '1.5rem', margin: '0 auto 0.5rem' }} />
                    <div style={{ fontWeight: 600 }}>Reject</div>
                  </button>
                </div>
              </div>

              {/* Reviewer Notes */}
              <div>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: 'var(--color-text-secondary)',
                  marginBottom: '0.5rem',
                }}>
                  Reviewer Notes *
                </label>
                <textarea
                  value={reviewDecision.reviewer_notes}
                  onChange={(e) =>
                    setReviewDecision({
                      ...reviewDecision,
                      reviewer_notes: e.target.value,
                    })
                  }
                  placeholder="Provide feedback on this request..."
                  rows={4}
                  style={{
                    ...inputStyle,
                    resize: 'vertical',
                  }}
                />
              </div>

              {/* Approved Fields (only if approved) */}
              {reviewDecision.status === 'approved' && (
                <>
                  <div>
                    <label style={{
                      display: 'block',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: 'var(--color-text-secondary)',
                      marginBottom: '0.5rem',
                    }}>
                      Approved Fields
                    </label>
                    <div style={{
                      background: 'var(--color-bg-tertiary)',
                      borderRadius: 'var(--radius-md)',
                      padding: '1rem',
                      maxHeight: '12rem',
                      overflowY: 'auto',
                    }}>
                      {selectedSubscription.required_fields?.map((field) => (
                        <label
                          key={field}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            padding: '0.5rem 0',
                            fontSize: '0.875rem',
                            color: 'var(--color-text-secondary)',
                            cursor: 'pointer',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={reviewDecision.approved_fields.includes(field)}
                            onChange={(e) => {
                              const fields = e.target.checked
                                ? [...reviewDecision.approved_fields, field]
                                : reviewDecision.approved_fields.filter((f) => f !== field);
                              setReviewDecision({
                                ...reviewDecision,
                                approved_fields: fields,
                              });
                            }}
                            style={{ borderRadius: 'var(--radius-sm)' }}
                          />
                          <span>{field}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Access Credentials */}
                  <div style={{
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                  }}>
                    <h3 style={{
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      color: 'var(--color-text-secondary)',
                    }}>
                      Access Credentials
                    </h3>

                    <div>
                      <label style={{
                        display: 'block',
                        fontSize: '0.75rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.25rem',
                      }}>
                        Username
                      </label>
                      <input
                        type="text"
                        value={reviewDecision.access_credentials.username}
                        onChange={(e) =>
                          setReviewDecision({
                            ...reviewDecision,
                            access_credentials: {
                              ...reviewDecision.access_credentials,
                              username: e.target.value,
                            },
                          })
                        }
                        style={inputStyle}
                      />
                    </div>

                    <div>
                      <label style={{
                        display: 'block',
                        fontSize: '0.75rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.25rem',
                      }}>
                        API Key
                      </label>
                      <input
                        type="text"
                        value={reviewDecision.access_credentials.api_key}
                        onChange={(e) =>
                          setReviewDecision({
                            ...reviewDecision,
                            access_credentials: {
                              ...reviewDecision.access_credentials,
                              api_key: e.target.value,
                            },
                          })
                        }
                        style={inputStyle}
                      />
                    </div>

                    <div>
                      <label style={{
                        display: 'block',
                        fontSize: '0.75rem',
                        color: 'var(--color-text-tertiary)',
                        marginBottom: '0.25rem',
                      }}>
                        Connection String (optional)
                      </label>
                      <input
                        type="text"
                        value={reviewDecision.access_credentials.connection_string}
                        onChange={(e) =>
                          setReviewDecision({
                            ...reviewDecision,
                            access_credentials: {
                              ...reviewDecision.access_credentials,
                              connection_string: e.target.value,
                            },
                          })
                        }
                        placeholder="jdbc:postgresql://host:port/db"
                        style={inputStyle}
                      />
                    </div>
                  </div>

                  <div style={{
                    background: 'rgba(0,112,173,0.06)',
                    border: '1px solid rgba(0,112,173,0.2)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.75rem',
                  }}>
                    <AlertCircle style={{
                      width: '1.25rem',
                      height: '1.25rem',
                      color: '#0070AD',
                      flexShrink: 0,
                      marginTop: '0.125rem',
                    }} />
                    <div>
                      <h4 style={{
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        color: '#0070AD',
                        marginBottom: '0.25rem',
                      }}>
                        Contract Update
                      </h4>
                      <p style={{
                        fontSize: '0.875rem',
                        color: 'var(--color-text-secondary)',
                      }}>
                        Approving this request will generate a new version of the data contract
                        with the subscription details and SLA requirements.
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              position: 'sticky',
              bottom: 0,
              background: 'var(--color-bg-secondary)',
              borderTop: '1px solid var(--color-border-default)',
              padding: '1.5rem',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '1rem',
            }}>
              <button
                onClick={() => {
                  setShowReviewModal(false);
                  setSelectedSubscription(null);
                }}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'var(--color-bg-tertiary)',
                  color: 'var(--color-text-primary)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border-default)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  fontWeight: 500,
                }}
              >
                Cancel
              </button>
              <button
                onClick={submitReview}
                style={{
                  padding: '0.75rem 1.5rem',
                  borderRadius: 'var(--radius-md)',
                  transition: 'all 0.2s',
                  fontWeight: 500,
                  border: 'none',
                  cursor: 'pointer',
                  color: '#FFFFFF',
                  background: reviewDecision.status === 'approved' ? '#16a34a' : '#dc2626',
                }}
              >
                {reviewDecision.status === 'approved' ? 'Approve Request' : 'Reject Request'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
