"""Unit tests for the Data Transformation module (src/transform.py)."""

from datetime import date
import pandas as pd
import pytest

from src.transform import (
    calculate_total_amount,
    cast_numeric_columns,
    clean_column_names,
    parse_date_series,
    standardize_string_fields,
    transform_sales_data,
)


def test_clean_column_names() -> None:
    """Test column name normalization (lowercase, stripped, underscored)."""
    df = pd.DataFrame(columns=[" Order-ID ", "Unit Price", "PRODUCT_NAME"])
    cleaned = clean_column_names(df)
    assert list(cleaned.columns) == ["order_id", "unit_price", "product_name"]


def test_standardize_string_fields() -> None:
    """Test string whitespace trimming and title casing."""
    df = pd.DataFrame(
        [
            {
                "order_id": "  ORD-001 ",
                "customer_id": " CUST-1 ",
                "product": " Mouse ",
                "category": "electronics",
                "region": "north",
            }
        ]
    )
    cleaned = standardize_string_fields(df)
    row = cleaned.iloc[0]
    assert row["order_id"] == "ORD-001"
    assert row["customer_id"] == "CUST-1"
    assert row["product"] == "Mouse"
    assert row["category"] == "Electronics"
    assert row["region"] == "North"


def test_parse_date_series() -> None:
    """Test parsing diverse date string formats to datetime.date objects."""
    s = pd.Series(["2024-01-15", "16/01/2024", "2024-02-01"])
    parsed = parse_date_series(s)
    assert parsed.iloc[0] == date(2024, 1, 15)
    assert parsed.iloc[1] == date(2024, 1, 16)
    assert parsed.iloc[2] == date(2024, 2, 1)


def test_cast_numeric_columns() -> None:
    """Test casting numeric values, stripping currency characters and commas."""
    df = pd.DataFrame(
        [
            {"quantity": " 3 ", "unit_price": " $1,250.50 "},
            {"quantity": "10", "unit_price": "45.00"},
        ]
    )
    casted = cast_numeric_columns(df)
    assert casted.iloc[0]["quantity"] == 3
    assert casted.iloc[0]["unit_price"] == 1250.50
    assert casted.iloc[1]["quantity"] == 10
    assert casted.iloc[1]["unit_price"] == 45.00


def test_calculate_total_amount() -> None:
    """Test derived total_amount calculation (quantity * unit_price)."""
    df = pd.DataFrame(
        [
            {"quantity": 3, "unit_price": 25.50},
            {"quantity": 7, "unit_price": 12.99},
        ]
    )
    result = calculate_total_amount(df)
    assert result.iloc[0]["total_amount"] == 76.50
    assert result.iloc[1]["total_amount"] == 90.93  # 7 * 12.99 = 90.93


def test_transform_sales_data_complete() -> None:
    """Test the full transformation pipeline on an accepted DataFrame."""
    df_raw_accepted = pd.DataFrame(
        [
            {
                "order_id": " ORD-999 ",
                "order_date": "2024-03-15",
                "customer_id": " CUST-88 ",
                "product": " USB Hub ",
                "category": "accessories",
                "quantity": "4",
                "unit_price": "$29.99",
                "region": "west",
            }
        ]
    )

    df_transformed = transform_sales_data(df_raw_accepted)

    assert len(df_transformed) == 1
    row = df_transformed.iloc[0]
    assert row["order_id"] == "ORD-999"
    assert row["order_date"] == date(2024, 3, 15)
    assert row["category"] == "Accessories"
    assert row["region"] == "West"
    assert row["quantity"] == 4
    assert row["unit_price"] == 29.99
    assert row["total_amount"] == 119.96
    assert "created_at" in df_transformed.columns
    assert "updated_at" in df_transformed.columns


def test_transform_sales_data_empty() -> None:
    """Test transformation on an empty DataFrame."""
    empty_df = pd.DataFrame()
    res = transform_sales_data(empty_df)
    assert res.empty
    assert "order_id" in res.columns
    assert "total_amount" in res.columns
