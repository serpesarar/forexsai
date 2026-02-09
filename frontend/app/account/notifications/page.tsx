"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Bell,
  Mail,
  Smartphone,
  RefreshCw,
  Check,
  TrendingUp,
  AlertTriangle,
  Newspaper,
} from "lucide-react";
import { useAuthStore, useUser, useIsAuthenticated } from "../../../lib/auth/store";
import AuthGuard from "../../../components/AuthGuard";

export default function NotificationsPage() {
  return (
    <AuthGuard>
      <NotificationsPageContent />
    </AuthGuard>
  );
}

function NotificationsPageContent() {
  const router = useRouter();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const { checkAuth, _hasHydrated } = useAuthStore();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  
  const [settings, setSettings] = useState({
    email_signals: true,
    email_news: false,
    email_updates: true,
    push_signals: true,
    push_alerts: true,
  });

  useEffect(() => {
    const init = async () => {
      await checkAuth();
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

  const handleToggle = (key: keyof typeof settings) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    // Simulated save - in real app, save to backend
    await new Promise(resolve => setTimeout(resolve, 500));
    setMessage({ type: "success", text: "Bildirim ayarları kaydedildi!" });
    setIsSaving(false);
    setTimeout(() => setMessage(null), 3000);
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
            <h1 className="text-2xl font-bold">Bildirim Ayarları</h1>
            <p className="text-sm text-textSecondary">E-posta ve push bildirimlerini yönetin</p>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`p-4 rounded-xl flex items-center gap-3 ${message.type === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
            <Check className="w-5 h-5" />
            {message.text}
          </div>
        )}

        {/* Email Notifications */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Mail className="w-5 h-5 text-accent" />
            E-posta Bildirimleri
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-green-400" />
                <div>
                  <p className="font-medium">Trading Sinyalleri</p>
                  <p className="text-sm text-textSecondary">Yeni sinyal oluştuğunda e-posta al</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle("email_signals")}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.email_signals ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.email_signals ? "left-7" : "left-1"}`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition">
              <div className="flex items-center gap-3">
                <Newspaper className="w-5 h-5 text-blue-400" />
                <div>
                  <p className="font-medium">Piyasa Haberleri</p>
                  <p className="text-sm text-textSecondary">Önemli haberler için e-posta al</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle("email_news")}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.email_news ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.email_news ? "left-7" : "left-1"}`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition">
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-purple-400" />
                <div>
                  <p className="font-medium">Sistem Güncellemeleri</p>
                  <p className="text-sm text-textSecondary">Yeni özellikler ve güncellemeler</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle("email_updates")}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.email_updates ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.email_updates ? "left-7" : "left-1"}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Push Notifications */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-accent" />
            Push Bildirimleri
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-green-400" />
                <div>
                  <p className="font-medium">Anlık Sinyaller</p>
                  <p className="text-sm text-textSecondary">Yeni sinyal oluştuğunda bildirim</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle("push_signals")}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.push_signals ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.push_signals ? "left-7" : "left-1"}`} />
              </button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <div>
                  <p className="font-medium">Fiyat Alarmları</p>
                  <p className="text-sm text-textSecondary">Belirlediğiniz seviyelere ulaşınca</p>
                </div>
              </div>
              <button
                onClick={() => handleToggle("push_alerts")}
                className={`relative w-12 h-6 rounded-full transition-colors ${settings.push_alerts ? "bg-accent" : "bg-white/20"}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${settings.push_alerts ? "left-7" : "left-1"}`} />
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
