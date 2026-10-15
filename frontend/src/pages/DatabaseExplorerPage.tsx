import React, { useEffect, useState } from 'react';
import {
  Database,
  Table as TableIcon,
  Search,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Code2,
  Lock,
  Layers,
  Key,
} from 'lucide-react';
import { api } from '../api';
import { TableDataResponse, TableMetadata } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const DatabaseExplorerPage: React.FC<{ refreshKey: number }> = ({ refreshKey }) => {
  const [tables, setTables] = useState<TableMetadata[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('sales_records');
  const [tableData, setTableData] = useState<TableDataResponse | null>(null);

  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);
  const [search, setSearch] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const [isLoadingTables, setIsLoadingTables] = useState<boolean>(true);
  const [isLoadingRecords, setIsLoadingRecords] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load available table schemas
  const loadTables = async () => {
    setIsLoadingTables(true);
    setError(null);
    try {
      const res = await api.getDatabaseTables();
      setTables(res);
      if (res.length > 0 && !res.some((t) => t.table_name === selectedTable)) {
        setSelectedTable(res[0].table_name);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to inspect database tables.');
    } finally {
      setIsLoadingTables(false);
    }
  };

  // Load table data
  const loadRecords = async () => {
    setIsLoadingRecords(true);
    try {
      const res = await api.getTableRecords(selectedTable, {
        page,
        pageSize,
        search,
        sortBy: sortBy || undefined,
        sortOrder,
      });
      setTableData(res);
    } catch (err: any) {
      console.error(`Failed to load data for ${selectedTable}:`, err);
    } finally {
      setIsLoadingRecords(false);
    }
  };

  useEffect(() => {
    loadTables();
  }, [refreshKey]);

  useEffect(() => {
    loadRecords();
  }, [refreshKey, selectedTable, page, pageSize, search, sortBy, sortOrder]);

  const handleTableChange = (name: string) => {
    setSelectedTable(name);
    setPage(1);
    setSearch('');
    setSortBy('');
    setSortOrder('asc');
  };

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('asc');
    }
    setPage(1);
  };

  if (isLoadingTables && tables.length === 0) {
    return <LoadingSpinner message="Inspecting database catalog and schema metadata..." />;
  }

  if (error && tables.length === 0) {
    return <ErrorAlert message={error} onRetry={loadTables} />;
  }

  const currentTableMeta = tables.find((t) => t.table_name === selectedTable);

  return (
    <div className="space-y-6">
      {/* Table Selector Pills */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-sm flex flex-wrap items-center gap-3">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-2 flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5" />
          <span>Warehouse Tables:</span>
        </span>
        {tables.map((t) => {
          const isSelected = selectedTable === t.table_name;
          return (
            <button
              key={t.table_name}
              onClick={() => handleTableChange(t.table_name)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                isSelected
                  ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                  : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              <span>{t.table_name}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  isSelected ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-200 text-slate-600'
                }`}
              >
                {t.row_count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Table Schema Definition Card */}
      {currentTableMeta && (
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Code2 className="w-4 h-4 text-indigo-600" />
                <span>Schema Definition for '{selectedTable}'</span>
              </h3>
              <p className="text-[11px] text-slate-400">
                PostgreSQL schema definition & data types inspected via SQLAlchemy metadata
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
              <Lock className="w-3 h-3" />
              <span>Read-Only Explorer</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {currentTableMeta.columns.map((col) => (
              <div
                key={col.name}
                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-[11px] flex items-center gap-2"
              >
                {col.primary_key && <Key className="w-3 h-3 text-amber-500 shrink-0" />}
                <span className="font-mono font-semibold text-slate-800">{col.name}</span>
                <span className="text-[10px] font-mono text-slate-400">{col.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Data Grid */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <TableIcon className="w-4 h-4 text-indigo-600" />
              <span>Table Records Browser</span>
            </h3>
            <p className="text-xs text-slate-500">
              Parameterized pagination with bounded limits (SQL injection protected)
            </p>
          </div>

          <span className="text-xs font-semibold text-slate-500 bg-slate-50 px-3 py-1 rounded-lg border border-slate-200">
            {tableData?.total_records || 0} Records Total
          </span>
        </div>

        {/* Search & Page Size */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4">
          <div className="relative flex-1 w-full sm:max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder={`Search in ${selectedTable}...`}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500 shrink-0">
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
              <option value={15}>15</option>
              <option value={30}>30</option>
              <option value={50}>50</option>
            </select>
            <span>rows per page</span>
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto border border-slate-100 rounded-lg">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                {tableData?.columns.map((col) => (
                  <th
                    key={col}
                    onClick={() => handleSort(col)}
                    className="py-2.5 px-3 cursor-pointer hover:text-slate-900 whitespace-nowrap"
                  >
                    <div className="flex items-center gap-1">
                      <span>{col}</span>
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {isLoadingRecords ? (
                <tr>
                  <td
                    colSpan={tableData?.columns.length || 1}
                    className="py-8 text-center text-slate-400"
                  >
                    Querying records...
                  </td>
                </tr>
              ) : !tableData || tableData.rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={tableData?.columns.length || 1}
                    className="py-8 text-center text-slate-400"
                  >
                    No records found in '{selectedTable}'.
                  </td>
                </tr>
              ) : (
                tableData.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                    {tableData.columns.map((col) => {
                      const val = row[col];
                      return (
                        <td key={col} className="py-2.5 px-3 font-mono text-[11px] whitespace-nowrap">
                          {val === null || val === undefined ? (
                            <span className="text-slate-300">null</span>
                          ) : typeof val === 'number' ? (
                            <span className="font-semibold text-slate-800">{val}</span>
                          ) : (
                            <span className="text-slate-700">{String(val)}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {tableData && tableData.total_pages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-2">
            <span className="text-xs text-slate-500">
              Page <span className="font-semibold text-slate-800">{tableData.page}</span> of{' '}
              <span className="font-semibold text-slate-800">{tableData.total_pages}</span>
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={tableData.page <= 1}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, tableData.total_pages))}
                disabled={tableData.page >= tableData.total_pages}
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
