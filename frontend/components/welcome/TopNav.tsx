"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Menu, X, ArrowRight } from "lucide-react";
import { usePathname } from "next/navigation";

export function TopNav() {
  const { t, locale, setLocale } = useI18n();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();

  const { scrollY } = useScroll();
  const navOpacity = useTransform(scrollY, [0, 100], [0.4, 0.85]);
  const navShadow = useTransform(
    scrollY,
    [0, 100],
    ["0 0 0 rgba(0,0,0,0)", "0 4px 30px rgba(0,0,0,0.3)"]
  );

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { href: "#features", label: t("nav.features") },
    { href: "#how-it-works", label: t("nav.howItWorks") },
    { href: "/pricing", label: t("nav.pricing") },
  ];

  const isActive = (href: string) => {
    if (href.startsWith("#")) return pathname.includes(href);
    return pathname === href;
  };

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="fixed top-0 left-0 right-0 z-50"
    >
      <div className="mx-4 mt-3">
        <motion.nav
          style={{
            backgroundColor: `rgba(11, 18, 32, ${scrolled ? 0.7 : 0.4})`,
            boxShadow: scrolled
              ? "0 4px 30px rgba(0,0,0,0.3)"
              : "0 0 0 rgba(0,0,0,0)",
          }}
          transition={{ duration: 0.3 }}
          className="max-w-6xl mx-auto px-5 h-[56px] rounded-2xl backdrop-blur-md border border-white/[0.08] flex items-center"
        >
          <div className="flex items-center justify-between w-full">
            {/* Logo */}
            <Link
              href="/"
              className="flex items-center gap-2 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-lg"
            >
              <motion.div
                whileHover={{ scale: 1.05, rotate: 3 }}
                whileTap={{ scale: 0.95 }}
                className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] flex items-center justify-center shadow-lg shadow-[#00E0C6]/20"
              >
                <span className="text-[#0B1220] font-bold text-xs">F</span>
              </motion.div>
              <span className="text-lg font-bold text-white tracking-tight">
                ForexsAi
              </span>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="relative px-4 py-2 text-sm text-[#E5E7EB]/70 hover:text-white transition-colors group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-lg"
                >
                  <span className="relative z-10">{link.label}</span>
                  {/* Hover glow */}
                  <motion.div
                    className="absolute inset-0 rounded-lg bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"
                    layoutId="navHover"
                  />
                  {/* Active underline */}
                  {isActive(link.href) && (
                    <motion.div
                      layoutId="activeNav"
                      className="absolute -bottom-0.5 left-4 right-4 h-0.5 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-full"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              ))}
            </div>

            {/* Right Section */}
            <div className="hidden md:flex items-center gap-3">
              {/* Language Selector - Segmented Pill */}
              <div className="flex items-center p-1 rounded-full bg-white/[0.05] border border-white/[0.08]">
                {["en", "tr"].map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLocale(lang as "en" | "tr")}
                    className={`relative px-3 py-1 text-xs font-medium rounded-full transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 ${
                      locale === lang
                        ? "text-[#0B1220]"
                        : "text-[#E5E7EB]/60 hover:text-[#E5E7EB]"
                    }`}
                    aria-label={`Switch to ${lang === "en" ? "English" : "Turkish"}`}
                  >
                    {locale === lang && (
                      <motion.div
                        layoutId="langPill"
                        className="absolute inset-0 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-full"
                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                      />
                    )}
                    <span className="relative z-10 uppercase">{lang}</span>
                  </button>
                ))}
              </div>

              {/* Login - Subtle secondary */}
              <Link
                href="/login"
                className="px-3 py-2 text-sm text-[#E5E7EB]/60 hover:text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-lg"
              >
                {t("nav.login")}
              </Link>

              {/* Primary CTA */}
              <motion.div
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.97 }}
              >
                <Link
                  href="/signup"
                  className="group flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-[#0B1220] bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-full hover:shadow-lg hover:shadow-[#00E0C6]/25 transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50"
                >
                  {t("nav.startFree")}
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </motion.div>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-white rounded-lg hover:bg-white/5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileMenuOpen}
            >
              <motion.div
                animate={{ rotate: mobileMenuOpen ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </motion.div>
            </button>
          </div>
        </motion.nav>

        {/* Mobile Menu */}
        <motion.div
          initial={false}
          animate={{
            height: mobileMenuOpen ? "auto" : 0,
            opacity: mobileMenuOpen ? 1 : 0,
          }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="md:hidden overflow-hidden mt-2"
        >
          <div className="max-w-6xl mx-auto rounded-2xl backdrop-blur-xl bg-[#0B1220]/90 border border-white/10 p-4 space-y-2">
            {navLinks.map((link, i) => (
              <motion.div
                key={link.href}
                initial={{ opacity: 0, x: -10 }}
                animate={{
                  opacity: mobileMenuOpen ? 1 : 0,
                  x: mobileMenuOpen ? 0 : -10,
                }}
                transition={{ delay: i * 0.05 }}
              >
                <Link
                  href={link.href}
                  className="block px-4 py-3 text-[#E5E7EB]/80 hover:text-white hover:bg-white/5 rounded-xl transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              </motion.div>
            ))}
            <div className="pt-2 mt-2 border-t border-white/10 flex items-center justify-between">
              {/* Mobile Language Toggle */}
              <div className="flex items-center p-1 rounded-full bg-white/[0.05]">
                {["en", "tr"].map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLocale(lang as "en" | "tr")}
                    className={`relative px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                      locale === lang
                        ? "text-[#0B1220]"
                        : "text-[#E5E7EB]/60"
                    }`}
                  >
                    {locale === lang && (
                      <motion.div
                        layoutId="mobileLangPill"
                        className="absolute inset-0 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-full"
                      />
                    )}
                    <span className="relative z-10 uppercase">{lang}</span>
                  </button>
                ))}
              </div>
              <Link
                href="/login"
                className="px-4 py-2 text-sm text-[#E5E7EB]/60 hover:text-white"
                onClick={() => setMobileMenuOpen(false)}
              >
                {t("nav.login")}
              </Link>
            </div>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{
                opacity: mobileMenuOpen ? 1 : 0,
                y: mobileMenuOpen ? 0 : 10,
              }}
              transition={{ delay: 0.15 }}
            >
              <Link
                href="/signup"
                className="block w-full px-4 py-3 text-center font-semibold text-[#0B1220] bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-xl"
                onClick={() => setMobileMenuOpen(false)}
              >
                {t("nav.startFree")}
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </motion.header>
  );
}
