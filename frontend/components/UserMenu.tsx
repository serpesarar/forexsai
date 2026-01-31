"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  LogOut,
  Settings,
  Crown,
  ChevronDown,
  LogIn,
  UserPlus,
  Shield,
  Bell,
  Palette,
  HelpCircle,
  ExternalLink,
  Sparkles,
  Check,
} from "lucide-react";
import { useAuthStore, useUser, useIsAuthenticated, useMembershipTier } from "../lib/auth/store";

const TIER_CONFIG = {
  free: {
    name: "Free",
    color: "text-gray-400",
    bgColor: "bg-gray-500/20",
    icon: User,
  },
  pro: {
    name: "Pro",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/20",
    icon: Crown,
  },
  enterprise: {
    name: "Enterprise",
    color: "text-purple-400",
    bgColor: "bg-purple-500/20",
    icon: Sparkles,
  },
  admin: {
    name: "Admin",
    color: "text-red-400",
    bgColor: "bg-red-500/20",
    icon: Shield,
  },
};

export default function UserMenu() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const membershipTier = useMembershipTier();
  const { logout, _hasHydrated } = useAuthStore();

  const tierConfig = TIER_CONFIG[membershipTier] || TIER_CONFIG.free;
  const TierIcon = tierConfig.icon;

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close on escape
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setIsOpen(false);
    }
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
    router.push("/");
  };

  // Not hydrated yet - show loading
  if (!_hasHydrated) {
    return (
      <div className="w-9 h-9 rounded-full bg-white/10 animate-pulse" />
    );
  }

  // Not authenticated - show login/signup buttons
  if (!isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <Link
          href="/login"
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white/70 hover:text-white hover:bg-white/10 transition"
        >
          <LogIn className="w-4 h-4" />
          <span className="hidden sm:inline">Giriş</span>
        </Link>
        <Link
          href="/signup"
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-accent text-white hover:bg-accent/90 transition"
        >
          <UserPlus className="w-4 h-4" />
          <span className="hidden sm:inline">Kayıt Ol</span>
        </Link>
      </div>
    );
  }

  // Authenticated - show user menu
  return (
    <div ref={menuRef} className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-2 py-1.5 rounded-xl transition-all ${
          isOpen ? "bg-white/15" : "hover:bg-white/10"
        }`}
      >
        {/* Avatar */}
        <div className={`flex h-8 w-8 items-center justify-center rounded-full ${tierConfig.bgColor}`}>
          <span className={`text-sm font-bold ${tierConfig.color}`}>
            {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
          </span>
        </div>
        
        {/* Name & Tier (hidden on mobile) */}
        <div className="hidden md:flex flex-col items-start">
          <span className="text-sm font-medium text-white leading-tight">
            {user?.full_name || user?.email?.split("@")[0] || "Kullanıcı"}
          </span>
          <span className={`text-[10px] ${tierConfig.color} leading-tight flex items-center gap-1`}>
            <TierIcon className="w-3 h-3" />
            {tierConfig.name}
          </span>
        </div>
        
        <ChevronDown className={`w-4 h-4 text-white/50 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-72 rounded-2xl bg-slate-900/95 backdrop-blur-xl border border-white/10 shadow-2xl overflow-hidden z-50"
          >
            {/* User Info Header */}
            <div className="p-4 border-b border-white/10 bg-gradient-to-r from-accent/10 to-purple-500/10">
              <div className="flex items-center gap-3">
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${tierConfig.bgColor}`}>
                  <span className={`text-lg font-bold ${tierConfig.color}`}>
                    {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate">
                    {user?.full_name || "Kullanıcı"}
                  </p>
                  <p className="text-xs text-textSecondary truncate">{user?.email}</p>
                  <div className={`inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${tierConfig.bgColor} ${tierConfig.color}`}>
                    <TierIcon className="w-3 h-3" />
                    {tierConfig.name} Üyelik
                  </div>
                </div>
              </div>
            </div>

            {/* Menu Items */}
            <div className="p-2">
              {/* Profile */}
              <Link
                href="/account"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/80 hover:text-white hover:bg-white/10 transition"
              >
                <User className="w-4 h-4" />
                <span>Profil</span>
              </Link>

              {/* Account Settings */}
              <Link
                href="/account/settings"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/80 hover:text-white hover:bg-white/10 transition"
              >
                <Settings className="w-4 h-4" />
                <span>Hesap Ayarları</span>
              </Link>

              {/* Notifications */}
              <Link
                href="/account/notifications"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/80 hover:text-white hover:bg-white/10 transition"
              >
                <Bell className="w-4 h-4" />
                <span>Bildirimler</span>
                <span className="ml-auto bg-accent/20 text-accent text-[10px] px-1.5 py-0.5 rounded-full">Yeni</span>
              </Link>

              {/* Appearance */}
              <Link
                href="/account/appearance"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/80 hover:text-white hover:bg-white/10 transition"
              >
                <Palette className="w-4 h-4" />
                <span>Görünüm</span>
              </Link>

              <div className="my-2 border-t border-white/10" />

              {/* Upgrade (for free users) */}
              {membershipTier === "free" && (
                <Link
                  href="/pricing"
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-400 hover:from-yellow-500/30 hover:to-orange-500/30 transition"
                >
                  <Crown className="w-4 h-4" />
                  <span>Pro'ya Yükselt</span>
                  <Sparkles className="w-3 h-3 ml-auto" />
                </Link>
              )}

              {/* Help */}
              <Link
                href="/help"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/80 hover:text-white hover:bg-white/10 transition"
              >
                <HelpCircle className="w-4 h-4" />
                <span>Yardım & Destek</span>
              </Link>

              <div className="my-2 border-t border-white/10" />

              {/* Referral Code */}
              {user?.referral_code && (
                <div className="px-3 py-2 mb-2">
                  <p className="text-[10px] text-textSecondary mb-1">REFERANS KODUNUZ</p>
                  <div className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2">
                    <code className="text-sm text-accent font-mono">{user.referral_code}</code>
                    <button
                      onClick={() => navigator.clipboard.writeText(user.referral_code)}
                      className="ml-auto text-xs text-white/50 hover:text-white transition"
                    >
                      Kopyala
                    </button>
                  </div>
                  <p className="text-[10px] text-textSecondary mt-1">
                    {user.referral_count} kişi davet edildi
                  </p>
                </div>
              )}

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition"
              >
                <LogOut className="w-4 h-4" />
                <span>Çıkış Yap</span>
              </button>
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-white/10 bg-white/5">
              <div className="flex items-center justify-between text-[10px] text-textSecondary">
                <span>ForexsAI v2.0</span>
                <a
                  href="https://forexsai.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition flex items-center gap-1"
                >
                  Gizlilik <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
