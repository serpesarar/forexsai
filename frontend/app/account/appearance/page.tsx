"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Palette,
  Sun,
  Moon,
  Globe,
  Check,
  RefreshCw,
  Monitor,
} from "lucide-react";
import { useAuthStore, useUser, useIsAuthenticated } from "../../../lib/auth/store";
import AuthGuard from "../../../components/AuthGuard";

const THEMES = [
  { id: "dark", name: "Koyu", icon: Moon, color: "bg-slate-800" },
  { id: "light", name: "Açık", icon: Sun, color: "bg-white" },
  { id: "system", name: "Sistem", icon: Monitor, color: "bg-gradient-to-r from-slate-800 to-white" },
];

const LANGUAGES = [
  { id: "tr", name: "Türkçe", flag: "🇹🇷" },
  { id: "en", name: "English", flag: "🇺🇸" },
];

export default function AppearancePage() {
  return (
    <AuthGuard>
      <AppearancePageContent />
    </AuthGuard>
  );
}

function AppearancePageContent() {
  const router = useRouter();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const { checkAuth, _hasHydrated } = useAuthStore();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  
  const [settings, setSettings] = useState({
    theme: "dark",
    language: "tr",
    compactMode: false,
    animations: true,
  });

  useEffect(() => {
    const init = async () => {
      await checkAuth();
      // Load saved preferences from localStorage
      const savedTheme = localStorage.getItem("theme") || "dark";
      const savedLang = localStorage.getItem("locale") || "tr";
      setSettings(prev => ({ ...prev, theme: savedTheme, language: savedLang }));
      setIsLoading(false);
    };
    if (_hasHydrated) {
      init();
    }
  }, [checkAuth, _hasHydrated]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && _hasHydrated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router, _hasHydrated]);

  const handleSave = async () => {
    setIsSaving(true);
    
    // Save to localStorage
    localStorage.setItem("theme", settings.theme);
    localStorage.setItem("locale", settings.language);
    
    await new Promise(resolve => setTimeout(resolve, 300));
    
    setMessage({ type: "success", text: "Görünüm ayarları kaydedildi!" });
    setIsSaving(false);
    
    // Reload to apply changes
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  if (isLoading || !_hasHydrated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background text-white">
      <div className="max-w-2xl mx-auto p-4 md:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/account" className="p-2 rounded-xl hover:bg-white/10 transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Görünüm</h1>
            <p className="text-sm text-textSecondary">Tema ve dil tercihlerinizi ayarlayın</p>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`p-4 rounded-xl flex items-center gap-3 ${message.type === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
            <Check className="w-5 h-5" />
            {message.text}
          </div>
        )}

        {/* Theme */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Palette className="w-5 h-5 text-accent" />
            Tema
          </h3>
          
          <div className="grid grid-cols-3 gap-3">
            {THEMES.map((theme) => {
              const Icon = theme.icon;
              return (
                <button
                  key={theme.id}
                  onClick={() => setSettings(prev => ({ ...prev, theme: theme.id }))}
                  className={`relative p-4 rounded-xl border-2 transition-all ${
                    settings.theme === theme.id
                      ? "border-accent bg-accent/10"
                      : "border-white/10 hover:border-white/30"
                  }`}
                >
                  {settings.theme === theme.id && (
                    <div className="absolute top-2 right-2">
                      <Check className="w-4 h-4 text-accent" />
                    </div>
                  )}
                  <div className={`w-full h-12 rounded-lg mb-3 ${theme.color}`} />
                  <div className="flex items-center justify-center gap-2">
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{theme.name}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Language */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-accent" />
            Dil
          </h3>
          
          <div className="grid grid-cols-2 gap-3">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.id}
                onClick={() => setSettings(prev => ({ ...prev, language: lang.id }))}
                className={`relative p-4 rounded-xl border-2 transition-all ${
                  settings.language === lang.id
                    ? "border-accent bg-accent/10"
                    : "border-white/10 hover:border-white/30"
                }`}
              >
                {settings.language === lang.id && (
                  <div className="absolute top-2 right-2">
                    <Check className="w-4 h-4 text-accent" />
                  </div>
                )}
                <div className="text-3xl mb-2">{lang.flag}</div>
                <span className="text-sm font-medium">{lang.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Additional Options */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4">Ek Ayarlar</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
              <div>
                <p className="font-medium">Kompakt Mod</p>
                <p className="text-sm text-textSecondary">Daha az boşluk kullan</p>
              </div>
              <button
                onClick={() => setSettings(prev => ({ ...prev, compactMode: !prev.compactMode }))}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.compactMode ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.compactMode ? "left-7" : "left-1"}`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
              <div>
                <p className="font-medium">Animasyonlar</p>
                <p className="text-sm text-textSecondary">Geçiş animasyonlarını etkinleştir</p>
              </div>
              <button
                onClick={() => setSettings(prev => ({ ...prev, animations: !prev.animations }))}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.animations ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.animations ? "left-7" : "left-1"}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-accent text-white font-semibold hover:bg-accent/90 transition disabled:opacity-50"
        >
          {isSaving ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Check className="w-5 h-5" />}
          Ayarları Kaydet
        </button>
      </div>
    </div>
  );
}
