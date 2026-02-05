import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Database, ShoppingCart, Shield, BarChart3 } from 'lucide-react';

export function RoleSelector() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const roles = [
    {
      id: 'owner',
      name: 'Data Owner',
      description: 'Register and manage datasets, view violations',
      icon: Database,
      color: 'from-blue-500 to-blue-600',
      path: '/owner/register',
    },
    {
      id: 'consumer',
      name: 'Data Consumer',
      description: 'Browse catalog and subscribe to datasets',
      icon: ShoppingCart,
      color: 'from-green-500 to-green-600',
      path: '/consumer/catalog',
    },
    {
      id: 'steward',
      name: 'Data Steward',
      description: 'Review and approve subscription requests',
      icon: Shield,
      color: 'from-purple-500 to-purple-600',
      path: '/steward/approvals',
    },
    {
      id: 'admin',
      name: 'Platform Admin',
      description: 'View compliance metrics and violation trends',
      icon: BarChart3,
      color: 'from-orange-500 to-orange-600',
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-6">
      <div className="max-w-6xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            Data Governance Platform
          </h1>
          <p className="text-xl text-gray-400">
            Select your role to continue
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <button
                key={role.id}
                onClick={() => selectRole(role)}
                className="group relative bg-gray-800 rounded-2xl p-8 hover:bg-gray-750 transition-all duration-300 border border-gray-700 hover:border-gray-600 hover:shadow-2xl hover:scale-105"
              >
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${role.color} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`}
                />

                <div className="relative">
                  <div
                    className={`w-16 h-16 mx-auto mb-6 bg-gradient-to-br ${role.color} rounded-xl flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300`}
                  >
                    <Icon className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="text-xl font-bold text-white mb-3">
                    {role.name}
                  </h3>

                  <p className="text-gray-400 text-sm leading-relaxed">
                    {role.description}
                  </p>

                  <div className="mt-6 text-sm font-semibold text-gray-500 group-hover:text-white transition-colors">
                    Continue as {role.name} →
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-500 text-sm">
            Demo Mode - No authentication required
          </p>
        </div>
      </div>
    </div>
  );
}
