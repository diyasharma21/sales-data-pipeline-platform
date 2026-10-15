"""Data Quality and Validation Engine for Sales Data Pipeline.

Performs field-level and record-level validation, checks domain constraints,
identifies duplicates, and categorizes rejection reasons into an audit report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from src.config import REQUIRED_COLUMNS, VALID_CATEGORIES, VALID_REGIONS

logger = logging.getLogger("sales_pipeline.validate")


@dataclass
class ValidationReport:
    """Detailed summary of the validation outcome for a dataset."""
    total_records: int
    accepted_count: int
    rejected_count: int
    duplicate_count: int
    rejection_reasons_summary: Dict[str, int] = field(default_factory=dict)
    accepted_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    rejected_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    def summary_dict(self) -> Dict[str, Any]:
        """Return a dictionary view of the summary metrics."""
        return {
            "total_records": self.total_records,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "duplicate_count": self.duplicate_count,
            "rejection_reasons": self.rejection_reasons_summary,
        }

    def print_summary(self) -> None:
        """Log and display formatted processing metrics."""
        logger.info("================ VALIDATION REPORT ================")
        logger.info(f"Total Input Records  : {self.total_records}")
        logger.info(f"Accepted Records     : {self.accepted_count}")
        logger.info(f"Rejected Records     : {self.rejected_count}")
        logger.info(f"Duplicate Order IDs  : {self.duplicate_count}")
        if self.rejection_reasons_summary:
            logger.info("Rejection Reason Breakdown:")
            for reason, count in sorted(self.rejection_reasons_summary.items()):
                logger.info(f"  - {reason}: {count}")
        logger.info("===================================================")


def validate_required_fields(row: pd.Series, required_cols: Optional[List[str]] = None) -> List[str]:
    """Check that all required fields are present and not empty or whitespace-only."""
    cols = required_cols or REQUIRED_COLUMNS
    errors = []
    for col in cols:
        val = row.get(col, "")
        if pd.isna(val) or str(val).strip() == "":
            errors.append(f"MISSING_REQUIRED_FIELD: '{col}' is blank or null")
    return errors


def validate_date_format(date_str: Any) -> Tuple[bool, Optional[str]]:
    """Verify if the date string can be reliably parsed as a valid calendar date."""
    if pd.isna(date_str) or str(date_str).strip() == "":
        return False, "INVALID_DATE: date string is empty"

    val_str = str(date_str).strip()
    try:
        parsed = pd.to_datetime(val_str, format="mixed", errors="raise")
        # Ensure year is reasonable (e.g., between 2000 and 2100)
        if parsed.year < 2000 or parsed.year > 2100:
            return False, f"INVALID_DATE: year {parsed.year} out of valid range (2000-2100)"
        return True, None
    except Exception:
        return False, f"INVALID_DATE: unable to parse date value '{val_str}'"


def validate_quantity(qty_val: Any) -> Tuple[bool, Optional[str]]:
    """Validate that quantity is a valid integer strictly greater than zero."""
    if pd.isna(qty_val) or str(qty_val).strip() == "":
        return False, "INVALID_QUANTITY: value is empty"

    val_str = str(qty_val).strip()
    try:
        # Check if integer
        qty_float = float(val_str)
        if not qty_float.is_integer():
            return False, f"INVALID_QUANTITY: '{val_str}' is not an integer"
        qty_int = int(qty_float)
        if qty_int <= 0:
            return False, f"INVALID_QUANTITY: '{qty_int}' must be strictly greater than 0"
        return True, None
    except ValueError:
        return False, f"INVALID_QUANTITY: '{val_str}' is not a numeric value"


def validate_unit_price(price_val: Any) -> Tuple[bool, Optional[str]]:
    """Validate that unit_price is a valid numeric value greater than or equal to 0.00."""
    if pd.isna(price_val) or str(price_val).strip() == "":
        return False, "INVALID_UNIT_PRICE: value is empty"

    val_str = str(price_val).strip().replace("$", "")
    try:
        price = float(val_str)
        if price < 0.0:
            return False, f"INVALID_UNIT_PRICE: '{price}' cannot be negative"
        return True, None
    except ValueError:
        return False, f"INVALID_UNIT_PRICE: '{val_str}' is not a valid number"


def validate_category(
    category_val: Any,
    allowed_categories: Optional[Set[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """Check if category belongs to the accepted business taxonomy."""
    allowed = allowed_categories or VALID_CATEGORIES
    val_str = str(category_val).strip()
    # Case-insensitive match check
    matches = [cat for cat in allowed if cat.lower() == val_str.lower()]
    if matches:
        return True, None
    return False, f"INVALID_CATEGORY: '{val_str}' not in allowed taxonomy: {sorted(list(allowed))}"


def validate_region(
    region_val: Any,
    allowed_regions: Optional[Set[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """Check if region belongs to the accepted operating regions."""
    allowed = allowed_regions or VALID_REGIONS
    val_str = str(region_val).strip()
    matches = [reg for reg in allowed if reg.lower() == val_str.lower()]
    if matches:
        return True, None
    return False, f"INVALID_REGION: '{val_str}' not in allowed regions: {sorted(list(allowed))}"


def validate_sales_dataframe(
    df: pd.DataFrame,
    source_file: str = "unknown",
) -> ValidationReport:
    """Validate each record in the raw DataFrame against all data quality rules.

    Accounts for every input row: separates into accepted records and quarantined
    rejected records with precise failure reasons.

    Args:
        df: Raw extracted DataFrame.
        source_file: Name of the input file for audit trail tracking.

    Returns:
        ValidationReport: Summary metrics, accepted DataFrame, and rejected DataFrame.
    """
    total_records = len(df)
    accepted_rows: List[Dict[str, Any]] = []
    rejected_rows: List[Dict[str, Any]] = []
    reasons_counter: Dict[str, int] = {}

    seen_order_ids: Set[str] = set()
    duplicate_counter = 0

    now_iso = datetime.now().isoformat()

    for idx, row in df.iterrows():
        row_errors: List[str] = []
        raw_order_id = str(row.get("order_id", "")).strip()

        # Rule 1: Check required non-null fields
        req_errors = validate_required_fields(row)
        row_errors.extend(req_errors)

        # Rule 2: Check Duplicate Order ID within the batch
        if raw_order_id:
            if raw_order_id in seen_order_ids:
                row_errors.append(f"DUPLICATE_ORDER_ID: '{raw_order_id}' already seen in this batch")
                duplicate_counter += 1
            else:
                seen_order_ids.add(raw_order_id)

        # Rule 3: Date Format Validation
        date_valid, date_err = validate_date_format(row.get("order_date"))
        if not date_valid and date_err:
            row_errors.append(date_err)

        # Rule 4: Quantity Validation
        qty_valid, qty_err = validate_quantity(row.get("quantity"))
        if not qty_valid and qty_err:
            row_errors.append(qty_err)

        # Rule 5: Unit Price Validation
        price_valid, price_err = validate_unit_price(row.get("unit_price"))
        if not price_valid and price_err:
            row_errors.append(price_err)

        # Rule 6: Category Validation (if category is present)
        if row.get("category"):
            cat_valid, cat_err = validate_category(row.get("category"))
            if not cat_valid and cat_err:
                row_errors.append(cat_err)

        # Rule 7: Region Validation (if region is present)
        if row.get("region"):
            reg_valid, reg_err = validate_region(row.get("region"))
            if not reg_valid and reg_err:
                row_errors.append(reg_err)

        # Decision: Accept or Reject
        if not row_errors:
            accepted_rows.append(row.to_dict())
        else:
            combined_reasons = "; ".join(row_errors)
            # Record individual reason codes for summary aggregation
            for err in row_errors:
                code = err.split(":")[0].strip()
                reasons_counter[code] = reasons_counter.get(code, 0) + 1

            rejected_record = {
                "raw_order_id": raw_order_id,
                "raw_order_date": str(row.get("order_date", "")),
                "raw_customer_id": str(row.get("customer_id", "")),
                "raw_product": str(row.get("product", "")),
                "raw_category": str(row.get("category", "")),
                "raw_quantity": str(row.get("quantity", "")),
                "raw_unit_price": str(row.get("unit_price", "")),
                "raw_region": str(row.get("region", "")),
                "rejection_reason": combined_reasons,
                "source_file": source_file,
                "created_at": now_iso,
            }
            rejected_rows.append(rejected_record)

    accepted_df = pd.DataFrame(accepted_rows)
    rejected_df = pd.DataFrame(rejected_rows)

    report = ValidationReport(
        total_records=total_records,
        accepted_count=len(accepted_rows),
        rejected_count=len(rejected_rows),
        duplicate_count=duplicate_counter,
        rejection_reasons_summary=reasons_counter,
        accepted_df=accepted_df,
        rejected_df=rejected_df,
    )

    # Sanity check: Ensure total accounting matches exactly
    assert (
        report.accepted_count + report.rejected_count == report.total_records
    ), f"Accounting discrepancy: {report.accepted_count} accepted + {report.rejected_count} rejected != {report.total_records} total"

    return report
