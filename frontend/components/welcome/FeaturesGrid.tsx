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
    <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-transparent via-white/[0.02] to-transparent">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            {t("features.title")}
          </h2>
          <p className="text-lg text-[#E5E7EB]/70 max-w-2xl mx-auto">
            {t("features.subtitle")}
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = icons[feature.key as keyof typeof icons];
            return (
              <motion.div
                key={feature.key}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <AnimatedCard
                  icon={<Icon className="w-6 h-6" />}
                  title={t(`features.items.${feature.key}.title`)}
                  description={t(`features.items.${feature.key}.description`)}
                />
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
