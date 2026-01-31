"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { ArrowRight, Play, Activity } from "lucide-react";
import { AnimatedButton } from "./ui/Button";
import { AnimatedBackground } from "./AnimatedBackground";
import { TypeAnimation } from 'react-type-animation';

export function Hero() {
  const { t } = useI18n();

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-24 pb-16 overflow-hidden">
      <AnimatedBackground />

      {/* Aurora Gradient Overlay */}
      <div 
        className="absolute inset-0 z-[1] pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse 80% 50% at 20% 40%, rgba(168, 85, 247, 0.15) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 30%, rgba(99, 102, 241, 0.15) 0%, transparent 55%),
            radial-gradient(ellipse 50% 30% at 50% 80%, rgba(14, 165, 233, 0.1) 0%, transparent 50%),
            radial-gradient(ellipse 40% 25% at 70% 70%, rgba(236, 72, 153, 0.1) 0%, transparent 45%)
          `,
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 backdrop-blur-md shadow-glow-sm hover:bg-white/10 transition-colors cursor-default"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-sm font-medium text-emerald-400/90 tracking-wide uppercase text-[10px]">System Online</span>
          <div className="h-3 w-[1px] bg-white/10 mx-1" />
          <span className="text-xs text-white/70 flex items-center gap-1">
             <Activity className="w-3 h-3 text-emerald-400" /> Live Analysis
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-7xl font-bold text-white leading-tight mb-6 tracking-tight"
        >
          <span className="block mb-2">{t("hero.headline").split("NASDAQ")[0]}</span>
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
             NASDAQ & GOLD
          </span>
        </motion.h1>

        {/* Dynamic Subheadline with Type Animation */}
        <motion.div
           initial={{ opacity: 0 }}
           animate={{ opacity: 1 }}
           transition={{ duration: 0.6, delay: 0.3 }}
           className="h-8 mb-6 text-xl md:text-2xl text-indigo-300/90 font-light"
        >
             <TypeAnimation
                sequence={[
                    ' AI-Powered Predictions',
                    2000,
                    ' Real-time Market Data',
                    2000,
                    ' Institutional Grade Analysis',
                    2000,
                ]}
                wrapper="span"
                speed={50}
                repeat={Infinity}
            />
        </motion.div>

        {/* Description */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-lg md:text-xl text-[#E5E7EB]/70 max-w-3xl mx-auto mb-10 leading-relaxed font-light"
        >
          {t("hero.subheadline")}
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8"
        >
          <AnimatedButton href="/signup" size="lg" className="w-full sm:w-auto shadow-glow-md hover:shadow-glow-lg transition-shadow">
            <span className="flex items-center gap-2">
              {t("hero.ctaPrimary")}
              <ArrowRight className="w-5 h-5" />
            </span>
          </AnimatedButton>

          <AnimatedButton href="/demo" variant="secondary" size="lg" className="w-full sm:w-auto border-white/10 hover:bg-white/5">
            <span className="flex items-center gap-2">
              <Play className="w-5 h-5" />
              {t("hero.ctaSecondary")}
            </span>
          </AnimatedButton>
        </motion.div>

        {/* Disclaimer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-xs text-[#E5E7EB]/30 max-w-lg mx-auto"
        >
          {t("hero.disclaimer")}
        </motion.p>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 pt-12 border-t border-white/5"
        >
          {[
            { value: "30s", label: "Refresh Rate", sub: "Live Data" },
            { value: "4+", label: "Timeframes", sub: "M15 to D1" },
            { value: "92%", label: "Accuracy", sub: "Trend Detect" },
            { value: "24/7", label: "Monitoring", sub: "Auto-Pilot" },
          ].map((stat, index) => (
            <div key={index} className="text-center group cursor-default">
              <div className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white to-white/60 group-hover:to-white transition-all duration-300">
                {stat.value}
              </div>
              <div className="text-sm font-medium text-indigo-300/80 mt-1">{stat.label}</div>
              <div className="text-xs text-white/30 mt-1 uppercase tracking-wider">{stat.sub}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
