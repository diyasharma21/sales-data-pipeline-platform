import React from 'react';
import {
  BarChart3,
  TrendingUp,
  Activity,
  ShieldCheck,
  Database,
  Layers,
  Sparkles,
} from 'lucide-react';

export type PageId = 'overview' | 'analytics' | 'pipeline' | 'quality' | 'database';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  databaseDialect?: string;
  isDbConnected?: boolean;
}

const navItems = [
  { id: 'overview' as PageId, label: 'Overview', icon: BarChart3, desc: 'Executive KPI Summary' },
  { id: 'analytics' as PageId, label: 'Sales Analytics', icon: TrendingUp, desc: 'Revenue & Trends' },
  { id: 'pipeline' as PageId, label: 'Pipeline Monitor', icon: Activity, desc: 'ETL Execution Lineage' },
  { id: 'quality' as PageId, label: 'Data Quality', icon: ShieldCheck, desc: 'Quarantine & Auditing' },
  { id: 'database' as PageId, label: 'Database Explorer', icon: Database, desc: 'Read-only Warehouse Grid' },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  databaseDialect = 'PostgreSQL',
  isDbConnected = true,
}) => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200/90 flex flex-col justify-between shrink-0 min-h-screen">
      <div>
        {/* Brand Header */}
        <div className="p-6 border-b border-slate-100 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-100">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-base text-slate-900 tracking-tight flex items-center gap-1.5">
              SalesEngine
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                PRO
              </span>
            </h1>
            <p className="text-xs text-slate-500 font-medium">Data Platform</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Core Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onSelectPage(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm transition-all duration-150 text-left ${
                  isActive
                    ? 'bg-indigo-50/90 text-indigo-700 font-semibold border border-indigo-200/80 shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100/70 hover:text-slate-900 font-medium'
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-indigo-600' : 'text-slate-400'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Connection Status */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50">
        <div className="bg-white rounded-lg p-3 border border-slate-200/80 shadow-2xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-slate-500">Warehouse</span>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isDbConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              <span className="text-xs font-semibold text-slate-700 capitalize">
                {databaseDialect}
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>ETL Architecture</span>
            <span className="font-mono text-slate-600 font-medium">v2.0</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
