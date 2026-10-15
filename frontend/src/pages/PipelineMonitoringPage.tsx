import React, { useEffect, useState } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Play,
  FileText,
  ChevronLeft,
  ChevronRight,
  Database,
  RefreshCw,
  Info,
} from 'lucide-react';
import { api } from '../api';
import {
  PaginatedResponse,
  PipelineOverviewSummary,
  PipelineRunItem,
  RawFileItem,
} from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';

export const PipelineMonitoringPage: React.FC<{
  refreshKey: number;
  onRunTriggered: () => void;
}> = ({ refreshKey, onRunTriggered }) => {
  const [summary, setSummary] = useState<PipelineOverviewSummary | null>(null);
  const [runsData, setRunsData] = useState<PaginatedResponse<PipelineRunItem> | null>(null);
  const [rawFiles, setRawFiles] = useState<RawFileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('sales_sample.csv');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [selectedError, setSelectedError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, runsRes, filesRes] = await Promise.all([
        api.getPipelineSummary(),
        api.getPipelineRuns({ page, pageSize, status: statusFilter || undefined }),
        api.getAvailableFiles(),
      ]);
      setSummary(sumRes);
      setRunsData(runsRes);
      setRawFiles(filesRes.files);
      if (filesRes.files.length > 0 && !selectedFile) {
        setSelectedFile(filesRes.files[0].filename);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load pipeline monitoring data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [refreshKey, page, pageSize, statusFilter]);

  const handleTrigger = async () => {
    setIsRunning(true);
    try {
      await api.triggerPipelineRun(selectedFile);
      onRunTriggered();
      loadData();
    } catch (err: any) {
      alert(`Trigger failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  if (isLoading && !summary) {
    return <LoadingSpinner message="Querying pipeline operational logs..." />;
  }

  if (error && !summary) {
    return <ErrorAlert message={error} onRetry={loadData} />;
  }

  return (
    <div className="space-y-6">
      {/* Run Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Total Pipeline Runs
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary?.total_runs || 0}</div>
          <div className="text-xs text-slate-400 mt-1">Batch execution events</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Clean Success Runs
          </div>
          <div className="text-2xl font-bold text-emerald-600">
            {summary?.successful_runs || 0}
          </div>
          <div className="text-xs text-slate-400 mt-1">100% valid records</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Partial Success (Quarantined)
          </div>
          <div className="text-2xl font-bold text-amber-600">{summary?.partial_runs || 0}</div>
          <div className="text-xs text-slate-400 mt-1">Handled anomalies safely</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Failed Runs
          </div>
          <div className="text-2xl font-bold text-rose-600">{summary?.failed_runs || 0}</div>
          <div className="text-xs text-slate-400 mt-1">System errors / missing files</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Last Successful Run
          </div>
          <div className="text-sm font-bold text-slate-800 truncate">
            {summary?.last_successful_run
              ? new Date(summary.last_successful_run).toLocaleDateString()
              : 'N/A'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {summary?.last_successful_run
              ? new Date(summary.last_successful_run).toLocaleTimeString()
              : 'No completed run yet'}
          </div>
        </div>
      </div>

      {/* Manual Ingestion Trigger Banner */}
      <div className="bg-gradient-to-r from-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <span className="text-[10px] font-bold tracking-widest uppercase bg-indigo-500/30 text-indigo-300 px-2.5 py-1 rounded-md border border-indigo-400/20">
            Batch Orchestrator
          </span>
          <h3 className="text-lg font-bold text-white mt-2">Trigger Ingestion & Transformation</h3>
          <p className="text-xs text-slate-300 max-w-xl mt-1">
            Executes the complete ETL sequence on the selected raw CSV dataset. Automatically creates
            database tables, validates records, quarantines anomalies, and performs idempotent upsert.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <select
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
            disabled={isRunning}
            className="px-3.5 py-2 text-xs bg-slate-800/90 border border-slate-700 text-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 cursor-pointer"
          >
            {rawFiles.map((file) => (
              <option key={file.filename} value={file.filename}>
                {file.filename} ({(file.size_bytes / 1024).toFixed(1)} KB)
              </option>
            ))}
          </select>

          <button
            onClick={handleTrigger}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2 text-xs font-semibold text-slate-900 bg-white hover:bg-slate-100 disabled:opacity-50 rounded-xl transition-all shadow-md cursor-pointer active:scale-98"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Trigger Run</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Historical Execution Log Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-600" />
              <span>Historical Pipeline Runs (Lineage Log)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Audit log of all batch runs recorded in pipeline_runs table
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-700 cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="SUCCESS">Success Only</option>
              <option value="PARTIAL_SUCCESS">Partial Success (Quarantined)</option>
              <option value="FAILED">Failed</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto border border-slate-100 rounded-lg">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <th className="py-2.5 px-3">Run ID</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Source File</th>
                <th className="py-2.5 px-3 text-right">Extracted</th>
                <th className="py-2.5 px-3 text-right">Loaded</th>
                <th className="py-2.5 px-3 text-right">Quarantined</th>
                <th className="py-2.5 px-3 text-right">Duration</th>
                <th className="py-2.5 px-3 text-center">Status</th>
                <th className="py-2.5 px-3 text-center">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {!runsData || runsData.items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No pipeline runs recorded in the database.
                  </td>
                </tr>
              ) : (
                runsData.items.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-900">
                      {run.run_id}
                    </td>
                    <td className="py-2.5 px-3 text-slate-600">
                      {new Date(run.start_time).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-600">{run.source_file}</td>
                    <td className="py-2.5 px-3 text-right font-medium">
                      {run.total_records_extracted}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-emerald-700">
                      {run.records_loaded}
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-amber-700">
                      {run.records_rejected}
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-500">
                      {run.duration_seconds !== null && run.duration_seconds !== undefined
                        ? `${run.duration_seconds}s`
                        : '-'}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                          run.status === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : run.status === 'PARTIAL_SUCCESS'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {run.error_message ? (
                        <button
                          onClick={() => setSelectedError(run.error_message || '')}
                          className="px-2 py-0.5 text-[10px] font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded border border-rose-200 cursor-pointer"
                        >
                          View Error
                        </button>
                      ) : (
                        <span className="text-[11px] text-slate-400">Clean</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {runsData && runsData.total_pages > 1 && (
          <div className="flex items-center justify-between pt-4 mt-2">
            <span className="text-xs text-slate-500">
              Page <span className="font-semibold text-slate-800">{runsData.page}</span> of{' '}
              <span className="font-semibold text-slate-800">{runsData.total_pages}</span>
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={runsData.page <= 1}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, runsData.total_pages))}
                disabled={runsData.page >= runsData.total_pages}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error Details Modal */}
      {selectedError && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <h4 className="text-sm font-bold text-rose-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                <span>Pipeline Error Details</span>
              </h4>
              <button
                onClick={() => setSelectedError(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ✕
              </button>
            </div>
            <pre className="text-xs bg-slate-50 p-3 rounded-lg text-rose-900 font-mono overflow-x-auto whitespace-pre-wrap border border-slate-200">
              {selectedError}
            </pre>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setSelectedError(null)}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
