import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import { Layout } from './components/Layout';
import { TopNavLayout } from './components/TopNavLayout';
import { RoleSelector } from './pages/RoleSelector';

// Data Owner Pages
import { DatasetRegistrationWizard } from './pages/DataOwner/DatasetRegistrationWizard';
import { OwnerDashboard } from './pages/DataOwner/OwnerDashboard';

// Data Consumer Pages
import { DataCatalogBrowser } from './pages/DataConsumer/DataCatalogBrowser';

// Data Steward Pages
import { ApprovalQueue } from './pages/DataSteward/ApprovalQueue';

// Admin Pages
import { ComplianceDashboard as AdminDashboard } from './pages/Admin/ComplianceDashboard';

// Legacy Pages (keep for backward compatibility)
import { Dashboard } from './pages/Dashboard';
import { DatasetCatalog } from './pages/DatasetCatalog';
import { DatasetDetail } from './pages/DatasetDetail';
import { SchemaImport } from './pages/SchemaImport';
import { PolicyManager } from './pages/PolicyManager';
import { ContractViewer } from './pages/ContractViewer';
import { SubscriptionQueue } from './pages/SubscriptionQueue';
import { ComplianceDashboard } from './pages/ComplianceDashboard';
import { GitHistory } from './pages/GitHistory';
import { PolicyList, PolicyForm, PolicyDetail, PolicyReview, PolicyDashboard, PolicyTimeline, ComplianceReport, PolicyExchange, DomainGovernance, PolicyConflicts } from './components/PolicyAuthoring';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#0f1419',
              color: '#e8eaed',
              border: '1px solid rgba(139, 92, 246, 0.2)',
              fontFamily: "'Outfit', sans-serif",
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#0f1419',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#0f1419',
              },
            },
          }}
        />
        <Routes>
          {/* Role Selection */}
          <Route path="/select-role" element={<RoleSelector />} />

          {/* Data Owner Routes */}
          <Route path="/owner" element={<Layout />}>
            <Route index element={<Navigate to="/owner/dashboard" replace />} />
            <Route path="dashboard" element={<OwnerDashboard />} />
            <Route path="register" element={<DatasetRegistrationWizard />} />
            <Route path="datasets/:id" element={<DatasetDetail />} />
          </Route>

          {/* Data Consumer Routes */}
          <Route path="/consumer" element={<Layout />}>
            <Route index element={<Navigate to="/consumer/catalog" replace />} />
            <Route path="catalog" element={<DataCatalogBrowser />} />
            <Route path="datasets/:id" element={<DatasetDetail />} />
          </Route>

          {/* Data Steward Routes */}
          <Route path="/steward" element={<Layout />}>
            <Route index element={<Navigate to="/steward/approvals" replace />} />
            <Route path="approvals" element={<ApprovalQueue />} />
            <Route path="contracts/:id" element={<ContractViewer />} />
          </Route>

          {/* Admin Routes */}
          <Route path="/admin" element={<Layout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="compliance" element={<ComplianceDashboard />} />
          </Route>

          {/* Legacy Routes (backward compatibility) */}
          <Route path="/" element={<TopNavLayout />}>
            <Route index element={<Navigate to="/select-role" replace />} />
            <Route path="catalog" element={<DatasetCatalog />} />
            <Route path="datasets/:id" element={<DatasetDetail />} />
            <Route path="import" element={<SchemaImport />} />
            <Route path="policies" element={<PolicyManager />} />
            <Route path="contracts/:id" element={<ContractViewer />} />
            <Route path="subscriptions" element={<SubscriptionQueue />} />
            <Route path="compliance" element={<ComplianceDashboard />} />
            <Route path="git" element={<GitHistory />} />
            <Route path="policy-authoring" element={<PolicyList />} />
            <Route path="policy-authoring/new" element={<PolicyForm />} />
            <Route path="policy-authoring/:id" element={<PolicyDetail />} />
            <Route path="policy-authoring/:id/timeline" element={<PolicyTimeline />} />
            <Route path="policy-review" element={<PolicyReview />} />
            <Route path="policy-dashboard" element={<PolicyDashboard />} />
            <Route path="compliance-report" element={<ComplianceReport />} />
            <Route path="policy-exchange" element={<PolicyExchange />} />
            <Route path="domain-governance" element={<DomainGovernance />} />
            <Route path="policy-conflicts" element={<PolicyConflicts />} />
          </Route>

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/select-role" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
