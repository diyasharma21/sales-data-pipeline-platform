"""Unit and integration tests for the Database Loading module (src/load.py)."""

from datetime import datetime
import pandas as pd
import pytest
from sqlalchemy import Engine, inspect, select, text

from src.load import (
    init_database,
    load_rejected_records,
    load_sales_records_idempotent,
    pipeline_runs_table,
    record_pipeline_run,
    rejected_sales_table,
    sales_records_table,
)


def test_init_database_creates_all_tables(test_engine: Engine) -> None:
    """Verify that init_database creates all required schema tables."""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    assert "sales_records" in tables
    assert "rejected_sales_records" in tables
    assert "pipeline_runs" in tables


def test_load_sales_records_idempotent_insert_and_update(
    test_engine: Engine,
    sample_clean_df: pd.DataFrame,
) -> None:
    """Test idempotent loading: Initial insert followed by upsert on same order_id."""
    # First Load
    loaded_count = load_sales_records_idempotent(test_engine, sample_clean_df)
    assert loaded_count == 3

    with test_engine.connect() as conn:
        row_count = conn.execute(text("SELECT COUNT(*) FROM sales_records")).scalar()
        assert row_count == 3

        # Check initial total_amount for ORD-101
        res = conn.execute(
            text("SELECT total_amount FROM sales_records WHERE order_id = 'ORD-101'")
        ).scalar()
        assert float(res) == 50.00

    # Prepare updated version of the same records (e.g. quantity changed from 2 to 4)
    updated_df = sample_clean_df.copy()
    updated_df.loc[updated_df["order_id"] == "ORD-101", "quantity"] = 4
    updated_df.loc[updated_df["order_id"] == "ORD-101", "total_amount"] = 100.00

    # Second Load (Rerun with updated data)
    second_loaded_count = load_sales_records_idempotent(test_engine, updated_df)
    assert second_loaded_count == 3

    # Row count MUST remain 3 (no duplicate rows created)
    with test_engine.connect() as conn:
        total_rows = conn.execute(text("SELECT COUNT(*) FROM sales_records")).scalar()
        assert total_rows == 3

        # Value for ORD-101 should be updated to 100.00
        updated_amount = conn.execute(
            text("SELECT total_amount FROM sales_records WHERE order_id = 'ORD-101'")
        ).scalar()
        assert float(updated_amount) == 100.00


def test_load_rejected_records(test_engine: Engine) -> None:
    """Test persisting quarantined invalid records into rejected_sales_records."""
    df_rejected = pd.DataFrame(
        [
            {
                "raw_order_id": "ORD-ERR-1",
                "raw_order_date": "2024-99-99",
                "raw_customer_id": "CUST-9",
                "raw_product": "Mouse",
                "raw_category": "Accessories",
                "raw_quantity": "-1",
                "raw_unit_price": "20.00",
                "raw_region": "North",
                "rejection_reason": "INVALID_QUANTITY: must be > 0; INVALID_DATE: unable to parse",
                "source_file": "sales_sample.csv",
                "created_at": datetime.now().isoformat(),
            }
        ]
    )

    count = load_rejected_records(test_engine, df_rejected, pipeline_run_id="RUN-TEST-001")
    assert count == 1

    with test_engine.connect() as conn:
        rows = conn.execute(select(rejected_sales_table)).fetchall()
        assert len(rows) == 1
        assert rows[0].raw_order_id == "ORD-ERR-1"
        assert rows[0].pipeline_run_id == "RUN-TEST-001"
        assert "INVALID_QUANTITY" in rows[0].rejection_reason


def test_record_pipeline_run_audit(test_engine: Engine) -> None:
    """Test recording execution metrics into the pipeline_runs audit table."""
    start = datetime(2024, 1, 15, 10, 0, 0)
    end = datetime(2024, 1, 15, 10, 0, 5)

    record_pipeline_run(
        engine=test_engine,
        run_id="RUN-ABC-123",
        start_time=start,
        end_time=end,
        source_file="batch_01.csv",
        total_extracted=100,
        records_accepted=90,
        records_rejected=10,
        records_loaded=90,
        status="PARTIAL_SUCCESS",
        error_message=None,
    )

    with test_engine.connect() as conn:
        runs = conn.execute(select(pipeline_runs_table)).fetchall()
        assert len(runs) == 1
        run = runs[0]
        assert run.run_id == "RUN-ABC-123"
        assert run.status == "PARTIAL_SUCCESS"
        assert run.total_records_extracted == 100
        assert run.records_accepted == 90
        assert run.records_rejected == 10
