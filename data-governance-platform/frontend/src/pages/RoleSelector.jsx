import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Database, ShoppingCart, Shield, BarChart3 } from 'lucide-react';

const roleColors = {
  owner: '#0070AD',
  consumer: '#16a34a',
  steward: '#7c3aed',
  admin: '#d97706',
};

export function RoleSelector() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [hoveredRole, setHoveredRole] = useState(null);

  const roles = [
    {
      id: 'owner',
      name: 'Data Owner',
      description: 'Register and manage datasets, view violations',
      icon: Database,
      path: '/owner/register',
    },
    {
      id: 'consumer',
      name: 'Data Consumer',
      description: 'Browse catalog and subscribe to datasets',
      icon: ShoppingCart,
      path: '/consumer/catalog',
    },
    {
      id: 'steward',
      name: 'Data Steward',
      description: 'Review and approve subscription requests',
      icon: Shield,
      path: '/steward/approvals',
    },
    {
      id: 'admin',
      name: 'Platform Admin',
      description: 'View compliance metrics and violation trends',
      icon: BarChart3,
      path: '/admin/dashboard',
    },
  ];

  const selectRole = (role) => {
    login({
      id: `demo-${role.id}`,
      name: `Demo ${role.name}`,
      email: `${role.id}@demo.com`,
      role: role.id,
      token: 'demo-token',
    });
    navigate(role.path);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--color-bg-primary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-lg)',
      }}
    >
      <div style={{ maxWidth: '72rem', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-2xl)' }}>
          <h1
            style={{
              fontSize: '2.5rem',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-md)',
              fontFamily: 'var(--font-display)',
            }}
          >
            Data Governance Platform
          </h1>
          <p
            style={{
              fontSize: '1.25rem',
              color: 'var(--color-text-secondary)',
              fontFamily: 'var(--font-body)',
            }}
          >
            Select your role to continue
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: 'var(--space-lg)',
          }}
        >
          {roles.map((role) => {
            const Icon = role.icon;
            const color = roleColors[role.id];
            const isHovered = hoveredRole === role.id;
            return (
              <button
                key={role.id}
                onClick={() => selectRole(role)}
                onMouseEnter={() => setHoveredRole(role.id)}
                onMouseLeave={() => setHoveredRole(null)}
                style={{
                  position: 'relative',
                  background: isHovered
                    ? 'var(--color-bg-elevated)'
                    : 'var(--color-bg-secondary)',
                  borderRadius: 'var(--radius-xl)',
                  padding: 'var(--space-xl)',
                  transition: 'all 0.3s ease',
                  border: `1px solid ${isHovered ? color : 'var(--color-border-default)'}`,
                  boxShadow: isHovered ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
                  transform: isHovered ? 'scale(1.03)' : 'scale(1)',
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                <div>
                  <div
                    style={{
                      width: '4rem',
                      height: '4rem',
                      margin: '0 auto',
                      marginBottom: 'var(--space-lg)',
                      background: color,
                      borderRadius: 'var(--radius-lg)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transform: isHovered ? 'scale(1.1)' : 'scale(1)',
                      transition: 'transform 0.3s ease',
                    }}
                  >
                    <Icon
                      style={{ width: '2rem', height: '2rem', color: '#FFFFFF' }}
                    />
                  </div>

                  <h3
                    style={{
                      fontSize: '1.25rem',
                      fontWeight: 700,
                      color: 'var(--color-text-primary)',
                      marginBottom: 'var(--space-sm)',
                      fontFamily: 'var(--font-display)',
                    }}
                  >
                    {role.name}
                  </h3>

                  <p
                    style={{
                      color: 'var(--color-text-secondary)',
                      fontSize: '0.875rem',
                      lineHeight: 1.6,
                      fontFamily: 'var(--font-body)',
                    }}
                  >
                    {role.description}
                  </p>

                  <div
                    style={{
                      marginTop: 'var(--space-lg)',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      color: isHovered ? color : 'var(--color-text-tertiary)',
                      transition: 'color 0.3s ease',
                      fontFamily: 'var(--font-body)',
                    }}
                  >
                    Continue as {role.name} →
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: 'var(--space-2xl)', textAlign: 'center' }}>
          <p
            style={{
              color: 'var(--color-text-muted)',
              fontSize: '0.875rem',
              fontFamily: 'var(--font-body)',
            }}
          >
            Demo Mode - No authentication required
          </p>
        </div>
      </div>
    </div>
  );
}
