"use client";

import Link from "next/link";
import { Brain, LineChart, BarChart3 } from "lucide-react";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { useI18nStore } from "../lib/i18n/store";

interface SharedNavHeaderProps {
  activePage: "dashboard" | "charts" | "trading";
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
    { href: "/", key: "dashboard" as const, label: "Dashboard", icon: Brain, iconColor: "text-accent" },
    { href: "/charts", key: "charts" as const, label: t("nav.charts"), icon: LineChart, iconColor: "text-blue-400" },
    { href: "/trading", key: "trading" as const, label: "AI Trading", icon: BarChart3, iconColor: "text-purple-400" },
  ];

  return (
    <header className="sticky top-0 z-50 relative">
      {/* Animated mesh background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(139,92,246,0.15),transparent_50%),radial-gradient(ellipse_at_bottom_right,rgba(6,182,212,0.1),transparent_50%)]" />
      <div className="absolute inset-0 bg-gradient-to-b from-black/90 via-slate-900/95 to-slate-900/98 backdrop-blur-xl" />

      {/* Animated top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-accent to-transparent animate-pulse" />
        <div className="absolute inset-0 bg-gradient-to-r from-accent via-purple-500 to-cyan-400 animate-gradient-x" style={{ animationDuration: '3s' }} />
      </div>

      {/* ─────────────── TOP ROW: Brand + Tickers + Status ─────────────── */}
      <div className="relative border-b border-white/[0.06]">
        <div className="mx-auto max-w-[1600px] px-4 md:px-6 lg:px-8">
          <div className="flex h-16 md:h-20 items-center justify-between">

            {/* Brand Section */}
            <div className="flex items-center gap-5">
              {/* Logo */}
              <div className="relative group">
                <div className="absolute -inset-2 rounded-2xl bg-gradient-to-r from-accent/30 via-purple-500/20 to-cyan-400/30 blur-lg opacity-0 group-hover:opacity-100 transition-all duration-500" />
                <div className="relative h-11 w-11 md:h-12 md:w-12 rounded-xl overflow-hidden border border-white/10 bg-white/5 shadow-lg">
                  <img src="/bu.png" alt="ForexsAI" className="w-full h-full object-cover" />
                </div>
              </div>

              {/* Title */}
              <div>
                <h1 className="text-xl md:text-2xl font-black tracking-tight">
                  <span className="bg-gradient-to-r from-white via-white to-white/80 bg-clip-text text-transparent">AI Trading</span>
                  <span className="bg-gradient-to-r from-accent to-cyan-400 bg-clip-text text-transparent ml-2">Dashboard</span>
                </h1>
                <div className="flex items-center gap-3 mt-0.5">
                  <span className="text-[10px] md:text-xs font-semibold uppercase tracking-[0.2em] text-white/40">Quantitative Analysis</span>
                  <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-success/20 border border-success/30">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-success"></span>
                    </span>
                    <span className="text-[10px] font-bold text-success uppercase tracking-wider">Live</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Center Content (Market Tickers etc.) */}
            {centerContent}

            {/* Right Section - Quick Actions */}
            <div className="flex items-center gap-2">
              {rightContent}
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </div>

      {/* ─────────────── BOTTOM ROW: Navigation + CTA ─────────────── */}
      <div className="relative bg-gradient-to-r from-white/[0.02] via-white/[0.04] to-white/[0.02]">
        <div className="mx-auto max-w-[1600px] px-4 md:px-6 lg:px-8">
          <div className="flex h-12 md:h-14 items-center justify-between">

            {/* Navigation Tabs */}
            <div className="flex items-center gap-0.5 md:gap-1">
              {navItems.map((item) => {
                const isActive = item.key === activePage;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    className={`flex items-center gap-1.5 md:gap-2 px-2.5 md:px-4 py-1.5 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-all ${
                      isActive
                        ? "bg-white/10 border border-white/10 text-white"
                        : "text-white/60 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <Icon className={`h-3.5 w-3.5 md:h-4 md:w-4 ${isActive ? item.iconColor : ""}`} />
                    <span className="hidden sm:inline">{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* Right side of nav row (CTA button or mobile live indicator) */}
            {bottomRightContent || (
              <div className="flex md:hidden items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 border border-success/20">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-success"></span>
                </span>
                <span className="text-[10px] font-bold text-success">LIVE</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom glow line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
    </header>
  );
}
