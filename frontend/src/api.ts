/**
 * API Service Client for Sales Data Platform
 */

import {
  CategoryBreakdownItem,
  DashboardSummary,
  DataQualitySummary,
  HealthStatus,
  PaginatedResponse,
  PipelineOverviewSummary,
  PipelineRunItem,
  RawFileItem,
  RegionBreakdownItem,
  RejectedRecordItem,
  RevenueTrendItem,
  SalesRecordItem,
  TableDataResponse,
  TableMetadata,
  TopProductItem,
} from './types';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Health
  getHealth: async (): Promise<HealthStatus> => {
    const res = await fetch(`${BASE_URL}/health`);
    return handleResponse<HealthStatus>(res);
  },

  // Dashboard Overview
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const res = await fetch(`${BASE_URL}/dashboard/summary`);
    return handleResponse<DashboardSummary>(res);
  },

  // Analytics
  getRevenueTrend: async (params?: {
    granularity?: 'daily' | 'monthly';
    startDate?: string;
    endDate?: string;
  }): Promise<RevenueTrendItem[]> => {
    const query = new URLSearchParams();
    if (params?.granularity) query.append('granularity', params.granularity);
    if (params?.startDate) query.append('start_date', params.startDate);
    if (params?.endDate) query.append('end_date', params.endDate);
    const res = await fetch(`${BASE_URL}/analytics/revenue-trend?${query.toString()}`);
    return handleResponse<RevenueTrendItem[]>(res);
  },

  getCategoryBreakdown: async (): Promise<CategoryBreakdownItem[]> => {
    const res = await fetch(`${BASE_URL}/analytics/category-breakdown`);
    return handleResponse<CategoryBreakdownItem[]>(res);
  },

  getRegionBreakdown: async (): Promise<RegionBreakdownItem[]> => {
    const res = await fetch(`${BASE_URL}/analytics/region-breakdown`);
    return handleResponse<RegionBreakdownItem[]>(res);
  },

  getTopProducts: async (limit = 5): Promise<TopProductItem[]> => {
    const res = await fetch(`${BASE_URL}/analytics/top-products?limit=${limit}`);
    return handleResponse<TopProductItem[]>(res);
  },

  getSalesRecords: async (params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    category?: string;
    region?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<PaginatedResponse<SalesRecordItem>> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.pageSize) query.append('page_size', params.pageSize.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.category) query.append('category', params.category);
    if (params?.region) query.append('region', params.region);
    if (params?.sortBy) query.append('sort_by', params.sortBy);
    if (params?.sortOrder) query.append('sort_order', params.sortOrder);
    const res = await fetch(`${BASE_URL}/analytics/sales-records?${query.toString()}`);
    return handleResponse<PaginatedResponse<SalesRecordItem>>(res);
  },

  // Pipeline Monitoring
  getPipelineSummary: async (): Promise<PipelineOverviewSummary> => {
    const res = await fetch(`${BASE_URL}/pipeline/summary`);
    return handleResponse<PipelineOverviewSummary>(res);
  },

  getPipelineRuns: async (params?: {
    page?: number;
    pageSize?: number;
    status?: string;
  }): Promise<PaginatedResponse<PipelineRunItem>> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.pageSize) query.append('page_size', params.pageSize.toString());
    if (params?.status) query.append('status', params.status);
    const res = await fetch(`${BASE_URL}/pipeline/runs?${query.toString()}`);
    return handleResponse<PaginatedResponse<PipelineRunItem>>(res);
  },

  getAvailableFiles: async (): Promise<{ files: RawFileItem[] }> => {
    const res = await fetch(`${BASE_URL}/pipeline/files`);
    return handleResponse<{ files: RawFileItem[] }>(res);
  },

  triggerPipelineRun: async (filename: string): Promise<{ status: string; message: string; exit_code: number; filename: string }> => {
    const res = await fetch(`${BASE_URL}/pipeline/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    return handleResponse(res);
  },

  // Data Quality
  getDataQualitySummary: async (): Promise<DataQualitySummary> => {
    const res = await fetch(`${BASE_URL}/data-quality/summary`);
    return handleResponse<DataQualitySummary>(res);
  },

  getRejectedRecords: async (params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    reason?: string;
  }): Promise<PaginatedResponse<RejectedRecordItem>> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.pageSize) query.append('page_size', params.pageSize.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.reason) query.append('reason', params.reason);
    const res = await fetch(`${BASE_URL}/data-quality/rejected-records?${query.toString()}`);
    return handleResponse<PaginatedResponse<RejectedRecordItem>>(res);
  },

  // Database Explorer
  getDatabaseTables: async (): Promise<TableMetadata[]> => {
    const res = await fetch(`${BASE_URL}/database/tables`);
    return handleResponse<TableMetadata[]>(res);
  },

  getTableRecords: async (
    tableName: string,
    params?: {
      page?: number;
      pageSize?: number;
      search?: string;
      sortBy?: string;
      sortOrder?: 'asc' | 'desc';
    }
  ): Promise<TableDataResponse> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.pageSize) query.append('page_size', params.pageSize.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.sortBy) query.append('sort_by', params.sortBy);
    if (params?.sortOrder) query.append('sort_order', params.sortOrder);
    const res = await fetch(`${BASE_URL}/database/tables/${tableName}/records?${query.toString()}`);
    return handleResponse<TableDataResponse>(res);
  },
};
