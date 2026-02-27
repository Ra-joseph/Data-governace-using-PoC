"""
Tests for Stage 7 – Domain Governance & Policy Analytics.

Covers:
  - Domain listing with policy counts and coverage scores
  - Domain detail with policies, gaps, and datasets
  - Cross-domain governance matrix
  - Comprehensive policy analytics
  - Policy effectiveness and health scoring
"""

import pytest
from fastapi.testclient import TestClient
from app.models.dataset import Dataset
from app.models.contract import Contract


# ── helpers ──────────────────────────────────────────────────────────────

def _create_policy(client, **overrides):
    payload = {
        "title": "Domain Test Policy",
        "description": "Test policy for domain governance.",
        "policy_category": "security",
        "affected_domains": ["finance"],
        "severity": "CRITICAL",
        "scanner_hint": "rule_based",
        "remediation_guide": "Apply appropriate controls.",
        "authored_by": "Author",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/policies/authored/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _approve(client, pid):
    client.post(f"/api/v1/policies/authored/{pid}/submit")
    resp = client.post(f"/api/v1/policies/authored/{pid}/approve", json={"approver_name": "Admin"})
    assert resp.status_code == 200
    return resp.json()


# ── Domain Listing ──────────────────────────────────────────────────────

class TestDomainListing:
    def test_empty_domains(self, client):
        """No policies → no domains."""
        resp = client.get("/api/v1/domain-governance/domains")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_domains"] == 0
        assert data["domains"] == []

    def test_single_domain(self, client):
        """Policies in one domain appear correctly."""
        _create_policy(client, title="Finance P1", affected_domains=["finance"])
        _create_policy(client, title="Finance P2", affected_domains=["finance"], policy_category="compliance")

        resp = client.get("/api/v1/domain-governance/domains")
        data = resp.json()
        assert data["total_domains"] == 1
        fin = data["domains"][0]
        assert fin["domain"] == "finance"
        assert fin["total_policies"] == 2
        assert fin["draft"] == 2
        assert "security" in fin["categories_covered"]
        assert "compliance" in fin["categories_covered"]

    def test_multiple_domains(self, client):
        """Multi-domain policy counted in each domain."""
        _create_policy(client, title="Cross Domain", affected_domains=["finance", "hr"])
        _create_policy(client, title="HR Only", affected_domains=["hr"], policy_category="privacy")

        resp = client.get("/api/v1/domain-governance/domains")
        data = resp.json()
        domains = {d["domain"]: d for d in data["domains"]}

        assert "finance" in domains
        assert "hr" in domains
        assert domains["finance"]["total_policies"] == 1
        assert domains["hr"]["total_policies"] == 2

    def test_status_counts(self, client):
        """Approved vs draft counts are correct."""
        p1 = _create_policy(client, title="Approved Finance", affected_domains=["finance"])
        _approve(client, p1["id"])
        _create_policy(client, title="Draft Finance", affected_domains=["finance"])

        resp = client.get("/api/v1/domain-governance/domains")
        data = resp.json()
        fin = data["domains"][0]
        assert fin["approved"] == 1
        assert fin["draft"] == 1

    def test_coverage_score(self, client):
        """Coverage score reflects categories covered."""
        # 1 out of 6 categories → ~17%
        _create_policy(client, title="One Cat", affected_domains=["finance"], policy_category="security")

        resp = client.get("/api/v1/domain-governance/domains")
        fin = resp.json()["domains"][0]
        assert fin["coverage_score"] == 17  # 1/6 ≈ 16.67 → rounds to 17


# ── Domain Detail ───────────────────────────────────────────────────────

class TestDomainDetail:
    def test_domain_detail(self, client):
        """Detail endpoint returns policies and coverage info."""
        p = _create_policy(client, title="Detail Policy", affected_domains=["marketing"], policy_category="data_quality")
        _approve(client, p["id"])

        resp = client.get("/api/v1/domain-governance/domains/marketing")
        assert resp.status_code == 200
        data = resp.json()
        assert data["domain"] == "marketing"
        assert data["total_policies"] == 1
        assert data["active_policies"] == 1
        assert len(data["policies"]) == 1
        assert data["policies"][0]["title"] == "Detail Policy"
        assert "data_quality" in data["categories_covered"]
        assert "security" in data["categories_missing"]

    def test_domain_detail_all_domain(self, client):
        """Policies with domain 'ALL' appear in any domain query."""
        _create_policy(client, title="Global Policy", affected_domains=["ALL"])

        resp = client.get("/api/v1/domain-governance/domains/engineering")
        data = resp.json()
        assert data["total_policies"] == 1
        assert data["policies"][0]["title"] == "Global Policy"

    def test_domain_detail_empty(self, client):
        """Domain with no policies returns empty lists."""
        resp = client.get("/api/v1/domain-governance/domains/nonexistent")
        data = resp.json()
        assert data["total_policies"] == 0
        assert data["policies"] == []
        assert len(data["categories_missing"]) == 6  # All missing

    def test_domain_detail_with_datasets(self, client, db):
        """Datasets matching domain name appear in response."""
        ds = Dataset(
            name="finance_transactions",
            description="Financial transaction data",
            owner_name="CFO",
            owner_email="cfo@example.com",
            source_type="postgres",
            source_connection="postgresql://localhost/fin",
            physical_location="public.transactions",
            schema_definition=[],
            classification="confidential",
            contains_pii=True,
        )
        db.add(ds)
        db.commit()

        _create_policy(client, title="Fin Policy", affected_domains=["finance"])

        resp = client.get("/api/v1/domain-governance/domains/finance")
        data = resp.json()
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["name"] == "finance_transactions"


# ── Governance Matrix ───────────────────────────────────────────────────

class TestGovernanceMatrix:
    def test_empty_matrix(self, client):
        """No approved policies → empty matrix."""
        resp = client.get("/api/v1/domain-governance/matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert data["matrix"] == []
        assert "categories" in data
        assert len(data["categories"]) == 6

    def test_matrix_with_approved(self, client):
        """Matrix shows approved policy coverage per domain."""
        p1 = _create_policy(client, title="Sec Finance", affected_domains=["finance"], policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="DQ Finance", affected_domains=["finance"], policy_category="data_quality")
        _approve(client, p2["id"])
        p3 = _create_policy(client, title="Sec HR", affected_domains=["hr"], policy_category="security")
        _approve(client, p3["id"])

        resp = client.get("/api/v1/domain-governance/matrix")
        data = resp.json()
        rows = {r["domain"]: r for r in data["matrix"]}

        assert "finance" in rows
        assert rows["finance"]["security"] == 1
        assert rows["finance"]["data_quality"] == 1
        assert rows["finance"]["privacy"] == 0
        assert rows["finance"]["total"] == 2
        # 2 out of 6 categories ≈ 33%
        assert rows["finance"]["coverage_pct"] == 33

        assert "hr" in rows
        assert rows["hr"]["security"] == 1
        assert rows["hr"]["total"] == 1
        # 1 out of 6 ≈ 17%
        assert rows["hr"]["coverage_pct"] == 17

    def test_matrix_excludes_drafts(self, client):
        """Draft policies don't appear in the matrix."""
        _create_policy(client, title="Draft Only", affected_domains=["finance"], policy_category="security")

        resp = client.get("/api/v1/domain-governance/matrix")
        data = resp.json()
        assert data["matrix"] == []


# ── Analytics ───────────────────────────────────────────────────────────

class TestAnalytics:
    def test_empty_analytics(self, client):
        """No policies → zero counts."""
        resp = client.get("/api/v1/domain-governance/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_policies"] == 0
        assert data["approval_funnel"]["drafted"] == 0
        assert data["top_authors"] == []
        assert data["avg_versions_per_policy"] == 0

    def test_analytics_with_policies(self, client):
        """Analytics with mixed statuses."""
        p1 = _create_policy(client, title="Analytic A", authored_by="Alice")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Analytic B", authored_by="Alice")
        client.post(f"/api/v1/policies/authored/{p2['id']}/submit")
        _create_policy(client, title="Analytic C", authored_by="Bob")

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        assert data["total_policies"] == 3

        funnel = data["approval_funnel"]
        assert funnel["drafted"] == 3
        assert funnel["submitted"] >= 1
        assert funnel["approved"] >= 1

    def test_category_distribution(self, client):
        """Category distribution counts correctly."""
        _create_policy(client, title="Cat Sec1", policy_category="security")
        _create_policy(client, title="Cat Sec2", policy_category="security")
        _create_policy(client, title="Cat Priv", policy_category="privacy")

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        assert data["category_distribution"]["security"] == 2
        assert data["category_distribution"]["privacy"] == 1

    def test_severity_distribution(self, client):
        """Severity distribution counts correctly."""
        _create_policy(client, title="Sev Crit", severity="CRITICAL")
        _create_policy(client, title="Sev Warn", severity="WARNING")
        _create_policy(client, title="Sev Info", severity="INFO")

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        assert data["severity_distribution"]["CRITICAL"] == 1
        assert data["severity_distribution"]["WARNING"] == 1
        assert data["severity_distribution"]["INFO"] == 1

    def test_top_authors(self, client):
        """Top authors leaderboard."""
        _create_policy(client, title="Auth A1", authored_by="Alice")
        _create_policy(client, title="Auth A2", authored_by="Alice")
        _create_policy(client, title="Auth A3", authored_by="Alice")
        _create_policy(client, title="Auth B1", authored_by="Bob")

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        authors = data["top_authors"]
        assert authors[0]["author"] == "Alice"
        assert authors[0]["count"] == 3
        assert authors[1]["author"] == "Bob"
        assert authors[1]["count"] == 1

    def test_multi_domain_count(self, client):
        """Multi-domain policies counted."""
        _create_policy(client, title="Multi", affected_domains=["finance", "hr", "legal"])
        _create_policy(client, title="Single", affected_domains=["finance"])

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        assert data["multi_domain_policies"] == 1

    def test_audit_events_counted(self, client):
        """Approval logs counted as audit events."""
        p = _create_policy(client, title="Audit Policy")
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        client.post(f"/api/v1/policies/authored/{p['id']}/approve", json={"approver_name": "Admin"})

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        assert data["total_audit_events"] >= 2  # submit + approve

    def test_avg_versions(self, client):
        """Average versions per policy."""
        p = _create_policy(client, title="Versioned")
        _approve(client, p["id"])
        # Revise bumps to v2
        client.post(f"/api/v1/policies/authored/{p['id']}/revise")

        resp = client.get("/api/v1/domain-governance/analytics")
        data = resp.json()
        assert data["avg_versions_per_policy"] >= 1.0


# ── Effectiveness ───────────────────────────────────────────────────────

class TestEffectiveness:
    def test_empty_effectiveness(self, client):
        """No policies or contracts → zero health score."""
        resp = client.get("/api/v1/domain-governance/effectiveness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["health_score"] == 0
        assert data["total_contracts"] == 0
        assert data["active_policies"] == 0

    def test_effectiveness_with_policies(self, client):
        """Approved policies contribute to coverage score."""
        p = _create_policy(client, title="Effective Policy", policy_category="security")
        _approve(client, p["id"])

        resp = client.get("/api/v1/domain-governance/effectiveness")
        data = resp.json()
        assert data["active_policies"] == 1
        assert data["policy_coverage_pct"] > 0
        assert len(data["policy_summaries"]) == 1
        assert data["policy_summaries"][0]["title"] == "Effective Policy"

    def test_effectiveness_with_contracts(self, client, db):
        """Contracts affect validation stats and health score."""
        import json as json_mod

        p = _create_policy(client, title="Contract Eff", policy_category="security")
        _approve(client, p["id"])

        # Create datasets first
        ds1 = Dataset(name="test_ds_pass", description="Pass DS", owner_name="O", owner_email="o@x.com",
                      source_type="postgres", source_connection="pg://localhost/db",
                      physical_location="public.t1", schema_definition=[], classification="internal")
        ds2 = Dataset(name="test_ds_fail", description="Fail DS", owner_name="O", owner_email="o@x.com",
                      source_type="postgres", source_connection="pg://localhost/db",
                      physical_location="public.t2", schema_definition=[], classification="internal")
        db.add_all([ds1, ds2])
        db.commit()
        db.refresh(ds1)
        db.refresh(ds2)

        # Create a passing contract
        c1 = Contract(
            dataset_id=ds1.id,
            version="1.0.0",
            machine_readable=json_mod.dumps({"dataset": {"name": "test"}, "schema": [], "governance": {}, "quality_rules": {}}),
            human_readable="Test contract",
            schema_hash="abc123",
            validation_status="passed",
            validation_results={"violations": []},
        )
        # Create a failing contract
        c2 = Contract(
            dataset_id=ds2.id,
            version="1.0.0",
            machine_readable=json_mod.dumps({"dataset": {"name": "test"}, "schema": [], "governance": {}, "quality_rules": {}}),
            human_readable="Test contract 2",
            schema_hash="def456",
            validation_status="failed",
            validation_results={"violations": [{"code": "SG001", "message": "Missing description"}]},
        )
        db.add_all([c1, c2])
        db.commit()

        resp = client.get("/api/v1/domain-governance/effectiveness")
        data = resp.json()
        assert data["total_contracts"] == 2
        assert data["contracts_validated"] == 2
        assert data["pass_rate_pct"] == 50.0
        assert data["total_violations_detected"] == 1
        assert data["health_score"] > 0

    def test_policy_summaries_include_metadata(self, client):
        """Policy summaries include version and domain info."""
        p = _create_policy(client, title="Summary P", affected_domains=["hr", "legal"], policy_category="privacy")
        _approve(client, p["id"])

        resp = client.get("/api/v1/domain-governance/effectiveness")
        data = resp.json()
        summary = data["policy_summaries"][0]
        assert summary["category"] == "privacy"
        assert summary["severity"] == "CRITICAL"
        assert "hr" in summary["domains"]
        assert "legal" in summary["domains"]
        assert summary["version"] >= 1

    def test_health_score_bounds(self, client, db):
        """Health score stays within 0-100."""
        import json as json_mod

        # Create many approved policies (all categories)
        for cat in ["data_quality", "security", "privacy", "compliance", "lineage", "sla"]:
            p = _create_policy(client, title=f"Full Coverage {cat}", policy_category=cat)
            _approve(client, p["id"])

        # Create all passing contracts
        for i in range(5):
            ds = Dataset(name=f"healthy_{i}", description=f"DS {i}", owner_name="O", owner_email="o@x.com",
                         source_type="postgres", source_connection="pg://localhost/db",
                         physical_location=f"public.t{i}", schema_definition=[], classification="internal")
            db.add(ds)
            db.commit()
            db.refresh(ds)
            c = Contract(
                dataset_id=ds.id,
                version="1.0.0",
                machine_readable=json_mod.dumps({"dataset": {"name": f"ds_{i}"}, "schema": [], "governance": {}, "quality_rules": {}}),
                human_readable=f"Contract {i}",
                schema_hash=f"hash_{i}",
                validation_status="passed",
                validation_results={"violations": []},
            )
            db.add(c)
        db.commit()

        resp = client.get("/api/v1/domain-governance/effectiveness")
        data = resp.json()
        assert 0 <= data["health_score"] <= 100
        assert data["policy_coverage_pct"] == 100
        assert data["pass_rate_pct"] == 100.0
        assert data["health_score"] == 100.0
