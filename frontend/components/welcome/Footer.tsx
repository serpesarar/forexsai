"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";

export function Footer() {
  const { t } = useI18n();
  const year = new Date().getFullYear();

  const links = {
    product: ["features", "pricing", "changelog"],
    company: ["about", "blog", "careers"],
    legal: ["privacy", "terms", "disclaimer"],
  };

  return (
    <footer className="py-16 px-4 sm:px-6 lg:px-8 border-t border-white/10">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] flex items-center justify-center">
                <span className="text-[#0B1220] font-bold text-sm">F</span>
              </div>
              <span className="text-xl font-bold text-white">ForexsAi</span>
            </Link>
            <p className="text-sm text-[#E5E7EB]/60 leading-relaxed">
              {t("footer.tagline")}
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">{t("footer.links.product")}</h4>
            <ul className="space-y-3">
              {links.product.map((key) => (
                <li key={key}>
                  <Link
                    href={`/${key}`}
                    className="text-sm text-[#E5E7EB]/60 hover:text-white transition-colors"
                  >
                    {t(`footer.links.${key}`)}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">{t("footer.links.company")}</h4>
            <ul className="space-y-3">
              {links.company.map((key) => (
                <li key={key}>
                  <Link
                    href={`/${key}`}
                    className="text-sm text-[#E5E7EB]/60 hover:text-white transition-colors"
                  >
                    {t(`footer.links.${key}`)}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4">{t("footer.links.legal")}</h4>
            <ul className="space-y-3">
              {links.legal.map((key) => (
                <li key={key}>
                  <Link
                    href={`/${key}`}
                    className="text-sm text-[#E5E7EB]/60 hover:text-white transition-colors"
                  >
                    {t(`footer.links.${key}`)}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4"
        >
          <p className="text-sm text-[#E5E7EB]/40">
            © {year} ForexsAi. {t("footer.copyright")}
          </p>
          <p className="text-xs text-[#E5E7EB]/30">
            Not financial advice. Trade responsibly.
          </p>
        </motion.div>
      </div>
    </footer>
  );
}
