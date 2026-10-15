import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Calendar,
  Layers,
  MapPin,
  Tag,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { api } from '../api';
import {
  CategoryBreakdownItem,
  PaginatedResponse,
  RegionBreakdownItem,
  RevenueTrendItem,
  SalesRecordItem,
} from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { EmptyState } from '../components/EmptyState';

export const SalesAnalyticsPage: React.FC<{ refreshKey: number }> = ({ refreshKey }) => {
  // Chart and trend state
  const [trends, setTrends] = useState<RevenueTrendItem[]>([]);
  const [categories, setCategories] = useState<CategoryBreakdownItem[]>([]);
  const [regions, setRegions] = useState<RegionBreakdownItem[]>([]);
  const [granularity, setGranularity] = useState<'daily' | 'monthly'>('daily');

  // Sales records table state
  const [recordsData, setRecordsData] = useState<PaginatedResponse<SalesRecordItem> | null>(null);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [search, setSearch] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('order_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isTableLoading, setIsTableLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load trends & filter options
  const loadAnalyticsData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [trendRes, catRes, regRes] = await Promise.all([
        api.getRevenueTrend({ granularity }),
        api.getCategoryBreakdown(),
        api.getRegionBreakdown(),
      ]);
      setTrends(trendRes);
      setCategories(catRes);
      setRegions(regRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load sales analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  // Load paginated table
  const loadRecords = async () => {
    setIsTableLoading(true);
    try {
      const res = await api.getSalesRecords({
        page,
        pageSize,
        search,
        category: selectedCategory || undefined,
        region: selectedRegion || undefined,
        sortBy,
        sortOrder,
      });
      setRecordsData(res);
    } catch (err: any) {
      console.error('Failed to load sales records:', err);
    } finally {
      setIsTableLoading(false);
    }
  };

  useEffect(() => {
    loadAnalyticsData();
  }, [refreshKey, granularity]);

  useEffect(() => {
    loadRecords();
  }, [refreshKey, page, pageSize, search, selectedCategory, selectedRegion, sortBy, sortOrder]);

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('desc');
    }
    setPage(1);
  };

  if (isLoading && trends.length === 0) {
    return <LoadingSpinner message="Calculating analytics aggregations..." />;
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={loadAnalyticsData} />;
  }

  return (
    <div className="space-y-6">
      {/* Analytics Visual Chart Header */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <span>Revenue & Volume Aggregations</span>
            </h3>
            <p className="text-xs text-slate-500">
              Interactive timeline showing revenue and order frequency
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => setGranularity('daily')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                granularity === 'daily'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Daily Trends
            </button>
            <button
              onClick={() => setGranularity('monthly')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                granularity === 'monthly'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Monthly Rollup
            </button>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="analyticsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b' }}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                tickFormatter={(val) => `$${val}`}
              />
              <Tooltip
                formatter={(val: any, name: any) => [
                  name === 'revenue' ? `$${Number(val).toFixed(2)}` : val,
                  name === 'revenue' ? 'Revenue' : 'Units Sold',
                ]}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  fontSize: '12px',
                }}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#4f46e5"
                strokeWidth={2}
                fill="url(#analyticsGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Searchable & Paginated Clean Sales Records */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-100 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>Clean Sales Transactions (Fact Table)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Showing validated and loaded records stored in PostgreSQL
            </p>
          </div>

          <span className="text-xs font-semibold text-slate-500 bg-slate-50 px-3 py-1 rounded-lg border border-slate-200">
            {recordsData?.total || 0} Total Records
          </span>
        </div>

        {/* Filters and Search Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          {/* Keyword Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Order, Customer, Product..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Category Filter */}
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.category} value={c.category}>
                  {c.category} ({c.order_count})
                </option>
              ))}
            </select>
          </div>

          {/* Region Filter */}
          <div className="relative">
            <select
              value={selectedRegion}
              onChange={(e) => {
                setSelectedRegion(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-700 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
            >
              <option value="">All Regions</option>
              {regions.map((r) => (
                <option key={r.region} value={r.region}>
                  {r.region} ({r.order_count})
                </option>
              ))}
            </select>
          </div>

          {/* Page Size Selector */}
          <div className="flex items-center justify-end gap-2 text-xs text-slate-500">
            <span>Show</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="px-2 py-1 text-xs bg-slate-50 border border-slate-200 rounded-md cursor-pointer"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span>rows</span>
          </div>
        </div>

        {/* Data Grid Table */}
        <div className="overflow-x-auto border border-slate-100 rounded-lg">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <th
                  onClick={() => toggleSort('order_id')}
                  className="py-2.5 px-3 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center gap-1">
                    <span>Order ID</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('order_date')}
                  className="py-2.5 px-3 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center gap-1">
                    <span>Date</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-3">Customer</th>
                <th
                  onClick={() => toggleSort('product')}
                  className="py-2.5 px-3 cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center gap-1">
                    <span>Product</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Region</th>
                <th
                  onClick={() => toggleSort('quantity')}
                  className="py-2.5 px-3 text-right cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Qty</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('unit_price')}
                  className="py-2.5 px-3 text-right cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Unit Price</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => toggleSort('total_amount')}
                  className="py-2.5 px-3 text-right cursor-pointer hover:text-slate-900"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Total</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {isTableLoading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    Loading records...
                  </td>
                </tr>
              ) : !recordsData || recordsData.items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No sales records found matching the filter criteria.
                  </td>
                </tr>
              ) : (
                recordsData.items.map((row) => (
                  <tr key={row.order_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-900">
                      {row.order_id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">{row.order_date}</td>
                    <td className="py-2.5 px-3 font-mono text-slate-500">{row.customer_id}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-800">{row.product}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">
                        {row.category}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {row.region}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-medium">{row.quantity}</td>
                    <td className="py-2.5 px-3 text-right text-slate-500">
                      ${row.unit_price.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                      ${row.total_amount.toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {recordsData && recordsData.total_pages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-2">
            <span className="text-xs text-slate-500">
              Page <span className="font-semibold text-slate-800">{recordsData.page}</span> of{' '}
              <span className="font-semibold text-slate-800">{recordsData.total_pages}</span>
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={recordsData.page <= 1}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, recordsData.total_pages))}
                disabled={recordsData.page >= recordsData.total_pages}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
