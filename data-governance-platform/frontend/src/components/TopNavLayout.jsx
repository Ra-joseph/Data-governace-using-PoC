import { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Database,
  Upload,
  FileText,
  PenTool,
  ClipboardCheck,
  BarChart3,
  FileCheck,
  Package,
  Globe,
  AlertTriangle,
  GitBranch,
  Bell,
  CheckCircle,
  ChevronDown,
  UserCircle,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './TopNavLayout.css';

const navGroups = [
  {
    label: 'Data',
    items: [
      { name: 'Dashboard',      path: '/',        icon: LayoutDashboard },
      { name: 'Dataset Catalog', path: '/catalog', icon: Database },
      { name: 'Import Schema',  path: '/import',  icon: Upload },
    ],
  },
  {
    label: 'Policies',
    items: [
      { name: 'Policy Manager',    path: '/policies',          icon: FileText },
      { name: 'Policy Authoring',  path: '/policy-authoring',  icon: PenTool },
      { name: 'Policy Review',     path: '/policy-review',     icon: ClipboardCheck },
      { name: 'Policy Dashboard',  path: '/policy-dashboard',  icon: BarChart3 },
      { name: 'Compliance Report', path: '/compliance-report', icon: FileCheck },
      { name: 'Policy Exchange',   path: '/policy-exchange',   icon: Package },
      { name: 'Domain Governance', path: '/domain-governance', icon: Globe },
      { name: 'Policy Exceptions', path: '/policy-conflicts',  icon: AlertTriangle },
    ],
  },
  {
    label: 'Operations',
    items: [
      { name: 'Subscriptions', path: '/subscriptions', icon: Bell },
      { name: 'Compliance',    path: '/compliance',    icon: CheckCircle },
      { name: 'Git History',   path: '/git',           icon: GitBranch },
    ],
  },
];

const roleMeta = {
  owner:    { label: 'Data Owner',     color: '#3b82f6' },
  consumer: { label: 'Data Consumer',  color: '#22c55e' },
  steward:  { label: 'Data Steward',   color: '#a855f7' },
  admin:    { label: 'Platform Admin', color: '#f97316' },
};

function DropdownGroup({ group, onClose }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="topnav-group" ref={ref}>
      <button
        className={`topnav-group-btn${open ? ' open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="true"
      >
        <span>{group.label}</span>
        <ChevronDown size={14} className={`chevron${open ? ' rotated' : ''}`} />
      </button>

      {open && (
        <div className="topnav-dropdown" role="menu">
          {group.items.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `topnav-dropdown-item${isActive ? ' active' : ''}`
                }
                onClick={() => { setOpen(false); onClose?.(); }}
                role="menuitem"
              >
                <Icon size={16} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </div>
      )}
    </div>
  );
}

export const TopNavLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const meta = user ? roleMeta[user.role] : null;

  const handleSwitchRole = () => {
    logout();
    navigate('/select-role');
  };

  return (
    <div className="topnav-layout">
      <header className="topnav-header">
        {/* Brand */}
        <div className="topnav-brand">
          <div className="topnav-logo">
            <Shield size={20} />
          </div>
          <span className="topnav-title">Data Governance</span>
        </div>

        {/* Navigation groups */}
        <nav className="topnav-nav" aria-label="Main navigation">
          {navGroups.map((group) => (
            <DropdownGroup key={group.label} group={group} />
          ))}
        </nav>

        {/* Right side: user info + switch role */}
        <div className="topnav-actions">
          {user && meta && (
            <div className="topnav-user">
              <UserCircle size={18} style={{ color: meta.color }} />
              <span className="topnav-user-name">{user.name}</span>
              <span
                className="topnav-role-badge"
                style={{ color: meta.color, borderColor: meta.color }}
              >
                {meta.label}
              </span>
            </div>
          )}
          <button className="topnav-switch-btn" onClick={handleSwitchRole}>
            <LogOut size={15} />
            <span>Switch Role</span>
          </button>
        </div>
      </header>

      <main className="topnav-main">
        <Outlet />
      </main>
    </div>
  );
};
