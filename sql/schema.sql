-- =============================================================================
-- Automated Sales Data Engineering Pipeline - Target Database Schema
-- Dialect: PostgreSQL (Compatible with ANSI SQL & SQLite)
-- =============================================================================

-- Table 1: Clean Sales Records (Analytical Fact Table)
-- Enforces data integrity through primary keys, check constraints, and not-null rules.
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

-- Performance Indexes for Analytical Filtering & Aggregation
CREATE INDEX IF NOT EXISTS idx_sales_order_date ON sales_records (order_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_records (product);
CREATE INDEX IF NOT EXISTS idx_sales_category ON sales_records (category);
CREATE INDEX IF NOT EXISTS idx_sales_region ON sales_records (region);


-- Table 2: Rejected Sales Records (Quarantine & Audit Table)
-- Preserves verbatim raw data and exact failure reasons for debugging and data reconciliation.
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
    pipeline_run_id     VARCHAR(50),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rejected_run_id ON rejected_sales_records (pipeline_run_id);


-- Table 3: Pipeline Runs (Operational Metadata & Execution Audit)
-- Tracks pipeline executions, duration, data lineage, and row-level accounting.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id                  VARCHAR(50) PRIMARY KEY,
    start_time              TIMESTAMP NOT NULL,
    end_time                TIMESTAMP,
    source_file             VARCHAR(255) NOT NULL,
    total_records_extracted INTEGER NOT NULL DEFAULT 0,
    records_accepted        INTEGER NOT NULL DEFAULT 0,
    records_rejected        INTEGER NOT NULL DEFAULT 0,
    records_loaded          INTEGER NOT NULL DEFAULT 0,
    status                  VARCHAR(30) NOT NULL, -- 'SUCCESS', 'FAILED', 'PARTIAL_SUCCESS'
    error_message           TEXT,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
