"""Daily Remote Database Sync Connector.

Extracts incremental sales records directly from a remote database server
(PostgreSQL, MySQL, SQL Server, etc.), validates them through the data quality
engine, and upserts them into the analytics warehouse.
"""

from datetime import datetime, timedelta
import logging
import os
from typing import Optional
import pandas as pd
from sqlalchemy import create_engine, text

from src.load import (
    get_db_engine,
    load_rejected_records,
    load_sales_records_idempotent,
    record_pipeline_run,
)
from src.transform import transform_sales_data
from src.validate import validate_sales_dataframe

logger = logging.getLogger("sales_pipeline.connector.remote_db")


def sync_from_remote_database(
    remote_db_url: Optional[str] = None,
    query: Optional[str] = None,
    days_back: int = 1,
) -> int:
    """Extract incremental sales data from a remote server database and sync to warehouse.

    Args:
        remote_db_url: SQLAlchemy connection string to the remote database.
                       Defaults to REMOTE_DB_URL environment variable.
        query: Custom SQL extract query. If None, default incremental query is used.
        days_back: Number of past days to extract for daily incremental sync.

    Returns:
        int: Number of records successfully accepted and synced.
    """
    start_time = datetime.now()
    run_id = f"SYNC-DB-{start_time.strftime('%Y%m%d%H%M%S')}"

    # 1. Resolve remote connection string
    source_url = remote_db_url or os.getenv(
        "REMOTE_DB_URL",
        "postgresql://username:password@remote-server.company.com:5432/production_db",
    )
    safe_source = source_url.split("@")[-1] if "@" in source_url else source_url
    logger.info(f"Connecting to remote database server: ...@{safe_source}")

    target_engine = get_db_engine()

    try:
        remote_engine = create_engine(source_url)
        watermark_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        # 2. Default extraction query with watermark filter
        extract_sql = query or """
            SELECT 
                order_id,
                order_date,
                customer_id,
                product,
                category,
                quantity,
                unit_price,
                region
            FROM sales_orders
            WHERE order_date >= :watermark;
        """

        logger.info(f"Executing incremental sync query (Watermark >= {watermark_date})...")
        with remote_engine.connect() as conn:
            df_raw = pd.read_sql(text(extract_sql), conn, params={"watermark": watermark_date})

        total_extracted = len(df_raw)
        logger.info(f"Extracted {total_extracted} records from remote server.")

        if df_raw.empty:
            logger.info("No new records to sync.")
            record_pipeline_run(
                engine=target_engine,
                run_id=run_id,
                start_time=start_time,
                end_time=datetime.now(),
                source_file=f"remote_db:{safe_source}",
                total_extracted=0,
                records_accepted=0,
                records_rejected=0,
                records_loaded=0,
                status="SUCCESS",
            )
            return 0

        # 3. Data Quality Validation
        validation_report = validate_sales_dataframe(
            df_raw,
            source_file=f"remote_db:{safe_source}",
        )

        # 4. Quarantine Rejected Records
        if not validation_report.rejected_df.empty:
            load_rejected_records(
                engine=target_engine,
                df_rejected=validation_report.rejected_df,
                pipeline_run_id=run_id,
            )

        # 5. Transform & Upsert Valid Records
        records_loaded = 0
        if not validation_report.accepted_df.empty:
            df_transformed = transform_sales_data(validation_report.accepted_df)
            records_loaded = load_sales_records_idempotent(target_engine, df_transformed)

        # 6. Audit Logging
        status = "SUCCESS" if validation_report.rejected_count == 0 else "PARTIAL_SUCCESS"
        record_pipeline_run(
            engine=target_engine,
            run_id=run_id,
            start_time=start_time,
            end_time=datetime.now(),
            source_file=f"remote_db:{safe_source}",
            total_extracted=total_extracted,
            records_accepted=validation_report.accepted_count,
            records_rejected=validation_report.rejected_count,
            records_loaded=records_loaded,
            status=status,
        )

        logger.info(
            f"Daily sync completed: {records_loaded} loaded, "
            f"{validation_report.rejected_count} quarantined."
        )
        return records_loaded

    except Exception as exc:
        logger.error(f"Daily remote sync failed: {str(exc)}", exc_info=True)
        record_pipeline_run(
            engine=target_engine,
            run_id=run_id,
            start_time=start_time,
            end_time=datetime.now(),
            source_file=f"remote_db:{safe_source}",
            total_extracted=0,
            records_accepted=0,
            records_rejected=0,
            records_loaded=0,
            status="FAILED",
            error_message=str(exc),
        )
        raise
