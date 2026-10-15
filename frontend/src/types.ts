/**
 * TypeScript Interfaces for Sales Data Platform API
 */

export interface HealthStatus {
  status: string;
  timestamp: string;
  database_connected: boolean;
  database_dialect: string;
  version: string;
}

export interface PipelineRunSummary {
  run_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  source_file: string;
  records_loaded: number;
  records_rejected: number;
}

export interface DashboardSummary {
  total_revenue: number;
  total_orders: number;
  total_units_sold: number;
  average_order_value: number;
  data_quality_pass_rate: number;
  total_records_processed: number;
  total_quarantined_records: number;
  last_run?: PipelineRunSummary;
}

export interface RevenueTrendItem {
  date: string;
  revenue: number;
  orders_count: number;
  units_sold: number;
}

export interface CategoryBreakdownItem {
  category: string;
  total_revenue: number;
  order_count: number;
  total_quantity: number;
  avg_order_value: number;
}

export interface RegionBreakdownItem {
  region: string;
  total_revenue: number;
  order_count: number;
  total_units_sold: number;
  avg_order_value: number;
}

export interface TopProductItem {
  product: string;
  category: string;
  total_revenue: number;
  units_sold: number;
  total_orders: number;
  avg_unit_price: number;
}

export interface SalesRecordItem {
  order_id: string;
  order_date: string;
  customer_id: string;
  product: string;
  category: string;
  quantity: number;
  unit_price: number;
  total_amount: number;
  region: string;
  created_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PipelineRunItem {
  run_id: string;
  start_time: string;
  end_time?: string;
  source_file: string;
  total_records_extracted: number;
  records_accepted: number;
  records_rejected: number;
  records_loaded: number;
  status: 'SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED' | string;
  duration_seconds?: number;
  error_message?: string;
}

export interface PipelineOverviewSummary {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  partial_runs: number;
  last_successful_run?: string;
  latest_run?: PipelineRunItem;
}

export interface DataQualitySummary {
  total_inspected: number;
  valid_records: number;
  rejected_records: number;
  duplicate_records: number;
  pass_rate: number;
  reasons_breakdown: Record<string, number>;
}

export interface RejectedRecordItem {
  id: number;
  raw_order_id?: string;
  raw_order_date?: string;
  raw_customer_id?: string;
  raw_product?: string;
  raw_category?: string;
  raw_quantity?: string;
  raw_unit_price?: string;
  raw_region?: string;
  rejection_reason: string;
  source_file: string;
  pipeline_run_id: string;
  created_at?: string;
}

export interface ColumnSchemaInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

export interface TableMetadata {
  table_name: string;
  row_count: number;
  columns: ColumnSchemaInfo[];
}

export interface TableDataResponse {
  table_name: string;
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
  columns: string[];
  rows: Record<string, any>[];
}

export interface RawFileItem {
  filename: string;
  size_bytes: number;
  modified_at: string;
}
