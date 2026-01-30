"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Eye, EyeOff, Mail, Lock, User, Gift, ArrowRight, ArrowLeft,
  Check, AlertCircle, Loader2, Sparkles, TrendingUp, Shield, Zap,
  CheckCircle2, Users, Crown
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Form state
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [referralCode, setReferralCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [referralValid, setReferralValid] = useState<boolean | null>(null);
  const [referrerName, setReferrerName] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [newReferralCode, setNewReferralCode] = useState<string | null>(null);

  // Get referral code from URL
  useEffect(() => {
    const ref = searchParams.get("ref");
    if (ref) {
      setReferralCode(ref);
      validateReferralCode(ref);
    }
  }, [searchParams]);

  // Password strength - simplified (min 5 chars)
  const getPasswordStrength = (pw: string) => {
    if (pw.length < 5) return 0;
    if (pw.length < 8) return 1;
    if (pw.length < 12) return 2;
    return 3;
  };

  const passwordStrength = getPasswordStrength(password);
  const strengthLabels = ["Çok Kısa", "Orta", "İyi", "Güçlü"];
  const strengthColors = ["bg-red-500", "bg-yellow-500", "bg-green-500", "bg-emerald-500"];

  // Validate referral code
  const validateReferralCode = async (code: string) => {
    if (!code || code.length < 4) {
      setReferralValid(null);
      setReferrerName(null);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/auth/validate-referral/${code}`);
      const data = await res.json();
      setReferralValid(data.valid);
      setReferrerName(data.valid ? data.referrer_name : null);
    } catch {
      setReferralValid(null);
    }
  };

  // Handle signup
  const handleSignup = async () => {
    setLoading(true);
    setError(null);

    // Validate
    if (password !== confirmPassword) {
      setError("Şifreler eşleşmiyor");
      setLoading(false);
      return;
    }

    if (password.length < 5) {
      setError("Şifre en az 5 karakter olmalı");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName || null,
          referral_code: referralCode || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Kayıt başarısız");
      }

      setNewReferralCode(data.referral_code);
      setSuccess(true);
      setStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  // Step validation
  const canProceed = () => {
    if (step === 1) return email.includes("@") && email.includes(".");
    if (step === 2) return password.length >= 5 && password === confirmPassword;
    if (step === 3) return true;
    return false;
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <TrendingUp className="w-7 h-7 text-white" />
          </div>
          <span className="text-2xl font-bold text-white">XAUUSD Panel</span>
        </div>

        {/* Progress Steps */}
        {!success && (
          <div className="flex items-center justify-center gap-2 mb-8">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                    step > s
                      ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                      : step === s
                      ? "bg-purple-600 text-white ring-4 ring-purple-500/30"
                      : "bg-slate-800 text-slate-500"
                  }`}
                >
                  {step > s ? <Check className="w-5 h-5" /> : s}
                </div>
                {s < 3 && (
                  <div
                    className={`w-12 h-1 mx-1 rounded transition-all ${
                      step > s ? "bg-gradient-to-r from-purple-500 to-pink-500" : "bg-slate-800"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Form Card */}
        <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 p-8">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
              <span className="text-red-400 text-sm">{error}</span>
            </div>
          )}

          {/* Step 1: Email */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Ücretsiz Hesap Oluştur</h2>
                <p className="text-slate-400">Email adresinizle başlayın</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email Adresi
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ornek@email.com"
                    autoFocus
                    className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                  />
                </div>
              </div>

              <button
                onClick={() => setStep(2)}
                disabled={!canProceed()}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                Devam Et
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>

              {/* Free Features */}
              <div className="pt-4 border-t border-slate-800">
                <p className="text-sm text-slate-500 mb-3">Ücretsiz hesapla:</p>
                <div className="space-y-2">
                  {[
                    "Gerçek zamanlı XAUUSD verileri",
                    "Temel teknik göstergeler",
                    "ML tabanlı sinyal paneli",
                  ].map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-slate-400">
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                      {feature}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Password */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Güvenli Şifre</h2>
                <p className="text-slate-400">En az 8 karakter, büyük/küçük harf ve rakam</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Şifre
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
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

                {/* Password Strength */}
                {password && (
                  <div className="mt-3">
                    <div className="flex gap-1 mb-1">
                      {[0, 1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded ${
                            i < passwordStrength ? strengthColors[passwordStrength] : "bg-slate-700"
                          }`}
                        />
                      ))}
                    </div>
                    <p className={`text-xs ${passwordStrength >= 3 ? "text-green-400" : "text-slate-500"}`}>
                      Şifre gücü: {strengthLabels[passwordStrength]}
                    </p>
                  </div>
                )}
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
                    placeholder="••••••••"
                    className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                  />
                  {confirmPassword && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      {password === confirmPassword ? (
                        <Check className="w-5 h-5 text-green-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold flex items-center justify-center gap-2 transition-all"
                >
                  <ArrowLeft className="w-5 h-5" />
                  Geri
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={!canProceed()}
                  className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                >
                  Devam Et
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Profile & Referral */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Son Adım</h2>
                <p className="text-slate-400">İsteğe bağlı bilgiler</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Ad Soyad (opsiyonel)
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Adınız Soyadınız"
                    className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Referans Kodu (opsiyonel)
                </label>
                <div className="relative">
                  <Gift className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  <input
                    type="text"
                    value={referralCode}
                    onChange={(e) => {
                      setReferralCode(e.target.value.toUpperCase());
                      validateReferralCode(e.target.value);
                    }}
                    placeholder="ABCD1234"
                    className="w-full pl-12 pr-12 py-3.5 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all uppercase"
                  />
                  {referralValid !== null && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      {referralValid ? (
                        <Check className="w-5 h-5 text-green-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                {referralValid && referrerName && (
                  <p className="mt-2 text-sm text-green-400">
                    ✨ {referrerName} sizi davet etti!
                  </p>
                )}
              </div>

              {/* Referral Bonus Info */}
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Crown className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-purple-300 font-medium">Referans Programı</p>
                    <p className="text-sm text-slate-400">
                      5 arkadaş davet et, <span className="text-purple-300 font-semibold">1 hafta Pro ücretsiz!</span>
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold flex items-center justify-center gap-2 transition-all"
                >
                  <ArrowLeft className="w-5 h-5" />
                  Geri
                </button>
                <button
                  onClick={handleSignup}
                  disabled={loading}
                  className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      Kayıt Ol
                      <Sparkles className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Success */}
          {step === 4 && success && (
            <div className="text-center space-y-6">
              <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
                <Check className="w-10 h-10 text-white" />
              </div>

              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Kayıt Başarılı! 🎉</h2>
                <p className="text-slate-400">
                  Hesabınız aktif! <span className="text-white font-medium">{email}</span> ile giriş yapabilirsiniz.
                </p>
              </div>

              {newReferralCode && (
                <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700">
                  <p className="text-sm text-slate-400 mb-2">Senin referans kodun:</p>
                  <div className="flex items-center justify-center gap-2 mb-3">
                    <code className="text-2xl font-mono font-bold text-purple-400">
                      {newReferralCode}
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(newReferralCode);
                        alert("Referans kodu kopyalandı!");
                      }}
                      className="p-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 transition-all"
                      title="Kopyala"
                    >
                      📋
                    </button>
                  </div>
                  
                  {/* Share Buttons */}
                  <div className="flex items-center justify-center gap-3 mb-3">
                    <button
                      onClick={() => {
                        const shareUrl = `https://forexsai.com/signup?ref=${newReferralCode}`;
                        const message = `🚀 ForexSAI ile akıllı trading yapmaya başla! Kayıt ol ve yapay zeka destekli analiz al. Referans kodum: ${newReferralCode}\n\n${shareUrl}`;
                        window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
                      }}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-green-500/20 hover:bg-green-500/30 text-green-400 font-medium transition-all"
                    >
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                      </svg>
                      WhatsApp
                    </button>
                    <button
                      onClick={() => {
                        const shareUrl = `https://forexsai.com/signup?ref=${newReferralCode}`;
                        const message = `ForexSAI ile akıllı trading! Referans kodum: ${newReferralCode} ${shareUrl}`;
                        window.open(`sms:?body=${encodeURIComponent(message)}`, '_blank');
                      }}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 font-medium transition-all"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      SMS
                    </button>
                    <button
                      onClick={() => {
                        const shareUrl = `https://forexsai.com/signup?ref=${newReferralCode}`;
                        navigator.clipboard.writeText(shareUrl);
                        alert("Link kopyalandı!");
                      }}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-700/50 hover:bg-slate-700 text-slate-300 font-medium transition-all"
                    >
                      🔗 Link
                    </button>
                  </div>
                  
                  <p className="text-xs text-slate-500">
                    5 arkadaşını davet et, <span className="text-purple-400 font-semibold">1 hafta Pro kazan!</span>
                  </p>
                </div>
              )}

              <div className="space-y-3">
                <Link
                  href="/login"
                  className="block w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold text-center transition-all"
                >
                  Giriş Yap
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Login Link */}
        {!success && (
          <p className="text-center text-slate-400 mt-6">
            Zaten hesabın var mı?{" "}
            <Link
              href="/login"
              className="text-purple-400 hover:text-purple-300 font-medium transition-colors"
            >
              Giriş Yap
            </Link>
          </p>
        )}
      </div>
    </div>
  );
}

function SignupLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500 mx-auto mb-4" />
        <p className="text-slate-400">Yükleniyor...</p>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<SignupLoading />}>
      <SignupForm />
    </Suspense>
  );
}
