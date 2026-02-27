import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Shield,
  Bell,
  CheckCircle,
  PenTool,
  BarChart3,
  FileCheck,
  Menu,
  X,
  LogOut,
  UserCircle,
  FilePlus,
  ListChecks,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import './Layout.css';

// Role-specific navigation items
const roleNavigation = {
  owner: [
    { name: 'My Dashboard', path: '/owner/dashboard', icon: LayoutDashboard },
    { name: 'Register Dataset', path: '/owner/register', icon: FilePlus },
  ],
  consumer: [
    { name: 'Data Catalog', path: '/consumer/catalog', icon: Database },
  ],
  steward: [
    { name: 'Approval Queue', path: '/steward/approvals', icon: ListChecks },
  ],
  admin: [
    { name: 'Compliance Dashboard', path: '/admin/dashboard', icon: BarChart3 },
    { name: 'Compliance Report', path: '/admin/compliance', icon: FileCheck },
  ],
};

const roleMeta = {
  owner:    { label: 'Data Owner',     color: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
  consumer: { label: 'Data Consumer',  color: '#22c55e', bg: 'rgba(34,197,94,0.15)'  },
  steward:  { label: 'Data Steward',   color: '#a855f7', bg: 'rgba(168,85,247,0.15)' },
  admin:    { label: 'Platform Admin', color: '#f97316', bg: 'rgba(249,115,22,0.15)' },
};

export const Layout = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const navigation = (user && roleNavigation[user.role]) || [];
  const meta = user ? roleMeta[user.role] : null;

  const handleSwitchRole = () => {
    logout();
    navigate('/select-role');
  };

  // Close drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.classList.add('drawer-open');
    } else {
      document.body.classList.remove('drawer-open');
    }
    return () => document.body.classList.remove('drawer-open');
  }, [mobileOpen]);

  // Get current page title for the mobile header
  const currentPage = navigation.find(
    (item) => location.pathname === item.path || location.pathname.startsWith(item.path + '/')
  );

  return (
    <div className="layout">
      {/* Mobile top header bar */}
      <header className="mobile-header">
        <button
          className="mobile-menu-btn"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span className="mobile-header-title">
          {currentPage?.name ?? 'Data Governance'}
        </span>
      </header>

      {/* Overlay backdrop */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="sidebar-overlay visible"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
        )}
      </AnimatePresence>

      <aside className={`sidebar${mobileOpen ? ' mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo-container">
            <motion.div
              className="logo-icon"
              animate={{
                boxShadow: [
                  '0 0 20px rgba(139, 92, 246, 0.3)',
                  '0 0 30px rgba(139, 92, 246, 0.5)',
                  '0 0 20px rgba(139, 92, 246, 0.3)',
                ],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <Shield size={24} />
            </motion.div>
            <div className="logo-text">
              <h1>Data Governance</h1>
              <p>Policy-as-Code Platform</p>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item, index) => (
            <motion.div
              key={item.path}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <NavLink
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                <item.icon size={20} />
                <span>{item.name}</span>
              </NavLink>
            </motion.div>
          ))}
        </nav>

        <div className="sidebar-footer">
          {user && meta && (
            <div className="user-info">
              <div className="user-info-row">
                <UserCircle size={20} style={{ color: meta.color, flexShrink: 0 }} />
                <span className="user-name">{user.name}</span>
              </div>
              <div
                className="role-badge"
                style={{ color: meta.color, background: meta.bg }}
              >
                {meta.label}
              </div>
            </div>
          )}
          <button className="switch-role-btn" onClick={handleSwitchRole}>
            <LogOut size={16} />
            <span>Switch Role</span>
          </button>
          <div className="status-indicator" style={{ marginTop: '0.5rem' }}>
            <div className="status-dot"></div>
            <span>System Healthy</span>
          </div>
          <p className="version">v1.0.0</p>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};
