"use client";

import { useRef, useState, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  RefreshCw,
  Sun,
  Moon,
  Clock,
  TrendingUp,
  TrendingDown,
  Zap,
  Menu,
  Bell,
  Search,
  User,
  ChevronDown,
} from "lucide-react";
import { LanguageSwitcher } from "./LanguageSwitcher";

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
  const [time, setTime] = useState<Date | null>(null);
  const [scrolled, setScrolled] = useState(false);

  // Live clock
  useEffect(() => {
    setTime(new Date());
    const interval = setInterval(() => setTime(new Date()), 1000);
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => {
      clearInterval(interval);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <>
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${scrolled ? "h-[70px] bg-slate-950/80 backdrop-blur-xl border-b border-white/5" : "h-[80px] bg-transparent border-b border-transparent"
          }`}
      >
        {/* Background Gradient Mesh (Subtle) */}
        {!scrolled && (
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-[-50%] left-[20%] w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px]" />
            <div className="absolute top-[-50%] right-[20%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[100px]" />
          </div>
        )}

        <div className="relative mx-auto flex h-full max-w-[1920px] items-center justify-between px-6 lg:px-8">

          {/* LEFT: Logo & Brand */}
          <div className="flex items-center gap-8">
            <Link href="/" className="group flex items-center gap-3 relative">
              {/* Logo Icon */}
              <div className="relative w-10 h-10 flex items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-[0_0_20px_rgba(37,99,235,0.3)] group-hover:shadow-[0_0_30px_rgba(37,99,235,0.5)] transition-all duration-300 transform group-hover:scale-105">
                <Activity className="text-white w-6 h-6" />
                <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              {/* Brand Text */}
              <div className="flex flex-col justify-center">
                <h1 className="text-xl font-black tracking-tight text-white leading-none font-sans">
                  FOREXS<span className="text-blue-500">AI</span>
                </h1>
                <p className="text-[10px] font-medium text-slate-400 tracking-[0.2em] uppercase leading-none mt-1 group-hover:text-blue-400 transition-colors">
                  Intelligence
                </p>
              </div>
            </Link>

            {/* Quick Stats / Tickers (Desktop) */}
            <div className="hidden xl:flex items-center gap-3">
              <div className="h-8 w-px bg-white/10 mx-2" />
              {marketTickers.slice(0, 3).map((ticker, i) => (
                <div key={i} className="group relative flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900/50 border border-white/5 hover:border-blue-500/30 hover:bg-slate-800/80 transition-all duration-300">
                  <div className={`p-1.5 rounded-lg ${ticker.trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {ticker.trend === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  </div>
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-xs font-bold text-slate-300">{ticker.label}</span>
                      <span className="text-xs font-mono text-white">{ticker.price}</span>
                    </div>
                    <span className={`text-[10px] font-bold ${ticker.trend === 'up' ? 'text-emerald-500' : 'text-red-500'}`}>
                      {ticker.change}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CENTER: Search Bar (Optional/Fake) or Navigation */}
          <div className="hidden md:flex items-center absolute left-1/2 transform -translate-x-1/2">
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full opacity-20 group-hover:opacity-50 blur transition duration-500" />
              <div className="relative flex items-center bg-slate-900 border border-white/10 rounded-full px-4 py-2 w-[300px] focus-within:w-[400px] focus-within:border-blue-500/50 transition-all duration-300">
                <Search className="w-4 h-4 text-slate-500 mr-2" />
                <input
                  type="text"
                  placeholder="Sembol, Parite veya Haber Ara..."
                  className="bg-transparent border-none outline-none text-sm text-white w-full placeholder:text-slate-600"
                />
                <div className="text-[10px] font-mono text-slate-600 border border-slate-700 rounded px-1.5 py-0.5">⌘K</div>
              </div>
            </div>
          </div>

          {/* RIGHT: Actions */}
          <div className="flex items-center gap-4">

            {/* RUN ANALYSIS BUTTON - HERO */}
            <button
              onClick={fetchAll}
              disabled={isLoading}
              className="group relative flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-sm shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)] transition-all duration-300 active:scale-95 disabled:opacity-50 disabled:pointer-events-none overflow-hidden"
            >
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-[200%] h-full bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-[-20deg] translate-x-[-150%] group-hover:animate-shine" />
              </div>
              {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4 fill-white" />}
              <span>{isLoading ? "ANALİZ YAPILIYOR..." : "YAPAY ZEKA ANALİZİ"}</span>
            </button>

            <div className="h-6 w-px bg-white/10 mx-1" />

            {/* Theme & Notifications */}
            <button onClick={() => setTheme(theme === 'evening' ? 'morning' : 'evening')} className="p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
              {theme === 'evening' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button className="relative p-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-slate-950" />
            </button>

            {/* User Profile */}
            <div className="flex items-center gap-3 pl-2 cursor-pointer group">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-bold text-white group-hover:text-blue-400 transition-colors">Demo Trader</div>
                <div className="text-[10px] text-emerald-400 font-medium bg-emerald-500/10 px-1.5 rounded inline-block">PRO PLAN</div>
              </div>
              <div className="relative w-10 h-10 rounded-full bg-gradient-to-b from-slate-700 to-slate-800 border border-white/10 flex items-center justify-center overflow-hidden">
                <User className="text-slate-300 w-5 h-5" />
                <div className="absolute inset-0 border-2 border-transparent group-hover:border-blue-500/50 rounded-full transition-colors" />
              </div>
              <ChevronDown size={14} className="text-slate-500 group-hover:text-white transition-colors" />
            </div>

            <LanguageSwitcher />

          </div>
        </div>

        {/* Decorative Bottom Line */}
        <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-500/50 to-transparent opacity-50" />
      </header>

      {/* Spacer for fixed header */}
      <div className="h-[90px]" />

      <style jsx global>{`
      @keyframes shine {
        0% { transform: translateX(-150%) skewX(-20deg); }
        100% { transform: translateX(150%) skewX(-20deg); }
      }
      .animate-shine {
        animation: shine 1.5s ease-in-out infinite;
      }
    `}</style>
    </>
  );
}
