import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading data from warehouse...',
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-500 space-y-3">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      <p className="text-xs font-medium tracking-wide">{message}</p>
    </div>
  );
};
