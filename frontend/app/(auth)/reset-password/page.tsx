"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Lock, Eye, EyeOff, Loader2, CheckCircle2, AlertCircle, TrendingUp } from "lucide-react";
import { getApiBase } from "@/lib/api/base";

const API_BASE = getApiBase();

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 5) {
      setError("Şifre en az 5 karakter olmalı");
      return;
    }

    if (password !== confirmPassword) {
      setError("Şifreler eşleşmiyor");
      return;
    }

    if (!token) {
      setError("Geçersiz sıfırlama linki");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Bir hata oluştu");
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center space-y-6">
        <div className="w-20 h-20 mx-auto rounded-full bg-red-500/20 flex items-center justify-center">
          <AlertCircle className="w-10 h-10 text-red-400" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Geçersiz Link</h2>
          <p className="text-slate-400">
            Bu şifre sıfırlama linki geçersiz veya süresi dolmuş.
          </p>
        </div>
        <Link
          href="/forgot-password"
          className="block w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold text-center transition-all"
        >
          Yeni Link İste
        </Link>
      </div>
    );
  }

  if (success) {
    return (
      <div className="text-center space-y-6">
        <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
          <CheckCircle2 className="w-10 h-10 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Şifre Değiştirildi!</h2>
          <p className="text-slate-400">
            Şifreniz başarıyla değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.
          </p>
        </div>
        <Link
          href="/login"
          className="block w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold text-center transition-all"
        >
          Giriş Yap
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Yeni Şifre Belirle</h1>
        <p className="text-slate-400">
          Hesabınız için yeni bir şifre belirleyin.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
          <span className="text-red-400 text-sm">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Yeni Şifre
          </label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="En az 5 karakter"
              required
              className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Şifre Tekrar
          </label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Şifrenizi tekrar girin"
              required
              className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
            />
          </div>
          {confirmPassword && password !== confirmPassword && (
            <p className="mt-2 text-sm text-red-400">Şifreler eşleşmiyor</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || password.length < 5 || password !== confirmPassword}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            "Şifremi Değiştir"
          )}
        </button>
      </form>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <TrendingUp className="w-7 h-7 text-white" />
          </div>
          <span className="text-2xl font-bold text-white">XAUUSD Panel</span>
        </div>

        {/* Card */}
        <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 p-8">
          <Suspense fallback={<div className="text-center text-slate-400">Yükleniyor...</div>}>
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
