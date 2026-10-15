"""Data Quality and Quarantine endpoints."""

from datetime import datetime
import math
from typing import Dict, Optional
from fastapi import APIRouter, Query
from sqlalchemy import text

from src.api.schemas import (
    DataQualitySummaryResponse,
    PaginatedResponse,
    RejectedRecordItem,
)
from src.load import get_db_engine

router = APIRouter(prefix="/api/data-quality", tags=["Data Quality"])


@router.get("/summary", response_model=DataQualitySummaryResponse)
def get_data_quality_summary() -> DataQualitySummaryResponse:
    """Compute data quality statistics and rejection reason distributions."""
    engine = get_db_engine()

    try:
        with engine.connect() as conn:
            valid_count = conn.execute(
                text("SELECT COUNT(*) FROM sales_records;")
            ).scalar() or 0
            rejected_count = conn.execute(
                text("SELECT COUNT(*) FROM rejected_sales_records;")
            ).scalar() or 0

            # Scan rejection reasons
            reasons_rows = conn.execute(
                text("SELECT rejection_reason FROM rejected_sales_records;")
            ).fetchall()

            breakdown: Dict[str, int] = {
                "DUPLICATE_ORDER_ID": 0,
                "INVALID_QUANTITY": 0,
                "INVALID_UNIT_PRICE": 0,
                "INVALID_DATE": 0,
                "MISSING_REQUIRED_FIELD": 0,
                "INVALID_CATEGORY": 0,
                "INVALID_REGION": 0,
            }

            duplicate_count = 0

            for (reason_str,) in reasons_rows:
                if not reason_str:
                    continue
                parts = [p.strip() for p in str(reason_str).split(";")]
                for part in parts:
                    code = part.split(":")[0].strip()
                    if code:
                        breakdown[code] = breakdown.get(code, 0) + 1
                        if code == "DUPLICATE_ORDER_ID":
                            duplicate_count += 1

            total_inspected = valid_count + rejected_count
            pass_rate = (
                round((valid_count / total_inspected) * 100.0, 1)
                if total_inspected > 0
                else 100.0
            )

            return DataQualitySummaryResponse(
                total_inspected=total_inspected,
                valid_records=valid_count,
                rejected_records=rejected_count,
                duplicate_records=duplicate_count,
                pass_rate=pass_rate,
                reasons_breakdown=breakdown,
            )
    finally:
        engine.dispose()


@router.get("/rejected-records", response_model=PaginatedResponse[RejectedRecordItem])
def get_rejected_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    reason: Optional[str] = None,
) -> PaginatedResponse[RejectedRecordItem]:
    """Retrieve quarantined invalid records with rejection audit trails."""
    engine = get_db_engine()

    where_clauses = []
    params = {}

    if search and search.strip():
        where_clauses.append(
            "(LOWER(raw_order_id) LIKE :search OR LOWER(raw_product) LIKE :search OR LOWER(raw_customer_id) LIKE :search)"
        )
        params["search"] = f"%{search.strip().lower()}%"

    if reason and reason.strip():
        where_clauses.append("LOWER(rejection_reason) LIKE :reason")
        params["reason"] = f"%{reason.strip().lower()}%"

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    offset = (page - 1) * page_size

    count_sql = f"SELECT COUNT(*) FROM rejected_sales_records {where_sql};"
    data_sql = f"""
        SELECT 
            id, raw_order_id, raw_order_date, raw_customer_id, raw_product,
            raw_category, raw_quantity, raw_unit_price, raw_region,
            rejection_reason, source_file, pipeline_run_id, created_at
        FROM rejected_sales_records
        {where_sql}
        ORDER BY id DESC
        LIMIT :limit OFFSET :offset;
    """
    params["limit"] = page_size
    params["offset"] = offset

    try:
        with engine.connect() as conn:
            total_count = conn.execute(text(count_sql), params).scalar() or 0
            rows = conn.execute(text(data_sql), params).mappings().fetchall()
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

            items = [
                RejectedRecordItem(
                    id=row["id"],
                    raw_order_id=row["raw_order_id"],
                    raw_order_date=row["raw_order_date"],
                    raw_customer_id=row["raw_customer_id"],
                    raw_product=row["raw_product"],
                    raw_category=row["raw_category"],
                    raw_quantity=row["raw_quantity"],
                    raw_unit_price=row["raw_unit_price"],
                    raw_region=row["raw_region"],
                    rejection_reason=row["rejection_reason"],
                    source_file=row["source_file"],
                    pipeline_run_id=row["pipeline_run_id"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

            return PaginatedResponse[RejectedRecordItem](
                items=items,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
    finally:
        engine.dispose()
