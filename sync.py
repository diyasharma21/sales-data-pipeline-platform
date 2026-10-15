"""CLI Runner for Remote Server & Database Daily Sync Jobs."""

import argparse
import logging
import sys
import time
from datetime import datetime

from src.connectors.remote_api import sync_from_remote_api
from src.connectors.remote_db import sync_from_remote_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sales_pipeline.sync")


def run_sync(source: str, days: int) -> int:
    """Execute a single sync run."""
    logger.info(f"Starting scheduled sync for source: '{source}' (days_back={days})...")
    if source == "db":
        return sync_from_remote_database(days_back=days)
    elif source == "api":
        return sync_from_remote_api(days_back=days)
    else:
        logger.error(f"Unknown source: '{source}'. Choose 'db' or 'api'.")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Daily Remote Server Synchronization Worker",
    )
    parser.add_argument(
        "--source",
        choices=["db", "api"],
        default="db",
        help="Data source type to fetch from: 'db' (remote database) or 'api' (REST endpoint)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of past days to extract for incremental sync (default: 1)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously in the background, executing daily at midnight",
    )
    parser.add_argument(
        "--interval-hours",
        type=int,
        default=24,
        help="Interval in hours when running in daemon mode (default: 24)",
    )

    args = parser.parse_args()

    if not args.daemon:
        # Run one-off sync (ideal for Windows Task Scheduler or cron)
        try:
            records = run_sync(args.source, args.days)
            logger.info(f"Sync complete. Successfully processed {records} records.")
            sys.exit(0)
        except Exception as exc:
            logger.error(f"Sync execution failed: {exc}")
            sys.exit(1)
    else:
        # Long-running daemon mode
        logger.info(f"Starting sync daemon. Interval: every {args.interval_hours} hour(s).")
        while True:
            try:
                run_sync(args.source, args.days)
            except Exception as exc:
                logger.error(f"Daemon sync cycle encountered an error: {exc}")

            sleep_seconds = args.interval_hours * 3600
            logger.info(f"Sleeping for {args.interval_hours} hour(s) until next cycle...")
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
