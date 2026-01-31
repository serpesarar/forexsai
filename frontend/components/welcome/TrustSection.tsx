"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { Shield, Lock, AlertTriangle, CheckCircle2 } from "lucide-react";
import { AnimatedCard } from "./ui/Card";

const icons = {
  data: Lock,
  privacy: Shield,
  advice: AlertTriangle,
};

export function TrustSection() {
  const { t } = useI18n();

  const items = [
    { key: "data" },
    { key: "privacy" },
    { key: "advice" },
  ];

  return (
    <section className="relative py-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/5 rounded-full blur-3xl opacity-30" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">
            {t("trust.title")}
          </h2>
          <p className="text-lg text-[#E5E7EB]/70 max-w-2xl mx-auto font-light">
            {t("trust.subtitle")}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {items.map((item, index) => {
            const Icon = icons[item.key as keyof typeof icons];
            return (
              <motion.div
                key={item.key}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <AnimatedCard
                  icon={<Icon className="w-6 h-6 text-indigo-400" />}
                  title={t(`trust.items.${item.key}.title`)}
                  description={t(`trust.items.${item.key}.description`)}
                  className="bg-white/5 border-white/10 hover:border-indigo-500/30 hover:shadow-glow-sm transition-all duration-300"
                />
              </motion.div>
            );
          })}
        </div>

        {/* Security Seals / Badges Row */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex flex-wrap justify-center gap-6 mt-16 opacity-70 grayscale hover:grayscale-0 transition-all duration-500"
        >
          {['256-Bit SSL', 'Secure Cloud', 'Data Encryption', 'No Log Policy'].map((badge) => (
            <div key={badge} className="flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span className="text-xs font-medium text-white/80">{badge}</span>
            </div>
          ))}
        </motion.div>

        {/* Improved Disclaimer Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-12 p-8 rounded-2xl bg-gradient-to-r from-red-500/10 via-orange-500/5 to-transparent border-l-4 border-l-red-500/50 border-y border-r border-white/10"
        >
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-6 h-6 text-red-400 shrink-0 mt-1" />
            <div className="text-sm text-left">
              <h4 className="font-semibold text-red-200 mb-2">Risk Disclosure</h4>
              <p className="text-[#E5E7EB]/60 leading-relaxed">
                All trading involves risk. Past performance is not indicative of future results.
                ForexsAi provides analytical tools only and does not constitute financial, investment, or trading advice.
                You are solely responsible for your investment decisions.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
