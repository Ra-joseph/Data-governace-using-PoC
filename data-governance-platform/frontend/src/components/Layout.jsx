import { Outlet, NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Database, 
  FileText, 
  Shield, 
  GitBranch,
  Bell,
  CheckCircle,
  Upload
} from 'lucide-react';
import { motion } from 'framer-motion';
import './Layout.css';

const navigation = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Dataset Catalog', path: '/catalog', icon: Database },
  { name: 'Import Schema', path: '/import', icon: Upload },
  { name: 'Policy Manager', path: '/policies', icon: Shield },
  { name: 'Git History', path: '/git', icon: GitBranch },
  { name: 'Subscriptions', path: '/subscriptions', icon: Bell },
  { name: 'Compliance', path: '/compliance', icon: CheckCircle },
];

export const Layout = () => {
  return (
    <div className="layout">
      <aside className="sidebar">
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
              transition={{ delay: index * 0.1 }}
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
          <div className="status-indicator">
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
