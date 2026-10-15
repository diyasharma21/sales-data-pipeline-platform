import React, { useEffect, useState } from 'react';
import {
  DollarSign,
  ShoppingCart,
  Package,
  TrendingUp,
  ShieldCheck,
  Calendar,
  Layers,
  ArrowUpRight,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
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
  DashboardSummary,
  RegionBreakdownItem,
  RevenueTrendItem,
  TopProductItem,
} from '../types';
import { KpiCard } from '../components/KpiCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

const COLORS = ['#6366f1', '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899'];

export const OverviewPage: React.FC<{ refreshKey: number }> = ({ refreshKey }) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<RevenueTrendItem[]>([]);
  const [categories, setCategories] = useState<CategoryBreakdownItem[]>([]);
  const [regions, setRegions] = useState<RegionBreakdownItem[]>([]);
  const [topProducts, setTopProducts] = useState<TopProductItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [trendGranularity, setTrendGranularity] = useState<'daily' | 'monthly'>('daily');

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, trendRes, catRes, regRes, prodRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getRevenueTrend({ granularity: trendGranularity }),
        api.getCategoryBreakdown(),
        api.getRegionBreakdown(),
        api.getTopProducts(5),
      ]);
      setSummary(sumRes);
      setTrends(trendRes);
      setCategories(catRes);
      setRegions(regRes);
      setTopProducts(prodRes);
    } catch (err: any) {
      setError(err.message || 'Error loading dashboard metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [refreshKey, trendGranularity]);

  if (isLoading && !summary) {
    return <LoadingSpinner message="Calculating warehouse metrics..." />;
  }

  if (error && !summary) {
    return <ErrorAlert message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-6">
      {/* 5 KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Total Revenue"
          value={`$${(summary?.total_revenue || 0).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}`}
          subtitle="Net verified sales"
          icon={DollarSign}
          accentColor="indigo"
          badge={{ text: 'Verified', variant: 'success' }}
        />
        <KpiCard
          title="Total Orders"
          value={summary?.total_orders.toLocaleString() || '0'}
          subtitle="Unique order identifiers"
          icon={ShoppingCart}
          accentColor="blue"
        />
        <KpiCard
          title="Units Sold"
          value={summary?.total_units_sold.toLocaleString() || '0'}
          subtitle="Physical item volume"
          icon={Package}
          accentColor="purple"
        />
        <KpiCard
          title="Avg Order Value"
          value={`$${(summary?.average_order_value || 0).toFixed(2)}`}
          subtitle="Revenue per valid order"
          icon={TrendingUp}
          accentColor="emerald"
        />
        <KpiCard
          title="Quality Pass Rate"
          value={`${(summary?.data_quality_pass_rate || 100).toFixed(1)}%`}
          subtitle={`${summary?.total_quarantined_records || 0} quarantined rows`}
          icon={ShieldCheck}
          accentColor="amber"
          badge={{
            text: (summary?.data_quality_pass_rate || 100) >= 90 ? 'Healthy' : 'Audited',
            variant: (summary?.data_quality_pass_rate || 100) >= 90 ? 'success' : 'warning',
          }}
        />
      </div>

      {/* Main Revenue Trend Chart */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <span>Revenue & Order Volume Over Time</span>
            </h3>
            <p className="text-xs text-slate-500">
              Aggregated financial trends calculated directly in SQL
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
            <button
              onClick={() => setTrendGranularity('daily')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                trendGranularity === 'daily'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Daily
            </button>
            <button
              onClick={() => setTrendGranularity('monthly')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                trendGranularity === 'monthly'
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Monthly
            </button>
          </div>
        </div>

        <div className="h-72 w-full">
          {trends.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              No revenue records recorded yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
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
                    name === 'revenue' ? 'Net Revenue' : 'Orders Count',
                  ]}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#4f46e5"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#revenueGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Two Column Breakdown: Category & Region */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                Revenue by Category
              </h3>
              <p className="text-xs text-slate-500">Sales volume per product taxonomy</p>
            </div>
            <span className="text-xs font-semibold text-slate-400">
              {categories.length} Categories
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categories} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="category"
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
                  formatter={(val: any) => [`$${Number(val).toFixed(2)}`, 'Revenue']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="total_revenue" radius={[6, 6, 0, 0]}>
                  {categories.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Regional Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                Geographic Region Share
              </h3>
              <p className="text-xs text-slate-500">Revenue contribution across territories</p>
            </div>
            <span className="text-xs font-semibold text-slate-400">
              {regions.length} Operating Regions
            </span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={regions}
                  dataKey="total_revenue"
                  nameKey="region"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                >
                  {regions.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any) => [`$${Number(val).toFixed(2)}`, 'Revenue']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(val) => <span className="text-xs text-slate-600">{val}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Top 5 Best-Selling Products Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Top 5 Best-Selling Products
            </h3>
            <p className="text-xs text-slate-500">Highest grossing items in inventory</p>
          </div>
          <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-100">
            Top Rank
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                <th className="py-2.5 px-3">Product</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 text-right">Units Sold</th>
                <th className="py-2.5 px-3 text-right">Avg Price</th>
                <th className="py-2.5 px-3 text-right">Total Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {topProducts.map((prod, idx) => (
                <tr key={prod.product} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-3 font-semibold text-slate-900 flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    <span>{prod.product}</span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">
                      {prod.category}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right font-medium">{prod.units_sold}</td>
                  <td className="py-3 px-3 text-right text-slate-500">
                    ${prod.avg_unit_price.toFixed(2)}
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-indigo-700">
                    ${prod.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
