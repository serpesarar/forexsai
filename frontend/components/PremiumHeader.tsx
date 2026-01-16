"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  PlayCircle,
  RefreshCw,
  Sun,
  Moon,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Sparkles,
} from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";

interface MarketTicker {
  label: string;
  price: string;
  change: string;
  trend: "up" | "down";
}

interface PremiumHeaderProps {
  marketTickers: MarketTicker[];
  theme: "evening" | "morning";
  setTheme: (theme: "evening" | "morning") => void;
  autoRefresh: boolean;
  toggleAutoRefresh: (checked: boolean) => void;
  isLoading: boolean;
  fetchAll: () => void;
  t: (key: string) => string;
}

export default function PremiumHeader({
  marketTickers,
  theme,
  setTheme,
  autoRefresh,
  toggleAutoRefresh,
  isLoading,
  fetchAll,
  t,
}: PremiumHeaderProps) {
  const headerRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [glowIntensity, setGlowIntensity] = useState(0);
  const [time, setTime] = useState(new Date());

  // Mouse tracking for spotlight effect
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!headerRef.current) return;
    const rect = headerRef.current.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }, []);

  // Pulse glow animation
  useEffect(() => {
    const interval = setInterval(() => {
      setGlowIntensity((prev) => (prev + 0.02) % 1);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Live clock
  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const pulseGlow = 0.3 + Math.sin(glowIntensity * Math.PI * 2) * 0.2;

  return (
    <header
      ref={headerRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className="relative overflow-hidden border-b border-white/10"
      style={{
        background: `
          radial-gradient(
            600px circle at ${mousePosition.x}px ${mousePosition.y}px,
            rgba(192, 192, 192, ${isHovering ? 0.08 : 0}),
            transparent 40%
          ),
          linear-gradient(
            180deg,
            rgba(15, 15, 25, 0.95) 0%,
            rgba(10, 10, 18, 0.98) 100%
          )
        `,
      }}
    >
      {/* Animated gradient border top */}
      <div className="absolute top-0 left-0 right-0 h-[2px] overflow-hidden">
        <div
          className="absolute inset-0 animate-gradient-x"
          style={{
            background: `linear-gradient(90deg, 
              transparent 0%, 
              rgba(192, 192, 192, ${pulseGlow}) 25%, 
              rgba(147, 112, 219, ${pulseGlow}) 50%, 
              rgba(192, 192, 192, ${pulseGlow}) 75%, 
              transparent 100%
            )`,
            backgroundSize: "200% 100%",
          }}
        />
      </div>

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 rounded-full bg-white/20 animate-float"
            style={{
              left: `${15 + i * 15}%`,
              animationDelay: `${i * 0.5}s`,
              animationDuration: `${3 + i * 0.5}s`,
            }}
          />
        ))}
      </div>

      {/* Main content */}
      <div className="relative mx-auto flex h-[72px] max-w-7xl items-center justify-between px-6">
        {/* Logo & Title - Premium style */}
        <div className="flex items-center gap-4 group">
          <div className="relative">
            {/* Outer glow ring */}
            <div
              className="absolute -inset-1 rounded-xl opacity-75 blur-sm transition-all duration-500 group-hover:opacity-100 group-hover:blur-md"
              style={{
                background: `linear-gradient(135deg, rgba(192,192,192,${pulseGlow * 0.5}) 0%, rgba(147,112,219,${pulseGlow * 0.5}) 100%)`,
              }}
            />
            {/* Icon container */}
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/10 shadow-lg transition-transform duration-300 group-hover:scale-110">
              <Activity className="h-5 w-5 text-silver animate-pulse" style={{ color: '#C0C0C0' }} />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                {t("header.title")}
              </h1>
              <Sparkles className="h-3.5 w-3.5 text-purple-400 animate-pulse" />
            </div>
            <p className="text-[10px] uppercase tracking-[0.4em] text-gray-500 font-medium">
              {t("header.subtitle")}
            </p>
          </div>
        </div>

        {/* Market Tickers - Animated cards */}
        <div className="hidden lg:flex items-center gap-4">
          {marketTickers.map((ticker, index) => (
            <div
              key={ticker.label}
              className="group relative"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Hover glow */}
              <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-white/5 to-purple-500/5 opacity-0 group-hover:opacity-100 blur transition-all duration-300" />
              
              <div className="relative flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2 backdrop-blur-sm transition-all duration-300 group-hover:border-white/20 group-hover:bg-white/[0.05]">
                {/* Mini trend indicator */}
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                  ticker.trend === "up" 
                    ? "bg-emerald-500/10 text-emerald-400" 
                    : "bg-red-500/10 text-red-400"
                }`}>
                  {ticker.trend === "up" ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                </div>
                
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase tracking-wider text-gray-500 font-medium">
                    {ticker.label}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold text-white">
                      ${ticker.price}
                    </span>
                    <span
                      className={`font-mono text-xs font-bold px-1.5 py-0.5 rounded ${
                        ticker.trend === "up"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {ticker.change}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Actions - Premium buttons */}
        <div className="flex items-center gap-3">
          {/* AI Trading Panel - Premium Link */}
          <Link
            href="/trading"
            className="group relative overflow-hidden rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-300"
          >
            {/* Animated gradient background */}
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 via-pink-500/20 to-purple-600/20 animate-gradient-x" />
            <div className="absolute inset-0 border border-purple-500/30 rounded-xl group-hover:border-purple-400/50 transition-colors" />
            {/* Shine effect on hover */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
              <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            </div>
            <span className="relative flex items-center gap-2 text-purple-300 group-hover:text-purple-200">
              <BarChart3 className="h-4 w-4" />
              AI Trading Panel
            </span>
          </Link>

          {/* Run Analysis - Premium Button */}
          <button
            onClick={fetchAll}
            disabled={isLoading}
            className="group relative overflow-hidden rounded-xl px-5 py-2.5 text-xs font-bold uppercase tracking-wider transition-all duration-300"
          >
            {/* Glowing background */}
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 via-teal-500 to-emerald-600 animate-gradient-x" />
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-600 to-teal-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            {/* Inner glow */}
            <div className="absolute inset-[1px] rounded-[10px] bg-gradient-to-b from-white/20 to-transparent opacity-50" />
            {/* Pulse ring */}
            <div className="absolute -inset-1 rounded-xl bg-emerald-500/30 blur-md opacity-0 group-hover:opacity-100 animate-pulse transition-opacity" />
            
            <span className="relative flex items-center gap-2 text-white">
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              {isLoading ? t("common.running") : t("common.runAnalysis")}
            </span>
          </button>

          {/* Theme Toggle - Minimal */}
          <button
            onClick={() => setTheme(theme === "evening" ? "morning" : "evening")}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.02] text-gray-400 transition-all duration-300 hover:border-white/20 hover:bg-white/[0.05] hover:text-white"
          >
            {theme === "evening" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>

          {/* Language Switcher */}
          <LanguageSwitcher />

          {/* Auto Refresh & Live Status */}
          <div className="hidden md:flex items-center gap-4 pl-3 border-l border-white/10">
            <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer group">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => toggleAutoRefresh(e.target.checked)}
                  className="peer sr-only"
                />
                <div className="h-5 w-9 rounded-full bg-gray-700 peer-checked:bg-emerald-600 transition-colors" />
                <div className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform peer-checked:translate-x-4" />
              </div>
              <span className="group-hover:text-gray-300 transition-colors">
                {t("common.auto30s")}
              </span>
            </label>

            {/* Live indicator */}
            <div className="flex items-center gap-2 text-xs">
              <div className="relative">
                <div className="h-2 w-2 rounded-full bg-emerald-500" />
                <div className="absolute inset-0 h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
              </div>
              <span className="text-emerald-400 font-medium">{t("common.live")}</span>
            </div>

            {/* Clock */}
            <div className="flex items-center gap-1.5 text-xs text-gray-500 font-mono">
              <Clock className="h-3.5 w-3.5" />
              {time.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </header>
  );
}
