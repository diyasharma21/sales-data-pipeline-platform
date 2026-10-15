"""Sales Data Engineering Pipeline - Main CLI Orchestrator.

Orchestrates the complete end-to-end ETL lifecycle:
1. Load configuration and initialize logging
2. Extract raw sales data from CSV
3. Validate and clean records according to data-quality rules
4. Separate accepted and quarantined records
5. Load clean records into target database idempotently
6. Persist rejected records and pipeline execution audit logs
7. Produce processing summary metrics
8. Execute analytical SQL queries for business intelligence
"""

from __future__ import annotations

import argparse
from datetime import datetime
import logging
from pathlib import Path
import sys
import uuid

import pandas as pd

from src.analytics import print_analytics_summary
from src.config import (
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    get_database_url,
    setup_logging,
)
from src.extract import (
    EmptyFileError,
    ExtractionError,
    MissingFileError,
    SchemaValidationError,
    extract_sales_csv,
)
from src.load import (
    get_db_engine,
    init_database,
    load_rejected_records,
    load_sales_records_idempotent,
    record_pipeline_run,
)
from src.transform import transform_sales_data
from src.validate import ValidationReport, validate_sales_dataframe


def run_pipeline(
    input_file: Path,
    db_url: str | None = None,
    export_csv: bool = True,
) -> int:
    """Execute the automated sales data pipeline.

    Args:
        input_file: Path to the raw sales CSV file.
        db_url: Optional SQLAlchemy database connection string.
        export_csv: If True, exports clean & rejected datasets to data/processed/.

    Returns:
        int: 0 on success (including partial data quality quarantines), 1 on critical pipeline error.
    """
    logger = logging.getLogger("sales_pipeline")
    run_id = f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    start_time = datetime.now()

    logger.info("=" * 65)
    logger.info(f"STARTING SALES DATA PIPELINE | Run ID: {run_id}")
    logger.info(f"Source Input File: {input_file}")
    logger.info("=" * 65)

    engine = None
    total_extracted = 0
    records_accepted = 0
    records_rejected = 0
    records_loaded = 0

    try:
        # Step 1: Initialize Database Connection & Schema
        resolved_db_url = db_url or get_database_url()
        engine = get_db_engine(resolved_db_url)
        init_database(engine)

        # Step 2: Extraction
        df_raw, total_extracted = extract_sales_csv(input_file)

        # Step 3: Data Quality Validation & Accounting
        validation_report: ValidationReport = validate_sales_dataframe(
            df=df_raw,
            source_file=input_file.name,
        )
        records_accepted = validation_report.accepted_count
        records_rejected = validation_report.rejected_count
        validation_report.print_summary()

        # Step 4: Transformation of Accepted Records
        df_transformed = transform_sales_data(validation_report.accepted_df)

        # Step 5: Database Loading (Idempotent Upsert)
        records_loaded = load_sales_records_idempotent(engine, df_transformed)

        # Step 6: Persist Quarantined Records
        if records_rejected > 0:
            load_rejected_records(engine, validation_report.rejected_df, run_id)

        # Optional Step 6b: Export CSV artifacts for audit trail
        if export_csv:
            clean_export_path = PROCESSED_DATA_DIR / f"clean_{input_file.stem}_{run_id}.csv"
            rejected_export_path = PROCESSED_DATA_DIR / f"rejected_{input_file.stem}_{run_id}.csv"

            if not df_transformed.empty:
                df_transformed.to_csv(clean_export_path, index=False)
                logger.info(f"Exported clean records to: {clean_export_path}")
            if not validation_report.rejected_df.empty:
                validation_report.rejected_df.to_csv(rejected_export_path, index=False)
                logger.info(f"Exported quarantined records to: {rejected_export_path}")

        # Step 7: Execute & Display SQL Analytics
        print_analytics_summary(engine)

        # Step 8: Record Run Audit Metadata
        status = "SUCCESS" if records_rejected == 0 else "PARTIAL_SUCCESS"
        end_time = datetime.now()
        record_pipeline_run(
            engine=engine,
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            source_file=input_file.name,
            total_extracted=total_extracted,
            records_accepted=records_accepted,
            records_rejected=records_rejected,
            records_loaded=records_loaded,
            status=status,
            error_message=None,
        )

        logger.info("=" * 65)
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY ({status}) in {(end_time - start_time).total_seconds():.2f}s")
        logger.info(f"Processed: {total_extracted} | Loaded: {records_loaded} | Quarantined: {records_rejected}")
        logger.info("=" * 65)
        return 0

    except (MissingFileError, EmptyFileError, SchemaValidationError) as e:
        logger.error(f"PIPELINE CRITICAL EXTRACTION ERROR: {e}")
        _record_failed_run(engine, run_id, start_time, input_file.name, total_extracted, str(e))
        return 1
    except Exception as e:
        logger.exception(f"PIPELINE UNEXPECTED FATAL ERROR: {e}")
        _record_failed_run(engine, run_id, start_time, input_file.name, total_extracted, str(e))
        return 1
    finally:
        if engine is not None:
            engine.dispose()


def _record_failed_run(
    engine,
    run_id: str,
    start_time: datetime,
    source_file: str,
    total_extracted: int,
    error_msg: str,
) -> None:
    """Helper to record failed pipeline run if database engine is reachable."""
    if engine is not None:
        try:
            record_pipeline_run(
                engine=engine,
                run_id=run_id,
                start_time=start_time,
                end_time=datetime.now(),
                source_file=source_file,
                total_extracted=total_extracted,
                records_accepted=0,
                records_rejected=0,
                records_loaded=0,
                status="FAILED",
                error_message=error_msg,
            )
        except Exception as db_err:
            logging.getLogger("sales_pipeline").error(f"Could not persist failure status: {db_err}")


def main() -> None:
    """CLI Entry Point."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Automated Sales Data Engineering Pipeline (ETL & SQL Analytics)"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=str(RAW_DATA_DIR / "sales_sample.csv"),
        help="Path to the raw sales CSV input file (default: data/raw/sales_sample.csv)",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database connection URL override (e.g. postgresql+psycopg2://...)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Disable exporting clean/quarantined CSV files to data/processed/",
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    exit_code = run_pipeline(
        input_file=input_path,
        db_url=args.db_url,
        export_csv=not args.no_export,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
