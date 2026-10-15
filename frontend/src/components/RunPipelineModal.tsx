import React, { useEffect, useState } from 'react';
import { X, Play, CheckCircle2, AlertTriangle, FileText, Loader2, Database, ShieldAlert } from 'lucide-react';
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
  const [files, setFiles] = useState<RawFileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('sales_sample.csv');
  const [isLoadingFiles, setIsLoadingFiles] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<{
    status: string;
    message: string;
  } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setExecutionResult(null);
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
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleRun = async () => {
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
              <h3 className="text-base font-bold text-slate-900">Trigger ETL Pipeline</h3>
              <p className="text-xs text-slate-500">Extract, validate, transform & load batch dataset</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* File Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Select Raw Source File (data/raw/)
            </label>
            {isLoadingFiles ? (
              <div className="flex items-center gap-2 text-xs text-slate-500 py-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Scanning raw files directory...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-2">
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
          <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 text-xs text-slate-600 space-y-2">
            <div className="font-semibold text-slate-800 text-[11px] uppercase tracking-wider">
              Pipeline Execution Sequence
            </div>
            <ul className="space-y-1.5 text-[11px] text-slate-600">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                <span>Extraction & required schema header verification</span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>Field-level quality checks & quarantine categorization</span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                <span>Date parsing, numeric normalization & revenue calculation</span>
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                <span>Idempotent Upsert into PostgreSQL (preventing duplicates)</span>
              </li>
            </ul>
          </div>

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
                  Data warehouse and analytics have been updated.
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-end gap-3 bg-slate-50/50">
          <button
            onClick={onClose}
            disabled={isRunning}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
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
        </div>
      </div>
    </div>
  );
};
