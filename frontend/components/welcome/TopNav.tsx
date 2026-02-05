"use client";

import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import { Menu, X, ArrowRight, MessageSquareWarning } from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { usePathname } from "next/navigation";
import { FeedbackModal } from "@/components/FeedbackModal";

// Animated shine component for the AI text
function AIText({ prefersReducedMotion }: { prefersReducedMotion: boolean }) {
  // ... (unchanged)
  return (
    <span className="relative inline-flex items-center">
      {/* ... (unchanged) */}
    </span>
  );
}

export function TopNav() {
  const { t, locale, setLocale } = useI18n();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false); // New state
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
    <>
      <FeedbackModal isOpen={feedbackOpen} onClose={() => setFeedbackOpen(false)} />

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
            className={`max-w-7xl mx-auto px-6 h-[72px] md:h-[76px] rounded-2xl backdrop-blur-lg border border-white/[0.10] flex items-center transition-shadow duration-300 ${scrolled ? "shadow-2xl shadow-black/30" : "shadow-lg shadow-black/20"
              }`}
          >
            <div className="flex items-center justify-between w-full">
              {/* Logo */}
              <Link
                href="/welcome"
                aria-label="ForexsAi home"
                className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-xl p-1 -ml-1"
              >
                {/* ... Logo Content ... */}
                <motion.div
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 400, damping: 17 }}
                  className="relative w-8 h-8 md:w-9 md:h-9 group-hover:drop-shadow-[0_0_8px_rgba(0,224,198,0.4)]"
                >
                  <Image
                    src="/logo.png"
                    alt="ForexsAi logo"
                    width={36}
                    height={36}
                    className="w-full h-full object-contain"
                    priority
                  />
                </motion.div>
                <motion.span
                  className="text-xl md:text-2xl font-bold tracking-tight"
                  whileHover={{ y: -1 }}
                  transition={{ type: "spring", stiffness: 400, damping: 17 }}
                >
                  <span className="text-white">Forexs</span>
                  <AIText prefersReducedMotion={prefersReducedMotion ?? false} />
                </motion.span>
              </Link>

              {/* Desktop Nav */}
              <div className="hidden md:flex items-center gap-1">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="relative px-4 py-2.5 text-base text-[#E5E7EB]/70 hover:text-white transition-colors duration-200 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-xl"
                  >
                    <span className="relative z-10 font-medium">{link.label}</span>
                    <motion.div
                      className="absolute inset-0 rounded-xl bg-white/[0.06] opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                      layoutId="navHover"
                    />
                    {isActive(link.href) && (
                      <motion.div
                        layoutId="activeNavUnderline"
                        className="absolute -bottom-0.5 left-3 right-3 h-[2px] rounded-full"
                        style={{
                          background: "linear-gradient(90deg, #00E0C6, #3B82F6, #00E0C6)",
                          backgroundSize: "200% 100%",
                        }}
                        transition={{ type: "spring", stiffness: 380, damping: 30 }}
                      />
                    )}
                  </Link>
                ))}
              </div>

              {/* Right Section */}
              <div className="hidden md:flex items-center gap-3">

                {/* Bug Report Button */}
                <button
                  onClick={() => setFeedbackOpen(true)}
                  className="p-2.5 text-[#E5E7EB]/70 hover:text-white hover:bg-white/10 rounded-xl transition-all focus:outline-none flex items-center gap-2 group"
                  title="Sorun Bildir / Report Bug"
                >
                  <MessageSquareWarning className="w-5 h-5 group-hover:text-[#F59E0B] transition-colors" />
                  <span className="text-sm font-medium hidden lg:block">Sorun Bildir</span>
                </button>

                <div className="w-px h-6 bg-white/10 mx-1" />

                {/* Language Selector */}
                <div className="hidden md:block">
                  <LanguageSwitcher />
                </div>

                {/* Login */}
                <Link
                  href="/login"
                  className="px-4 py-2 text-base text-[#E5E7EB]/60 hover:text-white transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E0C6]/50 rounded-xl font-medium"
                >
                  {t("nav.login")}
                </Link>

                {/* Primary CTA */}
                <motion.div
                  whileHover={{ y: -2, scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  className="relative"
                >
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

              {/* Mobile Bug Report */}
              <button
                onClick={() => { setFeedbackOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-4 py-3 text-[#E5E7EB]/80 hover:text-white hover:bg-white/5 rounded-xl transition-colors font-medium border border-red-500/20 bg-red-500/5 mb-2"
              >
                <MessageSquareWarning className="w-5 h-5 text-red-400" />
                Sorun/Hata Bildir
              </button>

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
                      className={`relative px-4 py-1.5 text-sm font-medium rounded-full transition-all ${locale === lang ? "text-[#0B1220]" : "text-[#E5E7EB]/60"
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
    </>
  );
}
