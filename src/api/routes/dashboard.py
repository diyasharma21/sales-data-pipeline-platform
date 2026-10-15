"""Dashboard overview KPI summary endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from sqlalchemy import text

from src.api.schemas import DashboardSummaryResponse, PipelineRunSummary
from src.config import get_database_url
from src.load import get_db_engine

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary() -> DashboardSummaryResponse:
    """Retrieve top-level executive KPIs and data quality pass rate."""
    engine = get_db_engine()

    try:
        with engine.connect() as conn:
            # Query 1: Sales aggregations
            sales_query = text("""
                SELECT 
                    COUNT(DISTINCT order_id) AS total_orders,
                    COALESCE(SUM(quantity), 0) AS total_units_sold,
                    COALESCE(ROUND(SUM(total_amount), 2), 0.0) AS total_revenue,
                    COALESCE(ROUND(AVG(total_amount), 2), 0.0) AS average_order_value
                FROM sales_records;
            """)
            sales_res = conn.execute(sales_query).mappings().first()
            total_orders = int(sales_res["total_orders"] or 0)
            total_units_sold = int(sales_res["total_units_sold"] or 0)
            total_revenue = float(sales_res["total_revenue"] or 0.0)
            aov = float(sales_res["average_order_value"] or 0.0)

            # Query 2: Quarantined records count
            reject_query = text("SELECT COUNT(*) AS total_rejected FROM rejected_sales_records;")
            total_rejected = int(conn.execute(reject_query).scalar() or 0)

            # Pass rate calculation: valid / (valid + rejected)
            total_processed = total_orders + total_rejected
            pass_rate = (
                round((total_orders / total_processed) * 100.0, 1)
                if total_processed > 0
                else 100.0
            )

            # Query 3: Latest pipeline run
            latest_run_query = text("""
                SELECT 
                    run_id, status, start_time, end_time, source_file,
                    records_loaded, records_rejected
                FROM pipeline_runs
                ORDER BY start_time DESC
                LIMIT 1;
            """)
            run_res = conn.execute(latest_run_query).mappings().first()
            last_run = None
            if run_res:
                s_time = run_res["start_time"]
                e_time = run_res["end_time"]
                
                # Normalize to datetime objects if returned as strings by SQLite
                if s_time and not isinstance(s_time, datetime):
                    s_time = datetime.fromisoformat(str(s_time))
                if e_time and not isinstance(e_time, datetime):
                    e_time = datetime.fromisoformat(str(e_time))

                duration = None
                if s_time and e_time:
                    duration = round((e_time - s_time).total_seconds(), 2)

                last_run = PipelineRunSummary(
                    run_id=run_res["run_id"],
                    status=run_res["status"],
                    start_time=s_time,
                    end_time=e_time,
                    duration_seconds=duration,
                    source_file=run_res["source_file"],
                    records_loaded=run_res["records_loaded"],
                    records_rejected=run_res["records_rejected"],
                )

            return DashboardSummaryResponse(
                total_revenue=total_revenue,
                total_orders=total_orders,
                total_units_sold=total_units_sold,
                average_order_value=aov,
                data_quality_pass_rate=pass_rate,
                total_records_processed=total_processed,
                total_quarantined_records=total_rejected,
                last_run=last_run,
            )
    finally:
        engine.dispose()
