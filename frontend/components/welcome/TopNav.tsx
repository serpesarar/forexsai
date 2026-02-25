"use client";

import { useState, useEffect } from "react";
import { motion, useScroll } from "framer-motion";
import { useI18n } from "@/lib/i18n";
import Link from "next/link";
import Image from "next/image";
import { Menu, X, MessageSquareWarning, ArrowRight } from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { usePathname } from "next/navigation";
import { FeedbackModal } from "@/components/FeedbackModal";

export function TopNav() {
  const { t, locale, setLocale } = useI18n();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { href: "/features", label: t("nav.features") || "Features" },
    { href: "/about", label: t("nav.howItWorks") || "About" },
    { href: "/pricing", label: t("nav.pricing") || "Pricing" },
  ];

  const isActive = (href: string) => pathname === href;

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
          <nav
            className={`max-w-7xl mx-auto px-6 h-[68px] rounded-xl border border-white/[0.08] flex items-center transition-all duration-300 ${scrolled
                ? "bg-black/90 backdrop-blur-xl shadow-[0_4px_30px_rgba(0,0,0,0.5)]"
                : "bg-black/60 backdrop-blur-lg shadow-[0_4px_20px_rgba(0,0,0,0.3)]"
              }`}
          >
            <div className="flex items-center justify-between w-full">
              {/* Logo */}
              <Link href="/welcome" aria-label="ForexsAi home" className="flex items-center gap-2 group">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="relative w-8 h-8">
                  <Image src="/logo.png" alt="ForexsAi logo" width={32} height={32} className="w-full h-full object-contain" priority />
                </motion.div>
                <span className="text-lg font-bold tracking-[0.1em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">FOREXS</span>
                <span className="text-lg font-light tracking-[0.08em] text-white/70 -ml-1">AI</span>
              </Link>

              {/* Desktop Nav */}
              <div className="hidden md:flex items-center gap-1">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative px-4 py-2 text-xs uppercase tracking-[0.2em] font-light transition-colors duration-200 rounded-lg ${isActive(link.href) ? "text-white bg-white/[0.06] border border-white/8" : "text-gray-500 hover:text-gray-200 hover:bg-white/[0.04]"
                      }`}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>

              {/* Right Section */}
              <div className="hidden md:flex items-center gap-3">
                <button
                  onClick={() => setFeedbackOpen(true)}
                  className="p-2 text-gray-600 hover:text-gray-300 hover:bg-white/5 rounded-lg transition-all flex items-center gap-2"
                  title="Report Issue"
                >
                  <MessageSquareWarning className="w-4 h-4" />
                  <span className="text-xs font-light tracking-widest uppercase hidden lg:block">Report</span>
                </button>

                <div className="w-px h-5 bg-white/8" />
                <div className="hidden md:block"><LanguageSwitcher /></div>

                <Link href="/login" className="px-4 py-2 text-xs text-gray-500 hover:text-white transition-colors font-light tracking-widest uppercase">
                  {t("nav.login") || "Login"}
                </Link>

                {/* CTA — Dark Metalic */}
                <motion.div whileHover={{ y: -1, scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                  <Link
                    href="/signup"
                    className="group flex items-center gap-2 px-5 py-2 text-xs font-light text-white bg-gradient-to-r from-gray-700 via-gray-500 to-gray-700 border border-gray-500/40 rounded-sm hover:shadow-[0_0_20px_rgba(200,200,200,0.15)] hover:from-gray-600 hover:via-gray-400 hover:to-gray-600 transition-all duration-300 uppercase tracking-widest"
                  >
                    {t("nav.startFree") || "Start Free"}
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </motion.div>
              </div>

              {/* Mobile Menu Button */}
              <button
                className="md:hidden p-2 text-white rounded-lg hover:bg-white/5 transition-colors"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              >
                <motion.div animate={{ rotate: mobileMenuOpen ? 180 : 0 }} transition={{ duration: 0.25 }}>
                  {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                </motion.div>
              </button>
            </div>
          </nav>

          {/* Mobile Menu */}
          <motion.div
            initial={false}
            animate={{ height: mobileMenuOpen ? "auto" : 0, opacity: mobileMenuOpen ? 1 : 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="md:hidden overflow-hidden mt-3"
          >
            <div className="max-w-7xl mx-auto rounded-xl bg-black/95 backdrop-blur-xl border border-white/8 p-4 space-y-1">
              <button
                onClick={() => { setFeedbackOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors font-light border border-red-500/10 bg-red-500/3 mb-2"
              >
                <MessageSquareWarning className="w-4 h-4 text-red-400/60" />
                <span className="uppercase tracking-widest text-xs">Report Issue</span>
              </button>

              {navLinks.map((link, i) => (
                <motion.div
                  key={link.href}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: mobileMenuOpen ? 1 : 0, x: mobileMenuOpen ? 0 : -10 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Link
                    href={link.href}
                    className="block px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors font-light text-xs uppercase tracking-widest"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {link.label}
                  </Link>
                </motion.div>
              ))}

              <div className="pt-3 mt-3 border-t border-white/5 flex items-center justify-between">
                <div className="flex items-center p-1 rounded-full bg-white/[0.04] border border-white/6">
                  {(["en", "tr"] as const).map((lang) => (
                    <button
                      key={lang}
                      onClick={() => setLocale(lang)}
                      className={`px-3 py-1 text-xs font-light rounded-full transition-all uppercase tracking-wider ${locale === lang ? "text-white bg-white/10" : "text-gray-600"
                        }`}
                    >
                      {lang}
                    </button>
                  ))}
                </div>
                <Link href="/login" className="px-4 py-2 text-xs text-gray-500 hover:text-white font-light uppercase tracking-widest" onClick={() => setMobileMenuOpen(false)}>
                  {t("nav.login")}
                </Link>
              </div>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: mobileMenuOpen ? 1 : 0, y: mobileMenuOpen ? 0 : 10 }}
                transition={{ delay: 0.15 }}
                className="pt-2"
              >
                <Link
                  href="/signup"
                  className="block w-full px-4 py-3 text-center font-light text-white bg-gradient-to-r from-gray-700 via-gray-500 to-gray-700 border border-gray-500/30 rounded-sm uppercase tracking-widest text-xs"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t("nav.startFree") || "Start Free"}
                </Link>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </motion.header>
    </>
  );
}
