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

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-400 bg-yellow-500/10';
      case 'approved':
        return 'text-green-400 bg-green-500/10';
      case 'rejected':
        return 'text-red-400 bg-red-500/10';
      default:
        return 'text-gray-400 bg-gray-500/10';
    }
  };

  const stats = {
    pending: subscriptions.filter((s) => s.status === 'pending').length,
    approved: subscriptions.filter((s) => s.status === 'approved').length,
    rejected: subscriptions.filter((s) => s.status === 'rejected').length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-white">Loading approvals...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Data Steward Approval Queue
          </h1>
          <p className="text-gray-400">
            Review and approve data access requests
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <Clock className="w-8 h-8 text-yellow-400" />
              <span className="text-3xl font-bold text-white">{stats.pending}</span>
            </div>
            <p className="text-gray-400 text-sm">Pending Reviews</p>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <CheckCircle className="w-8 h-8 text-green-400" />
              <span className="text-3xl font-bold text-white">{stats.approved}</span>
            </div>
            <p className="text-gray-400 text-sm">Approved</p>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <XCircle className="w-8 h-8 text-red-400" />
              <span className="text-3xl font-bold text-white">{stats.rejected}</span>
            </div>
            <p className="text-gray-400 text-sm">Rejected</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['pending', 'approved', 'rejected'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-6 py-3 rounded-lg font-medium capitalize transition-all ${
                filter === status
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {status}
              {stats[status] > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-gray-900 rounded text-xs">
                  {stats[status]}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Subscriptions List */}
        <div className="bg-gray-800 rounded-xl border border-gray-700">
          {subscriptions.length === 0 ? (
            <div className="p-12 text-center">
              <Clock className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-400 mb-2">
                No subscriptions found
              </h3>
              <p className="text-gray-500">
                No {filter} subscription requests at the moment
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {subscriptions.map((subscription) => (
                <div key={subscription.id} className="p-6 hover:bg-gray-750 transition-all">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {subscription.dataset?.name || 'Unknown Dataset'}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${getStatusColor(
                            subscription.status
                          )}`}
                        >
                          {subscription.status}
                        </span>
                      </div>

                      <div className="flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />
                          <span>{subscription.consumer_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>
                            {new Date(subscription.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {subscription.access_duration_days && (
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            <span>{subscription.access_duration_days} days</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {subscription.status === 'pending' && (
                      <button
                        onClick={() => openReviewModal(subscription)}
                        className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all flex items-center gap-2"
                      >
                        <Eye className="w-4 h-4" />
                        Review
                      </button>
                    )}
                  </div>

                  {/* Details Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {/* Use Case */}
                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                        <FileText className="w-4 h-4" />
                        <span>Use Case</span>
                      </div>
                      <p className="text-white text-sm">{subscription.use_case}</p>
                    </div>

                    {/* Business Justification */}
                    <div className="bg-gray-900 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                        <Shield className="w-4 h-4" />
                        <span>Business Justification</span>
                      </div>
                      <p className="text-white text-sm">
                        {subscription.business_justification}
                      </p>
                    </div>
                  </div>

                  {/* SLA Requirements */}
                  {subscription.sla_requirements && (
                    <div className="bg-gray-900 rounded-lg p-4 mb-4">
                      <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                        <TrendingUp className="w-4 h-4" />
                        <span>SLA Requirements</span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500 mb-1">Max Latency</p>
                          <p className="text-white font-medium">
                            {subscription.sla_requirements.max_latency_ms}ms
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-500 mb-1">Min Availability</p>
                          <p className="text-white font-medium">
                            {subscription.sla_requirements.min_availability_pct}%
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-500 mb-1">Max Staleness</p>
                          <p className="text-white font-medium">
                            {subscription.sla_requirements.max_staleness_minutes}min
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Required Fields */}
                  {subscription.required_fields && subscription.required_fields.length > 0 && (
                    <div className="bg-gray-900 rounded-lg p-4">
                      <p className="text-sm text-gray-500 mb-2">Required Fields:</p>
                      <div className="flex flex-wrap gap-2">
                        {subscription.required_fields.map((field) => (
                          <span
                            key={field}
                            className="px-3 py-1 bg-gray-800 text-gray-300 rounded text-xs"
                          >
                            {field}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Review Notes (if approved/rejected) */}
                  {subscription.reviewer_notes && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <p className="text-sm text-gray-500 mb-2">Reviewer Notes:</p>
                      <p className="text-sm text-gray-300">{subscription.reviewer_notes}</p>
                      {subscription.reviewed_by && (
                        <p className="text-xs text-gray-500 mt-2">
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-xl border border-gray-700 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  Review Subscription Request
                </h2>
                <p className="text-gray-400">
                  {selectedSubscription.dataset?.name} - {selectedSubscription.consumer_name}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowReviewModal(false);
                  setSelectedSubscription(null);
                }}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Decision */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Decision *
                </label>
                <div className="flex gap-4">
                  <button
                    onClick={() =>
                      setReviewDecision({ ...reviewDecision, status: 'approved' })
                    }
                    className={`flex-1 px-6 py-4 rounded-lg border-2 transition-all ${
                      reviewDecision.status === 'approved'
                        ? 'border-green-500 bg-green-500/10 text-white'
                        : 'border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <CheckCircle className="w-6 h-6 mx-auto mb-2" />
                    <div className="font-semibold">Approve</div>
                  </button>

                  <button
                    onClick={() =>
                      setReviewDecision({ ...reviewDecision, status: 'rejected' })
                    }
                    className={`flex-1 px-6 py-4 rounded-lg border-2 transition-all ${
                      reviewDecision.status === 'rejected'
                        ? 'border-red-500 bg-red-500/10 text-white'
                        : 'border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    <XCircle className="w-6 h-6 mx-auto mb-2" />
                    <div className="font-semibold">Reject</div>
                  </button>
                </div>
              </div>

              {/* Reviewer Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
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
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              {/* Approved Fields (only if approved) */}
              {reviewDecision.status === 'approved' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Approved Fields
                    </label>
                    <div className="bg-gray-900 rounded-lg p-4 max-h-48 overflow-y-auto">
                      {selectedSubscription.required_fields?.map((field) => (
                        <label
                          key={field}
                          className="flex items-center gap-2 py-2 text-sm text-gray-300 hover:text-white cursor-pointer"
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
                            className="rounded"
                          />
                          <span>{field}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Access Credentials */}
                  <div className="bg-gray-900 rounded-lg p-4 space-y-3">
                    <h3 className="text-sm font-semibold text-gray-300">
                      Access Credentials
                    </h3>

                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
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
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
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
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-gray-500 mb-1">
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
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-purple-500"
                      />
                    </div>
                  </div>

                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-semibold text-blue-400 mb-1">
                        Contract Update
                      </h4>
                      <p className="text-sm text-gray-400">
                        Approving this request will generate a new version of the data contract
                        with the subscription details and SLA requirements.
                      </p>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-800 border-t border-gray-700 p-6 flex justify-end gap-4">
              <button
                onClick={() => {
                  setShowReviewModal(false);
                  setSelectedSubscription(null);
                }}
                className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={submitReview}
                className={`px-6 py-3 rounded-lg transition-all font-medium ${
                  reviewDecision.status === 'approved'
                    ? 'bg-green-500 hover:bg-green-600 text-white'
                    : 'bg-red-500 hover:bg-red-600 text-white'
                }`}
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
