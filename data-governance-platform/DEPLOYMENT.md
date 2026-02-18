# Data Governance Platform - Deployment Instructions

## Table of Contents

- [What's Included](#whats-included)
- [Quick Deployment](#quick-deployment)
- [Verification Checklist](#verification-checklist)
- [Security Checklist](#security-checklist)
- [Production Deployment](#production-deployment)
- [Monitoring & Observability](#monitoring--observability)
- [Maintenance](#maintenance)
- [Support & Resources](#support--resources)
- [Learning Resources](#learning-resources)
- [Next Steps](#next-steps)

## 📦 What's Included

This complete, production-ready Data Governance Platform includes:

### Core Application (90+ Files)
- **Backend API**: FastAPI application with 5 routers and 28+ endpoints
- **Database Models**: 4 SQLAlchemy models (Dataset, Contract, Subscription, User)
- **Pydantic Schemas**: 3 schema modules with full v2 validation
- **Rule-Based Policy Engine**: 17 YAML-defined governance policies (SD, DQ, SG)
- **Semantic Policy Engine**: 8 LLM-powered policies via local Ollama
- **Policy Orchestrator**: FAST/BALANCED/THOROUGH/ADAPTIVE validation routing
- **Services**: PostgreSQL connector (PII detection), Git service, Contract service, Ollama client
- **Frontend**: React 18 multi-role application (Owner, Consumer, Steward, Admin)
- **Demo Database**: PostgreSQL with 3 tables and realistic financial data

### Documentation (9 Files)
- **README.md**: Complete platform documentation
- **QUICKSTART.md**: Full-stack setup guide (backend + frontend)
- **PROJECT_SUMMARY.md**: Technical architecture deep-dive
- **DEPLOYMENT.md**: This file — deployment instructions
- **SEMANTIC_SCANNING.md**: LLM-powered validation guide
- **POLICY_ORCHESTRATION.md**: Intelligent routing guide
- **FRONTEND_GUIDE.md**: Multi-role frontend guide
- **MANIFEST.md**: Complete file listing
- **FULL_STACK_INVENTORY.md**: Full package inventory

### Configuration (5 Files)
- **docker-compose.yml**: PostgreSQL 15 demo setup
- **requirements.txt**: Python dependencies (15+ packages)
- **package.json**: Frontend npm dependencies (15 packages)
- **start.sh**: Quick backend start script
- **vite.config.js**: Frontend build configuration with API proxy

### Demo & Testing (5 Files)
- **setup_postgres.sql**: Database schema with 3 tables
- **sample_data.sql**: 39 records with intentional violations
- **test_setup.py**: Automated 5-check setup verification
- **register_customer_accounts.json**: Example dataset registration payload
- **backend/tests/**: 101 pytest tests across 8 test files

## 🚀 Quick Deployment

### Local Development (Full Stack)

```bash
# 1. Clone the repository
git clone https://github.com/Ra-joseph/Data-governace-using-PoC.git
cd Data-governace-using-PoC/data-governance-platform

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
cd backend && pip install -r requirements.txt && cd ..

# 3. Start PostgreSQL demo database
docker-compose up -d

# 4. Start backend (Terminal 1)
chmod +x start.sh
./start.sh

# 5. Start frontend (Terminal 2)
cd frontend
npm install
npm run dev

# 6. Verify setup (Terminal 3)
source venv/bin/activate
python test_setup.py
```

**Expected Test Output:**
```
✓ Health Check
✓ PostgreSQL Connection
✓ Schema Import
✓ Dataset Registration
✓ List Datasets

🎉 All tests passed! Setup is complete.
```

**Access the Application:**
- Role Selector: http://localhost:5173/select-role
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Backend Only (No Frontend)

```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
docker-compose -f ../docker-compose.yml up -d
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment (Alternative)

```bash
# Build Docker image
docker build -t governance-platform:latest ./backend

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

*(Note: docker-compose.prod.yml not included — create for production)*

## ✅ Verification Checklist

After deployment, verify:

**Backend**
- [ ] API accessible at http://localhost:8000
- [ ] Swagger docs at http://localhost:8000/api/docs
- [ ] Health check: `curl http://localhost:8000/health` → `{"status": "healthy"}`
- [ ] PostgreSQL running with 3 demo tables: `docker ps | grep governance_postgres`
- [ ] All 5 setup tests pass: `python test_setup.py`
- [ ] Contracts directory initialized with Git: `ls backend/contracts/`
- [ ] Policy files loaded (4 YAML files): `ls backend/policies/`

**Frontend**
- [ ] Frontend accessible at http://localhost:5173/select-role
- [ ] 4 role cards visible (Owner, Consumer, Steward, Admin)
- [ ] Dashboard charts load when selecting Admin role
- [ ] Catalog loads datasets when selecting Consumer role

**Optional: Semantic Scanning**
- [ ] Ollama running: `curl http://localhost:11434` → response from Ollama
- [ ] Semantic health: `curl http://localhost:8000/api/v1/semantic/health` → `{"available": true}`

## 🔒 Security Checklist

### Critical (Must Have)
- [ ] Implement authentication (OAuth2/JWT)
- [ ] Add authorization/RBAC
- [ ] Encrypt sensitive database fields
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting
- [ ] Implement input validation
- [ ] Enable CORS properly

### Important (Should Have)
- [ ] Add audit logging
- [ ] Implement secret rotation
- [ ] Use Azure Key Vault or similar
- [ ] Add request/response logging
- [ ] Enable monitoring and alerting
- [ ] Set up backup procedures
- [ ] Add health checks
- [ ] Implement circuit breakers

### Recommended (Nice to Have)
- [ ] Add API versioning
- [ ] Implement caching (Redis)
- [ ] Add request throttling
- [ ] Enable distributed tracing
- [ ] Add performance monitoring
- [ ] Implement blue-green deployment
- [ ] Add chaos engineering tests

## 🚀 Production Deployment

### Prerequisites
- **Kubernetes Cluster** or **Azure App Service**
- **PostgreSQL Database** (Azure Database for PostgreSQL)
- **Git Repository** (GitHub, GitLab, Azure Repos)
- **Azure Key Vault** (for secrets)
- **Azure Storage** (for contract backups)

### Deployment Steps

1. **Database Setup**
   ```bash
   # Create Azure Database for PostgreSQL
   az postgres server create \
     --resource-group governance-rg \
     --name governance-db \
     --sku-name GP_Gen5_2
   
   # Run migrations
   python -m alembic upgrade head
   ```

2. **Application Deployment**
   ```bash
   # Build and push Docker image
   docker build -t your-registry/governance:latest .
   docker push your-registry/governance:latest
   
   # Deploy to Kubernetes
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

3. **Configuration**
   ```bash
   # Set environment variables
   kubectl create secret generic governance-secrets \
     --from-literal=POSTGRES_PASSWORD=xxx \
     --from-literal=GIT_TOKEN=xxx
   ```

4. **Monitoring Setup**
   ```bash
   # Deploy monitoring stack
   kubectl apply -f monitoring/prometheus.yaml
   kubectl apply -f monitoring/grafana.yaml
   ```

### Azure-Specific Deployment

```bash
# Create App Service
az webapp create \
  --resource-group governance-rg \
  --plan governance-plan \
  --name governance-api \
  --runtime "PYTHON:3.10"

# Configure app settings
az webapp config appsettings set \
  --resource-group governance-rg \
  --name governance-api \
  --settings @appsettings.json

# Deploy code
az webapp deployment source config-zip \
  --resource-group governance-rg \
  --name governance-api \
  --src governance-platform.zip
```

## 📊 Monitoring & Observability

### Key Metrics to Track

**Application Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (percentage)
- Active connections

**Business Metrics:**
- Datasets registered (per day)
- Contracts validated (per day)
- Policy violations (by type)
- Compliance rate (percentage)

**Infrastructure Metrics:**
- CPU utilization
- Memory usage
- Database connections
- Disk I/O

### Recommended Tools
- **APM**: Application Insights, DataDog, New Relic
- **Logging**: ELK Stack, Azure Log Analytics
- **Metrics**: Prometheus + Grafana
- **Alerting**: PagerDuty, Opsgenie

## 🔄 Maintenance

### 📅 Daily
- Monitor error rates and response times
- Check system health endpoints
- Review critical alerts

### 📅 Weekly
- Review policy violation trends
- Check database performance
- Update dependencies (security patches)

### 📅 Monthly
- Capacity planning review
- Security audit
- Backup verification
- Performance optimization

### 📅 Quarterly
- Major version updates
- Security penetration testing
- Disaster recovery drill
- User feedback review

## 📚 Support & Resources

### Documentation
- **Full Docs**: README.md (comprehensive guide)
- **Quick Start**: QUICKSTART.md (5-minute guide)
- **Technical Deep-Dive**: PROJECT_SUMMARY.md
- **API Reference**: http://localhost:8000/api/docs

### Getting Help
1. Check documentation files
2. Review test output for errors
3. Check troubleshooting section in README
4. Review logs: `docker logs governance_postgres`

### 🔧 Common Issues

**PostgreSQL won't start:**
```bash
docker-compose down -v
docker-compose up -d
```

**Backend crashes:**
```bash
# Check Python version
python --version  # Must be 3.10+

# Reinstall dependencies
pip install -r backend/requirements.txt --upgrade
```

**Tests fail:**
```bash
# Ensure services are running
docker ps  # PostgreSQL
curl http://localhost:8000/health  # Backend
```

## 📚 Learning Resources

### Included Examples
1. **Financial Demo**: 3 tables with realistic data
2. **Policy Violations**: Intentional violations for learning
3. **Test Suite**: Automated validation examples
4. **API Examples**: Sample curl commands

### Suggested Learning Path
1. **Day 1**: Follow QUICKSTART.md
2. **Day 2**: Explore demo data and violations
3. **Day 3**: Review policy files and validation
4. **Day 4**: Try registering new datasets
5. **Day 5**: Explore Git contracts and versioning

## 📈 Next Steps

### Immediate (Week 1)
1. Complete local setup
2. Run all tests successfully
3. Explore demo scenario
4. Review generated contracts

### Short-term (Month 1)
1. Connect to your PostgreSQL database
2. Import your first real dataset
3. Customize policies for your organization
4. Add authentication

### Medium-term (Quarter 1)
1. Deploy to production environment
2. Build React frontend (Phase 2)
3. Implement subscription workflow
4. Add monitoring and alerting

### Long-term (Year 1)
1. Add Azure Data Lake connector
2. Implement data lineage
3. Build ML-powered features
4. Scale to multiple teams

## 🎉 Success!

You now have a complete, production-ready Data Governance Platform that:

✅ Validates data contracts against policies
✅ Prevents compliance violations before publication
✅ Tracks all changes in Git
✅ Provides actionable remediation guidance
✅ Supports federated governance (UN Peacekeeping model)
✅ Includes comprehensive documentation
✅ Has automated testing
✅ Comes with realistic demo data

**Ready to govern your data!** 🚀

---

**Version**: 2.0.0 (Phase 1 + Phase 2 + Semantic AI)
**Last Updated**: February 18, 2026
**License**: Educational/Demo Project
