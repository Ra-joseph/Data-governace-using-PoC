# Frontend Guide — Multi-Role React Application

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Role-Based User Interfaces](#role-based-user-interfaces)
  - [Data Owner UI](#data-owner-ui)
  - [Data Consumer UI](#data-consumer-ui)
  - [Data Steward UI](#data-steward-ui)
  - [Platform Admin UI](#platform-admin-ui)
- [Architecture](#architecture)
- [Component Structure](#component-structure)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Design System](#design-system)
- [Testing](#testing)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Production Build](#production-build)

## Overview

The Data Governance Platform frontend is a **multi-role React 18 application** built with Vite, providing dedicated user interfaces for each role in the governance workflow:

- **Data Owner**: Register datasets, view violations, track subscribers
- **Data Consumer**: Browse catalog, request access with SLA negotiation
- **Data Steward**: Review and approve subscription requests
- **Platform Admin**: Monitor compliance metrics and violation trends

**Access URL**: http://localhost:5173/select-role

## Quick Start

```bash
# Prerequisites: Node.js 18+, backend running on port 8000

# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

Frontend starts on **http://localhost:5173**.

### Verify Frontend is Working

1. Open http://localhost:5173/select-role
2. You should see 4 role cards (Data Owner, Consumer, Steward, Admin)
3. Click any card to access that role's interface
4. Data loads from the backend API (port 8000) via Vite proxy

## Role-Based User Interfaces

### Data Owner UI

**Entry point**: http://localhost:5173/select-role → "Data Owner"

#### Owner Dashboard (`/owner/dashboard`)

The dashboard shows all datasets owned by the current user:

- **Dataset cards** with name, status, and violation count
- **Violation alerts** with severity badges (critical/warning)
- **Subscriber count** for each dataset
- **Quick actions**: Register new dataset, view details

**What violations look like:**
```
SD001 [CRITICAL] PII fields require encryption
  → customer_ssn, customer_email, customer_phone
  → Remediation: Set encryption_required: true...

SD003 [WARNING] PII datasets should have compliance tags
  → governance.compliance_tags is empty
  → Remediation: Add compliance_tags: ['GDPR', 'CCPA']
```

#### Dataset Registration Wizard (`/owner/register`)

A 4-step guided form for registering new datasets:

**Step 1 — Basic Info**
- Dataset name and description
- Owner name and email
- Data source type (PostgreSQL, file, Azure)

**Step 2 — Schema Definition**
- Option A: Import from PostgreSQL (auto-detects PII, extracts column types)
- Option B: Manual field-by-field entry
- PII fields are highlighted automatically

**Step 3 — Governance Metadata**
- Data classification (public / internal / confidential / restricted)
- Retention period (days)
- Compliance tags (GDPR, CCPA, HIPAA, SOX, PCI-DSS)
- Encryption settings

**Step 4 — Review & Submit**
- Final review of all fields
- Estimated violations shown before submission
- Submit triggers contract generation and policy validation

After submission, violations are displayed with actionable remediation.

---

### Data Consumer UI

**Entry point**: http://localhost:5173/select-role → "Data Consumer"

#### Catalog Browser (`/consumer/catalog`)

Grid view of all published datasets:

- **Search bar** — filter by name or description
- **Classification filter** — public, internal, confidential, restricted
- **Dataset cards** showing owner, classification, field count, compliance status
- **"Request Access"** button opens subscription form

#### Subscription Request Form

Appears as a modal when clicking "Request Access":

- **Business justification** — why you need this data
- **Use case** — analytics, reporting, integration, ML, compliance
- **Field selection** — choose only the fields you need
- **SLA requirements**:
  - Max latency (ms)
  - Min availability (%)
  - Max staleness (minutes)
  - Max data age (hours)
- **Access duration** — how long access is needed

Submitted requests appear in the Data Steward's approval queue.

---

### Data Steward UI

**Entry point**: http://localhost:5173/select-role → "Data Steward"

#### Approval Queue (`/steward/approvals`)

Table view of all subscription requests:

- **Status filter tabs** — Pending, Approved, Rejected
- **Request details**: consumer email, dataset name, use case, submission date
- **"Review" button** opens the approval modal

#### Review Modal

- Consumer's business justification and use case
- Requested fields list
- SLA requirements
- **Approve** or **Reject** action
- **Field selection**: approve all or a subset of requested fields
- **Access credentials** to provide (username, API key, connection string)
- **Reviewer notes**

When approved:
1. Subscription status → "approved"
2. Access credentials stored
3. New contract version generated (v1.1.0, v1.2.0, etc.)
4. Consumer SLA terms embedded in contract
5. Contract committed to Git

---

### Platform Admin UI

**Entry point**: http://localhost:5173/select-role → "Platform Admin"

#### Compliance Dashboard (`/admin/dashboard`)

**Key Metrics (top row):**
- Compliance rate (% of datasets passing all policies)
- Total active violations
- Active subscriptions
- Pending approval requests

**Analytics Charts (Recharts):**

1. **Violation Trends** (Line chart)
   - X-axis: date
   - Y-axis: violation count
   - Shows governance health over time

2. **Violations by Severity** (Pie chart)
   - Critical (red), Warning (orange), Info (blue)
   - Click segments to filter

3. **Top Violated Policies** (Bar chart)
   - Policy ID on X-axis
   - Count on Y-axis
   - Identifies systemic issues

4. **Compliance by Classification** (Stacked bar)
   - Public, Internal, Confidential, Restricted
   - Passed vs failed breakdown

**Recent Activity Feed:**
- Latest policy violations with timestamps
- New subscription requests
- Dataset registration events

## Architecture

```
frontend/
├── src/
│   ├── App.jsx              # React Router configuration
│   │   Routes:
│   │   /select-role        → RoleSelector
│   │   /owner/dashboard    → OwnerDashboard
│   │   /owner/register     → DatasetRegistrationWizard
│   │   /consumer/catalog   → DataCatalogBrowser
│   │   /steward/approvals  → ApprovalQueue
│   │   /admin/dashboard    → ComplianceDashboard
│   │
│   ├── components/
│   │   └── Layout.jsx      # Sidebar navigation (role-based links)
│   │
│   ├── contexts/
│   │   └── AuthContext.jsx # Current role context (set on role selection)
│   │
│   ├── pages/              # Role-based page components
│   │   ├── RoleSelector.jsx
│   │   ├── DataOwner/
│   │   ├── DataConsumer/
│   │   ├── DataSteward/
│   │   └── Admin/
│   │
│   ├── services/
│   │   └── api.js          # All API calls (datasets, subscriptions, git)
│   │
│   └── stores/
│       └── index.js        # Zustand stores (5 stores)
│
├── vite.config.js           # API proxy: /api → http://localhost:8000
└── vitest.config.js         # Test configuration
```

## Component Structure

### Layout.jsx

The shared layout wraps all pages with:
- **Sidebar navigation** with role-specific links
- **Top header** with current role indicator
- **Main content area** for page content

Navigation links change based on role:
- Owner: Dashboard, Register Dataset
- Consumer: Catalog, My Subscriptions
- Steward: Approval Queue, History
- Admin: Compliance Dashboard, Reports

### AuthContext.jsx

Provides role context throughout the app:

```javascript
const { currentRole, setRole } = useAuth();
// currentRole: 'owner' | 'consumer' | 'steward' | 'admin' | null
```

Set on role selection. Persists in Zustand store for session duration.

## State Management

Uses **Zustand** for lightweight state management:

```javascript
// stores/index.js — 5 stores
import { useDatasetStore, useSubscriptionStore, useAuthStore,
         useGitStore, useUIStore } from './stores';

// Dataset store
const { datasets, loading, fetchDatasets } = useDatasetStore();

// Subscription store
const { subscriptions, createSubscription } = useSubscriptionStore();
```

Zustand was chosen for:
- No boilerplate (no reducers, no actions)
- Direct state updates
- React devtools integration
- Small bundle size

## API Integration

All API calls go through `src/services/api.js`:

```javascript
// Datasets
const datasets = await api.get('/api/v1/datasets/');
const dataset = await api.get(`/api/v1/datasets/${id}`);
const schema = await api.post('/api/v1/datasets/import-schema', payload);

// Subscriptions
const subs = await api.get('/api/v1/subscriptions/');
const result = await api.post(`/api/v1/subscriptions/${id}/approve`, data);

// Git
const commits = await api.get('/api/v1/git/commits');
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`, so there are no CORS issues in development.

**In `vite.config.js`:**
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## Design System

### Color Palette

```css
:root {
  --bg-primary: #0a0e14;        /* Dark background */
  --accent-primary: #8b5cf6;    /* Purple accent */
  --success: #10b981;           /* Green */
  --warning: #f59e0b;           /* Orange */
  --error: #ef4444;             /* Red */
  --text-primary: #e2e8f0;      /* Light text */
  --text-secondary: #94a3b8;    /* Muted text */
}
```

### Typography

- **Display**: Outfit (headings, large text)
- **Mono**: IBM Plex Mono (code, IDs, technical values)

### Severity Badge Colors

| Severity | Color | Background |
|----------|-------|-----------|
| Critical | #ef4444 | rgba(239,68,68,0.1) |
| Warning | #f59e0b | rgba(245,158,11,0.1) |
| Info | #3b82f6 | rgba(59,130,246,0.1) |
| Passed | #10b981 | rgba(16,185,129,0.1) |

### Responsive Breakpoints

- **Desktop (>1024px)**: Full sidebar + multi-column grids
- **Tablet (768-1024px)**: Compact sidebar + adapted grids
- **Mobile (<768px)**: Icon-only sidebar + single column

## Testing

### Frontend Test Setup

```bash
# Run tests
cd frontend
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### Test Structure

```
frontend/src/test/
├── setup.js         # Global test setup (jsdom environment)
└── api.test.js      # API service tests
```

### Writing Component Tests

```javascript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DataCatalogBrowser from '../pages/DataConsumer/DataCatalogBrowser';

describe('DataCatalogBrowser', () => {
  it('renders catalog heading', () => {
    render(
      <MemoryRouter>
        <DataCatalogBrowser />
      </MemoryRouter>
    );
    expect(screen.getByText(/Data Catalog/i)).toBeInTheDocument();
  });
});
```

## Customization

### Change Theme Colors

Edit `frontend/src/App.css`:

```css
:root {
  --accent-primary: #your-brand-color;
  --bg-primary: #your-background;
}
```

### Add a New Page

1. Create `src/pages/YourRole/YourPage.jsx`
2. Add route in `src/App.jsx`:
   ```jsx
   <Route path="/your-route" element={<YourPage />} />
   ```
3. Add navigation link in `src/components/Layout.jsx`

### Add a New API Call

Add to `src/services/api.js`:

```javascript
export const yourApi = {
  list: () => api.get('/api/v1/your-endpoint/'),
  get: (id) => api.get(`/api/v1/your-endpoint/${id}`),
  create: (data) => api.post('/api/v1/your-endpoint/', data),
};
```

### Add a New Chart

```javascript
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
  <BarChart data={yourData}>
    <XAxis dataKey="name" />
    <YAxis />
    <Bar dataKey="value" fill="#8b5cf6" />
  </BarChart>
</ResponsiveContainer>
```

## Troubleshooting

### Frontend won't start

```bash
# Check Node.js version
node --version  # Must be 18+

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### "Failed to fetch" errors in browser

```bash
# Backend must be running
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Charts not rendering

```bash
# Reinstall recharts
npm uninstall recharts
npm install recharts@^2.10.3
```

### Subscription approval fails

Check the browser console (F12 → Console) for errors. Common causes:
- Dataset must have at least one subscriber field defined
- Git must be initialized in `backend/contracts/`
- Backend logs will show specific contract versioning errors

### CORS errors

In development, the Vite proxy handles CORS. If you see CORS errors:
1. Check `vite.config.js` has the proxy configuration
2. Ensure backend is running on port 8000
3. Use the Vite dev server (port 5173), not a static build

## Production Build

```bash
# Build for production
cd frontend
npm run build

# Output is in frontend/dist/
# Serve with nginx, Netlify, Vercel, or Azure Static Web Apps
```

**Environment variable for production API URL:**

Create `frontend/.env.production`:
```env
VITE_API_URL=https://your-api-domain.com
```

Update `api.js` to use:
```javascript
const BASE_URL = import.meta.env.VITE_API_URL || '';
```

---

**Frontend Access URL**: http://localhost:5173/select-role
**Backend API**: http://localhost:8000
**API Documentation**: http://localhost:8000/api/docs
**More Details**: See the [main README](./README.md) for complete platform documentation.
