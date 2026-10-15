"""Pytest shared fixtures and configuration for Sales Data Pipeline."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest
from sqlalchemy import Engine, create_engine

from src.load import init_database, metadata


@pytest.fixture
def tmp_csv_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory for test CSVs."""
    csv_dir = tmp_path / "raw_csvs"
    csv_dir.mkdir(parents=True, exist_ok=True)
    return csv_dir


@pytest.fixture
def valid_csv_file(tmp_csv_dir: Path) -> Path:
    """Fixture providing a valid 3-row sales CSV file."""
    file_path = tmp_csv_dir / "valid_sales.csv"
    content = (
        "order_id,order_date,customer_id,product,category,quantity,unit_price,region\n"
        "ORD-001,2024-01-10,CUST-01,Wireless Mouse,Accessories,2,25.00,North\n"
        "ORD-002,2024-01-11,CUST-02,Mechanical Keyboard,Electronics,1,100.00,South\n"
        "ORD-003,2024-01-12,CUST-03,Desk Mat,Office Supplies,3,15.00,East\n"
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def empty_csv_file(tmp_csv_dir: Path) -> Path:
    """Fixture providing a 0-byte CSV file."""
    file_path = tmp_csv_dir / "empty.csv"
    file_path.touch()
    return file_path


@pytest.fixture
def header_only_csv_file(tmp_csv_dir: Path) -> Path:
    """Fixture providing a CSV file with only headers and 0 rows."""
    file_path = tmp_csv_dir / "header_only.csv"
    file_path.write_text(
        "order_id,order_date,customer_id,product,category,quantity,unit_price,region\n",
        encoding="utf-8",
    )
    return file_path


@pytest.fixture
def missing_columns_csv_file(tmp_csv_dir: Path) -> Path:
    """Fixture providing a CSV file missing unit_price and region."""
    file_path = tmp_csv_dir / "missing_cols.csv"
    file_path.write_text(
        "order_id,order_date,customer_id,product,category,quantity\n"
        "ORD-001,2024-01-10,CUST-01,Wireless Mouse,Accessories,2\n",
        encoding="utf-8",
    )
    return file_path


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    """Fixture providing an isolated in-memory SQLite database initialized with the schema."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    init_database(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    """Fixture providing a sample transformed clean DataFrame ready for database insertion."""
    return pd.DataFrame(
        [
            {
                "order_id": "ORD-101",
                "order_date": date(2024, 1, 15),
                "customer_id": "CUST-01",
                "product": "Wireless Mouse",
                "category": "Accessories",
                "quantity": 2,
                "unit_price": 25.00,
                "total_amount": 50.00,
                "region": "North",
            },
            {
                "order_id": "ORD-102",
                "order_date": date(2024, 1, 16),
                "customer_id": "CUST-02",
                "product": "Mechanical Keyboard",
                "category": "Electronics",
                "quantity": 1,
                "unit_price": 100.00,
                "total_amount": 100.00,
                "region": "West",
            },
            {
                "order_id": "ORD-103",
                "order_date": date(2024, 1, 17),
                "customer_id": "CUST-03",
                "product": "Standing Desk",
                "category": "Furniture",
                "quantity": 1,
                "unit_price": 400.00,
                "total_amount": 400.00,
                "region": "Central",
            },
        ]
    )
