"use client";

import { Component, ReactNode } from "react";
import { AlertCircle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      return (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
          <AlertCircle className="w-10 h-10 mx-auto mb-3 text-red-400" />
          <h3 className="text-sm font-medium text-white mb-2">
            Bir hata oluştu
          </h3>
          <p className="text-xs text-slate-400 mb-3">
            {this.state.error?.message || "Bilinmeyen hata"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs rounded-lg transition"
          >
            Tekrar Dene
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
