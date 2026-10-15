import React from 'react';
import { Play, RotateCw } from 'lucide-react';
import { PageId } from './Sidebar';

interface HeaderProps {
  currentPage: PageId;
  onRefresh: () => void;
  onOpenRunModal: () => void;
  isRefreshing?: boolean;
}

const pageDetails: Record<PageId, { title: string; desc: string }> = {
  overview: {
    title: 'Platform Overview',
    desc: 'Executive performance KPIs, revenue distribution, and operational metrics.',
  },
  analytics: {
    title: 'Sales & Revenue Analytics',
    desc: 'Deep-dive analytical aggregations, product performance, and searchable order records.',
  },
  pipeline: {
    title: 'Pipeline Monitoring',
    desc: 'ETL execution lineage, historical batch runs, error auditing, and manual trigger controls.',
  },
  quality: {
    title: 'Data Quality & Quarantine',
    desc: 'Data validation pass rate, error code distributions, and quarantined anomaly inspection.',
  },
  database: {
    title: 'Database Explorer',
    desc: 'Read-only relational table inspection, schema definitions, and parameterized pagination.',
  },
};

export const Header: React.FC<HeaderProps> = ({
  currentPage,
  onRefresh,
  onOpenRunModal,
  isRefreshing = false,
}) => {
  const current = pageDetails[currentPage];

  return (
    <header className="bg-white border-b border-slate-200/90 px-8 py-5 flex items-center justify-between sticky top-0 z-20 shadow-2xs">
      <div>
        <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
          <span>Platform</span>
          <span>/</span>
          <span className="text-indigo-600 font-semibold capitalize">{currentPage}</span>
        </div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">{current.title}</h2>
        <p className="text-xs text-slate-500 mt-0.5">{current.desc}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors disabled:opacity-50 cursor-pointer"
          title="Refresh metrics from warehouse"
        >
          <RotateCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-indigo-600' : ''}`} />
          <span>Refresh</span>
        </button>

        {/* Run Pipeline Button */}
        <button
          onClick={onOpenRunModal}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm shadow-indigo-100 transition-all hover:shadow-md cursor-pointer active:scale-98"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Run Pipeline</span>
        </button>
      </div>
    </header>
  );
};
