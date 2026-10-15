-- =============================================================================
-- Automated Sales Data Engineering Pipeline - Analytical SQL Queries
-- =============================================================================

-- Query 1: Executive KPI Overview
-- Calculates total revenue, total unique orders, total units sold, and overall Average Order Value (AOV).
-- Aggregation Logic: SUM(total_amount), COUNT(DISTINCT order_id), SUM(quantity), AVG(total_amount).
SELECT 
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity)            AS total_units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_order_value
FROM sales_records;


-- Query 2: Revenue and Volume by Product
-- Identifies top-performing products, units sold, and their contribution to overall sales.
SELECT 
    product,
    category,
    COUNT(DISTINCT order_id)    AS total_orders,
    SUM(quantity)               AS units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(unit_price), 2)   AS avg_unit_price
FROM sales_records
GROUP BY product, category
ORDER BY total_revenue DESC;


-- Query 3: Performance by Category
-- Measures category market share, revenue, and total volume.
SELECT 
    category,
    COUNT(DISTINCT order_id)    AS order_count,
    SUM(quantity)               AS total_quantity,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM sales_records
GROUP BY category
ORDER BY total_revenue DESC;


-- Query 4: Performance by Geographic Region
-- Evaluates sales distribution across territories.
SELECT 
    region,
    COUNT(DISTINCT order_id)    AS order_count,
    SUM(quantity)               AS total_units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM sales_records
GROUP BY region
ORDER BY total_revenue DESC;


-- Query 5: Daily Revenue Trends
-- Tracks day-over-day financial performance and transaction counts.
SELECT 
    order_date,
    COUNT(DISTINCT order_id)    AS orders_count,
    SUM(quantity)               AS units_sold,
    ROUND(SUM(total_amount), 2) AS daily_revenue
FROM sales_records
GROUP BY order_date
ORDER BY order_date ASC;


-- Query 6: Monthly Revenue Trends
-- Aggregates performance by month (using standard strftime/extract for date aggregation).
SELECT 
    SUBSTR(CAST(order_date AS VARCHAR), 1, 7) AS sales_month,
    COUNT(DISTINCT order_id)                  AS total_orders,
    SUM(quantity)                             AS total_units,
    ROUND(SUM(total_amount), 2)               AS monthly_revenue,
    ROUND(AVG(total_amount), 2)               AS avg_order_value
FROM sales_records
GROUP BY SUBSTR(CAST(order_date AS VARCHAR), 1, 7)
ORDER BY sales_month ASC;


-- Query 7: Top 5 Best-Selling Products by Revenue
SELECT 
    product,
    category,
    SUM(quantity)               AS units_sold,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM sales_records
GROUP BY product, category
ORDER BY total_revenue DESC
LIMIT 5;


-- Query 8: Average Order Value (AOV) by Region
SELECT 
    region,
    ROUND(AVG(total_amount), 2) AS average_order_value,
    ROUND(MIN(total_amount), 2) AS min_order_value,
    ROUND(MAX(total_amount), 2) AS max_order_value
FROM sales_records
GROUP BY region
ORDER BY average_order_value DESC;
