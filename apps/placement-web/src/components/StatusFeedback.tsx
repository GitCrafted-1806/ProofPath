"use client";

import React from "react";
import { AlertCircle, RefreshCw, Inbox, Loader2 } from "lucide-react";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  title?: string;
}

export function ErrorState({
  message,
  onRetry,
  title = "Unable to load data",
}: ErrorStateProps) {
  return (
    <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 my-4 text-slate-200">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
        <div className="flex-1">
          <h4 className="font-semibold text-rose-300 text-sm">{title}</h4>
          <p className="text-xs text-rose-200/80 mt-1 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-medium border border-rose-500/30 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading data from backend..." }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
      <p className="text-sm text-slate-400 font-medium">{message}</p>
      <p className="text-xs text-slate-500 mt-1">Connecting to ProofPath FastAPI engine</p>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-xl border border-dashed border-[#1F293D] bg-[#131926]/50 my-4">
      <div className="w-12 h-12 rounded-full bg-[#1B2336] flex items-center justify-center text-slate-400 mb-4">
        <Inbox className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <p className="text-xs text-slate-400 max-w-md mt-1 mb-4">{description}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
