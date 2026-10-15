# Automated Sales Data Engineering Pipeline

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2%2B-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Pytest](https://img.shields.io/badge/Pytest-8.3%2B-0A9EDC.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Code Coverage](https://img.shields.io/badge/Coverage-85%25-brightgreen.svg)]()

> A production-grade, beginner-friendly Data Engineering project demonstrating core ETL principles, automated data quality validation, idempotent database loading into PostgreSQL, and SQL business intelligence analytics. Designed for college student portfolios, technical interviews, and resume demonstrations.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Business Problem](#2-business-problem)
3. [Architecture Diagram](#3-architecture-diagram)
4. [Technology Stack](#4-technology-stack)
5. [Project Directory Structure](#5-project-directory-structure)
6. [Data Quality & Quarantine Rules](#6-data-quality--quarantine-rules)
7. [Database Schema Design](#7-database-schema-design)
8. [ETL Workflow Lifecycle](#8-etl-workflow-lifecycle)
9. [Setup Instructions (Windows)](#9-setup-instructions-windows)
10. [Database Configuration & Options](#10-database-configuration--options)
11. [Pipeline Execution Guide](#11-pipeline-execution-guide)
12. [Automated Testing Suite](#12-automated-testing-suite)
13. [SQL Analytics & Insights](#13-sql-analytics--insights)
14. [Real Pipeline Execution Summary](#14-real-pipeline-execution-summary)
15. [Error Handling: Record vs. Pipeline Failures](#15-error-handling-record-vs-pipeline-failures)
16. [Known Limitations & Future Improvements](#16-known-limitations--future-improvements)

---

## 1. Project Overview

In real-world data engineering, upstream CSV sources from transactional order systems, e-commerce storefronts, and third-party partners are rarely clean. Common issues include duplicate order identifiers, malformed date strings, negative quantities or prices, and missing customer IDs.

This project implements a complete, reliable, and auditable **Extract, Transform, Load (ETL)** pipeline in Python and SQL:
- **Extracts** raw sales data from CSV files with file integrity and schema enforcement.
- **Validates** records using strict business rules and isolates bad data into a **quarantine table** with detailed rejection reasons instead of silently dropping records.
- **Transforms** clean records by parsing multi-format dates, standardizing headers, casting numeric types, and computing derived metrics (`total_amount`).
- **Loads** clean records idempotently into **PostgreSQL** using atomic upserts (`ON CONFLICT DO UPDATE`) to prevent double-counting.
- **Audits** execution lineage by logging pipeline metadata, durations, row counts, and status codes.
- **Analyzes** revenue, order volumes, product performance, and Average Order Value (AOV) via modular SQL queries.

---

## 2. Business Problem

An e-commerce retailer receives daily sales exports from regional stores. The business intelligence team faced three major hurdles:
1. **Silent Data Ingestion**: Corrupted records (e.g., negative quantities, missing customer IDs) entered downstream reporting, resulting in distorted revenue dashboards.
2. **Double Counting on Reruns**: If an ingestion script was triggered multiple times on the same day, orders were duplicated in the database.
3. **Lack of Operational Visibility**: When pipeline runs failed, there was no auditable trace of which records failed or why.

**The Solution**: An automated data engineering pipeline featuring a **quarantine-first architecture**, an **idempotent upsert loading strategy**, and **operational execution metadata** tracking.

---

## 3. Architecture Diagram

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion Layer"]
        CSV[("Raw Sales CSV Files\n(data/raw/)")]
        EXTRACT["src/extract.py\n- File Integrity Check\n- Schema Validation\n- Row Extraction"]
        CSV --> EXTRACT
    end

    subgraph Quality ["2. Data Quality & Quarantine Layer"]
        VALIDATE["src/validate.py\nValidation Engine\n- Non-null Checks\n- Positive Quantity (> 0)\n- Non-negative Price (>= 0)\n- Date Format Verification\n- Batch Deduplication\n- Domain Taxonomy (Category & Region)"]
        EXTRACT --> VALIDATE
        
        VALIDATE -->|Rejected Records| QUARANTINE_DF["Quarantined DataFrame\n+ Rejection Reasons\n+ Source File Lineage"]
        VALIDATE -->|Accepted Records| CLEAN_DF["Clean Valid Records"]
    end

    subgraph Transform ["3. Transformation Layer"]
        TRANSFORM["src/transform.py\n- Standardize Column Headers\n- Normalize String Casing\n- Multi-Format Date Parsing\n- Cast Numerics (Int / Float)\n- Derive total_amount = qty * price\n- Inject Audit Timestamps"]
        CLEAN_DF --> TRANSFORM
    end

    subgraph Storage ["4. Target Storage Layer (PostgreSQL)"]
        TRANSFORM -->|Idempotent Upsert| FACT_TABLE[("sales_records\n(Clean Fact Table)\nPK: order_id")]
        QUARANTINE_DF -->|Insert Audit Trail| REJECT_TABLE[("rejected_sales_records\n(Quarantine Table)\nPK: id")]
        META["src/load.py\nPipeline Audit Logger"] -->|Insert Run Metrics| RUNS_TABLE[("pipeline_runs\n(Operational Audit)\nPK: run_id")]
    end

    subgraph Analytics ["5. Business Analytics Layer"]
        SQL["sql/analytics_queries.sql\nsrc/analytics.py\n- Executive KPIs\n- Revenue by Category & Region\n- Top 5 Best-Selling Products\n- Daily/Monthly Trends\n- Average Order Value (AOV)"]
        FACT_TABLE --> SQL
        SQL --> REPORT["Terminal Summary\n& Audit CSV Exports"]
    end
```

---

## 4. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Language** | Python | 3.13+ | Core programming and pipeline orchestration |
| **Data Processing** | Pandas | 2.2+ | In-memory data manipulation, vectorized casting, cleaning |
| **Database** | PostgreSQL | 15+ | Target analytical data warehouse (ACID compliant) |
| **Database Driver** | Psycopg2-binary | 2.9+ | High-performance C-extension database adapter |
| **ORM / Core Engine** | SQLAlchemy | 2.0+ | Dialect-agnostic DDL management, transactions, connection pooling |
| **Testing** | Pytest & Pytest-cov | 8.3+ | Automated unit tests, fixture management, code coverage |
| **Configuration** | Python-dotenv | 1.1+ | Environment variable management (12-factor application) |
| **Logging** | Python Logging | Standard Lib | Structured dual logging (stdout + rotating file) |

---

## 5. Project Directory Structure

```
sales-data-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Automated GitHub Actions CI workflow (multi-OS & Python test matrix)
├── data/
│   ├── raw/
│   │   ├── sales_sample.csv          # 31 records: 20 valid, 11 intentional anomalies for testing
│   │   ├── sales_clean_batch.csv     # 20 records: 100% valid baseline dataset
│   │   └── DATA_DICTIONARY.md        # Detailed data dictionary and anomaly explanation guide
│   └── processed/                    # Exported clean and quarantined CSV audit artifacts
├── src/
│   ├── __init__.py                   # Package initialization
│   ├── config.py                     # Pathlib paths, .env loader, domain taxonomies, logger setup
│   ├── extract.py                    # CSV extraction, file validation, schema enforcement
│   ├── validate.py                   # Data quality rules, rejection categorizer, accounting report
│   ├── transform.py                  # Header cleaner, date parser, numeric caster, total_amount
│   ├── load.py                       # PostgreSQL/SQLAlchemy loader, upsert logic, transaction rollback
│   └── analytics.py                  # SQL query runner, executive KPI aggregation, report formatter
├── sql/
│   ├── schema.sql                    # Production DDL: sales_records, rejected_sales_records, pipeline_runs
│   └── analytics_queries.sql         # 8 production SQL analytics queries with business logic
├── tests/
│   ├── __init__.py                   # Test package initialization
│   ├── conftest.py                   # Pytest fixtures (in-memory engine, sample CSVs, DataFrames)
│   ├── test_extract.py               # Unit tests: missing files, empty files, missing columns
│   ├── test_validate.py              # Unit tests: quality rules, duplicate detection, accounting
│   ├── test_transform.py             # Unit tests: date parsing, numeric casting, total_amount
│   ├── test_load.py                  # Integration tests: table DDL, idempotency, quarantine, audit
│   ├── test_analytics.py             # Integration tests: SQL aggregations, AOV, KPI calculations
│   └── test_main.py                  # Integration tests: CLI execution and exit codes
├── logs/
│   ├── .gitkeep                      # Git directory tracker
│   └── pipeline.log                  # Structured application log output
├── docker-compose.yml                # 1-click local PostgreSQL 15 container setup
├── main.py                           # CLI entry point orchestrator
├── run.ps1                           # PowerShell helper task runner for Windows
├── run_analytics.py                  # Standalone CLI tool for BI queries and CSV exports
├── requirements.txt                  # Python dependencies
├── .env.example                      # Configuration and database credentials template
├── .gitignore                        # Git exclusion rules (secrets, bytecode, cache)
├── RESUME_GUIDE.md                   # Resume bullet points, interview talking points & demo script
└── README.md                         # Comprehensive portfolio documentation
```

---

## 6. Data Quality & Quarantine Rules

Every incoming row is subjected to strict verification before any data is written to the warehouse. Problematic records are **quarantined** into `rejected_sales_records` alongside their full raw payload and error codes:

| Validation Rule | Condition Enforced | Rejection Code | Action on Failure |
|---|---|---|---|
| **Required Headers** | Raw CSV must contain all 8 mandatory columns | `SchemaValidationError` | Fails extraction phase immediately |
| **Non-Null Fields** | `order_id`, `customer_id`, `product` cannot be empty or whitespace | `MISSING_REQUIRED_FIELD` | Quarantined to rejection table |
| **Date Parsing** | Date must be valid calendar date (e.g. `2024-01-15`) | `INVALID_DATE` | Quarantined (`2024-99-99` rejected) |
| **Positive Quantity** | Quantity must be integer strictly `> 0` | `INVALID_QUANTITY` | Quarantined (`0`, `-3`, `2.5` rejected) |
| **Non-Negative Price** | Unit price must be numeric `>= 0.00` | `INVALID_UNIT_PRICE` | Quarantined (`-85.00` rejected) |
| **Category Taxonomy** | Must be in `Electronics`, `Accessories`, `Office Supplies`, `Audio`, `Furniture` | `INVALID_CATEGORY` | Quarantined (`UnknownCategory` rejected) |
| **Region Domain** | Must be in `North`, `South`, `East`, `West`, `Central` | `INVALID_REGION` | Quarantined (`Antarctica` rejected) |
| **Batch Deduplication** | `order_id` must be unique within the ingested file | `DUPLICATE_ORDER_ID` | First occurrence validated; duplicates quarantined |

> **Accounting Invariant**:  
> `Total Input Records = Accepted Records + Quarantined Records`  
> The pipeline asserts this equality before loading. Not a single record is dropped silently.

---

## 7. Database Schema Design

The target database architecture separates clean analytical data, rejected anomalies, and pipeline run logs.

### 1. `sales_records` (Analytical Fact Table)
```sql
CREATE TABLE IF NOT EXISTS sales_records (
    order_id        VARCHAR(50) PRIMARY KEY,
    order_date      DATE NOT NULL,
    customer_id     VARCHAR(50) NOT NULL,
    product         VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_amount    NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
    region          VARCHAR(50) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_order_date ON sales_records (order_date);
CREATE INDEX idx_sales_product    ON sales_records (product);
CREATE INDEX idx_sales_category   ON sales_records (category);
CREATE INDEX idx_sales_region     ON sales_records (region);
```

### 2. `rejected_sales_records` (Quarantine Audit Table)
```sql
CREATE TABLE IF NOT EXISTS rejected_sales_records (
    id                  SERIAL PRIMARY KEY,
    raw_order_id        VARCHAR(100),
    raw_order_date      VARCHAR(100),
    raw_customer_id     VARCHAR(100),
    raw_product         VARCHAR(100),
    raw_category        VARCHAR(100),
    raw_quantity        VARCHAR(100),
    raw_unit_price      VARCHAR(100),
    raw_region          VARCHAR(100),
    rejection_reason    TEXT NOT NULL,
    source_file         VARCHAR(255) NOT NULL,
    pipeline_run_id     VARCHAR(50) NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rejected_run_id ON rejected_sales_records (pipeline_run_id);
```

### 3. `pipeline_runs` (Operational Run Metadata)
```sql
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id                  VARCHAR(50) PRIMARY KEY,
    start_time              TIMESTAMP NOT NULL,
    end_time                TIMESTAMP,
    source_file             VARCHAR(255) NOT NULL,
    total_records_extracted INTEGER NOT NULL DEFAULT 0,
    records_accepted        INTEGER NOT NULL DEFAULT 0,
    records_rejected        INTEGER NOT NULL DEFAULT 0,
    records_loaded          INTEGER NOT NULL DEFAULT 0,
    status                  VARCHAR(30) NOT NULL, -- 'SUCCESS', 'PARTIAL_SUCCESS', 'FAILED'
    error_message           TEXT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. ETL Workflow Lifecycle

1. **Configuration & Initialization**:
   `src/config.py` resolves absolute directories using `pathlib.Path`, loads `.env`, initializes dual console/file logging (`logs/pipeline.log`), and builds the database engine.
2. **Data Extraction (`src/extract.py`)**:
   Checks that the source CSV exists and is not 0 bytes. Verifies that all mandatory columns are present. Extracts raw values as strings to prevent premature casting errors.
3. **Validation & Segregation (`src/validate.py`)**:
   Iterates through records. Evaluates each record against business constraints. Separates into `accepted_df` and `rejected_df`. Formats clear, aggregated error breakdowns.
4. **Data Transformation (`src/transform.py`)**:
   Standardizes column names to snake_case. Trims whitespace and title-cases categories/regions. Parses dates to ISO date objects. Casts `quantity` to integer and `unit_price` to float. Derives `total_amount = quantity * unit_price` (rounded to 2 decimal places). Adds `created_at` and `updated_at`.
5. **Idempotent Loading (`src/load.py`)**:
   Executes within an atomic transaction. Uses PostgreSQL `ON CONFLICT (order_id) DO UPDATE` (or SQLite upsert) to guarantee that re-running the pipeline on overlapping data updates existing rows without creating duplicates.
6. **Quarantine Persistence**:
   Inserts quarantined rows with the current `pipeline_run_id`.
7. **Operational Logging**:
   Records start time, end time, row counts, and status (`SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`) into `pipeline_runs`.
8. **SQL Analytics (`src/analytics.py`)**:
   Executes analytical queries to compute executive KPIs, category distributions, regional sales, and top-selling products.

---

## 9. Setup Instructions (Windows)

### Prerequisites
- Python 3.10+ installed and added to your `PATH`.
- PostgreSQL 14+ installed locally (or via Docker), OR use the built-in local SQLite fallback.

### Step 1: Open PowerShell and Navigate to the Project Directory
```powershell
cd C:\Users\Diaa\.gemini\antigravity-ide\scratch\sales-data-pipeline
```

### Step 2: (Optional but Recommended) Create a Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## 10. Database Configuration & Options

### Option A: Using PostgreSQL (Production Target)
1. Install PostgreSQL on Windows (from [postgresql.org](https://www.postgresql.org/download/windows/)) or run via Docker:
   ```powershell
   docker run --name sales-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=sales_dw -p 5432:5432 -d postgres:15
   ```
2. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Update `.env` with your database credentials:
   ```env
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=sales_dw
   ```

### Option B: Local Fallback (Zero Setup / Instant Run)
If PostgreSQL is not running on your machine, **you don't have to install anything!**  
The pipeline automatically defaults to a local file-based database (`data/sales_dw.db`), allowing all pipeline components, SQL analytics, upserts, and tests to execute immediately out-of-the-box.

---

## 11. Pipeline Execution Guide

### 1. Run the Pipeline on the Sample Dataset (with Anomalies)
```powershell
python main.py
```
*Expected Result*: Extracts 31 rows, accepts 20, quarantines 11 invalid rows, loads 20 into the database, displays executive KPIs, exports processed CSVs to `data/processed/`, and logs execution to `logs/pipeline.log`.

### 2. Run the Pipeline on the 100% Clean Batch
```powershell
python main.py -i data/raw/sales_clean_batch.csv
```
*Expected Result*: Ingests 20 records with 0 rejections, logging a clean `SUCCESS` run.

### 3. Verify Idempotency (Safe Reruns)
Run the exact same command a second time:
```powershell
python main.py -i data/raw/sales_clean_batch.csv
```
*Expected Result*: Existing records are updated; total order count and revenue do NOT double-count.

### 4. Command-Line Options
```powershell
# Custom input file
python main.py -i path\to\your_file.csv

# Custom database connection string
python main.py --db-url postgresql+psycopg2://postgres:password@localhost:5432/sales_dw

# Run without saving CSV exports to data/processed/
python main.py --no-export
```

---

## 12. Automated Testing Suite

The project includes an automated test suite implemented with `pytest` covering all edge cases:
- Missing input files, 0-byte files, and header-only files
- Missing required schema columns
- Date parsing variations and invalid date formats
- Quantity validation (> 0, rejecting negative, zero, floats, strings)
- Price validation (>= 0, rejecting negative and non-numeric)
- In-batch duplicate `order_id` detection
- Derived calculation accuracy (`total_amount = quantity * unit_price`)
- Database DDL schema creation, idempotent upserting, and quarantine logging
- SQL analytical aggregation accuracy
- Pipeline CLI exit code compliance (0 on success, 1 on fatal error)

### Run All Tests
```powershell
python -m pytest tests/ -v
```

### Run Tests with Code Coverage Report
```powershell
python -m pytest --cov=src --cov=main tests/
```

### Verified Test Output
```
collected 26 items

tests/test_analytics.py::test_empty_database_analytics PASSED            [  3%]
tests/test_analytics.py::test_analytics_with_data PASSED                 [  7%]
tests/test_extract.py::test_extract_sales_csv_success PASSED             [ 11%]
tests/test_extract.py::test_extract_sales_csv_missing_file PASSED        [ 15%]
tests/test_extract.py::test_extract_sales_csv_empty_file PASSED          [ 19%]
tests/test_extract.py::test_extract_sales_csv_header_only_file PASSED    [ 23%]
tests/test_extract.py::test_extract_sales_csv_missing_required_columns PASSED [ 26%]
tests/test_load.py::test_init_database_creates_all_tables PASSED         [ 30%]
tests/test_load.py::test_load_sales_records_idempotent_insert_and_update PASSED [ 34%]
tests/test_load.py::test_load_rejected_records PASSED                    [ 38%]
tests/test_load.py::test_record_pipeline_run_audit PASSED                [ 42%]
tests/test_main.py::test_run_pipeline_success_end_to_end PASSED          [ 46%]
tests/test_main.py::test_run_pipeline_missing_file_failure PASSED        [ 50%]
tests/test_transform.py::test_clean_column_names PASSED                  [ 53%]
tests/test_transform.py::test_standardize_string_fields PASSED           [ 57%]
tests/test_transform.py::test_parse_date_series PASSED                   [ 61%]
tests/test_transform.py::test_cast_numeric_columns PASSED                [ 65%]
tests/test_transform.py::test_calculate_total_amount PASSED              [ 69%]
tests/test_transform.py::test_transform_sales_data_complete PASSED       [ 73%]
tests/test_transform.py::test_transform_sales_data_empty PASSED          [ 76%]
tests/test_validate.py::test_validate_required_fields PASSED             [ 80%]
tests/test_validate.py::test_validate_date_format PASSED                 [ 84%]
tests/test_validate.py::test_validate_quantity PASSED                    [ 88%]
tests/test_validate.py::test_validate_unit_price PASSED                  [ 92%]
tests/test_validate.py::test_validate_category_and_region PASSED         [ 96%]
tests/test_validate.py::test_validate_sales_dataframe_full_accounting PASSED [100%]

============================= 26 passed in 0.63s ==============================
Coverage: 85% Total (Analytics: 98%, Transform: 100%, Validate: 91%, Extract: 84%, Load: 80%)
```

---

## 13. SQL Analytics & Insights

The pipeline executes analytical queries located in [`sql/analytics_queries.sql`](sql/analytics_queries.sql).

### Query 1: Executive KPI Summary
```sql
SELECT 
    COUNT(DISTINCT order_id)    AS total_orders,
    SUM(quantity)               AS total_units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM sales_records;
```
*Output*:
```
Total Unique Orders : 20
Total Units Sold    : 53
Total Net Revenue   : $3,522.33
Average Order Value : $176.12
```

### Query 2: Performance by Product Category
```sql
SELECT 
    category,
    COUNT(DISTINCT order_id)    AS order_count,
    SUM(quantity)               AS total_quantity,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM sales_records
GROUP BY category
ORDER BY total_revenue DESC;
```
*Output*:
```
Category        Revenue       Orders   Units   AOV
------------------------------------------------------
Electronics   : $1,289.96     5        7       $257.99
Furniture     : $  776.98     3        4       $258.99
Audio         : $  676.89     4        6       $169.22
Accessories   : $  471.50     5       17       $ 94.30
Office Supplies: $  307.00     3       19       $102.33
```

### Query 3: Top 5 Best-Selling Products by Revenue
```sql
SELECT 
    product,
    category,
    SUM(quantity)               AS units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM sales_records
GROUP BY product, category
ORDER BY total_revenue DESC
LIMIT 5;
```
*Output*:
```
1. UltraWide Monitor            | $550.00 (1 units)
2. Standing Desk                | $450.00 (1 units)
3. 4K Gaming Monitor            | $399.99 (1 units)
4. Noise Cancelling Headphones  | $299.90 (2 units)
5. Ergonomic Chair              | $249.00 (1 units)
```

---

## 14. Real Pipeline Execution Summary

Below is an authentic terminal log from executing `main.py` against `sales_sample.csv`:

```
2026-10-15 11:45:55 | INFO     | sales_pipeline | =================================================================
2026-10-15 11:45:55 | INFO     | sales_pipeline | STARTING SALES DATA PIPELINE | Run ID: RUN-20261015114555-c7d3af
2026-10-15 11:45:55 | INFO     | sales_pipeline | Source Input File: data\raw\sales_sample.csv
2026-10-15 11:45:55 | INFO     | sales_pipeline | =================================================================
2026-10-15 11:45:55 | INFO     | sales_pipeline.load | Initializing database engine...
2026-10-15 11:45:55 | INFO     | sales_pipeline.load | Database schema initialized successfully.
2026-10-15 11:45:55 | INFO     | sales_pipeline.extract | Extraction complete for 'sales_sample.csv': 31 rows extracted.
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | ================ VALIDATION REPORT ================
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | Total Input Records  : 31
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | Accepted Records     : 20
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | Rejected Records     : 11
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | Duplicate Order IDs  : 1
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | Rejection Reason Breakdown:
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - DUPLICATE_ORDER_ID: 1
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - INVALID_CATEGORY: 1
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - INVALID_DATE: 2
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - INVALID_QUANTITY: 3
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - INVALID_REGION: 1
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - INVALID_UNIT_PRICE: 1
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate |   - MISSING_REQUIRED_FIELD: 2
2026-10-15 11:45:55 | INFO     | sales_pipeline.validate | ===================================================
2026-10-15 11:45:55 | INFO     | sales_pipeline.transform | Transforming 20 accepted sales records.
2026-10-15 11:45:55 | INFO     | sales_pipeline.load | Successfully committed 20 records into sales_records.
2026-10-15 11:45:55 | INFO     | sales_pipeline.load | Persisted 11 quarantined records into rejected_sales_records.
2026-10-15 11:45:55 | INFO     | sales_pipeline.load | Pipeline run 'RUN-20261015114555-c7d3af' logged with status 'PARTIAL_SUCCESS'.
2026-10-15 11:45:55 | INFO     | sales_pipeline | PIPELINE COMPLETED SUCCESSFULLY (PARTIAL_SUCCESS) in 0.12s
2026-10-15 11:45:55 | INFO     | sales_pipeline | Processed: 31 | Loaded: 20 | Quarantined: 11
```

---

## 15. Error Handling: Record vs. Pipeline Failures

A critical architectural distinction in professional data engineering is separating **record-level data quality issues** from **system-level pipeline failures**:

### 1. Record-Level Data Quality Failures (Handled Gracefully)
- **Examples**: A row containing a negative quantity, a typo in a region name, or a duplicate order identifier.
- **Handling**: These records are flagged, quarantined into `rejected_sales_records`, and exported for human inspection.
- **Pipeline Behavior**: The pipeline does **NOT** crash; valid records in the batch are safely loaded into `sales_records`, the run status is logged as `PARTIAL_SUCCESS`, and the program exits with code `0`.

### 2. System-Level Pipeline Failures (Fatal Exceptions)
- **Examples**: Missing input file, empty 0-byte file, CSV header missing required columns, database network disconnection, or corrupted transaction.
- **Handling**: Caught at the outer orchestrator layer, rolled back atomically using SQLAlchemy transaction context managers, logged to `pipeline_runs` with status `FAILED`, and detailed stack traces written to `logs/pipeline.log`.
- **Pipeline Behavior**: The program terminates with exit code `1` to signal failure to scheduling orchestrators (e.g. Cron, Airflow, Jenkins).

---

## 16. Known Limitations & Future Improvements

### Current Limitations
1. **Single-Node Execution**: Designed for batch files that fit comfortably in memory on a single machine (ideal for daily batch files < 1GB).
2. **Synchronous Execution**: Currently executed sequentially via CLI command rather than an asynchronous event listener.
3. **Local Database Fallback**: Automated tests and local default execution utilize SQLite when a PostgreSQL instance is not actively configured in `.env`.

### Planned Roadmap
- **Orchestration**: Wrap pipeline tasks into Apache Airflow DAGs or Prefect flows with cron schedules and Slack alert webhooks.
- **Data Modeling (dbt)**: Introduce a dbt (data build tool) modeling layer on top of PostgreSQL for Kimball dimensional modeling (Facts and Dimensions).
- **Automated Schema Evolution**: Integrate Alembic for database migration tracking.
- **Cloud Warehouse Target**: Add adapters for Snowflake, AWS Redshift, or Google BigQuery.
