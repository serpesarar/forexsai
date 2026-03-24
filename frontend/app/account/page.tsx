"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  User,
  Settings,
  Bell,
  Palette,
  Shield,
  Crown,
  Mail,
  Calendar,
  Check,
  Copy,
  ArrowLeft,
  RefreshCw,
  Edit3,
  Save,
  X,
  Sparkles,
} from "lucide-react";
import { useAuthStore, useUser, useIsAuthenticated } from "../../lib/auth/store";
import AuthGuard from "../../components/AuthGuard";
import { getApiBase } from "../../lib/api/base";

const API_BASE = getApiBase();

const TIER_CONFIG = {
  free: { name: "Free", color: "text-gray-400", bgColor: "bg-gray-500/20" },
  pro: { name: "Pro", color: "text-yellow-400", bgColor: "bg-yellow-500/20" },
  enterprise: { name: "Enterprise", color: "text-purple-400", bgColor: "bg-purple-500/20" },
  admin: { name: "Admin", color: "text-red-400", bgColor: "bg-red-500/20" },
};

export default function AccountPage() {
  return (
    <AuthGuard>
      <AccountPageContent />
    </AuthGuard>
  );
}

function AccountPageContent() {
  const router = useRouter();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const { checkAuth, refreshUser, token, _hasHydrated } = useAuthStore();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: "",
  });
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

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
    if (user) {
      setEditForm({ full_name: user.full_name || "" });
    }
  }, [user]);

  // Auth redirect handled by AuthGuard wrapper

  const handleCopyReferral = () => {
    if (user?.referral_code) {
      navigator.clipboard.writeText(user.referral_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSave = async () => {
    if (!token) return;
    
    setIsSaving(true);
    setMessage(null);
    
    try {
      const res = await fetch(`${API_BASE}/api/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ full_name: editForm.full_name }),
      });

      if (res.ok) {
        await refreshUser();
        setIsEditing(false);
        setMessage({ type: "success", text: "Profil güncellendi!" });
      } else {
        const data = await res.json();
        setMessage({ type: "error", text: data.detail || "Güncelleme başarısız" });
      }
    } catch {
      setMessage({ type: "error", text: "Bağlantı hatası" });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading || !_hasHydrated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!user) return null;

  const tierConfig = TIER_CONFIG[user.membership_tier] || TIER_CONFIG.free;

  return (
    <div className="min-h-screen bg-background text-white">
      <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 rounded-xl hover:bg-white/10 transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Hesabım</h1>
            <p className="text-sm text-textSecondary">Profil bilgilerinizi yönetin</p>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`p-4 rounded-xl ${message.type === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
            {message.text}
          </div>
        )}

        {/* Profile Card */}
        <div className="glass-premium rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/10 bg-gradient-to-r from-accent/10 to-purple-500/10">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              {/* Avatar */}
              <div className={`flex h-20 w-20 items-center justify-center rounded-2xl ${tierConfig.bgColor}`}>
                <span className={`text-3xl font-bold ${tierConfig.color}`}>
                  {user.full_name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || "U"}
                </span>
              </div>
              
              {/* Info */}
              <div className="flex-1">
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.full_name}
                    onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                    placeholder="Ad Soyad"
                    className="text-2xl font-bold bg-white/10 border border-white/20 rounded-lg px-3 py-1 w-full max-w-xs"
                  />
                ) : (
                  <h2 className="text-2xl font-bold">{user.full_name || "İsimsiz Kullanıcı"}</h2>
                )}
                <p className="text-textSecondary">{user.email}</p>
                <div className={`inline-flex items-center gap-2 mt-2 px-3 py-1 rounded-full text-sm font-medium ${tierConfig.bgColor} ${tierConfig.color}`}>
                  <Crown className="w-4 h-4" />
                  {tierConfig.name} Üyelik
                </div>
              </div>

              {/* Edit Button */}
              <div className="flex gap-2">
                {isEditing ? (
                  <>
                    <button
                      onClick={() => setIsEditing(false)}
                      className="p-2 rounded-lg hover:bg-white/10 transition"
                    >
                      <X className="w-5 h-5" />
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent/90 transition disabled:opacity-50"
                    >
                      {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                      Kaydet
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition"
                  >
                    <Edit3 className="w-4 h-4" />
                    Düzenle
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 rounded-xl bg-white/5">
              <Mail className="w-5 h-5 mx-auto mb-2 text-accent" />
              <p className="text-xs text-textSecondary">E-posta Doğrulama</p>
              <p className={`font-semibold ${user.email_verified ? "text-green-400" : "text-yellow-400"}`}>
                {user.email_verified ? "Doğrulandı" : "Bekliyor"}
              </p>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/5">
              <Calendar className="w-5 h-5 mx-auto mb-2 text-accent" />
              <p className="text-xs text-textSecondary">Üyelik Bitiş</p>
              <p className="font-semibold">
                {user.tier_expires_at ? new Date(user.tier_expires_at).toLocaleDateString("tr-TR") : "Süresiz"}
              </p>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/5">
              <User className="w-5 h-5 mx-auto mb-2 text-accent" />
              <p className="text-xs text-textSecondary">Davet Edilen</p>
              <p className="font-semibold">{user.referral_count} kişi</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/5">
              <Sparkles className="w-5 h-5 mx-auto mb-2 text-accent" />
              <p className="text-xs text-textSecondary">Claude AI</p>
              <p className={`font-semibold ${user.can_use_claude ? "text-green-400" : "text-red-400"}`}>
                {user.can_use_claude ? "Aktif" : "Pasif"}
              </p>
            </div>
          </div>
        </div>

        {/* Referral Code */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-accent" />
            Referans Kodu
          </h3>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-white/5 rounded-xl px-4 py-3 font-mono text-lg text-accent">
              {user.referral_code}
            </div>
            <button
              onClick={handleCopyReferral}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-accent hover:bg-accent/90 transition"
            >
              {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
              {copied ? "Kopyalandı" : "Kopyala"}
            </button>
          </div>
          <p className="text-sm text-textSecondary mt-3">
            Arkadaşlarınızı davet edin ve ödüller kazanın! Her başarılı davet için 1 ay Pro üyelik kazanın.
          </p>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            href="/account/settings"
            className="glass-premium rounded-xl p-5 flex items-center gap-4 hover:bg-white/5 transition group"
          >
            <div className="p-3 rounded-xl bg-blue-500/20 group-hover:bg-blue-500/30 transition">
              <Settings className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold">Hesap Ayarları</h3>
              <p className="text-sm text-textSecondary">Şifre, güvenlik ve gizlilik</p>
            </div>
          </Link>

          <Link
            href="/account/notifications"
            className="glass-premium rounded-xl p-5 flex items-center gap-4 hover:bg-white/5 transition group"
          >
            <div className="p-3 rounded-xl bg-purple-500/20 group-hover:bg-purple-500/30 transition">
              <Bell className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="font-semibold">Bildirim Ayarları</h3>
              <p className="text-sm text-textSecondary">E-posta ve push bildirimleri</p>
            </div>
          </Link>

          <Link
            href="/account/appearance"
            className="glass-premium rounded-xl p-5 flex items-center gap-4 hover:bg-white/5 transition group"
          >
            <div className="p-3 rounded-xl bg-pink-500/20 group-hover:bg-pink-500/30 transition">
              <Palette className="w-6 h-6 text-pink-400" />
            </div>
            <div>
              <h3 className="font-semibold">Görünüm</h3>
              <p className="text-sm text-textSecondary">Tema ve dil tercihleri</p>
            </div>
          </Link>

          {user.membership_tier === "free" && (
            <Link
              href="/pricing"
              className="glass-premium rounded-xl p-5 flex items-center gap-4 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 hover:from-yellow-500/20 hover:to-orange-500/20 transition group border border-yellow-500/30"
            >
              <div className="p-3 rounded-xl bg-yellow-500/20 group-hover:bg-yellow-500/30 transition">
                <Crown className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <h3 className="font-semibold text-yellow-400">Pro'ya Yükselt</h3>
                <p className="text-sm text-textSecondary">Sınırsız erişim ve Claude AI</p>
              </div>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
