"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { ArrowRight, Play } from "lucide-react";
import { AnimatedButton } from "./ui/Button";
import { AnimatedBackground } from "./AnimatedBackground";

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
            radial-gradient(ellipse 80% 50% at 20% 40%, rgba(168, 85, 247, 0.12) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 80% 30%, rgba(99, 102, 241, 0.10) 0%, transparent 55%),
            radial-gradient(ellipse 50% 30% at 50% 80%, rgba(14, 165, 233, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse 40% 25% at 70% 70%, rgba(236, 72, 153, 0.06) 0%, transparent 45%)
          `,
        }}
      />

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-[#00E0C6] animate-pulse" />
          <span className="text-sm text-[#E5E7EB]/80">AI-Powered Market Analysis</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-6xl font-bold text-white leading-tight mb-6"
        >
          {t("hero.headline")}
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-lg md:text-xl text-[#E5E7EB]/70 max-w-3xl mx-auto mb-10 leading-relaxed"
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
          <AnimatedButton href="/signup" size="lg" className="w-full sm:w-auto">
            <span className="flex items-center gap-2">
              {t("hero.ctaPrimary")}
              <ArrowRight className="w-5 h-5" />
            </span>
          </AnimatedButton>

          <AnimatedButton href="/demo" variant="secondary" size="lg" className="w-full sm:w-auto">
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
          className="text-xs text-[#E5E7EB]/40"
        >
          {t("hero.disclaimer")}
        </motion.p>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="grid grid-cols-3 gap-8 mt-16 pt-16 border-t border-white/10"
        >
          {[
            { value: "30s", label: "Refresh Rate" },
            { value: "4", label: "Timeframes" },
            { value: "99%", label: "Uptime" },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-2xl md:text-3xl font-bold text-[#00E0C6]">{stat.value}</div>
              <div className="text-sm text-[#E5E7EB]/60 mt-1">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
