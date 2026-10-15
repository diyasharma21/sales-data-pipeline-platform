"""Daily Remote Web / REST API Sync Connector.

Pulls daily sales transactions from an external REST API, validates them
through the data quality engine, and upserts them into the analytics warehouse.
"""

from datetime import datetime, timedelta
import logging
import os
from typing import Dict, List, Optional
import pandas as pd
import requests

from src.load import (
    get_db_engine,
    load_rejected_records,
    load_sales_records_idempotent,
    record_pipeline_run,
)
from src.transform import transform_sales_data
from src.validate import validate_sales_dataframe

logger = logging.getLogger("sales_pipeline.connector.remote_api")


def sync_from_remote_api(
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    days_back: int = 1,
) -> int:
    """Fetch daily orders from an external REST API endpoint.

    Args:
        api_url: Target REST API endpoint URL (e.g., https://api.store.com/v1/orders).
        api_key: Optional Bearer token or API key for authentication.
        days_back: Number of past days to query.

    Returns:
        int: Number of records successfully accepted and synced.
    """
    start_time = datetime.now()
    run_id = f"SYNC-API-{start_time.strftime('%Y%m%d%H%M%S')}"

    endpoint = api_url or os.getenv("REMOTE_API_URL", "https://api.example.com/v1/orders")
    token = api_key or os.getenv("REMOTE_API_KEY", "")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    target_engine = get_db_engine()

    logger.info(f"Connecting to remote API server: {endpoint} (Since: {since_date})")

    try:
        response = requests.get(
            endpoint,
            headers=headers,
            params={"since": since_date, "limit": 1000},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        orders: List[Dict] = data if isinstance(data, list) else data.get("orders", data.get("data", []))

        df_raw = pd.DataFrame(orders)
        total_extracted = len(df_raw)
        logger.info(f"Retrieved {total_extracted} records from remote API.")

        if df_raw.empty:
            logger.info("No records returned from remote API.")
            record_pipeline_run(
                engine=target_engine,
                run_id=run_id,
                start_time=start_time,
                end_time=datetime.now(),
                source_file=f"remote_api:{endpoint}",
                total_extracted=0,
                records_accepted=0,
                records_rejected=0,
                records_loaded=0,
                status="SUCCESS",
            )
            return 0

        # Validate against quality rules
        validation_report = validate_sales_dataframe(
            df_raw,
            source_file=f"remote_api:{endpoint}",
        )

        # Quarantine
        if not validation_report.rejected_df.empty:
            load_rejected_records(
                engine=target_engine,
                df_rejected=validation_report.rejected_df,
                pipeline_run_id=run_id,
            )

        # Transform & Upsert
        records_loaded = 0
        if not validation_report.accepted_df.empty:
            df_transformed = transform_sales_data(validation_report.accepted_df)
            records_loaded = load_sales_records_idempotent(target_engine, df_transformed)

        # Audit
        status = "SUCCESS" if validation_report.rejected_count == 0 else "PARTIAL_SUCCESS"
        record_pipeline_run(
            engine=target_engine,
            run_id=run_id,
            start_time=start_time,
            end_time=datetime.now(),
            source_file=f"remote_api:{endpoint}",
            total_extracted=total_extracted,
            records_accepted=validation_report.accepted_count,
            records_rejected=validation_report.rejected_count,
            records_loaded=records_loaded,
            status=status,
        )

        return records_loaded

    except Exception as exc:
        logger.error(f"Daily API sync failed: {str(exc)}", exc_info=True)
        record_pipeline_run(
            engine=target_engine,
            run_id=run_id,
            start_time=start_time,
            end_time=datetime.now(),
            source_file=f"remote_api:{endpoint}",
            total_extracted=0,
            records_accepted=0,
            records_rejected=0,
            records_loaded=0,
            status="FAILED",
            error_message=str(exc),
        )
        raise
