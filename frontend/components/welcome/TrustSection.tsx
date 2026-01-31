"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { Shield, Lock, AlertTriangle } from "lucide-react";
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
    <section className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t("trust.title")}
          </h2>
          <p className="text-lg text-[#E5E7EB]/70 max-w-2xl mx-auto">
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
                  icon={<Icon className="w-6 h-6" />}
                  title={t(`trust.items.${item.key}.title`)}
                  description={t(`trust.items.${item.key}.description`)}
                />
              </motion.div>
            );
          })}
        </div>

        {/* Additional disclaimer banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-12 p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08] text-center"
        >
          <p className="text-sm text-[#E5E7EB]/50">
            All trading involves risk. Past performance is not indicative of future results. 
            ForexsAi provides analytical tools only and does not constitute financial, investment, or trading advice.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
