"""Automated integration tests for FastAPI backend endpoints (tests/test_api.py)."""

from fastapi.testclient import TestClient
import pytest

from src.api.app import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


def test_api_health_endpoint(client: TestClient) -> None:
    """Test /api/health returns healthy status and DB connection."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "database_dialect" in data


def test_api_dashboard_summary(client: TestClient) -> None:
    """Test /api/dashboard/summary returns executive metrics and pass rate."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "total_orders" in data
    assert "total_units_sold" in data
    assert "average_order_value" in data
    assert "data_quality_pass_rate" in data
    assert isinstance(data["data_quality_pass_rate"], (int, float))


def test_api_analytics_endpoints(client: TestClient) -> None:
    """Test analytics endpoints: trends, category, region, top products, sales records."""
    # Revenue trend
    res_trend = client.get("/api/analytics/revenue-trend?granularity=daily")
    assert res_trend.status_code == 200
    assert isinstance(res_trend.json(), list)

    # Category breakdown
    res_cat = client.get("/api/analytics/category-breakdown")
    assert res_cat.status_code == 200
    assert isinstance(res_cat.json(), list)

    # Region breakdown
    res_reg = client.get("/api/analytics/region-breakdown")
    assert res_reg.status_code == 200
    assert isinstance(res_reg.json(), list)

    # Top products with limit
    res_top = client.get("/api/analytics/top-products?limit=3")
    assert res_top.status_code == 200
    data_top = res_top.json()
    assert len(data_top) <= 3

    # Paginated sales records
    res_records = client.get("/api/analytics/sales-records?page=1&page_size=5&sort_by=order_date&sort_order=desc")
    assert res_records.status_code == 200
    data_records = res_records.json()
    assert "items" in data_records
    assert "total" in data_records
    assert "total_pages" in data_records


def test_api_pipeline_endpoints(client: TestClient) -> None:
    """Test pipeline summary, runs, and trigger validation."""
    res_summary = client.get("/api/pipeline/summary")
    assert res_summary.status_code == 200
    assert "total_runs" in res_summary.json()

    res_runs = client.get("/api/pipeline/runs?page=1&page_size=5")
    assert res_runs.status_code == 200
    assert "items" in res_runs.json()

    res_files = client.get("/api/pipeline/files")
    assert res_files.status_code == 200
    assert "files" in res_files.json()

    # Non-existent file trigger should return 404
    res_trigger_fail = client.post("/api/pipeline/run", json={"filename": "fake_file.csv"})
    assert res_trigger_fail.status_code == 404


def test_api_data_quality_endpoints(client: TestClient) -> None:
    """Test data quality summary and quarantined records pagination."""
    res_summary = client.get("/api/data-quality/summary")
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert "pass_rate" in data
    assert "reasons_breakdown" in data

    res_rejected = client.get("/api/data-quality/rejected-records?page=1&page_size=5")
    assert res_rejected.status_code == 200
    assert "items" in res_rejected.json()


def test_api_database_explorer_endpoints(client: TestClient) -> None:
    """Test database explorer table list, record retrieval, and security allowlist."""
    res_tables = client.get("/api/database/tables")
    assert res_tables.status_code == 200
    tables_data = res_tables.json()
    table_names = [t["table_name"] for t in tables_data]
    assert "sales_records" in table_names
    assert "rejected_sales_records" in table_names
    assert "pipeline_runs" in table_names

    # Allowed table records
    res_sales = client.get("/api/database/tables/sales_records/records?page=1&page_size=5")
    assert res_sales.status_code == 200
    assert "rows" in res_sales.json()

    # Forbidden table access should return 403
    res_forbidden = client.get("/api/database/tables/unauthorized_table/records")
    assert res_forbidden.status_code == 403

    # Invalid column sort should return 400
    res_bad_sort = client.get("/api/database/tables/sales_records/records?sort_by=malicious_col")
    assert res_bad_sort.status_code == 400
