"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";
import AuthGuard from "../AuthGuard";
import { TradingBackground } from "../TradingBackground";
import SymbolTopNav from "../SymbolTopNav";
import LivePriceBar from "../price/LivePriceBar";
import MetaSignalCard from "../meta/MetaSignalCard";
import SharedChart from "../chart/SharedChart";
import SignalGrid from "../signals/SignalGrid";
import ContextCards from "../context/ContextCards";
import PerformanceScoreboard from "../performance/PerformanceScoreboard";
import type { SymbolConfig } from "../../lib/symbolConfig";

const ClearTrendPanelV3 = dynamic(() => import("../panels/ClearTrendPanelV3"), { ssr: false });

interface Props {
  config: SymbolConfig;
}

function Section({
  title,
  subtitle,
  children,
  delay = 0,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay, ease: "easeOut" }}
      className="flex flex-col gap-3"
    >
      <div>
        <h2 className="text-lg font-bold text-white">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      {children}
    </motion.section>
  );
}

function SymbolPageInner({ config }: Props) {
  return (
    <div className="relative min-h-screen overflow-x-hidden text-slate-100">
      <TradingBackground />
      <SymbolTopNav />

      <div className="relative z-10 mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-3 py-4 sm:px-4 md:px-6 md:py-6 lg:px-8">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Link href="/" className="inline-flex items-center gap-1 hover:text-slate-300">
            <ArrowLeft className="h-3.5 w-3.5" /> Dashboard
          </Link>
          <span>/</span>
          <span className="text-slate-300">{config.label}</span>
        </div>

        {/* Section 1 — Top bar: price + meta signal */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
          <LivePriceBar config={config} />
          <MetaSignalCard symbol={config.symbol} />
        </div>

        {/* Section 2 — Chart group: SharedChart + Clear Trend (full-size) */}
        <Section title="Chart & Trend" subtitle="Multi-timeframe candles · ICT clear-trend analysis" delay={0.05}>
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <SharedChart symbol={config.symbol} defaultTimeframe="1h" height={560} />
            <div className="rounded-2xl border border-cyan-500/20 bg-slate-950/70 backdrop-blur-sm">
              <ClearTrendPanelV3 symbol={config.symbol} />
            </div>
          </div>
        </Section>

        {/* Section 3 — Signal grid, full panel heights */}
        <Section title="Signal Models" subtitle="6 models · weighted ensemble" delay={0.1}>
          <SignalGrid symbol={config.symbol} symbolLabel={config.label} />
        </Section>

        {/* Section 4 — Market context */}
        <Section title="Market Context" subtitle="Smart money flow · AI analysis" delay={0.15}>
          <ContextCards symbol={config.symbol} symbolLabel={config.label} />
        </Section>

        {/* Section 5 — Performance scoreboard */}
        <Section title="Model Performance" subtitle="Last 30 days · win rates & volume" delay={0.2}>
          <PerformanceScoreboard symbol={config.symbol} days={30} />
        </Section>
      </div>
    </div>
  );
}

export function SymbolPage({ config }: Props) {
  return (
    <AuthGuard>
      <SymbolPageInner config={config} />
    </AuthGuard>
  );
}

export default SymbolPage;
