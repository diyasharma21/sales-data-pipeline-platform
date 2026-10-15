from datetime import datetime
import math
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from sqlalchemy import text

from src.api.schemas import (
    CategoryBreakdownItem,
    ManualOrderInput,
    ManualOrderResponse,
    PaginatedResponse,
    RegionBreakdownItem,
    RevenueTrendItem,
    SalesRecordItem,
    TopProductItem,
)
from src.load import get_db_engine, load_rejected_records, load_sales_records_idempotent
from src.transform import transform_sales_data
from src.validate import validate_sales_dataframe

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/revenue-trend", response_model=List[RevenueTrendItem])
def get_revenue_trend(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = Query("daily", pattern="^(daily|monthly)$"),
) -> List[RevenueTrendItem]:
    """Retrieve time-series revenue and order volume trends."""
    engine = get_db_engine()

    where_clauses = []
    params = {}

    if start_date:
        where_clauses.append("order_date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        where_clauses.append("order_date <= :end_date")
        params["end_date"] = end_date

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    if granularity == "monthly":
        date_expr = "SUBSTR(CAST(order_date AS VARCHAR), 1, 7)"
    else:
        date_expr = "CAST(order_date AS VARCHAR)"

    sql = f"""
        SELECT 
            {date_expr} AS date_label,
            COUNT(DISTINCT order_id) AS orders_count,
            COALESCE(SUM(quantity), 0) AS units_sold,
            COALESCE(ROUND(SUM(total_amount), 2), 0.0) AS revenue
        FROM sales_records
        {where_sql}
        GROUP BY {date_expr}
        ORDER BY date_label ASC;
    """

    try:
        with engine.connect() as conn:
            results = conn.execute(text(sql), params).mappings().fetchall()
            return [
                RevenueTrendItem(
                    date=row["date_label"],
                    revenue=float(row["revenue"]),
                    orders_count=int(row["orders_count"]),
                    units_sold=int(row["units_sold"]),
                )
                for row in results
            ]
    finally:
        engine.dispose()


@router.get("/category-breakdown", response_model=List[CategoryBreakdownItem])
def get_category_breakdown() -> List[CategoryBreakdownItem]:
    """Retrieve sales and order volume grouped by product category."""
    engine = get_db_engine()
    sql = """
        SELECT 
            category,
            COUNT(DISTINCT order_id) AS order_count,
            COALESCE(SUM(quantity), 0) AS total_quantity,
            COALESCE(ROUND(SUM(total_amount), 2), 0.0) AS total_revenue,
            COALESCE(ROUND(AVG(total_amount), 2), 0.0) AS avg_order_value
        FROM sales_records
        GROUP BY category
        ORDER BY total_revenue DESC;
    """
    try:
        with engine.connect() as conn:
            results = conn.execute(text(sql)).mappings().fetchall()
            return [
                CategoryBreakdownItem(
                    category=row["category"],
                    total_revenue=float(row["total_revenue"]),
                    order_count=int(row["order_count"]),
                    total_quantity=int(row["total_quantity"]),
                    avg_order_value=float(row["avg_order_value"]),
                )
                for row in results
            ]
    finally:
        engine.dispose()


@router.get("/region-breakdown", response_model=List[RegionBreakdownItem])
def get_region_breakdown() -> List[RegionBreakdownItem]:
    """Retrieve sales and order volume grouped by geographic region."""
    engine = get_db_engine()
    sql = """
        SELECT 
            region,
            COUNT(DISTINCT order_id) AS order_count,
            COALESCE(SUM(quantity), 0) AS total_units_sold,
            COALESCE(ROUND(SUM(total_amount), 2), 0.0) AS total_revenue,
            COALESCE(ROUND(AVG(total_amount), 2), 0.0) AS avg_order_value
        FROM sales_records
        GROUP BY region
        ORDER BY total_revenue DESC;
    """
    try:
        with engine.connect() as conn:
            results = conn.execute(text(sql)).mappings().fetchall()
            return [
                RegionBreakdownItem(
                    region=row["region"],
                    total_revenue=float(row["total_revenue"]),
                    order_count=int(row["order_count"]),
                    total_units_sold=int(row["total_units_sold"]),
                    avg_order_value=float(row["avg_order_value"]),
                )
                for row in results
            ]
    finally:
        engine.dispose()


@router.get("/top-products", response_model=List[TopProductItem])
def get_top_products(limit: int = Query(5, ge=1, le=50)) -> List[TopProductItem]:
    """Retrieve top N best-selling products by revenue."""
    engine = get_db_engine()
    sql = f"""
        SELECT 
            product,
            category,
            COUNT(DISTINCT order_id) AS total_orders,
            COALESCE(SUM(quantity), 0) AS units_sold,
            COALESCE(ROUND(SUM(total_amount), 2), 0.0) AS total_revenue,
            COALESCE(ROUND(AVG(unit_price), 2), 0.0) AS avg_unit_price
        FROM sales_records
        GROUP BY product, category
        ORDER BY total_revenue DESC
        LIMIT :limit;
    """
    try:
        with engine.connect() as conn:
            results = conn.execute(text(sql), {"limit": limit}).mappings().fetchall()
            return [
                TopProductItem(
                    product=row["product"],
                    category=row["category"],
                    total_revenue=float(row["total_revenue"]),
                    units_sold=int(row["units_sold"]),
                    total_orders=int(row["total_orders"]),
                    avg_unit_price=float(row["avg_unit_price"]),
                )
                for row in results
            ]
    finally:
        engine.dispose()


@router.get("/sales-records", response_model=PaginatedResponse[SalesRecordItem])
def get_sales_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    sort_by: str = Query("order_date"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PaginatedResponse[SalesRecordItem]:
    """Retrieve paginated, filtered, and searchable clean sales records."""
    engine = get_db_engine()

    allowed_sort_cols = {
        "order_id": "order_id",
        "order_date": "order_date",
        "customer_id": "customer_id",
        "product": "product",
        "category": "category",
        "quantity": "quantity",
        "unit_price": "unit_price",
        "total_amount": "total_amount",
        "region": "region",
    }
    col_name = allowed_sort_cols.get(sort_by, "order_date")
    direction = "DESC" if sort_order.lower() == "desc" else "ASC"

    where_clauses = []
    params = {}

    if search and search.strip():
        where_clauses.append(
            "(LOWER(order_id) LIKE :search OR LOWER(customer_id) LIKE :search OR LOWER(product) LIKE :search)"
        )
        params["search"] = f"%{search.strip().lower()}%"

    if category and category.strip():
        where_clauses.append("LOWER(category) = :category")
        params["category"] = category.strip().lower()

    if region and region.strip():
        where_clauses.append("LOWER(region) = :region")
        params["region"] = region.strip().lower()

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    offset = (page - 1) * page_size

    count_sql = f"SELECT COUNT(*) FROM sales_records {where_sql};"
    data_sql = f"""
        SELECT 
            order_id, CAST(order_date AS VARCHAR) AS order_date, customer_id,
            product, category, quantity, unit_price, total_amount, region, created_at
        FROM sales_records
        {where_sql}
        ORDER BY {col_name} {direction}
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
                SalesRecordItem(
                    order_id=row["order_id"],
                    order_date=str(row["order_date"]),
                    customer_id=row["customer_id"],
                    product=row["product"],
                    category=row["category"],
                    quantity=row["quantity"],
                    unit_price=float(row["unit_price"]),
                    total_amount=float(row["total_amount"]),
                    region=row["region"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

            return PaginatedResponse[SalesRecordItem](
                items=items,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )
    finally:
        engine.dispose()


@router.post("/orders", response_model=ManualOrderResponse)
def ingest_manual_order(payload: ManualOrderInput) -> ManualOrderResponse:
    """Directly ingest a single sales transaction without needing a CSV file.

    Validates against business rules and either upserts into sales_records or
    quarantines into rejected_sales_records.
    """
    df_raw = pd.DataFrame([
        {
            "order_id": payload.order_id,
            "order_date": payload.order_date,
            "customer_id": payload.customer_id,
            "product": payload.product,
            "category": payload.category,
            "quantity": payload.quantity,
            "unit_price": payload.unit_price,
            "region": payload.region,
        }
    ])

    validation_result = validate_sales_dataframe(df_raw, source_file="direct_api_ingest")
    engine = get_db_engine()

    try:
        if not validation_result.accepted_df.empty:
            df_transformed = transform_sales_data(validation_result.accepted_df)
            load_sales_records_idempotent(engine, df_transformed)
            return ManualOrderResponse(
                status="SUCCESS",
                message=f"Order '{payload.order_id}' validated and upserted into database.",
                order_id=payload.order_id,
                is_valid=True,
            )
        else:
            reason = str(validation_result.rejected_df.iloc[0]["rejection_reason"])
            run_id = f"DIRECT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            load_rejected_records(
                engine,
                validation_result.rejected_df,
                pipeline_run_id=run_id,
            )
            return ManualOrderResponse(
                status="REJECTED",
                message=f"Order '{payload.order_id}' quarantined: {reason}",
                order_id=payload.order_id,
                is_valid=False,
                rejection_reason=reason,
            )
    finally:
        engine.dispose()
