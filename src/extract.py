"""Data Extraction Module for Sales Data Pipeline.

Reads raw sales CSV files, checks file accessibility, verifies required
header schemas, and logs extraction statistics.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd

from src.config import REQUIRED_COLUMNS, setup_logging

logger = logging.getLogger("sales_pipeline.extract")


class ExtractionError(Exception):
    """Base exception for all extraction-related failures."""
    pass


class MissingFileError(ExtractionError):
    """Raised when the specified input CSV file does not exist."""
    pass


class EmptyFileError(ExtractionError):
    """Raised when the CSV file is completely empty or has no rows."""
    pass


class SchemaValidationError(ExtractionError):
    """Raised when required columns are missing from the raw CSV header."""
    pass


def extract_sales_csv(
    file_path: Union[str, Path],
    required_columns: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, int]:
    """Read a raw sales CSV file, validate its structure, and return the DataFrame.

    Args:
        file_path: Path to the raw CSV file.
        required_columns: List of column names that must exist in the header.
            Defaults to REQUIRED_COLUMNS from config.

    Returns:
        Tuple[pd.DataFrame, int]: A tuple containing:
            - DataFrame with raw extracted records (as strings/raw objects)
            - Total number of rows extracted

    Raises:
        MissingFileError: If the file does not exist.
        EmptyFileError: If the file has 0 bytes or no data rows.
        SchemaValidationError: If required columns are missing.
        ExtractionError: If an unexpected parsing error occurs.
    """
    path = Path(file_path).resolve()
    cols_to_check = required_columns or REQUIRED_COLUMNS

    logger.info(f"Initiating extraction from raw source: {path}")

    # Check 1: File existence
    if not path.is_file():
        err_msg = f"Extraction failed: Source file not found at '{path}'"
        logger.error(err_msg)
        raise MissingFileError(err_msg)

    # Check 2: Empty file (zero size)
    if path.stat().st_size == 0:
        err_msg = f"Extraction failed: File '{path.name}' is completely empty (0 bytes)."
        logger.error(err_msg)
        raise EmptyFileError(err_msg)

    # Check 3: Read CSV data preserving raw strings to avoid premature type corruption
    try:
        df_raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError as e:
        err_msg = f"Extraction failed: File '{path.name}' contains no readable data columns."
        logger.error(err_msg)
        raise EmptyFileError(err_msg) from e
    except Exception as e:
        err_msg = f"Extraction failed: Could not parse CSV '{path.name}': {e}"
        logger.error(err_msg)
        raise ExtractionError(err_msg) from e

    # Check 4: Check if DataFrame is empty of rows
    if df_raw.empty:
        err_msg = f"Extraction failed: File '{path.name}' contains headers but zero data rows."
        logger.error(err_msg)
        raise EmptyFileError(err_msg)

    # Check 5: Schema validation (all required columns present)
    missing_cols = [col for col in cols_to_check if col not in df_raw.columns]
    if missing_cols:
        err_msg = (
            f"Schema validation error in '{path.name}': Missing required columns: {missing_cols}. "
            f"Found columns: {list(df_raw.columns)}"
        )
        logger.error(err_msg)
        raise SchemaValidationError(err_msg)

    total_rows = len(df_raw)
    logger.info(
        f"Extraction complete for '{path.name}': {total_rows} rows extracted successfully. "
        f"Columns present: {list(df_raw.columns)}"
    )

    return df_raw, total_rows
