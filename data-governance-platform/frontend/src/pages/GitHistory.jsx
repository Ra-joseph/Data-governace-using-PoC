import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  GitBranch, 
  GitCommit, 
  Calendar, 
  User, 
  FileText,
  Clock,
  Tag,
  Download,
  Eye
} from 'lucide-react';
import { gitAPI } from '../services/api';
import toast from 'react-hot-toast';
import './GitHistory.css';

export const GitHistory = () => {
  const [history, setHistory] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [status, setStatus] = useState(null);
  const [selectedCommit, setSelectedCommit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadGitData();
  }, []);

  const loadGitData = async () => {
    try {
      setLoading(true);
      const [historyRes, contractsRes, statusRes] = await Promise.all([
        gitAPI.history(),
        gitAPI.contracts(),
        gitAPI.status(),
      ]);
      
      setHistory(historyRes.data.history);
      setContracts(contractsRes.data.contracts);
      setStatus(statusRes.data);
    } catch (error) {
      toast.error('Failed to load Git data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const viewCommitDetails = async (commit) => {
    setSelectedCommit(commit);
  };

  const getTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
      year: 31536000,
      month: 2592000,
      week: 604800,
      day: 86400,
      hour: 3600,
      minute: 60,
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
      const interval = Math.floor(seconds / secondsInUnit);
      if (interval >= 1) {
        return `${interval} ${unit}${interval !== 1 ? 's' : ''} ago`;
      }
    }
    
    return 'just now';
  };

  const filteredHistory = history.filter(commit => {
    if (filter === 'all') return true;
    if (filter === 'today') {
      const commitDate = new Date(commit.date);
      const today = new Date();
      return commitDate.toDateString() === today.toDateString();
    }
    if (filter === 'week') {
      const commitDate = new Date(commit.date);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return commitDate >= weekAgo;
    }
    return true;
  });

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading Git repository...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Git Version Control</h1>
          <p className="page-subtitle">
            Complete audit trail of all contract changes
          </p>
        </div>
      </div>

      {/* Repository Status */}
      {status && (
        <motion.div 
          className="repo-status-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="status-header">
            <GitBranch size={24} />
            <div>
              <h3>Repository Status</h3>
              <p>{status.repository_path}</p>
            </div>
          </div>
          
          <div className="status-metrics">
            <div className="status-metric">
              <FileText size={20} />
              <div>
                <div className="status-value">{status.total_contracts}</div>
                <div className="status-label">Contracts</div>
              </div>
            </div>
            
            <div className="status-metric">
              <GitCommit size={20} />
              <div>
                <div className="status-value">{status.total_commits}</div>
                <div className="status-label">Commits</div>
              </div>
            </div>
            
            <div className="status-metric">
              <Tag size={20} />
              <div>
                <div className="status-value">{status.tags?.length || 0}</div>
                <div className="status-label">Tags</div>
              </div>
            </div>
            
            <div className="status-metric">
              <GitBranch size={20} />
              <div>
                <div className="status-value">{status.active_branch}</div>
                <div className="status-label">Branch</div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <div className="git-content">
        {/* Sidebar: Contracts List */}
        <motion.div 
          className="contracts-sidebar"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="sidebar-header">
            <h3>Contract Files</h3>
            <span className="badge badge-neutral">{contracts.length}</span>
          </div>
          
          <div className="contracts-list">
            {contracts.map((contract, index) => (
              <motion.div
                key={index}
                className="contract-item"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.05 }}
              >
                <FileText size={16} />
                <div className="contract-info">
                  <div className="contract-name">{contract.filename}</div>
                  <div className="contract-size">{(contract.size / 1024).toFixed(1)} KB</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Main: Commit History */}
        <div className="history-main">
          <div className="history-toolbar">
            <div className="toolbar-left">
              <h3>Commit History</h3>
              <span className="badge badge-accent">{history.length} commits</span>
            </div>
            
            <div className="toolbar-right">
              <select 
                value={filter} 
                onChange={(e) => setFilter(e.target.value)}
                className="filter-select"
              >
                <option value="all">All Time</option>
                <option value="today">Today</option>
                <option value="week">This Week</option>
              </select>
            </div>
          </div>

          <div className="commit-timeline">
            {filteredHistory.map((commit, index) => (
              <motion.div
                key={commit.commit_hash}
                className="commit-item"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => viewCommitDetails(commit)}
              >
                <div className="commit-indicator">
                  <div className="commit-dot"></div>
                  {index < filteredHistory.length - 1 && <div className="commit-line"></div>}
                </div>
                
                <div className="commit-content">
                  <div className="commit-header">
                    <div className="commit-message">{commit.message}</div>
                    <div className="commit-time">
                      <Clock size={14} />
                      {getTimeAgo(commit.date)}
                    </div>
                  </div>
                  
                  <div className="commit-meta">
                    <div className="commit-hash">
                      <GitCommit size={14} />
                      {commit.commit_hash.substring(0, 7)}
                    </div>
                    <div className="commit-author">
                      <User size={14} />
                      {commit.author}
                    </div>
                    <div className="commit-date">
                      <Calendar size={14} />
                      {new Date(commit.date).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="commit-actions">
                    <button className="btn-text btn-sm">
                      <Eye size={14} />
                      View
                    </button>
                    <button className="btn-text btn-sm">
                      <Download size={14} />
                      Download
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Commit Detail Modal */}
      {selectedCommit && (
        <motion.div 
          className="modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => setSelectedCommit(null)}
        >
          <motion.div 
            className="modal-content"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>Commit Details</h3>
              <button 
                className="modal-close"
                onClick={() => setSelectedCommit(null)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">Commit Hash:</span>
                <code>{selectedCommit.commit_hash}</code>
              </div>
              <div className="detail-row">
                <span className="detail-label">Author:</span>
                <span>{selectedCommit.author}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Date:</span>
                <span>{new Date(selectedCommit.date).toLocaleString()}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Message:</span>
                <p>{selectedCommit.message}</p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};
