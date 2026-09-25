"""
Integration tests for FastAPI REST Endpoints (NSO / RBI Integration)
"""

import pytest
from starlette.testclient import TestClient
from apix.api.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert "NSO (MoSPI)" in data["agency_consumers"]

def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["records"]["daily_index_records"] > 0

def test_latest_index_endpoint(client):
    resp = client.get("/api/v1/index/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert "two_tier_index" in data
    assert "laspeyres_index" in data
    assert "fisher_index" in data
    assert "jevons_index" in data
    assert "route_indices" in data
    assert "window_indices" in data
    assert data["two_tier_index"] > 80.0
    assert data["laspeyres_index"] > 80.0

def test_routes_metadata_endpoint(client):
    resp = client.get("/api/v1/routes")
    assert resp.status_code == 200
    routes = resp.json()
    assert len(routes) == 15
    weights_sum = sum(r["dgca_passenger_weight"] for r in routes)
    assert weights_sum == pytest.approx(1.0, abs=0.01)

def test_backtest_metrics_endpoint(client):
    resp = client.get("/api/v1/backtest")
    assert resp.status_code == 200
    data = resp.json()
    assert "pearson_correlation" in data
    assert data["pearson_correlation"] >= 0.88
    assert data["mape_pct"] < 5.0

def test_esankhyiki_endpoints(client):
    resp = client.get("/api/v1/esankhyiki/augmentation")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    assert "augmented_transport_cpi" in data[0]

    resp2 = client.get("/api/v1/esankhyiki/export")
    assert resp2.status_code == 200
    export_data = resp2.json()
    assert "metadata" in export_data
    assert export_data["metadata"]["custodian_division"] == "Price Statistics Division (PSD)"
