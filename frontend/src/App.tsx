import React, { useEffect, useState } from 'react';
import { Sidebar, PageId } from './components/Sidebar';
import { Header } from './components/Header';
import { RunPipelineModal } from './components/RunPipelineModal';
import { OverviewPage } from './pages/OverviewPage';
import { SalesAnalyticsPage } from './pages/SalesAnalyticsPage';
import { PipelineMonitoringPage } from './pages/PipelineMonitoringPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { DatabaseExplorerPage } from './pages/DatabaseExplorerPage';
import { api } from './api';
import { HealthStatus } from './types';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isRunModalOpen, setIsRunModalOpen] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const fetchHealth = () => {
    api
      .getHealth()
      .then(setHealth)
      .catch((err) => console.error('Health check failed:', err));
  };

  useEffect(() => {
    fetchHealth();
  }, [refreshKey]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setRefreshKey((k) => k + 1);
    fetchHealth();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  const handlePipelineSuccess = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Sidebar Navigation */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        databaseDialect={health?.database_dialect || 'PostgreSQL'}
        isDbConnected={health?.database_connected ?? true}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          currentPage={currentPage}
          onRefresh={handleRefresh}
          onOpenRunModal={() => setIsRunModalOpen(true)}
          isRefreshing={isRefreshing}
        />

        <main className="p-8 max-w-7xl w-full mx-auto flex-1">
          {currentPage === 'overview' && <OverviewPage refreshKey={refreshKey} />}
          {currentPage === 'analytics' && <SalesAnalyticsPage refreshKey={refreshKey} />}
          {currentPage === 'pipeline' && (
            <PipelineMonitoringPage
              refreshKey={refreshKey}
              onRunTriggered={handlePipelineSuccess}
            />
          )}
          {currentPage === 'quality' && <DataQualityPage refreshKey={refreshKey} />}
          {currentPage === 'database' && <DatabaseExplorerPage refreshKey={refreshKey} />}
        </main>
      </div>

      {/* Modal for executing pipeline */}
      <RunPipelineModal
        isOpen={isRunModalOpen}
        onClose={() => setIsRunModalOpen(false)}
        onSuccess={handlePipelineSuccess}
      />
    </div>
  );
};

export default App;
