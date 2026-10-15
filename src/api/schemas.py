"""Pydantic Request and Response Schemas for the Analytics API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool
    database_dialect: str
    version: str


class PipelineRunSummary(BaseModel):
    run_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    source_file: str
    records_loaded: int
    records_rejected: int


class DashboardSummaryResponse(BaseModel):
    total_revenue: float
    total_orders: int
    total_units_sold: int
    average_order_value: float
    data_quality_pass_rate: float
    total_records_processed: int
    total_quarantined_records: int
    last_run: Optional[PipelineRunSummary] = None


class RevenueTrendItem(BaseModel):
    date: str
    revenue: float
    orders_count: int
    units_sold: int


class CategoryBreakdownItem(BaseModel):
    category: str
    total_revenue: float
    order_count: int
    total_quantity: int
    avg_order_value: float


class RegionBreakdownItem(BaseModel):
    region: str
    total_revenue: float
    order_count: int
    total_units_sold: int
    avg_order_value: float


class TopProductItem(BaseModel):
    product: str
    category: str
    total_revenue: float
    units_sold: int
    total_orders: int
    avg_unit_price: float


class SalesRecordItem(BaseModel):
    order_id: str
    order_date: str
    customer_id: str
    product: str
    category: str
    quantity: int
    unit_price: float
    total_amount: float
    region: str
    created_at: Optional[datetime] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PipelineRunItem(BaseModel):
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    source_file: str
    total_records_extracted: int
    records_accepted: int
    records_rejected: int
    records_loaded: int
    status: str
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class PipelineOverviewSummary(BaseModel):
    total_runs: int
    successful_runs: int
    failed_runs: int
    partial_runs: int
    last_successful_run: Optional[datetime] = None
    latest_run: Optional[PipelineRunItem] = None


class PipelineTriggerRequest(BaseModel):
    filename: str = Field(
        default="sales_sample.csv",
        description="Filename located inside data/raw/ directory to process",
    )


class PipelineTriggerResponse(BaseModel):
    status: str
    message: str
    exit_code: int
    filename: str


class DataQualitySummaryResponse(BaseModel):
    total_inspected: int
    valid_records: int
    rejected_records: int
    duplicate_records: int
    pass_rate: float
    reasons_breakdown: Dict[str, int]


class RejectedRecordItem(BaseModel):
    id: int
    raw_order_id: Optional[str] = None
    raw_order_date: Optional[str] = None
    raw_customer_id: Optional[str] = None
    raw_product: Optional[str] = None
    raw_category: Optional[str] = None
    raw_quantity: Optional[str] = None
    raw_unit_price: Optional[str] = None
    raw_region: Optional[str] = None
    rejection_reason: str
    source_file: str
    pipeline_run_id: str
    created_at: Optional[datetime] = None


class ColumnSchemaInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class TableMetadata(BaseModel):
    table_name: str
    row_count: int
    columns: List[ColumnSchemaInfo]


class TableDataResponse(BaseModel):
    table_name: str
    total_records: int
    page: int
    page_size: int
    total_pages: int
    columns: List[str]
    rows: List[Dict[str, Any]]


class ManualOrderInput(BaseModel):
    order_id: str
    order_date: str
    customer_id: str
    product: str
    category: str
    quantity: int
    unit_price: float
    region: str


class ManualOrderResponse(BaseModel):
    status: str
    message: str
    order_id: str
    is_valid: bool
    rejection_reason: Optional[str] = None


class RemoteSyncRequest(BaseModel):
    source_type: str = "db"
    remote_url: Optional[str] = None
    api_key: Optional[str] = None
    days_back: int = 1


class RemoteSyncResponse(BaseModel):
    status: str
    message: str
    records_synced: int
