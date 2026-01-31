"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import {
  Layers,
  Search,
  Gauge,
  SlidersHorizontal,
  Bell,
  Brain
} from "lucide-react";
import { AnimatedCard } from "./ui/Card";

const icons = {
  mtf: Layers,
  patterns: Search,
  confidence: Gauge,
  ml: SlidersHorizontal,
  alerts: Bell,
  claude: Brain,
};

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariant = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

export function FeaturesGrid() {
  const { t } = useI18n();

  const features = [
    { key: "mtf" },
    { key: "patterns" },
    { key: "confidence" },
    { key: "ml" },
    { key: "alerts" },
    { key: "claude" },
  ];

  return (
    <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent via-white/[0.02] to-transparent relative">
      {/* Subtle grid pattern background */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-[0.03] pointer-events-none"></div>

      <div className="max-w-6xl mx-auto relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-tight">
            {t("features.title")}
          </h2>
          <p className="text-lg text-[#E5E7EB]/70 max-w-2xl mx-auto font-light">
            {t("features.subtitle")}
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => {
            const Icon = icons[feature.key as keyof typeof icons];
            return (
              <motion.div
                key={feature.key}
                variants={itemVariant}
              >
                <AnimatedCard
                  icon={<Icon className="w-6 h-6 text-indigo-400 group-hover:text-white transition-colors duration-300" />}
                  title={t(`features.items.${feature.key}.title`)}
                  description={t(`features.items.${feature.key}.description`)}
                  className="group bg-white/5 border-white/10 hover:bg-white/10 hover:border-indigo-500/30 hover:shadow-glow-sm transition-all duration-300 h-full"
                />
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
