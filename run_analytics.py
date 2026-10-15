"""Standalone SQL Analytics and Business Intelligence CLI.

Allows users and interviewers to run analytical queries on-demand directly
against the warehouse without re-ingesting raw files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from src.analytics import (
    get_daily_revenue,
    get_executive_kpis,
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_revenue_by_region,
    get_top_selling_products,
    print_analytics_summary,
)
from src.config import get_database_url, setup_logging
from src.load import get_db_engine


def main() -> None:
    """CLI Entry Point for SQL Analytics."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Sales Data Engineering Pipeline - SQL Analytics & KPI Reporter"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Optional database URL override",
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default=None,
        help="Directory to save analytical query outputs as CSV files",
    )

    args = parser.parse_args()

    engine = get_db_engine(args.db_url or get_database_url())

    print("\n" + "=" * 65)
    print("       SALES DATA WAREHOUSE - BUSINESS INTELLIGENCE REPORT       ")
    print("=" * 65)

    print_analytics_summary(engine)

    if args.export_dir:
        out_dir = Path(args.export_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        get_revenue_by_category(engine).to_csv(out_dir / "category_revenue.csv", index=False)
        get_revenue_by_region(engine).to_csv(out_dir / "regional_revenue.csv", index=False)
        get_top_selling_products(engine, limit=10).to_csv(out_dir / "top_products.csv", index=False)
        get_daily_revenue(engine).to_csv(out_dir / "daily_trends.csv", index=False)
        get_monthly_revenue(engine).to_csv(out_dir / "monthly_trends.csv", index=False)

        print(f"\n[+] Analytics reports successfully exported to: {out_dir.resolve()}\n")

    engine.dispose()


if __name__ == "__main__":
    main()
