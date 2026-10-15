"""Data Transformation Module for Sales Data Pipeline.

Performs schema standardization, robust date parsing, numeric casting,
business metric derivation (total_amount), and auditing metadata enrichment.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger("sales_pipeline.transform")


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize DataFrame column headers.

    Converts to lowercase, removes leading/trailing spaces, and replaces
    spaces or dashes with underscores.
    """
    df_clean = df.copy()
    df_clean.columns = (
        df_clean.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df_clean


def standardize_string_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace and standardize casing for categorical text columns."""
    df_clean = df.copy()
    string_cols = ["order_id", "customer_id", "product", "category", "region"]
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
            # Normalize title casing for category and region
            if col in ["category", "region"]:
                df_clean[col] = df_clean[col].str.title()
    return df_clean


def parse_date_series(series: pd.Series) -> pd.Series:
    """Parse mixed date representations into normalized datetime.date objects.

    Supports ISO (YYYY-MM-DD), slash formats (DD/MM/YYYY, MM/DD/YYYY), etc.
    """
    parsed = pd.to_datetime(series, format="mixed", errors="coerce")
    return parsed.dt.date


def cast_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Cast quantity to integer and unit_price to 2-decimal rounded float."""
    df_clean = df.copy()

    # Clean potential currency symbols or commas
    if "unit_price" in df_clean.columns:
        df_clean["unit_price"] = (
            df_clean["unit_price"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
            .astype(float)
            .round(2)
        )

    if "quantity" in df_clean.columns:
        df_clean["quantity"] = (
            df_clean["quantity"]
            .astype(str)
            .str.strip()
            .astype(float)
            .astype(int)
        )

    return df_clean


def calculate_total_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived total_amount = quantity * unit_price rounded to 2 decimals."""
    df_clean = df.copy()
    df_clean["total_amount"] = (
        df_clean["quantity"] * df_clean["unit_price"]
    ).round(2)
    return df_clean


def transform_sales_data(df_accepted: pd.DataFrame) -> pd.DataFrame:
    """Apply the complete sequence of transformation rules to accepted sales records.

    Pipeline sequence:
    1. Standardize column names
    2. Clean string fields and standard title case for domains
    3. Parse order_date into date objects
    4. Cast quantity and unit_price to strict numeric types
    5. Derive total_amount
    6. Attach audit metadata timestamps

    Args:
        df_accepted: DataFrame containing validated, accepted records.

    Returns:
        pd.DataFrame: Transformed, analytics-ready DataFrame.
    """
    if df_accepted.empty:
        logger.info("Transform called with 0 accepted records. Returning empty transformed DataFrame.")
        return pd.DataFrame(
            columns=[
                "order_id",
                "order_date",
                "customer_id",
                "product",
                "category",
                "quantity",
                "unit_price",
                "total_amount",
                "region",
                "created_at",
                "updated_at",
            ]
        )

    logger.info(f"Transforming {len(df_accepted)} accepted sales records.")

    # 1. Clean columns
    df_transformed = clean_column_names(df_accepted)

    # 2. Clean strings
    df_transformed = standardize_string_fields(df_transformed)

    # 3. Parse dates
    df_transformed["order_date"] = parse_date_series(df_transformed["order_date"])

    # 4. Cast numerics
    df_transformed = cast_numeric_columns(df_transformed)

    # 5. Derive total_amount
    df_transformed = calculate_total_amount(df_transformed)

    # 6. Metadata timestamps
    now = datetime.now()
    df_transformed["created_at"] = now
    df_transformed["updated_at"] = now

    # Ensure clean column order matching target SQL table
    ordered_cols = [
        "order_id",
        "order_date",
        "customer_id",
        "product",
        "category",
        "quantity",
        "unit_price",
        "total_amount",
        "region",
        "created_at",
        "updated_at",
    ]
    df_transformed = df_transformed[ordered_cols]

    logger.info("Transformation completed successfully.")
    return df_transformed
