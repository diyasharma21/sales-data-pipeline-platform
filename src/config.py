"""Configuration management and logging setup for the Sales Data Pipeline.

Handles environment variable loading, path resolution using pathlib,
database connection string formatting, and centralized logging.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Set

from dotenv import load_dotenv

# Base Directory: Project Root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Load .env file from project root if it exists
ENV_PATH: Path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Directory Paths
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = PROJECT_ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
PROCESSED_DATA_DIR: Path = PROJECT_ROOT / os.getenv("PROCESSED_DATA_DIR", "data/processed")
LOGS_DIR: Path = PROJECT_ROOT / os.getenv("LOGS_DIR", "logs")
SQL_DIR: Path = PROJECT_ROOT / "sql"

# Ensure runtime directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Required Sales Data Columns
REQUIRED_COLUMNS: list[str] = [
    "order_id",
    "order_date",
    "customer_id",
    "product",
    "category",
    "quantity",
    "unit_price",
    "region",
]

# Business Rule Validation Domains
VALID_CATEGORIES: Set[str] = {
    "Electronics",
    "Accessories",
    "Office Supplies",
    "Audio",
    "Furniture",
}

VALID_REGIONS: Set[str] = {
    "North",
    "South",
    "East",
    "West",
    "Central",
}

# Database Configuration
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DB_NAME: str = os.getenv("DB_NAME", "sales_dw")
DATABASE_URL_ENV: Optional[str] = os.getenv("DATABASE_URL")


def get_database_url() -> str:
    """Return the active SQLAlchemy database connection string.

    Priority:
    1. If DATABASE_URL environment variable is provided, use it directly.
    2. If DB_PASSWORD and DB_USER are provided, construct PostgreSQL connection URL.
    3. Fallback: Local SQLite database for environments without PostgreSQL.

    Returns:
        str: SQLAlchemy database URI.
    """
    if DATABASE_URL_ENV and DATABASE_URL_ENV.strip():
        return DATABASE_URL_ENV.strip()

    if DB_PASSWORD and DB_PASSWORD.strip():
        # Standard PostgreSQL URL using psycopg2
        return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Default fallback to SQLite database file inside data directory
    sqlite_path = DATA_DIR / "sales_dw.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: Optional[str] = None,
) -> logging.Logger:
    """Configure centralized application logging for console and file output.

    Args:
        log_file: Optional path to log file. Defaults to logs/pipeline.log.
        log_level: Optional logging level name (e.g. INFO, DEBUG).

    Returns:
        logging.Logger: Root pipeline logger.
    """
    level_name = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, level_name, logging.INFO)

    target_log_file = log_file or (LOGS_DIR / "pipeline.log")

    logger = logging.getLogger("sales_pipeline")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console Stream Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
