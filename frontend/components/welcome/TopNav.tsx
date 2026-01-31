"use client";

import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { useState } from "react";
import { Menu, X, Globe } from "lucide-react";
import { AnimatedButton } from "./ui/Button";

export function TopNav() {
  const { t, locale, setLocale } = useI18n();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleLocale = () => {
    setLocale(locale === "en" ? "tr" : "en");
  };

  const navLinks = [
    { href: "#features", label: t("nav.features") },
    { href: "#how-it-works", label: t("nav.howItWorks") },
    { href: "/pricing", label: t("nav.pricing") },
  ];

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50"
    >
      <div className="mx-4 mt-4">
        <nav className="max-w-6xl mx-auto px-6 py-4 rounded-2xl backdrop-blur-xl bg-[#0B1220]/80 border border-white/10">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] flex items-center justify-center">
                <span className="text-[#0B1220] font-bold text-sm">F</span>
              </div>
              <span className="text-xl font-bold text-white">ForexsAi</span>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm text-[#E5E7EB]/80 hover:text-white transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </div>

            {/* Right Section */}
            <div className="hidden md:flex items-center gap-4">
              {/* Language Toggle */}
              <button
                onClick={toggleLocale}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-[#E5E7EB]/80 hover:text-white hover:bg-white/5 transition"
                aria-label="Switch language"
              >
                <Globe className="w-4 h-4" />
                <span className="uppercase">{locale}</span>
              </button>

              <Link
                href="/login"
                className="text-sm text-[#E5E7EB]/80 hover:text-white transition-colors"
              >
                {t("nav.login")}
              </Link>

              <AnimatedButton href="/signup" size="sm">
                {t("nav.startFree")}
              </AnimatedButton>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="md:hidden mt-4 pt-4 border-t border-white/10 space-y-4"
            >
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="block text-[#E5E7EB]/80 hover:text-white transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <div className="flex items-center gap-4 pt-4 border-t border-white/10">
                <button
                  onClick={toggleLocale}
                  className="flex items-center gap-1.5 text-[#E5E7EB]/80"
                >
                  <Globe className="w-4 h-4" />
                  <span className="uppercase">{locale}</span>
                </button>
                <Link href="/login" className="text-[#E5E7EB]/80">
                  {t("nav.login")}
                </Link>
                <AnimatedButton href="/signup" size="sm">
                  {t("nav.startFree")}
                </AnimatedButton>
              </div>
            </motion.div>
          )}
        </nav>
      </div>
    </motion.header>
  );
}
