import { useState, useEffect } from 'react';
import { prGovernanceAPI } from '../../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const STATUS_COLORS = {
  passed: '#16a34a',
  warning: '#d97706',
  failed: '#dc2626',
  error: '#6b7280',
  running: '#3b82f6',
  pending: '#9ca3af',
};

const SEVERITY_COLORS = {
  critical: '#dc2626',
  warning: '#d97706',
  info: '#3b82f6',
};

export function PRGovernanceDashboard() {
  const [stats, setStats] = useState(null);
  const [scans, setScans] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedScan, setSelectedScan] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterRepo, setFilterRepo] = useState('');

  useEffect(() => {
    loadData();
  }, [filterStatus, filterRepo]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (filterStatus) params.status = filterStatus;
      if (filterRepo) params.repo = filterRepo;
      params.limit = 50;

      const [statsRes, scansRes] = await Promise.all([
        prGovernanceAPI.stats(),
        prGovernanceAPI.listScans(params),
      ]);

      setStats(statsRes.data);
      setScans(scansRes.data.scans || []);
      setTotal(scansRes.data.total || 0);
    } catch (err) {
      setError('Failed to load PR governance data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRescan = async (scanId) => {
    try {
      await prGovernanceAPI.rescan(scanId);
      loadData();
    } catch (err) {
      console.error('Rescan failed:', err);
    }
  };

  const getStatusBadge = (status) => {
    const color = STATUS_COLORS[status] || '#6b7280';
    return (
      <span
        style={{
          display: 'inline-block',
          padding: '2px 10px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: 600,
          color: '#fff',
          backgroundColor: color,
          textTransform: 'uppercase',
        }}
      >
        {status}
      </span>
    );
  };

  const pieData = stats
    ? [
        { name: 'Passed', value: stats.passed, color: STATUS_COLORS.passed },
        { name: 'Warnings', value: stats.warnings, color: STATUS_COLORS.warning },
        { name: 'Failed', value: stats.failed, color: STATUS_COLORS.failed },
        { name: 'Error', value: stats.error, color: STATUS_COLORS.error },
      ].filter((d) => d.value > 0)
    : [];

  if (loading && !stats) {
    return (
      <div style={{ padding: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>
          PR Governance Scanner
        </h1>
        <p>Loading scan data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>
          PR Governance Scanner
        </h1>
        <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
          Automated governance policy scanning for pull requests
        </p>
      </div>

      {error && (
        <div
          style={{
            padding: '1rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#dc2626',
            marginBottom: '1.5rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem',
          }}
        >
          <StatCard label="Total Scans" value={stats.total_scans} />
          <StatCard
            label="Pass Rate"
            value={`${stats.pass_rate}%`}
            color={stats.pass_rate >= 80 ? '#16a34a' : stats.pass_rate >= 50 ? '#d97706' : '#dc2626'}
          />
          <StatCard label="Avg Violations" value={stats.avg_violations} />
          <StatCard label="Blocked PRs" value={stats.blocked_prs} color="#dc2626" />
        </div>
      )}

      {/* Charts */}
      {stats && stats.total_scans > 0 && pieData.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: '1.5rem',
            marginBottom: '2rem',
          }}
        >
          <div
            style={{
              background: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              padding: '1.5rem',
            }}
          >
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '1rem' }}>
              Scan Results Distribution
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Filters */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            fontSize: '0.875rem',
          }}
        >
          <option value="">All Statuses</option>
          <option value="passed">Passed</option>
          <option value="warning">Warning</option>
          <option value="failed">Failed</option>
          <option value="error">Error</option>
        </select>
        <input
          type="text"
          placeholder="Filter by repo..."
          value={filterRepo}
          onChange={(e) => setFilterRepo(e.target.value)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            fontSize: '0.875rem',
            width: '250px',
          }}
        />
        <button
          onClick={loadData}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            background: '#f9fafb',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          Refresh
        </button>
      </div>

      {/* Scans Table */}
      <div
        style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
              <th style={thStyle}>Repo</th>
              <th style={thStyle}>PR</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Violations</th>
              <th style={thStyle}>Strategy</th>
              <th style={thStyle}>Duration</th>
              <th style={thStyle}>When</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {scans.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af' }}>
                  No scans found. Configure a GitHub webhook to start scanning PRs.
                </td>
              </tr>
            ) : (
              scans.map((scan) => {
                const vs = scan.violations_summary || {};
                const totalV = (vs.critical || 0) + (vs.warning || 0) + (vs.info || 0);
                return (
                  <tr
                    key={scan.id}
                    style={{
                      borderBottom: '1px solid #f3f4f6',
                      cursor: 'pointer',
                      backgroundColor: selectedScan?.id === scan.id ? '#f0f9ff' : 'transparent',
                    }}
                    onClick={() => setSelectedScan(selectedScan?.id === scan.id ? null : scan)}
                  >
                    <td style={tdStyle}>{scan.github_repo}</td>
                    <td style={tdStyle}>
                      <span style={{ fontWeight: 600 }}>#{scan.pr_number}</span>
                      {scan.pr_title && (
                        <span style={{ color: '#6b7280', marginLeft: '0.5rem' }}>
                          {scan.pr_title.length > 40
                            ? scan.pr_title.substring(0, 40) + '...'
                            : scan.pr_title}
                        </span>
                      )}
                    </td>
                    <td style={tdStyle}>{getStatusBadge(scan.scan_status)}</td>
                    <td style={tdStyle}>
                      {totalV > 0 ? (
                        <span>
                          {vs.critical > 0 && (
                            <span style={{ color: SEVERITY_COLORS.critical, marginRight: '0.5rem' }}>
                              {vs.critical} critical
                            </span>
                          )}
                          {vs.warning > 0 && (
                            <span style={{ color: SEVERITY_COLORS.warning, marginRight: '0.5rem' }}>
                              {vs.warning} warn
                            </span>
                          )}
                          {vs.info > 0 && (
                            <span style={{ color: SEVERITY_COLORS.info }}>{vs.info} info</span>
                          )}
                        </span>
                      ) : (
                        <span style={{ color: '#9ca3af' }}>None</span>
                      )}
                    </td>
                    <td style={tdStyle}>
                      <span style={{ color: '#6b7280' }}>{scan.strategy_used || '-'}</span>
                    </td>
                    <td style={tdStyle}>
                      {scan.scan_duration_ms ? `${scan.scan_duration_ms}ms` : '-'}
                    </td>
                    <td style={tdStyle}>
                      {scan.triggered_at
                        ? new Date(scan.triggered_at).toLocaleDateString()
                        : '-'}
                    </td>
                    <td style={tdStyle}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRescan(scan.id);
                        }}
                        style={{
                          padding: '4px 12px',
                          borderRadius: '6px',
                          border: '1px solid #d1d5db',
                          background: '#fff',
                          cursor: 'pointer',
                          fontSize: '12px',
                        }}
                      >
                        Rescan
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Scan Detail Expandable */}
      {selectedScan && selectedScan.validation_results && (
        <div
          style={{
            marginTop: '1rem',
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '1.5rem',
          }}
        >
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>
            Scan Detail: PR #{selectedScan.pr_number} in {selectedScan.github_repo}
          </h3>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '1rem' }}>
            <span>Branch: {selectedScan.head_branch || 'N/A'}</span>
            <span style={{ margin: '0 1rem' }}>|</span>
            <span>SHA: {selectedScan.head_sha?.substring(0, 8) || 'N/A'}</span>
            <span style={{ margin: '0 1rem' }}>|</span>
            <span>Author: {selectedScan.pr_author || 'N/A'}</span>
          </div>

          {(selectedScan.validation_results.file_results || []).map((fr, idx) => (
            <div
              key={idx}
              style={{
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '1rem',
                marginBottom: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>{fr.filename}</span>
                {getStatusBadge(fr.status)}
              </div>
              {fr.violations && fr.violations.length > 0 ? (
                <div>
                  {fr.violations.map((v, vi) => (
                    <div
                      key={vi}
                      style={{
                        padding: '0.5rem 0.75rem',
                        marginTop: '0.5rem',
                        borderLeft: `3px solid ${SEVERITY_COLORS[v.type] || '#6b7280'}`,
                        backgroundColor: '#f9fafb',
                        borderRadius: '0 4px 4px 0',
                        fontSize: '0.8125rem',
                      }}
                    >
                      <div style={{ fontWeight: 600 }}>
                        <span
                          style={{
                            color: SEVERITY_COLORS[v.type] || '#6b7280',
                            textTransform: 'uppercase',
                            fontSize: '0.75rem',
                            marginRight: '0.5rem',
                          }}
                        >
                          {v.type}
                        </span>
                        {v.policy}
                        {v.field && (
                          <span style={{ color: '#6b7280', fontWeight: 400 }}>
                            {' '}
                            (field: {v.field})
                          </span>
                        )}
                      </div>
                      <div style={{ color: '#374151', marginTop: '0.25rem' }}>{v.message}</div>
                      {v.remediation && (
                        <div style={{ color: '#16a34a', marginTop: '0.25rem', fontSize: '0.75rem' }}>
                          Fix: {v.remediation}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#9ca3af', fontSize: '0.8125rem' }}>No violations</p>
              )}
            </div>
          ))}

          {selectedScan.validation_results.message && (
            <p style={{ color: '#6b7280' }}>{selectedScan.validation_results.message}</p>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        padding: '1.25rem',
      }}
    >
      <p style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>{label}</p>
      <p style={{ fontSize: '1.5rem', fontWeight: 700, color: color || '#111827' }}>{value}</p>
    </div>
  );
}

const thStyle = {
  textAlign: 'left',
  padding: '0.75rem 1rem',
  fontWeight: 600,
  fontSize: '0.75rem',
  color: '#6b7280',
  textTransform: 'uppercase',
};

const tdStyle = {
  padding: '0.75rem 1rem',
};
