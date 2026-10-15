# Sales Data Dictionary & Sample Anomaly Guide

## 1. Schema Definition

| Field Name    | Data Type (Raw) | Target SQL Type  | Description                                                 | Constraints / Rules                                     |
|---------------|-----------------|------------------|-------------------------------------------------------------|---------------------------------------------------------|
| `order_id`    | String          | `VARCHAR(50)`    | Unique identifier for each sales transaction                | Must not be null; must be unique across the dataset.    |
| `order_date`  | String          | `DATE`           | Date the order was placed                                   | ISO-8601 compatible date (`YYYY-MM-DD` or parsable).    |
| `customer_id` | String          | `VARCHAR(50)`    | Unique identifier for the customer                          | Must not be null or blank.                             |
| `product`     | String          | `VARCHAR(100)`   | Name of the item sold                                       | Must not be null or blank.                             |
| `category`    | String          | `VARCHAR(50)`    | Product classification                                      | Must be one of: Electronics, Accessories, Office Supplies, Audio, Furniture. |
| `quantity`    | String / Int    | `INTEGER`        | Units sold in this order                                    | Must be a positive integer (`quantity > 0`).           |
| `unit_price`  | String / Float  | `NUMERIC(10,2)`  | Price per unit                                              | Must be a non-negative number (`unit_price >= 0.00`).   |
| `region`      | String          | `VARCHAR(50)`    | Geographic sales region                                     | Must be one of: North, South, East, West, Central.      |
| `total_amount`| N/A (Derived)   | `NUMERIC(12,2)`  | Calculated total revenue (`quantity * unit_price`)          | Automatically computed during transformation.           |

---

## 2. Intentionally Invalid Records in `sales_sample.csv`

The synthetic dataset `data/raw/sales_sample.csv` contains 31 total raw records:
- **20 Valid Records** (Orders `ORD-2024-1001` through `ORD-2024-1020`)
- **11 Intentionally Invalid Records** crafted to validate pipeline error-handling and quarantine mechanisms:

| Order ID        | Row # | Problem Detected                               | Expected Pipeline Action                                      | Rejection Code              |
|-----------------|-------|------------------------------------------------|---------------------------------------------------------------|-----------------------------|
| `ORD-2024-1002` | 21    | Duplicate order identifier in the same batch   | Reject duplicate occurrence; keep first instance               | `DUPLICATE_ORDER_ID`        |
| `ORD-2024-1021` | 22    | Negative quantity (`-3`)                       | Reject record; quantity must be strictly > 0                  | `INVALID_QUANTITY`          |
| `ORD-2024-1022` | 23    | Zero quantity (`0`)                            | Reject record; quantity must be strictly > 0                  | `INVALID_QUANTITY`          |
| `ORD-2024-1023` | 24    | Negative unit price (`-85.00`)                 | Reject record; unit price cannot be negative                  | `INVALID_UNIT_PRICE`        |
| `ORD-2024-1024` | 25    | Malformed date (`2024-99-99`)                  | Reject record; cannot parse month/day                         | `INVALID_DATE`              |
| `ORD-2024-1025` | 26    | Non-date string (`invalid-date`)               | Reject record; unparsable date string                         | `INVALID_DATE`              |
| `ORD-2024-1026` | 27    | Missing customer ID (empty field)              | Reject record; customer ID is required                        | `MISSING_REQUIRED_FIELD`    |
| `ORD-2024-1027` | 28    | Missing product name (empty field)             | Reject record; product name is required                       | `MISSING_REQUIRED_FIELD`    |
| `ORD-2024-1028` | 29    | Invalid category (`UnknownCategory`)           | Reject record; category not in business domain taxonomy       | `INVALID_CATEGORY`          |
| `ORD-2024-1029` | 30    | Invalid region (`Antarctica`)                  | Reject record; region not in recognized operating territories | `INVALID_REGION`            |
| `ORD-2024-1030` | 31    | Non-numeric quantity (`abc`)                   | Reject record; quantity cannot be cast to integer             | `INVALID_QUANTITY_FORMAT`   |
