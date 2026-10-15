"""Unit tests for the Data Extraction module (src/extract.py)."""

from pathlib import Path
import pytest

from src.extract import (
    EmptyFileError,
    ExtractionError,
    MissingFileError,
    SchemaValidationError,
    extract_sales_csv,
)


def test_extract_sales_csv_success(valid_csv_file: Path) -> None:
    """Test successful extraction of a valid raw sales CSV."""
    df, row_count = extract_sales_csv(valid_csv_file)

    assert row_count == 3
    assert len(df) == 3
    assert "order_id" in df.columns
    assert "unit_price" in df.columns
    assert df.iloc[0]["order_id"] == "ORD-001"
    assert df.iloc[0]["product"] == "Wireless Mouse"


def test_extract_sales_csv_missing_file(tmp_path: Path) -> None:
    """Test that requesting a non-existent file raises MissingFileError."""
    fake_path = tmp_path / "non_existent.csv"
    with pytest.raises(MissingFileError) as exc_info:
        extract_sales_csv(fake_path)

    assert "Source file not found" in str(exc_info.value)


def test_extract_sales_csv_empty_file(empty_csv_file: Path) -> None:
    """Test that a 0-byte file raises EmptyFileError."""
    with pytest.raises(EmptyFileError) as exc_info:
        extract_sales_csv(empty_csv_file)

    assert "completely empty" in str(exc_info.value)


def test_extract_sales_csv_header_only_file(header_only_csv_file: Path) -> None:
    """Test that a file with only headers and no data rows raises EmptyFileError."""
    with pytest.raises(EmptyFileError) as exc_info:
        extract_sales_csv(header_only_csv_file)

    assert "zero data rows" in str(exc_info.value)


def test_extract_sales_csv_missing_required_columns(missing_columns_csv_file: Path) -> None:
    """Test that missing required columns triggers SchemaValidationError."""
    with pytest.raises(SchemaValidationError) as exc_info:
        extract_sales_csv(missing_columns_csv_file)

    err_str = str(exc_info.value)
    assert "Missing required columns" in err_str
    assert "unit_price" in err_str
    assert "region" in err_str
