"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import { Target, Zap, Focus, Eye } from "lucide-react";
import { AnimatedCard } from "./ui/Card";

const icons = {
  accuracy: Target,
  speed: Zap,
  focus: Focus,
  transparency: Eye,
};

export function ValueProps() {
  const { t } = useI18n();

  const items = [
    { key: "accuracy", icon: icons.accuracy },
    { key: "speed", icon: icons.speed },
    { key: "focus", icon: icons.focus },
    { key: "transparency", icon: icons.transparency },
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
            {t("valueProps.title")}
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {items.map((item, index) => {
            const Icon = item.icon;
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
                  title={t(`valueProps.items.${item.key}.title`)}
                  description={t(`valueProps.items.${item.key}.description`)}
                />
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
