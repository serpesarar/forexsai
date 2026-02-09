"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Lock,
  Shield,
  Trash2,
  Eye,
  EyeOff,
  RefreshCw,
  Check,
  AlertTriangle,
  Key,
} from "lucide-react";
import { useAuthStore, useUser, useIsAuthenticated } from "../../../lib/auth/store";
import AuthGuard from "../../../components/AuthGuard";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

export default function SettingsPage() {
  return (
    <AuthGuard>
      <SettingsPageContent />
    </AuthGuard>
  );
}

function SettingsPageContent() {
  const router = useRouter();
  const user = useUser();
  const isAuthenticated = useIsAuthenticated();
  const { checkAuth, token, logout, _hasHydrated } = useAuthStore();
  
  const [isLoading, setIsLoading] = useState(true);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
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
    if (!isLoading && !isAuthenticated && _hasHydrated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router, _hasHydrated]);

  const handlePasswordChange = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setMessage({ type: "error", text: "Yeni şifreler eşleşmiyor" });
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      setMessage({ type: "error", text: "Şifre en az 6 karakter olmalı" });
      return;
    }

    setIsChangingPassword(true);
    setMessage(null);

    try {
      const res = await fetch(`${API_BASE}/api/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: passwordForm.current_password,
          new_password: passwordForm.new_password,
        }),
      });

      if (res.ok) {
        setMessage({ type: "success", text: "Şifre başarıyla değiştirildi!" });
        setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      } else {
        const data = await res.json();
        setMessage({ type: "error", text: data.detail || "Şifre değiştirilemedi" });
      }
    } catch {
      setMessage({ type: "error", text: "Bağlantı hatası" });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "HESABIMI SİL") {
      setMessage({ type: "error", text: "Lütfen 'HESABIMI SİL' yazarak onaylayın" });
      return;
    }

    setIsDeleting(true);
    
    try {
      const res = await fetch(`${API_BASE}/api/auth/delete-account`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        await logout();
        router.push("/");
      } else {
        const data = await res.json();
        setMessage({ type: "error", text: data.detail || "Hesap silinemedi" });
      }
    } catch {
      setMessage({ type: "error", text: "Bağlantı hatası" });
    } finally {
      setIsDeleting(false);
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

  return (
    <div className="min-h-screen bg-background text-white">
      <div className="max-w-2xl mx-auto p-4 md:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/account" className="p-2 rounded-xl hover:bg-white/10 transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Hesap Ayarları</h1>
            <p className="text-sm text-textSecondary">Güvenlik ve gizlilik ayarları</p>
          </div>
        </div>

        {/* Message */}
        {message && (
          <div className={`p-4 rounded-xl flex items-center gap-3 ${message.type === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
            {message.type === "success" ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            {message.text}
          </div>
        )}

        {/* Change Password */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5 text-accent" />
            Şifre Değiştir
          </h3>
          
          <div className="space-y-4">
            {/* Current Password */}
            <div>
              <label className="text-sm text-textSecondary mb-1 block">Mevcut Şifre</label>
              <div className="relative">
                <input
                  type={showCurrentPassword ? "text" : "password"}
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-12 focus:border-accent focus:outline-none transition"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-white transition"
                >
                  {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div>
              <label className="text-sm text-textSecondary mb-1 block">Yeni Şifre</label>
              <div className="relative">
                <input
                  type={showNewPassword ? "text" : "password"}
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-12 focus:border-accent focus:outline-none transition"
                  placeholder="En az 6 karakter"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-white transition"
                >
                  {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="text-sm text-textSecondary mb-1 block">Yeni Şifre (Tekrar)</label>
              <input
                type="password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:border-accent focus:outline-none transition"
                placeholder="••••••••"
              />
            </div>

            <button
              onClick={handlePasswordChange}
              disabled={isChangingPassword || !passwordForm.current_password || !passwordForm.new_password}
              className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-accent text-white font-semibold hover:bg-accent/90 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isChangingPassword ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Lock className="w-5 h-5" />}
              Şifre Değiştir
            </button>
          </div>
        </div>

        {/* Security Info */}
        <div className="glass-premium rounded-2xl p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-accent" />
            Güvenlik Bilgileri
          </h3>
          
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
              <span className="text-textSecondary">Son Giriş</span>
              <span>Şimdi</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
              <span className="text-textSecondary">E-posta Doğrulama</span>
              <span className={user.email_verified ? "text-green-400" : "text-yellow-400"}>
                {user.email_verified ? "✓ Doğrulandı" : "Bekliyor"}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
              <span className="text-textSecondary">İki Faktörlü Doğrulama</span>
              <span className="text-textSecondary">Yakında</span>
            </div>
          </div>
        </div>

        {/* Delete Account */}
        <div className="glass-premium rounded-2xl p-6 border border-red-500/30">
          <h3 className="font-semibold mb-2 flex items-center gap-2 text-red-400">
            <Trash2 className="w-5 h-5" />
            Hesabı Sil
          </h3>
          <p className="text-sm text-textSecondary mb-4">
            Hesabınızı sildiğinizde tüm verileriniz kalıcı olarak silinecektir. Bu işlem geri alınamaz.
          </p>
          
          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 rounded-xl border border-red-500/50 text-red-400 hover:bg-red-500/10 transition"
            >
              Hesabımı Silmek İstiyorum
            </button>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-red-400">
                Onaylamak için aşağıya <strong>HESABIMI SİL</strong> yazın:
              </p>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="w-full bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 focus:border-red-500 focus:outline-none transition text-red-400"
                placeholder="HESABIMI SİL"
              />
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteConfirmText("");
                  }}
                  className="flex-1 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 transition"
                >
                  İptal
                </button>
                <button
                  onClick={handleDeleteAccount}
                  disabled={isDeleting || deleteConfirmText !== "HESABIMI SİL"}
                  className="flex-1 px-4 py-2 rounded-xl bg-red-500 text-white hover:bg-red-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isDeleting && <RefreshCw className="w-4 h-4 animate-spin" />}
                  Kalıcı Olarak Sil
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
