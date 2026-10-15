"""Database Loading and Persistence Layer for Sales Data Pipeline.

Manages SQLAlchemy engine creation, schema initialization, idempotent record loading,
quarantined failure persistence, and operational pipeline run auditing.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

import pandas as pd
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Engine,
    Float,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.config import get_database_url

logger = logging.getLogger("sales_pipeline.load")

# Shared SQLAlchemy Metadata instance
metadata = MetaData()

# Define Analytical Fact Table
sales_records_table = Table(
    "sales_records",
    metadata,
    Column("order_id", String(50), primary_key=True),
    Column("order_date", Date, nullable=False),
    Column("customer_id", String(50), nullable=False),
    Column("product", String(100), nullable=False),
    Column("category", String(50), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Numeric(10, 2), nullable=False),
    Column("total_amount", Numeric(12, 2), nullable=False),
    Column("region", String(50), nullable=False),
    Column("created_at", DateTime, default=datetime.now, nullable=False),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now, nullable=False),
    CheckConstraint("quantity > 0", name="chk_positive_quantity"),
    CheckConstraint("unit_price >= 0", name="chk_non_negative_price"),
    CheckConstraint("total_amount >= 0", name="chk_non_negative_total"),
)

# Define Rejected Quarantine Table
rejected_sales_table = Table(
    "rejected_sales_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("raw_order_id", String(100)),
    Column("raw_order_date", String(100)),
    Column("raw_customer_id", String(100)),
    Column("raw_product", String(100)),
    Column("raw_category", String(100)),
    Column("raw_quantity", String(100)),
    Column("raw_unit_price", String(100)),
    Column("raw_region", String(100)),
    Column("rejection_reason", Text, nullable=False),
    Column("source_file", String(255), nullable=False),
    Column("pipeline_run_id", String(50), nullable=False),
    Column("created_at", DateTime, default=datetime.now, nullable=False),
)

# Define Pipeline Audit Run Table
pipeline_runs_table = Table(
    "pipeline_runs",
    metadata,
    Column("run_id", String(50), primary_key=True),
    Column("start_time", DateTime, nullable=False),
    Column("end_time", DateTime),
    Column("source_file", String(255), nullable=False),
    Column("total_records_extracted", Integer, default=0, nullable=False),
    Column("records_accepted", Integer, default=0, nullable=False),
    Column("records_rejected", Integer, default=0, nullable=False),
    Column("records_loaded", Integer, default=0, nullable=False),
    Column("status", String(30), nullable=False),
    Column("error_message", Text),
    Column("created_at", DateTime, default=datetime.now, nullable=False),
)


def get_db_engine(db_url: Optional[str] = None) -> Engine:
    """Create and return a SQLAlchemy engine instance.

    Args:
        db_url: Optional database connection string. Defaults to get_database_url().

    Returns:
        Engine: SQLAlchemy Engine configured with connection pooling.
    """
    url = db_url or get_database_url()
    # Mask credentials for safe logging
    safe_url = url.split("@")[-1] if "@" in url else url
    logger.info(f"Initializing database engine: ...@{safe_url}")

    if "sqlite" in url:
        return create_engine(url, echo=False)
    return create_engine(url, pool_pre_ping=True, echo=False)


def init_database(engine: Engine) -> None:
    """Create all required tables and indexes if they do not already exist.

    Args:
        engine: SQLAlchemy Engine instance.
    """
    logger.info("Verifying and initializing database schema...")
    metadata.create_all(engine)
    logger.info("Database schema initialized successfully.")


def load_sales_records_idempotent(engine: Engine, df_sales: pd.DataFrame) -> int:
    """Load transformed sales records into sales_records table idempotently.

    Uses an Upsert (ON CONFLICT DO UPDATE) strategy based on order_id.
    Ensures that re-running the pipeline on duplicate or revised files updates existing
    records without creating duplicate entries or violating primary key constraints.

    Args:
        engine: SQLAlchemy Engine.
        df_sales: Transformed DataFrame.

    Returns:
        int: Total number of rows successfully inserted or updated.
    """
    if df_sales.empty:
        logger.info("No accepted sales records to load.")
        return 0

    records: List[Dict[str, Any]] = df_sales.to_dict(orient="records")
    dialect_name = engine.dialect.name
    rows_affected = 0

    logger.info(f"Loading {len(records)} sales records into database (Dialect: {dialect_name})...")

    with engine.begin() as conn:
        if dialect_name == "postgresql":
            for record in records:
                stmt = pg_insert(sales_records_table).values(record)
                update_dict = {
                    "order_date": stmt.excluded.order_date,
                    "customer_id": stmt.excluded.customer_id,
                    "product": stmt.excluded.product,
                    "category": stmt.excluded.category,
                    "quantity": stmt.excluded.quantity,
                    "unit_price": stmt.excluded.unit_price,
                    "total_amount": stmt.excluded.total_amount,
                    "region": stmt.excluded.region,
                    "updated_at": datetime.now(),
                }
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=["order_id"],
                    set_=update_dict,
                )
                conn.execute(upsert_stmt)
                rows_affected += 1

        elif dialect_name == "sqlite":
            for record in records:
                stmt = sqlite_insert(sales_records_table).values(record)
                update_dict = {
                    "order_date": stmt.excluded.order_date,
                    "customer_id": stmt.excluded.customer_id,
                    "product": stmt.excluded.product,
                    "category": stmt.excluded.category,
                    "quantity": stmt.excluded.quantity,
                    "unit_price": stmt.excluded.unit_price,
                    "total_amount": stmt.excluded.total_amount,
                    "region": stmt.excluded.region,
                    "updated_at": datetime.now(),
                }
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=["order_id"],
                    set_=update_dict,
                )
                conn.execute(upsert_stmt)
                rows_affected += 1
        else:
            # Generic fallback: Delete existing and insert within atomic transaction
            for record in records:
                conn.execute(
                    sales_records_table.delete().where(
                        sales_records_table.c.order_id == record["order_id"]
                    )
                )
                conn.execute(sales_records_table.insert().values(record))
                rows_affected += 1

    logger.info(f"Successfully committed {rows_affected} records into sales_records.")
    return rows_affected


def load_rejected_records(
    engine: Engine,
    df_rejected: pd.DataFrame,
    pipeline_run_id: str,
) -> int:
    """Persist quarantined rejected records with full audit attributes.

    Args:
        engine: SQLAlchemy Engine.
        df_rejected: DataFrame of invalid records with rejection reasons.
        pipeline_run_id: Unique UUID identifier of the current execution run.

    Returns:
        int: Number of rejected records persisted.
    """
    if df_rejected.empty:
        logger.info("No rejected records to store.")
        return 0

    df_copy = df_rejected.copy()
    df_copy["pipeline_run_id"] = pipeline_run_id

    # Format created_at to python datetime
    if "created_at" in df_copy.columns:
        df_copy["created_at"] = pd.to_datetime(df_copy["created_at"]).apply(
            lambda x: x.to_pydatetime() if hasattr(x, "to_pydatetime") else x
        )

    records = df_copy.to_dict(orient="records")

    logger.info(f"Persisting {len(records)} quarantined records into rejected_sales_records...")
    with engine.begin() as conn:
        conn.execute(rejected_sales_table.insert(), records)

    logger.info(f"Persisted {len(records)} quarantined records successfully.")
    return len(records)


def record_pipeline_run(
    engine: Engine,
    run_id: str,
    start_time: datetime,
    end_time: datetime,
    source_file: str,
    total_extracted: int,
    records_accepted: int,
    records_rejected: int,
    records_loaded: int,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """Log an execution summary entry into the pipeline_runs audit table.

    Args:
        engine: SQLAlchemy Engine.
        run_id: Unique UUID for the execution.
        start_time: Execution start timestamp.
        end_time: Execution finish timestamp.
        source_file: Filename of processed data.
        total_extracted: Count of extracted records.
        records_accepted: Count of validated records.
        records_rejected: Count of quarantined records.
        records_loaded: Count of rows saved in sales_records.
        status: Execution status ('SUCCESS', 'PARTIAL_SUCCESS', 'FAILED').
        error_message: Optional error message string if failed.
    """
    run_record = {
        "run_id": run_id,
        "start_time": start_time,
        "end_time": end_time,
        "source_file": source_file,
        "total_records_extracted": total_extracted,
        "records_accepted": records_accepted,
        "records_rejected": records_rejected,
        "records_loaded": records_loaded,
        "status": status,
        "error_message": error_message,
        "created_at": datetime.now(),
    }

    with engine.begin() as conn:
        conn.execute(pipeline_runs_table.insert().values(run_record))

    logger.info(f"Pipeline run '{run_id}' logged with status '{status}'.")
