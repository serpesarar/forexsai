"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { Lock, Crown, Sparkles, ArrowRight } from "lucide-react";
import { useIsPro, useIsAuthenticated } from "@/lib/auth/store";

interface ProFeatureGateProps {
  children: ReactNode;
  feature?: string;
  showPreview?: boolean;
  blurContent?: boolean;
  compact?: boolean;
}

export function ProFeatureGate({
  children,
  feature = "Bu özellik",
  showPreview = true,
  blurContent = true,
  compact = false,
}: ProFeatureGateProps) {
  const isPro = useIsPro();
  const isAuthenticated = useIsAuthenticated();

  // Pro users see content directly
  if (isPro) {
    return <>{children}</>;
  }

  // Compact version for inline usage
  if (compact) {
    return (
      <div className="relative">
        {showPreview && (
          <div className={blurContent ? "blur-sm pointer-events-none select-none" : "opacity-50 pointer-events-none"}>
            {children}
          </div>
        )}
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm rounded-xl">
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 border border-purple-500/30">
            <Lock className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-purple-300">Pro üyelik gerekli</span>
          </div>
        </div>
      </div>
    );
  }

  // Full overlay version
  return (
    <div className="relative">
      {showPreview && (
        <div className={blurContent ? "blur-sm pointer-events-none select-none" : "opacity-30 pointer-events-none"}>
          {children}
        </div>
      )}
      
      {/* Overlay */}
      <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90 backdrop-blur-md rounded-xl">
        <div className="text-center p-6 max-w-sm">
          {/* Icon */}
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 flex items-center justify-center">
            <Crown className="w-8 h-8 text-purple-400" />
          </div>

          {/* Title */}
          <h3 className="text-xl font-bold text-white mb-2">
            Pro Üyelik Gerekli
          </h3>

          {/* Description */}
          <p className="text-slate-400 mb-6">
            {feature} sadece <span className="text-purple-300 font-medium">Pro üyeler</span> için kullanılabilir.
          </p>

          {/* Features hint */}
          <div className="space-y-2 mb-6 text-left">
            {[
              "Claude AI haber analizi",
              "Günlük 50 AI analiz hakkı",
              "Gelişmiş pattern tanıma",
              "Öncelikli destek",
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-slate-300">
                <Sparkles className="w-4 h-4 text-purple-400 shrink-0" />
                {item}
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="space-y-3">
            {isAuthenticated ? (
              <Link
                href="/upgrade"
                className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold flex items-center justify-center gap-2 transition-all group"
              >
                Pro'ya Yükselt
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            ) : (
              <>
                <Link
                  href="/signup"
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold flex items-center justify-center gap-2 transition-all group"
                >
                  Ücretsiz Kayıt Ol
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  href="/login"
                  className="block text-sm text-slate-400 hover:text-white transition-colors"
                >
                  Zaten hesabın var mı? Giriş yap
                </Link>
              </>
            )}
          </div>

          {/* Referral hint */}
          <p className="mt-4 text-xs text-slate-500">
            💡 5 arkadaş davet et, 1 hafta Pro ücretsiz!
          </p>
        </div>
      </div>
    </div>
  );
}

// Simpler inline badge for showing pro requirement
export function ProBadge({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30 ${className}`}>
      <Crown className="w-3 h-3" />
      Pro
    </span>
  );
}

// Lock icon for disabled buttons
export function ProLockIcon({ size = 16 }: { size?: number }) {
  return (
    <div className="relative">
      <Lock style={{ width: size, height: size }} className="text-purple-400" />
    </div>
  );
}

// HOC for wrapping entire panels
export function withProGate<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  featureName: string
) {
  return function ProGatedComponent(props: P) {
    return (
      <ProFeatureGate feature={featureName}>
        <WrappedComponent {...props} />
      </ProFeatureGate>
    );
  };
}

export default ProFeatureGate;
