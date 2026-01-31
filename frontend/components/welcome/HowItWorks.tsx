"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { UserPlus, BarChart3, CheckCircle } from "lucide-react";

const icons = {
  1: UserPlus,
  2: BarChart3,
  3: CheckCircle,
};

export function HowItWorks() {
  const { t } = useI18n();

  return (
    <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t("howItWorks.title")}
          </h2>
          <p className="text-lg text-[#E5E7EB]/70 max-w-2xl mx-auto">
            {t("howItWorks.subtitle")}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[1, 2, 3].map((step, index) => {
            const Icon = icons[step as keyof typeof icons];
            return (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.15 }}
                className="relative"
              >
                {/* Connector line */}
                {index < 2 && (
                  <div className="hidden md:block absolute top-12 left-full w-full h-px bg-gradient-to-r from-[#00E0C6]/50 to-transparent" />
                )}

                <div className="relative p-8 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:border-[#00E0C6]/20 transition-colors">
                  {/* Step number */}
                  <div className="absolute -top-4 left-8 w-8 h-8 rounded-full bg-[#00E0C6] text-[#0B1220] font-bold flex items-center justify-center">
                    {step}
                  </div>

                  <div className="pt-4">
                    <div className="w-12 h-12 rounded-xl bg-[#00E0C6]/10 flex items-center justify-center mb-6">
                      <Icon className="w-6 h-6 text-[#00E0C6]" />
                    </div>

                    <h3 className="text-xl font-semibold text-white mb-3">
                      {t(`howItWorks.steps.${step}.title`)}
                    </h3>
                    <p className="text-[#E5E7EB]/70 leading-relaxed">
                      {t(`howItWorks.steps.${step}.description`)}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
