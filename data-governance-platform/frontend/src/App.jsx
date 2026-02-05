import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { DatasetCatalog } from './pages/DatasetCatalog';
import { DatasetDetail } from './pages/DatasetDetail';
import { SchemaImport } from './pages/SchemaImport';
import { PolicyManager } from './pages/PolicyManager';
import { ContractViewer } from './pages/ContractViewer';
import { SubscriptionQueue } from './pages/SubscriptionQueue';
import { ComplianceDashboard } from './pages/ComplianceDashboard';
import { GitHistory } from './pages/GitHistory';
import './App.css';

function App() {
  return (
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
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="catalog" element={<DatasetCatalog />} />
          <Route path="datasets/:id" element={<DatasetDetail />} />
          <Route path="import" element={<SchemaImport />} />
          <Route path="policies" element={<PolicyManager />} />
          <Route path="contracts/:id" element={<ContractViewer />} />
          <Route path="subscriptions" element={<SubscriptionQueue />} />
          <Route path="compliance" element={<ComplianceDashboard />} />
          <Route path="git" element={<GitHistory />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
