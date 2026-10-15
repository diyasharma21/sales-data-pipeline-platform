"""SQL Analytics Module for Sales Data Pipeline.

Executes analytical queries against the warehouse, computes key business metrics,
and renders formatted reports for executive review and pipeline summaries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import Engine, text

logger = logging.getLogger("sales_pipeline.analytics")


def get_executive_kpis(engine: Engine) -> Dict[str, Any]:
    """Calculate core high-level metrics: total revenue, total orders, units sold, and AOV.

    Args:
        engine: SQLAlchemy Engine.

    Returns:
        Dict[str, Any]: Executive KPI dictionary.
    """
    query = text("""
        SELECT 
            COUNT(DISTINCT order_id) AS total_orders,
            COALESCE(SUM(quantity), 0) AS total_units_sold,
            COALESCE(ROUND(SUM(total_amount), 2), 0.0) AS total_revenue,
            COALESCE(ROUND(AVG(total_amount), 2), 0.0) AS average_order_value
        FROM sales_records;
    """)

    with engine.connect() as conn:
        result = conn.execute(query).mappings().first()
        if not result:
            return {
                "total_orders": 0,
                "total_units_sold": 0,
                "total_revenue": 0.0,
                "average_order_value": 0.0,
            }
        return dict(result)


def get_revenue_by_product(engine: Engine, limit: Optional[int] = None) -> pd.DataFrame:
    """Calculate revenue, total volume, and order counts grouped by product."""
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
        SELECT 
            product,
            category,
            COUNT(DISTINCT order_id)    AS total_orders,
            SUM(quantity)               AS units_sold,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(AVG(unit_price), 2)   AS avg_unit_price
        FROM sales_records
        GROUP BY product, category
        ORDER BY total_revenue DESC
        {limit_clause};
    """
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


def get_revenue_by_category(engine: Engine) -> pd.DataFrame:
    """Calculate financial performance and volume grouped by product category."""
    query = """
        SELECT 
            category,
            COUNT(DISTINCT order_id)    AS order_count,
            SUM(quantity)               AS total_quantity,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM sales_records
        GROUP BY category
        ORDER BY total_revenue DESC;
    """
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


def get_revenue_by_region(engine: Engine) -> pd.DataFrame:
    """Calculate sales performance across geographic regions."""
    query = """
        SELECT 
            region,
            COUNT(DISTINCT order_id)    AS order_count,
            SUM(quantity)               AS total_units_sold,
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM sales_records
        GROUP BY region
        ORDER BY total_revenue DESC;
    """
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


def get_daily_revenue(engine: Engine) -> pd.DataFrame:
    """Compute day-by-day revenue trends."""
    query = """
        SELECT 
            order_date,
            COUNT(DISTINCT order_id)    AS orders_count,
            SUM(quantity)               AS units_sold,
            ROUND(SUM(total_amount), 2) AS daily_revenue
        FROM sales_records
        GROUP BY order_date
        ORDER BY order_date ASC;
    """
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


def get_monthly_revenue(engine: Engine) -> pd.DataFrame:
    """Compute month-by-month revenue trends."""
    query = """
        SELECT 
            SUBSTR(CAST(order_date AS VARCHAR), 1, 7) AS sales_month,
            COUNT(DISTINCT order_id)                  AS total_orders,
            SUM(quantity)                             AS total_units,
            ROUND(SUM(total_amount), 2)               AS monthly_revenue,
            ROUND(AVG(total_amount), 2)               AS avg_order_value
        FROM sales_records
        GROUP BY SUBSTR(CAST(order_date AS VARCHAR), 1, 7)
        ORDER BY sales_month ASC;
    """
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn)


def get_top_selling_products(engine: Engine, limit: int = 5) -> pd.DataFrame:
    """Return top N products ranked by total revenue generated."""
    return get_revenue_by_product(engine, limit=limit)


def run_all_analytics(engine: Engine) -> Dict[str, Any]:
    """Execute all analytical metrics and return a composite dictionary."""
    return {
        "kpis": get_executive_kpis(engine),
        "by_category": get_revenue_by_category(engine),
        "by_region": get_revenue_by_region(engine),
        "top_products": get_top_selling_products(engine, limit=5),
        "daily_trends": get_daily_revenue(engine),
        "monthly_trends": get_monthly_revenue(engine),
    }


def print_analytics_summary(engine: Engine) -> None:
    """Display human-readable analytical report in logs/terminal."""
    kpis = get_executive_kpis(engine)
    logger.info("================ EXECUTIVE SALES SUMMARY ================")
    logger.info(f"Total Unique Orders   : {kpis.get('total_orders', 0)}")
    logger.info(f"Total Units Sold      : {kpis.get('total_units_sold', 0)}")
    logger.info(f"Total Net Revenue     : ${float(kpis.get('total_revenue', 0)):,.2f}")
    logger.info(f"Average Order Value   : ${float(kpis.get('average_order_value', 0)):,.2f}")
    logger.info("---------------------------------------------------------")

    cat_df = get_revenue_by_category(engine)
    if not cat_df.empty:
        logger.info("Revenue by Category:")
        for _, row in cat_df.iterrows():
            logger.info(
                f"  - {row['category']:<16}: ${float(row['total_revenue']):>10,.2f} "
                f"({row['order_count']} orders, {row['total_quantity']} units)"
            )
        logger.info("---------------------------------------------------------")

    reg_df = get_revenue_by_region(engine)
    if not reg_df.empty:
        logger.info("Revenue by Region:")
        for _, row in reg_df.iterrows():
            logger.info(
                f"  - {row['region']:<16}: ${float(row['total_revenue']):>10,.2f} "
                f"(AOV: ${float(row['avg_order_value']):.2f})"
            )
        logger.info("---------------------------------------------------------")

    top_df = get_top_selling_products(engine, limit=5)
    if not top_df.empty:
        logger.info("Top 5 Best-Selling Products:")
        for rank, (_, row) in enumerate(top_df.iterrows(), start=1):
            logger.info(
                f"  {rank}. {row['product']:<28} | ${float(row['total_revenue']):>9,.2f} "
                f"({row['units_sold']} units)"
            )
    logger.info("=========================================================")
