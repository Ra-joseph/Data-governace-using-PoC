# Data Governance Platform - Frontend

A modern, production-ready React frontend for the Data Governance Platform with distinctive design and comprehensive Git integration.

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Styling System](#styling-system)
- [Development](#development)
- [Building for Production](#building-for-production)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎨 Design Philosophy

This frontend implements a **refined, professional aesthetic** with data visualization focus:

- **Typography**: Outfit (display) + IBM Plex Mono (code) for a tech-forward look
- **Color Scheme**: Dark theme with purple accent (#8b5cf6) and data viz highlights
- **Motion**: Framer Motion for smooth animations and micro-interactions
- **Spatial Design**: Card-based layouts with generous spacing and depth
- **Data Viz**: Recharts integration for beautiful charts and graphs

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on http://localhost:3000

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   └── Layout.jsx    # Main layout with sidebar
│   ├── pages/            # Page components
│   │   ├── Dashboard.jsx        # Metrics & charts
│   │   ├── DatasetCatalog.jsx   # Browse datasets
│   │   ├── DatasetDetail.jsx    # Dataset details
│   │   ├── GitHistory.jsx       # Git version control
│   │   └── [Phase 2 pages]      # Coming soon
│   ├── services/         # API integration
│   │   └── api.js        # Axios configuration
│   ├── stores/           # State management
│   │   └── index.js      # Zustand stores
│   ├── App.jsx           # Main app component
│   ├── App.css           # Global styles
│   └── main.jsx          # Entry point
├── package.json
├── vite.config.js
└── README.md
```

## 🎯 Features

### ✅ Implemented (Phase 1)

1. **Dashboard**
   - Real-time metrics (datasets, violations, PII)
   - Trend visualization (6-month dataset growth)
   - Classification distribution (pie chart)
   - Policy compliance (bar chart)
   - Recent activity feed

2. **Dataset Catalog**
   - Grid view with cards
   - Search functionality
   - Filter by status (published, draft, deprecated)
   - Badge system (status, classification, PII)
   - Owner information display

3. **Dataset Detail**
   - Comprehensive dataset information
   - Schema table with all fields
   - Metadata display
   - Owner and classification info

4. **Git History** ⭐ NEW
   - Complete commit timeline
   - Repository status dashboard
   - Contract file browser
   - Commit details modal
   - Time filtering (all time, today, week)
   - Visual timeline with dots and lines

5. **Layout & Navigation**
   - Animated sidebar with icons
   - Smooth page transitions
   - Responsive design (desktop, tablet, mobile)
   - System status indicator

#### 🔜 Coming Soon (Phase 2)

- Schema Import Wizard
- Policy Manager
- Contract Viewer with diff
- Subscription Queue
- Compliance Dashboard

## 🎨 Design System

### Color Variables

```css
--color-bg-primary: #0a0e14      /* Main background */
--color-bg-secondary: #0f1419    /* Cards */
--color-accent-primary: #8b5cf6  /* Purple accent */
--color-success: #10b981         /* Green */
--color-warning: #f59e0b         /* Orange */
--color-error: #ef4444           /* Red */
```

### Typography

```css
--font-display: 'Outfit'         /* Headings, UI */
--font-mono: 'IBM Plex Mono'     /* Code, data */
```

### Component Classes

```css
.card              /* Base card component */
.badge             /* Status badges */
.btn-primary       /* Primary action button */
.btn-secondary     /* Secondary button */
.metric-card       /* Dashboard metric */
```

## 📊 Data Visualization

### Charts Implemented

1. **Area Chart** - Dataset growth & violations over time
2. **Pie Chart** - Data classification distribution
3. **Bar Chart** - Policy compliance comparison

### Chart Configuration

All charts use:
- Dark theme colors
- Purple (#8b5cf6) for primary data
- Red (#ef4444) for violations
- Custom tooltips with dark styling
- Responsive containers

## 🔌 API Integration

### Service Layer

```javascript
// Dataset operations
datasetAPI.list(params)
datasetAPI.get(id)
datasetAPI.create(data)
datasetAPI.importSchema(data)

// Git operations ⭐ NEW
gitAPI.history(filename)
gitAPI.contracts()
gitAPI.status()
gitAPI.diff(commit1, commit2)
```

### State Management (Zustand)

```javascript
// Dataset store
const datasets = useDatasetStore(state => state.datasets);

// Git store ⭐ NEW
const history = useGitStore(state => state.history);
```

## 🎭 Animations

### Framer Motion

```javascript
// Page transitions
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}

// Staggered children
variants={container}
transition={{ staggerChildren: 0.1 }}

// Hover effects
whileHover={{ scale: 1.02 }}
```

## 📱 Responsive Design

### Breakpoints

- **Desktop**: > 1024px (full layout)
- **Tablet**: 768px - 1024px (adapted grid)
- **Mobile**: < 768px (single column, collapsed sidebar)

### Mobile Optimizations

- Collapsed sidebar (icons only)
- Single column grids
- Touch-friendly buttons
- Responsive typography (14px base on mobile)

## 🧪 Development

### Running the App

```bash
# Development mode with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

### Proxy Configuration

Vite automatically proxies `/api` requests to the backend:

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## 🎯 Git Integration Features

### Repository Status Dashboard ⭐

Displays:
- Total contracts in repository
- Total commits
- Active branch name
- Git tags count
- Last commit information

### Commit Timeline ⭐

Features:
- Visual timeline with dots and connecting lines
- Commit message, hash, author, and date
- Time-ago formatting ("2 hours ago")
- Clickable commits for details
- Filtering by time period

### Contract File Browser ⭐

Shows:
- All contract files in repository
- File sizes
- Click to view commit history
- Sidebar with sticky positioning

### Commit Details Modal ⭐

Displays:
- Full commit hash
- Complete author information
- Precise timestamp
- Full commit message
- Actions (view, download)

## 🚦 Status Indicators

### Badge System

```jsx
// Status badges
<span className="badge badge-success">Published</span>
<span className="badge badge-warning">Draft</span>
<span className="badge badge-error">PII</span>

// Classification badges
<span className="badge badge-info">Public</span>
<span className="badge badge-warning">Confidential</span>
```

## 🔐 Security

### Best Practices Implemented

- CORS configuration
- API token storage in localStorage
- Request/response interceptors
- Error handling with user-friendly messages
- No sensitive data in client state

## 📈 Performance

### Optimizations

- Code splitting with React Router
- Lazy loading for heavy components
- Memoization with React hooks
- Debounced search inputs
- Optimized re-renders with Zustand

## 🎨 Customization

### Changing Theme Colors

Edit `App.css`:

```css
:root {
  --color-accent-primary: #your-color;
  --color-accent-secondary: #your-color;
}
```

### Adding New Pages

1. Create page in `src/pages/YourPage.jsx`
2. Add route in `src/App.jsx`
3. Add navigation link in `src/components/Layout.jsx`

### Custom Components

Follow the existing pattern:

```jsx
import { motion } from 'framer-motion';
import './YourComponent.css';

export const YourComponent = () => {
  return (
    <motion.div 
      className="your-component"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* Your content */}
    </motion.div>
  );
};
```

## 🐛 Troubleshooting

### API Connection Issues

```bash
# Check backend is running
curl http://localhost:8000/health

# Check proxy configuration
# Verify vite.config.js proxy settings
```

### Chart Rendering Issues

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Git Integration Issues

```bash
# Ensure Git endpoints are registered
# Check backend/app/main.py includes git router

# Test Git endpoints
curl http://localhost:8000/api/v1/git/status
```

## 📚 Dependencies

### Core

- **React 18.2**: UI framework
- **React Router 6**: Navigation
- **Vite**: Build tool and dev server

### State & Data

- **Zustand**: State management
- **Axios**: HTTP client

### UI & Animation

- **Framer Motion**: Animations
- **Recharts**: Data visualization
- **Lucide React**: Icons
- **React Hot Toast**: Notifications

### Utilities

- **date-fns**: Date formatting
- **React Markdown**: Markdown rendering
- **YAML**: YAML parsing

## 🎓 Learning Resources

### Key Concepts

1. **Framer Motion**: https://www.framer.com/motion/
2. **Zustand**: https://github.com/pmndrs/zustand
3. **Recharts**: https://recharts.org/
4. **Vite**: https://vitejs.dev/

### Code Examples

Check the existing pages for patterns:
- `Dashboard.jsx` - Charts and metrics
- `DatasetCatalog.jsx` - Grid layouts and filtering
- `GitHistory.jsx` - Timeline and modals

## 🚀 Deployment

### Production Build

```bash
npm run build
```

Output in `dist/` folder.

### Deployment Options

1. **Static Hosting**: Netlify, Vercel, GitHub Pages
2. **Docker**: Use nginx to serve static files
3. **Azure Static Web Apps**: Direct deployment

### Environment Configuration

Set `VITE_API_URL` for production:

```env
VITE_API_URL=https://your-api-domain.com
```

## 📝 Next Steps

1. Complete Schema Import wizard
2. Build Contract Viewer with diff
3. Implement Subscription workflow
4. Add Policy Manager
5. Create Compliance Dashboard
6. Add user authentication
7. Implement real-time updates

## 🎉 Features Summary

### ✅ Fully Functional

- Dashboard with live metrics
- Dataset catalog and search
- Dataset detail views
- **Git version control viewer** ⭐
- **Complete commit history** ⭐
- **Repository status dashboard** ⭐
- Responsive navigation
- Toast notifications
- Loading states
- Error handling

### 🎯 Ready for Phase 2

The architecture is ready for:
- Subscription management
- Policy editing
- Contract diff viewer
- Advanced filtering
- User management

---

**Built with React + Vite + Framer Motion** 🚀
