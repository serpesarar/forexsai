"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: React.ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class PanelErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[PanelErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 flex flex-col items-center justify-center gap-3 min-h-[120px]">
          <AlertTriangle className="w-6 h-6 text-red-400" />
          <p className="text-sm text-red-300">
            {this.props.fallbackMessage || "Bu panel yüklenirken hata oluştu"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs text-white/70 transition"
          >
            <RefreshCw className="w-3 h-3" />
            Tekrar Dene
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
