"""Read-only Database Explorer endpoints."""

import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import inspect, text

from src.api.schemas import ColumnSchemaInfo, TableDataResponse, TableMetadata
from src.load import get_db_engine

router = APIRouter(prefix="/api/database", tags=["Database Explorer"])

ALLOWED_TABLES = {"sales_records", "rejected_sales_records", "pipeline_runs"}


@router.get("/tables", response_model=List[TableMetadata])
def list_database_tables() -> List[TableMetadata]:
    """Retrieve metadata and schema information for all approved warehouse tables."""
    engine = get_db_engine()
    tables_meta: List[TableMetadata] = []

    try:
        inspector = inspect(engine)
        with engine.connect() as conn:
            for table_name in sorted(list(ALLOWED_TABLES)):
                # Count records
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar() or 0

                # Inspect columns
                columns_info: List[ColumnSchemaInfo] = []
                for col in inspector.get_columns(table_name):
                    columns_info.append(
                        ColumnSchemaInfo(
                            name=col["name"],
                            type=str(col["type"]),
                            nullable=col.get("nullable", True),
                            primary_key=bool(col.get("primary_key", False)),
                        )
                    )

                tables_meta.append(
                    TableMetadata(
                        table_name=table_name,
                        row_count=int(count),
                        columns=columns_info,
                    )
                )

        return tables_meta
    finally:
        engine.dispose()


@router.get("/tables/{table_name}/records", response_model=TableDataResponse)
def get_table_records(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
) -> TableDataResponse:
    """Read-only data browser for an approved table with search and pagination."""
    if table_name not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=403,
            detail=f"Access to table '{table_name}' is forbidden. Allowed: {sorted(list(ALLOWED_TABLES))}",
        )

    engine = get_db_engine()

    try:
        inspector = inspect(engine)
        valid_cols = [c["name"] for c in inspector.get_columns(table_name)]

        # Validate sorting column
        if sort_by and sort_by not in valid_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort column '{sort_by}'. Valid: {valid_cols}",
            )

        order_col = sort_by or valid_cols[0]
        direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        where_clauses = []
        params: Dict[str, Any] = {}

        if search and search.strip():
            # Search across string columns safely
            search_likes = []
            for col in valid_cols:
                param_key = f"s_{col}"
                search_likes.append(f"CAST({col} AS VARCHAR) LIKE :{param_key}")
                params[param_key] = f"%{search.strip()}%"
            if search_likes:
                where_clauses.append(f"({' OR '.join(search_likes)})")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        offset = (page - 1) * page_size

        count_sql = f"SELECT COUNT(*) FROM {table_name} {where_sql};"
        data_sql = f"""
            SELECT * FROM {table_name}
            {where_sql}
            ORDER BY {order_col} {direction}
            LIMIT :limit OFFSET :offset;
        """
        params["limit"] = page_size
        params["offset"] = offset

        with engine.connect() as conn:
            total_count = conn.execute(text(count_sql), params).scalar() or 0
            results = conn.execute(text(data_sql), params).mappings().fetchall()

            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

            rows: List[Dict[str, Any]] = []
            for r in results:
                row_dict = {}
                for k, v in r.items():
                    if hasattr(v, "isoformat"):
                        row_dict[k] = v.isoformat()
                    else:
                        row_dict[k] = v
                rows.append(row_dict)

            return TableDataResponse(
                table_name=table_name,
                total_records=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                columns=valid_cols,
                rows=rows,
            )
    finally:
        engine.dispose()
