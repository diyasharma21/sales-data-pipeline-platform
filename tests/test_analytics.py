"""Unit and integration tests for the SQL Analytics module (src/analytics.py)."""

import pandas as pd
import pytest
from sqlalchemy import Engine

from src.analytics import (
    get_daily_revenue,
    get_executive_kpis,
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_revenue_by_region,
    get_top_selling_products,
    run_all_analytics,
)
from src.load import load_sales_records_idempotent


def test_empty_database_analytics(test_engine: Engine) -> None:
    """Test analytics functions when database contains zero records."""
    kpis = get_executive_kpis(test_engine)
    assert kpis["total_orders"] == 0
    assert kpis["total_units_sold"] == 0
    assert kpis["total_revenue"] == 0.0
    assert kpis["average_order_value"] == 0.0

    cat_df = get_revenue_by_category(test_engine)
    assert cat_df.empty

    reg_df = get_revenue_by_region(test_engine)
    assert reg_df.empty


def test_analytics_with_data(test_engine: Engine, sample_clean_df: pd.DataFrame) -> None:
    """Test analytics calculations against populated sample sales records.

    sample_clean_df contents:
    - ORD-101: qty 2, price 25.00, total 50.00, Accessories, North, 2024-01-15
    - ORD-102: qty 1, price 100.00, total 100.00, Electronics, West, 2024-01-16
    - ORD-103: qty 1, price 400.00, total 400.00, Furniture, Central, 2024-01-17
    Total Orders: 3
    Total Units: 4
    Total Revenue: 550.00
    Average Order Value: 550.00 / 3 = 183.33
    """
    load_sales_records_idempotent(test_engine, sample_clean_df)

    # 1. Executive KPIs
    kpis = get_executive_kpis(test_engine)
    assert kpis["total_orders"] == 3
    assert kpis["total_units_sold"] == 4
    assert float(kpis["total_revenue"]) == 550.00
    assert float(kpis["average_order_value"]) == 183.33

    # 2. Revenue by Product
    prod_df = get_revenue_by_product(test_engine)
    assert len(prod_df) == 3
    # Top product is Standing Desk with 400.00
    assert prod_df.iloc[0]["product"] == "Standing Desk"
    assert float(prod_df.iloc[0]["total_revenue"]) == 400.00

    # 3. Revenue by Category
    cat_df = get_revenue_by_category(test_engine)
    assert len(cat_df) == 3
    assert cat_df.iloc[0]["category"] == "Furniture"
    assert float(cat_df.iloc[0]["total_revenue"]) == 400.00

    # 4. Revenue by Region
    reg_df = get_revenue_by_region(test_engine)
    assert len(reg_df) == 3
    assert set(reg_df["region"]) == {"Central", "West", "North"}

    # 5. Top Selling Products with limit
    top_2_df = get_top_selling_products(test_engine, limit=2)
    assert len(top_2_df) == 2
    assert top_2_df.iloc[0]["product"] == "Standing Desk"
    assert top_2_df.iloc[1]["product"] == "Mechanical Keyboard"

    # 6. Daily Revenue
    daily_df = get_daily_revenue(test_engine)
    assert len(daily_df) == 3

    # 7. Composite Analytics Dictionary
    all_metrics = run_all_analytics(test_engine)
    assert "kpis" in all_metrics
    assert "by_category" in all_metrics
    assert "by_region" in all_metrics
    assert "top_products" in all_metrics
