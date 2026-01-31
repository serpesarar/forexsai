"use client";

import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Menu, X, ArrowRight } from "lucide-react";
import { usePathname } from "next/navigation";

// Animated shine component for the AI text
function AIText({ prefersReducedMotion }: { prefersReducedMotion: boolean }) {
  return (
    <span className="relative inline-flex items-center">
      <span className="bg-gradient-to-r from-[#00E0C6] via-[#3B82F6] to-[#00E0C6] bg-clip-text text-transparent text-[1.15em] font-extrabold tracking-tight">
        AI
      </span>
      {!prefersReducedMotion && (
        <motion.span
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
          initial={{ x: "-100%" }}
          animate={{ x: "100%" }}
          transition={{
            duration: 2.5,
            repeat: Infinity,
            repeatDelay: 1.5,
            ease: "easeInOut",
          }}
          style={{
            backgroundSize: "50% 100%",
            backgroundRepeat: "no-repeat",
          }}
        />
      )}
      <span className="absolute -inset-1 bg-gradient-to-r from-[#00E0C6]/20 to-[#3B82F6]/20 blur-xl opacity-50" />
    </span>
  );
}

export function TopNav() {
  const { t, locale, setLocale } = useI18n();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();
  const prefersReducedMotion = useReducedMotion();

  const { scrollY } = useScroll();
  const navOpacity = useTransform(scrollY, [0, 100], [0.55, 0.85]);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 30);
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
      initial={{ y: -30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="fixed top-0 left-0 right-0 z-50"
    >
      <div className="mx-4 mt-4">
        <motion.nav
          style={{
            backgroundColor: scrolled
              ? "rgba(11, 18, 32, 0.85)"
              : "rgba(11, 18, 32, 0.55)",
          }}
          className={`max-w-7xl mx-auto px-6 h-[72px] md:h-[76px] rounded-2xl backdrop-blur-lg border border-white/[0.10] flex items-center transition-shadow duration-300 ${
            scrolled ? "shadow-2xl shadow-black/30" : "shadow-lg shadow-black/20"
          }`}
        >
          <div className="flex items-center justify-between w-full">
            {/* Logo - Enhanced */}
            <Link
              href="/"
              className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-xl p-1 -ml-1"
            >
              <motion.div
                whileHover={{ scale: 1.08, rotate: 4 }}
                whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
                className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] flex items-center justify-center shadow-lg shadow-[#00E0C6]/25"
              >
                <span className="text-[#0B1220] font-bold text-sm md:text-base">F</span>
              </motion.div>
              <span className="text-xl md:text-2xl font-bold tracking-tight">
                <span className="text-white">Forex</span>
                <AIText prefersReducedMotion={prefersReducedMotion ?? false} />
              </span>
            </Link>

            {/* Desktop Nav - Larger */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="relative px-4 py-2.5 text-base text-[#E5E7EB]/70 hover:text-white transition-colors duration-200 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-xl"
                >
                  <span className="relative z-10 font-medium">{link.label}</span>
                  {/* Hover glow */}
                  <motion.div
                    className="absolute inset-0 rounded-xl bg-white/[0.06] opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    layoutId="navHover"
                  />
                  {/* Active underline - animated gradient */}
                  {isActive(link.href) && (
                    <motion.div
                      layoutId="activeNavUnderline"
                      className="absolute -bottom-0.5 left-3 right-3 h-[2px] rounded-full"
                      style={{
                        background: "linear-gradient(90deg, #00E0C6, #3B82F6, #00E0C6)",
                        backgroundSize: "200% 100%",
                      }}
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    >
                      {!prefersReducedMotion && (
                        <motion.div
                          className="absolute inset-0 rounded-full"
                          style={{
                            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)",
                            backgroundSize: "50% 100%",
                          }}
                          animate={{ x: ["-100%", "100%"] }}
                          transition={{
                            duration: 2,
                            repeat: Infinity,
                            ease: "linear",
                          }}
                        />
                      )}
                    </motion.div>
                  )}
                </Link>
              ))}
            </div>

            {/* Right Section */}
            <div className="hidden md:flex items-center gap-4">
              {/* Language Selector - Segmented Pill */}
              <div className="flex items-center p-1 rounded-full bg-white/[0.06] border border-white/[0.08]">
                {["en", "tr"].map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLocale(lang as "en" | "tr")}
                    className={`relative px-3.5 py-1.5 text-sm font-medium rounded-full transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 ${
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
                className="px-4 py-2 text-base text-[#E5E7EB]/60 hover:text-white transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-xl font-medium"
              >
                {t("nav.login")}
              </Link>

              {/* Primary CTA - Prominent with animated glow */}
              <motion.div
                whileHover={{ y: -2, scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                className="relative"
              >
                {/* Animated glow ring on hover */}
                <motion.div
                  className="absolute -inset-[2px] rounded-full bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] opacity-0 blur-md"
                  whileHover={{ opacity: 0.6 }}
                  transition={{ duration: 0.2 }}
                />
                <Link
                  href="/signup"
                  className="relative group flex items-center gap-2 px-5 py-2.5 text-base font-semibold text-[#0B1220] bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-full hover:shadow-xl hover:shadow-[#00E0C6]/30 transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0B1220]"
                >
                  {t("nav.startFree")}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-200" />
                </Link>
              </motion.div>
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2.5 text-white rounded-xl hover:bg-white/5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileMenuOpen}
            >
              <motion.div
                animate={{ rotate: mobileMenuOpen ? 180 : 0 }}
                transition={{ duration: 0.25 }}
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
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
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="md:hidden overflow-hidden mt-3"
        >
          <div className="max-w-7xl mx-auto rounded-2xl backdrop-blur-xl bg-[#0B1220]/95 border border-white/10 p-4 space-y-1">
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
                  className="block px-4 py-3 text-[#E5E7EB]/80 hover:text-white hover:bg-white/5 rounded-xl transition-colors font-medium"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              </motion.div>
            ))}
            <div className="pt-3 mt-3 border-t border-white/10 flex items-center justify-between">
              {/* Mobile Language Toggle */}
              <div className="flex items-center p-1 rounded-full bg-white/[0.06]">
                {["en", "tr"].map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLocale(lang as "en" | "tr")}
                    className={`relative px-4 py-1.5 text-sm font-medium rounded-full transition-all ${
                      locale === lang ? "text-[#0B1220]" : "text-[#E5E7EB]/60"
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
                className="px-4 py-2 text-sm text-[#E5E7EB]/60 hover:text-white font-medium"
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
              className="pt-2"
            >
              <Link
                href="/signup"
                className="block w-full px-4 py-3.5 text-center font-semibold text-[#0B1220] bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] rounded-xl"
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
