"use client";

import Link from "next/link";
import { Brain, LineChart, BarChart3, Activity, Zap } from "lucide-react";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { useI18nStore } from "../lib/i18n/store";

interface SharedNavHeaderProps {
  activePage: "dashboard" | "charts" | "trading" | "analysis" | "signals";
  /** Content rendered in center of top row (e.g. market tickers) */
  centerContent?: React.ReactNode;
  /** Content rendered on right side of top row (e.g. theme toggle, auto-refresh, user menu) */
  rightContent?: React.ReactNode;
  /** Content rendered on right side of bottom nav row (e.g. CTA button) */
  bottomRightContent?: React.ReactNode;
}

export default function SharedNavHeader({ activePage, centerContent, rightContent, bottomRightContent }: SharedNavHeaderProps) {
  const { t } = useI18nStore();

  const navItems = [
    { href: "/", key: "dashboard" as const, label: "Dashboard", icon: Brain, iconColor: "text-blue-400" },
    { href: "/charts", key: "charts" as const, label: t("nav.charts"), icon: LineChart, iconColor: "text-emerald-400" },
    { href: "/trading", key: "trading" as const, label: "AI Trading", icon: BarChart3, iconColor: "text-purple-400" },
    { href: "/analysis", key: "analysis" as const, label: "Analysis", icon: Brain, iconColor: "text-amber-400" },
    { href: "/signals", key: "signals" as const, label: "Detailed Signals", icon: Zap, iconColor: "text-red-400" },
  ];

  return (
    <header className="sticky top-0 z-50">
      {/* Background Container with Glassmorphism */}
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xl border-b border-white/5 shadow-2xl" />

      {/* Neon Mesh Gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-50%] left-[10%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] opacity-70" />
        <div className="absolute top-[-50%] right-[10%] w-[400px] h-[400px] bg-purple-600/20 rounded-full blur-[100px] opacity-60" />
      </div>

      {/* Animated Top Border */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />

      {/* ─────────────── TOP ROW: Brand + Tickers + Right Actions ─────────────── */}
      <div className="relative border-b border-white/5">
        <div className="mx-auto max-w-[1920px] px-6">
          <div className="flex h-20 items-center justify-between">

            {/* Modern Brand Section */}
            <div className="flex items-center gap-4 min-w-[240px]">
              <Link href="/" className="group flex items-center gap-3 relative">
                <div className="relative w-10 h-10 flex items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-[0_0_15px_rgba(37,99,235,0.4)] group-hover:shadow-[0_0_25px_rgba(37,99,235,0.6)] transition-all duration-300 transform group-hover:scale-105">
                  <Activity className="text-white w-6 h-6 relative z-10" />
                  <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="flex flex-col justify-center">
                  <h1 className="text-xl font-black tracking-tight text-white leading-none font-sans">
                    FOREXS<span className="text-blue-500">AI</span>
                  </h1>
                  <p className="text-[10px] font-bold text-slate-400 tracking-[0.2em] uppercase leading-none mt-1 group-hover:text-blue-400 transition-colors">
                    Intelligence
                  </p>
                </div>
              </Link>
            </div>

            {/* Center Content (Injected Tickers) */}
            <div className="flex-1 flex justify-center px-4">
              {centerContent}
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4 min-w-[240px] justify-end">
              {rightContent}
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────── BOTTOM ROW: Nav + CTA ─────────────── */}
      <div className="relative bg-white/[0.01]">
        <div className="mx-auto max-w-[1920px] px-6">
          <div className="flex h-12 items-center justify-between">

            {/* Modern Tabs */}
            <div className="flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = item.key === activePage;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    className={`relative flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-300 group overflow-hidden ${isActive
                      ? "text-white bg-white/10 shadow-[0_0_10px_rgba(255,255,255,0.05)]"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                      }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? item.iconColor : "text-slate-500 group-hover:text-slate-300"}`} />
                    <span>{item.label}</span>
                    {isActive && (
                      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-blue-500 to-transparent" />
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Bottom Right CTA */}
            <div>
              {bottomRightContent}
            </div>

          </div>
        </div>
      </div>
    </header>
  );
}
