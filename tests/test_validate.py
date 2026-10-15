"""Unit tests for the Data Validation module (src/validate.py)."""

import pandas as pd
import pytest

from src.validate import (
    validate_category,
    validate_date_format,
    validate_quantity,
    validate_region,
    validate_required_fields,
    validate_sales_dataframe,
    validate_unit_price,
)


def test_validate_required_fields() -> None:
    """Test checking for missing and whitespace-only required fields."""
    row_valid = pd.Series({"order_id": "ORD-1", "product": "Mouse"})
    assert validate_required_fields(row_valid, required_cols=["order_id", "product"]) == []

    row_missing = pd.Series({"order_id": "ORD-1", "product": "   "})
    errors = validate_required_fields(row_missing, required_cols=["order_id", "product"])
    assert len(errors) == 1
    assert "MISSING_REQUIRED_FIELD: 'product'" in errors[0]


def test_validate_date_format() -> None:
    """Test calendar date parsing and format validation."""
    valid, err = validate_date_format("2024-01-15")
    assert valid is True
    assert err is None

    # Mixed format (e.g. DD/MM/YYYY)
    valid, err = validate_date_format("15/01/2024")
    assert valid is True

    # Impossible date
    valid, err = validate_date_format("2024-99-99")
    assert valid is False
    assert "unable to parse date" in err

    # Nonsense string
    valid, err = validate_date_format("not-a-date")
    assert valid is False
    assert "unable to parse date" in err


def test_validate_quantity() -> None:
    """Test integer and positive quantity validation."""
    valid, err = validate_quantity("5")
    assert valid is True

    # Zero quantity (rejected - orders must be > 0)
    valid, err = validate_quantity("0")
    assert valid is False
    assert "must be strictly greater than 0" in err

    # Negative quantity
    valid, err = validate_quantity("-3")
    assert valid is False
    assert "must be strictly greater than 0" in err

    # Non-integer / float quantity
    valid, err = validate_quantity("2.5")
    assert valid is False
    assert "not an integer" in err

    # String characters
    valid, err = validate_quantity("abc")
    assert valid is False
    assert "not a numeric value" in err


def test_validate_unit_price() -> None:
    """Test numeric and non-negative unit price validation."""
    valid, err = validate_unit_price("49.99")
    assert valid is True

    # Zero unit price (free promo item is non-negative)
    valid, err = validate_unit_price("0.00")
    assert valid is True

    # Negative unit price
    valid, err = validate_unit_price("-15.50")
    assert valid is False
    assert "cannot be negative" in err

    # Price with dollar sign
    valid, err = validate_unit_price("$29.95")
    assert valid is True

    # Non-numeric string
    valid, err = validate_unit_price("free")
    assert valid is False
    assert "not a valid number" in err


def test_validate_category_and_region() -> None:
    """Test category and region taxonomy checks."""
    assert validate_category("Electronics")[0] is True
    assert validate_category("furniture")[0] is True  # Case insensitive
    assert validate_category("UnknownCategory")[0] is False

    assert validate_region("North")[0] is True
    assert validate_region("central")[0] is True
    assert validate_region("Antarctica")[0] is False


def test_validate_sales_dataframe_full_accounting() -> None:
    """Test end-to-end DataFrame validation, duplicate detection, and accounting balance."""
    df_raw = pd.DataFrame(
        [
            {
                "order_id": "ORD-100",
                "order_date": "2024-01-10",
                "customer_id": "CUST-1",
                "product": "Mouse",
                "category": "Accessories",
                "quantity": "2",
                "unit_price": "25.00",
                "region": "North",
            },
            {
                # Duplicate order_id
                "order_id": "ORD-100",
                "order_date": "2024-01-11",
                "customer_id": "CUST-2",
                "product": "Keyboard",
                "category": "Electronics",
                "quantity": "1",
                "unit_price": "50.00",
                "region": "South",
            },
            {
                # Invalid quantity
                "order_id": "ORD-101",
                "order_date": "2024-01-12",
                "customer_id": "CUST-3",
                "product": "Webcam",
                "category": "Electronics",
                "quantity": "-2",
                "unit_price": "60.00",
                "region": "East",
            },
            {
                # Missing customer_id
                "order_id": "ORD-102",
                "order_date": "2024-01-13",
                "customer_id": "",
                "product": "Desk",
                "category": "Furniture",
                "quantity": "1",
                "unit_price": "300.00",
                "region": "West",
            },
        ]
    )

    report = validate_sales_dataframe(df_raw, source_file="test_batch.csv")

    assert report.total_records == 4
    assert report.accepted_count == 1
    assert report.rejected_count == 3
    assert report.duplicate_count == 1
    assert report.accepted_count + report.rejected_count == report.total_records

    # Check accepted record
    assert report.accepted_df.iloc[0]["order_id"] == "ORD-100"

    # Check rejection breakdown keys
    reasons = report.rejection_reasons_summary
    assert "DUPLICATE_ORDER_ID" in reasons
    assert "INVALID_QUANTITY" in reasons
    assert "MISSING_REQUIRED_FIELD" in reasons
