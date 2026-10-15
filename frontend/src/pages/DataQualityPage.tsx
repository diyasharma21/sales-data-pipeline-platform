import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertOctagon,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  FileWarning,
  CheckCircle,
  Copy,
  Info,
} from 'lucide-react';
import { api } from '../api';
import { DataQualitySummary, PaginatedResponse, RejectedRecordItem } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const DataQualityPage: React.FC<{ refreshKey: number }> = ({ refreshKey }) => {
  const [summary, setSummary] = useState<DataQualitySummary | null>(null);
  const [rejectedData, setRejectedData] = useState<PaginatedResponse<RejectedRecordItem> | null>(null);
  const [search, setSearch] = useState<string>('');
  const [selectedReason, setSelectedReason] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isTableLoading, setIsTableLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getDataQualitySummary();
      setSummary(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load data quality summary.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadRejectedRecords = async () => {
    setIsTableLoading(true);
    try {
      const res = await api.getRejectedRecords({
        page,
        pageSize,
        search,
        reason: selectedReason || undefined,
      });
      setRejectedData(res);
    } catch (err: any) {
      console.error('Failed to load quarantined records:', err);
    } finally {
      setIsTableLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [refreshKey]);

  useEffect(() => {
    loadRejectedRecords();
  }, [refreshKey, page, pageSize, search, selectedReason]);

  if (isLoading && !summary) {
    return <LoadingSpinner message="Auditing data quality and quarantine records..." />;
  }

  if (error && !summary) {
    return <ErrorAlert message={error} onRetry={loadSummary} />;
  }

  return (
    <div className="space-y-6">
      {/* Quality Health Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Pass Rate Card */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
              Data Quality Pass Rate
            </div>
            <div className="text-3xl font-extrabold text-slate-900">
              {(summary?.pass_rate || 100).toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Formula: Valid Records / Total Inspected
            </div>
          </div>
          <div
            className={`p-3 rounded-xl border ${
              (summary?.pass_rate || 100) >= 90
                ? 'bg-emerald-50 text-emerald-600 border-emerald-100'
                : 'bg-amber-50 text-amber-600 border-amber-100'
            }`}
          >
            <ShieldCheck className="w-7 h-7" />
          </div>
        </div>

        {/* Total Inspected */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Total Inspected
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary?.total_inspected || 0}</div>
          <div className="text-xs text-slate-400 mt-1">Combined input records</div>
        </div>

        {/* Clean Accepted */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Clean / Accepted
          </div>
          <div className="text-2xl font-bold text-emerald-600">{summary?.valid_records || 0}</div>
          <div className="text-xs text-slate-400 mt-1">Written to fact table</div>
        </div>

        {/* Quarantined Records */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Quarantined / Rejected
          </div>
          <div className="text-2xl font-bold text-rose-600">{summary?.rejected_records || 0}</div>
          <div className="text-xs text-slate-400 mt-1">Isolated with failure reasons</div>
        </div>
      </div>

      {/* Failure Taxonomy Breakdown Cards */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-amber-600" />
              <span>Data Anomaly & Rejection Taxonomy</span>
            </h3>
            <p className="text-xs text-slate-500">
              Categorization of rule violations detected during the validation phase
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-400">
            {Object.keys(summary?.reasons_breakdown || {}).length} Validation Rules
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(summary?.reasons_breakdown || {}).map(([reasonCode, count]) => (
            <div
              key={reasonCode}
              onClick={() => {
                setSelectedReason(selectedReason === reasonCode ? '' : reasonCode);
                setPage(1);
              }}
              className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                selectedReason === reasonCode
                  ? 'bg-indigo-50/80 border-indigo-400 text-indigo-950 font-medium'
                  : count > 0
                  ? 'bg-slate-50/60 border-slate-200 hover:bg-slate-100/70 text-slate-800'
                  : 'bg-white border-slate-100 text-slate-400 opacity-60'
              }`}
            >
              <div className="text-[11px] font-mono text-slate-500 truncate">{reasonCode}</div>
              <div className="text-xl font-bold mt-1 text-slate-900">{count}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">
                {count > 0 ? 'Click to filter table' : '0 violations detected'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quarantined Records Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <FileWarning className="w-4 h-4 text-rose-600" />
              <span>Quarantined Records Browser (rejected_sales_records)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Raw payloads preserved verbatim with diagnostic failure messages
            </p>
          </div>

          <span className="text-xs font-semibold text-rose-700 bg-rose-50 px-3 py-1 rounded-lg border border-rose-200">
            {rejectedData?.total || 0} Quarantined
          </span>
        </div>

        {/* Filter & Search Bar */}
        <div className="flex flex-col sm:flex-row items-center gap-3 mb-4">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search raw Order ID, product, customer..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {selectedReason && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-200 text-xs">
              <span>Filter: {selectedReason}</span>
              <button
                onClick={() => setSelectedReason('')}
                className="text-indigo-400 hover:text-indigo-900 font-bold ml-1"
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* Quarantined Records Table */}
        <div className="overflow-x-auto border border-slate-100 rounded-lg">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <th className="py-2.5 px-3">Raw Order ID</th>
                <th className="py-2.5 px-3">Raw Date</th>
                <th className="py-2.5 px-3">Raw Product</th>
                <th className="py-2.5 px-3 text-right">Raw Qty</th>
                <th className="py-2.5 px-3 text-right">Raw Price</th>
                <th className="py-2.5 px-3">Rejection Diagnostic Reasons</th>
                <th className="py-2.5 px-3">Source File</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {isTableLoading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading quarantined records...
                  </td>
                </tr>
              ) : !rejectedData || rejectedData.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No quarantined records found. All data is valid!
                  </td>
                </tr>
              ) : (
                rejectedData.items.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-900">
                      {row.raw_order_id || <span className="text-slate-300">null</span>}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">
                      {row.raw_order_date || <span className="text-slate-300">null</span>}
                    </td>
                    <td className="py-2.5 px-3 text-slate-800">
                      {row.raw_product || <span className="text-slate-300">null</span>}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono">
                      {row.raw_quantity || <span className="text-slate-300">null</span>}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono">
                      {row.raw_unit_price || <span className="text-slate-300">null</span>}
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="flex flex-wrap gap-1">
                        {row.rejection_reason.split(';').map((reasonPart, idx) => (
                          <span
                            key={idx}
                            className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-rose-50 text-rose-700 border border-rose-200"
                          >
                            {reasonPart.trim()}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">
                      {row.source_file}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {rejectedData && rejectedData.total_pages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-2">
            <span className="text-xs text-slate-500">
              Page <span className="font-semibold text-slate-800">{rejectedData.page}</span> of{' '}
              <span className="font-semibold text-slate-800">{rejectedData.total_pages}</span>
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={rejectedData.page <= 1}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, rejectedData.total_pages))}
                disabled={rejectedData.page >= rejectedData.total_pages}
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
