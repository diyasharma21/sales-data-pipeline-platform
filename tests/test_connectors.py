"""Unit tests for Remote Server and API Connectors."""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from src.connectors.remote_api import sync_from_remote_api
from src.connectors.remote_db import sync_from_remote_database
from src.load import init_database


@pytest.fixture
def mock_remote_db(tmp_path):
    """Create a temporary SQLite database simulating a remote production server."""
    db_file = tmp_path / "remote_production.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url)

    with engine.begin() as conn:
        conn.execute(
            text("""
            CREATE TABLE sales_orders (
                order_id VARCHAR(50),
                order_date VARCHAR(50),
                customer_id VARCHAR(50),
                product VARCHAR(100),
                category VARCHAR(50),
                quantity INTEGER,
                unit_price NUMERIC(10,2),
                region VARCHAR(50)
            );
        """)
        )
        conn.execute(
            text("""
            INSERT INTO sales_orders VALUES
            ('ORD-REMOTE-01', '2026-10-15', 'CUST-REMOTE-1', 'Server Node', 'Electronics', 2, 500.0, 'North'),
            ('ORD-REMOTE-02', '2026-10-15', 'CUST-REMOTE-2', 'Bad Item', 'Electronics', -1, 100.0, 'South');
        """)
        )

    return db_url


def test_sync_from_remote_database(mock_remote_db):
    """Test extracting from a remote DB, validating, and updating the warehouse."""
    records_loaded = sync_from_remote_database(remote_db_url=mock_remote_db, days_back=30)
    assert records_loaded == 1  # 1 valid accepted, 1 quarantined


@patch("requests.get")
def test_sync_from_remote_api(mock_get):
    """Test extracting from a remote REST API with mocked response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "orders": [
            {
                "order_id": "ORD-API-01",
                "order_date": "2026-10-15",
                "customer_id": "CUST-API-1",
                "product": "API Cloud Router",
                "category": "Electronics",
                "quantity": 1,
                "unit_price": 249.99,
                "region": "West",
            }
        ]
    }
    mock_get.return_value = mock_resp

    records_loaded = sync_from_remote_api(
        api_url="https://api.testcompany.com/v1/orders",
        api_key="test_token",
        days_back=1,
    )
    assert records_loaded == 1
