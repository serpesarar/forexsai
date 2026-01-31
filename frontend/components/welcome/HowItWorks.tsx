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

  const steps = [
    { key: 1, icon: icons[1] },
    { key: 2, icon: icons[2] },
    { key: 3, icon: icons[3] },
  ];

  return (
    <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 overflow-hidden">
      <div className="max-w-5xl mx-auto">
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

        {/* Steps Container with Connector */}
        <div className="relative">
          {/* Background Connector Line - only on desktop */}
          <div className="hidden md:block absolute top-[60px] left-[16.67%] right-[16.67%] h-[1px]">
            <div className="w-full h-full bg-gradient-to-r from-transparent via-[#00E0C6]/30 to-transparent" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-6">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.key}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.15 }}
                  className="relative"
                >
                  {/* Card */}
                  <div className="relative p-6 md:p-8 rounded-2xl bg-white/[0.02] border border-white/[0.06] hover:border-[#00E0C6]/20 transition-all duration-300 hover:bg-white/[0.04]">
                    {/* Step number badge */}
                    <div className="absolute -top-3 left-6 md:left-8">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] text-[#0B1220] text-sm font-bold flex items-center justify-center shadow-lg shadow-[#00E0C6]/20">
                        {step.key}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="pt-4">
                      {/* Icon */}
                      <div className="w-11 h-11 rounded-xl bg-[#00E0C6]/10 flex items-center justify-center mb-5">
                        <Icon className="w-5 h-5 text-[#00E0C6]" />
                      </div>

                      {/* Text */}
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {t(`howItWorks.steps.${step.key}.title`)}
                      </h3>
                      <p className="text-[#E5E7EB]/60 text-sm leading-relaxed">
                        {t(`howItWorks.steps.${step.key}.description`)}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
