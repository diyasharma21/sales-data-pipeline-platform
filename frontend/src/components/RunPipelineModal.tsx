import React, { useEffect, useState, useRef } from 'react';
import {
  X,
  Play,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Loader2,
  Upload,
  PlusCircle,
  Layers,
  Send,
  Server,
  Globe,
  Database,
} from 'lucide-react';
import { api } from '../api';
import { RawFileItem } from '../types';

interface RunPipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const RunPipelineModal: React.FC<RunPipelineModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'batch' | 'manual' | 'remote'>('batch');

  // Batch CSV state
  const [files, setFiles] = useState<RawFileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('sales_sample.csv');
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  // Manual Order state
  const [manualOrder, setManualOrder] = useState({
    order_id: `ORD-2026-${Math.floor(1000 + Math.random() * 9000)}`,
    order_date: new Date().toISOString().split('T')[0],
    customer_id: 'CUST-5001',
    product: 'Mechanical Gaming Keyboard',
    category: 'Electronics',
    quantity: 1,
    unit_price: 129.99,
    region: 'North',
  });
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);

  // Remote Server Sync state
  const [remoteSync, setRemoteSync] = useState({
    source_type: 'db' as 'db' | 'api',
    remote_url: '',
    api_key: '',
    days_back: 1,
  });
  const [isSyncingRemote, setIsSyncingRemote] = useState(false);

  // Result banner
  const [executionResult, setExecutionResult] = useState<{
    status: string;
    message: string;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshFiles = () => {
    setIsLoadingFiles(true);
    api
      .getAvailableFiles()
      .then((res) => {
        setFiles(res.files);
        if (res.files.length > 0 && !res.files.some((f) => f.filename === selectedFile)) {
          setSelectedFile(res.files[0].filename);
        }
      })
      .catch((err) => console.error('Failed to load raw files:', err))
      .finally(() => setIsLoadingFiles(false));
  };

  useEffect(() => {
    if (isOpen) {
      setExecutionResult(null);
      setUploadError(null);
      refreshFiles();
      setManualOrder((prev) => ({
        ...prev,
        order_id: `ORD-2026-${Math.floor(1000 + Math.random() * 9000)}`,
      }));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadError('Only CSV files (.csv) are supported.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await api.uploadPipelineFile(file);
      setSelectedFile(res.filename);
      refreshFiles();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload CSV file.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRunBatch = async () => {
    setIsRunning(true);
    setExecutionResult(null);

    try {
      const res = await api.triggerPipelineRun(selectedFile);
      setExecutionResult({
        status: res.status,
        message: res.message,
      });
      onSuccess();
    } catch (err: any) {
      setExecutionResult({
        status: 'FAILED',
        message: err.message || 'Execution failed unexpectedly.',
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleManualOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingOrder(true);
    setExecutionResult(null);

    try {
      const res = await api.ingestOrder({
        ...manualOrder,
        quantity: Number(manualOrder.quantity),
        unit_price: Number(manualOrder.unit_price),
      });

      setExecutionResult({
        status: res.status,
        message: res.message,
      });
      onSuccess();

      setManualOrder((prev) => ({
        ...prev,
        order_id: `ORD-2026-${Math.floor(1000 + Math.random() * 9000)}`,
      }));
    } catch (err: any) {
      setExecutionResult({
        status: 'FAILED',
        message: err.message || 'Order ingestion failed.',
      });
    } finally {
      setIsSubmittingOrder(false);
    }
  };

  const handleRemoteSyncSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSyncingRemote(true);
    setExecutionResult(null);

    try {
      const res = await api.syncRemoteServer({
        source_type: remoteSync.source_type,
        remote_url: remoteSync.remote_url.trim() || undefined,
        api_key: remoteSync.api_key.trim() || undefined,
        days_back: Number(remoteSync.days_back),
      });

      setExecutionResult({
        status: res.status,
        message: res.message,
      });
      onSuccess();
    } catch (err: any) {
      setExecutionResult({
        status: 'FAILED',
        message: err.message || 'Remote server sync failed.',
      });
    } finally {
      setIsSyncingRemote(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xl max-w-lg w-full overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100">
              <Play className="w-4 h-4 fill-current" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Data Ingestion Center</h3>
              <p className="text-xs text-slate-500">CSV batches, live transactions, or remote server sync</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-3 border-b border-slate-100 flex items-center gap-4 bg-white overflow-x-auto">
          <button
            type="button"
            onClick={() => {
              setActiveTab('batch');
              setExecutionResult(null);
            }}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'batch'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>CSV Batch</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('manual');
              setExecutionResult(null);
            }}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'manual'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Direct Order</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('remote');
              setExecutionResult(null);
            }}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'remote'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>Remote Server Sync</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 max-h-[65vh] overflow-y-auto">
          {activeTab === 'batch' && (
            <>
              {/* File Selection */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Select Raw File (data/raw/)
                  </label>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading}
                    className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100/80 px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                  >
                    {isUploading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Upload className="w-3.5 h-3.5" />
                    )}
                    <span>Upload CSV</span>
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>

                {uploadError && (
                  <div className="mb-2 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
                    <span>{uploadError}</span>
                  </div>
                )}

                {isLoadingFiles ? (
                  <div className="flex items-center gap-2 text-xs text-slate-500 py-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Scanning raw files directory...</span>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto pr-1">
                    {files.map((file) => (
                      <label
                        key={file.filename}
                        className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all ${
                          selectedFile === file.filename
                            ? 'border-indigo-500 bg-indigo-50/50 text-indigo-950 font-medium'
                            : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="radio"
                            name="rawFile"
                            value={file.filename}
                            checked={selectedFile === file.filename}
                            onChange={(e) => setSelectedFile(e.target.value)}
                            className="text-indigo-600 focus:ring-indigo-500"
                          />
                          <FileText className="w-4 h-4 text-slate-400" />
                          <span className="text-xs font-mono">{file.filename}</span>
                        </div>
                        <span className="text-[11px] text-slate-400 font-normal">
                          {(file.size_bytes / 1024).toFixed(1)} KB
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Workflow Steps Preview */}
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/80 text-xs text-slate-600 space-y-1.5">
                <div className="font-semibold text-slate-800 text-[11px] uppercase tracking-wider">
                  Automated ETL Operations
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                    <span>Header verification</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                    <span>Quarantine check</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0" />
                    <span>Revenue calculation</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                    <span>Idempotent Upsert</span>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'manual' && (
            <form id="manual-order-form" onSubmit={handleManualOrderSubmit} className="space-y-3">
              <div className="p-3 bg-indigo-50/60 border border-indigo-100 rounded-xl text-xs text-indigo-900 leading-relaxed">
                Test real-time validation and upsert without uploading a file. If data violates business rules, it will be quarantined.
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Order ID
                  </label>
                  <input
                    type="text"
                    required
                    value={manualOrder.order_id}
                    onChange={(e) => setManualOrder({ ...manualOrder, order_id: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Order Date
                  </label>
                  <input
                    type="date"
                    required
                    value={manualOrder.order_date}
                    onChange={(e) => setManualOrder({ ...manualOrder, order_date: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Customer ID
                  </label>
                  <input
                    type="text"
                    required
                    value={manualOrder.customer_id}
                    onChange={(e) => setManualOrder({ ...manualOrder, customer_id: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Product Name
                  </label>
                  <input
                    type="text"
                    required
                    value={manualOrder.product}
                    onChange={(e) => setManualOrder({ ...manualOrder, product: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Category
                  </label>
                  <select
                    value={manualOrder.category}
                    onChange={(e) => setManualOrder({ ...manualOrder, category: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white"
                  >
                    <option value="Electronics">Electronics</option>
                    <option value="Accessories">Accessories</option>
                    <option value="Audio">Audio</option>
                    <option value="Furniture">Furniture</option>
                    <option value="Office Supplies">Office Supplies</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Region
                  </label>
                  <select
                    value={manualOrder.region}
                    onChange={(e) => setManualOrder({ ...manualOrder, region: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-white"
                  >
                    <option value="North">North</option>
                    <option value="South">South</option>
                    <option value="East">East</option>
                    <option value="West">West</option>
                    <option value="Central">Central</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    required
                    value={manualOrder.quantity}
                    onChange={(e) => setManualOrder({ ...manualOrder, quantity: Number(e.target.value) })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Unit Price ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={manualOrder.unit_price}
                    onChange={(e) => setManualOrder({ ...manualOrder, unit_price: Number(e.target.value) })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </form>
          )}

          {activeTab === 'remote' && (
            <form id="remote-sync-form" onSubmit={handleRemoteSyncSubmit} className="space-y-3.5">
              <div className="p-3 bg-sky-50/70 border border-sky-100 rounded-xl text-xs text-sky-900 leading-relaxed">
                Connect and sync records directly from an external production database or web REST server on demand.
              </div>

              {/* Source Type Selector */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1.5">
                  Remote Server Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <label
                    className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      remoteSync.source_type === 'db'
                        ? 'border-sky-500 bg-sky-50/60 font-semibold text-sky-950'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="sourceType"
                      value="db"
                      checked={remoteSync.source_type === 'db'}
                      onChange={() => setRemoteSync({ ...remoteSync, source_type: 'db' })}
                      className="text-sky-600 focus:ring-sky-500"
                    />
                    <Database className="w-3.5 h-3.5" />
                    <span>Remote Database</span>
                  </label>

                  <label
                    className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      remoteSync.source_type === 'api'
                        ? 'border-sky-500 bg-sky-50/60 font-semibold text-sky-950'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="sourceType"
                      value="api"
                      checked={remoteSync.source_type === 'api'}
                      onChange={() => setRemoteSync({ ...remoteSync, source_type: 'api' })}
                      className="text-sky-600 focus:ring-sky-500"
                    />
                    <Globe className="w-3.5 h-3.5" />
                    <span>Remote Web API</span>
                  </label>
                </div>
              </div>

              {remoteSync.source_type === 'db' ? (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                    Database Connection URL (Optional - defaults to .env REMOTE_DB_URL)
                  </label>
                  <input
                    type="text"
                    placeholder="postgresql://user:pass@host:5432/dbname"
                    value={remoteSync.remote_url}
                    onChange={(e) => setRemoteSync({ ...remoteSync, remote_url: e.target.value })}
                    className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    Supports PostgreSQL, MySQL, SQL Server, and SQLite URIs.
                  </span>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                      API Endpoint URL (Optional - defaults to .env REMOTE_API_URL)
                    </label>
                    <input
                      type="url"
                      placeholder="https://api.mycompany.com/v1/orders"
                      value={remoteSync.remote_url}
                      onChange={(e) => setRemoteSync({ ...remoteSync, remote_url: e.target.value })}
                      className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                      Bearer Token / API Key (Optional)
                    </label>
                    <input
                      type="password"
                      placeholder="••••••••••••••••"
                      value={remoteSync.api_key}
                      onChange={(e) => setRemoteSync({ ...remoteSync, api_key: e.target.value })}
                      className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-[11px] font-semibold text-slate-600 uppercase mb-1">
                  Days Back (Incremental Watermark)
                </label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  required
                  value={remoteSync.days_back}
                  onChange={(e) => setRemoteSync({ ...remoteSync, days_back: Number(e.target.value) })}
                  className="w-full text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Fetches records created or modified within the past N days.
                </span>
              </div>
            </form>
          )}

          {/* Execution Result Banner */}
          {executionResult && (
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 ${
                executionResult.status === 'SUCCESS'
                  ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
                  : 'bg-amber-50/80 border-amber-200 text-amber-800'
              }`}
            >
              {executionResult.status === 'SUCCESS' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              )}
              <div className="text-xs">
                <div className="font-semibold">{executionResult.message}</div>
                <div className="text-[11px] mt-0.5 opacity-80">
                  {executionResult.status === 'SUCCESS'
                    ? 'Database updated and charts refreshed in real-time.'
                    : 'Operation encountered an issue or records were quarantined.'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50">
          <button
            onClick={onClose}
            disabled={isRunning || isSubmittingOrder || isSyncingRemote}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          >
            Close
          </button>

          {activeTab === 'batch' && (
            <button
              onClick={handleRunBatch}
              disabled={isRunning || files.length === 0}
              className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 rounded-lg shadow-sm shadow-indigo-100 transition-all cursor-pointer"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Batch...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Pipeline</span>
                </>
              )}
            </button>
          )}

          {activeTab === 'manual' && (
            <button
              type="submit"
              form="manual-order-form"
              disabled={isSubmittingOrder}
              className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 rounded-lg shadow-sm shadow-emerald-100 transition-all cursor-pointer"
            >
              {isSubmittingOrder ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Validating & Upserting...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Transaction</span>
                </>
              )}
            </button>
          )}

          {activeTab === 'remote' && (
            <button
              type="submit"
              form="remote-sync-form"
              disabled={isSyncingRemote}
              className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-700 disabled:opacity-60 rounded-lg shadow-sm shadow-sky-100 transition-all cursor-pointer"
            >
              {isSyncingRemote ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Connecting & Syncing...</span>
                </>
              ) : (
                <>
                  <Server className="w-3.5 h-3.5" />
                  <span>Sync Remote Server</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
