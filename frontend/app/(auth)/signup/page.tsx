"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Eye, EyeOff, Mail, Lock, User, Gift, ArrowRight, ArrowLeft,
  Check, AlertCircle, Loader2, Sparkles, TrendingUp, Shield, Crown
} from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

function SignupForm() {
  const { t } = useI18n();
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
  const strengthLabels = [
    t("auth.signup.weak"),
    t("auth.signup.medium"),
    t("auth.signup.strong"),
    t("auth.signup.secure")
  ];
  const strengthColors = ["bg-red-500", "bg-yellow-500", "bg-emerald-500", "bg-emerald-400"];

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
      setError(t("auth.signup.passwordMismatch") || "Şifreler eşleşmiyor"); // Note: passwordMismatch key might need to be added or fallback
      setLoading(false);
      return;
    }

    if (password.length < 5) {
      setError(t("auth.signup.passwordTooShort") || "Şifre en az 5 karakter olmalı");
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
    <main className="min-h-screen bg-[#0B1220] flex items-center justify-center p-4 sm:p-6 relative overflow-hidden text-gray-200 font-sans">
      <AnimatedBackground />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg z-10"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            ForexsAi
          </span>
        </div>

        {/* Progress Steps */}
        {!success && (
          <div className="flex items-center justify-center gap-2 mb-8">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm transition-all duration-300 ${step > s
                      ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                      : step === s
                        ? "bg-indigo-600 text-white ring-4 ring-indigo-500/20 shadow-lg shadow-indigo-500/30"
                        : "bg-[#1F2937] text-gray-500 border border-white/5"
                    }`}
                >
                  {step > s ? <Check className="w-4 h-4" /> : s}
                </div>
                {s < 3 && (
                  <div
                    className={`w-12 h-0.5 mx-2 rounded transition-all duration-500 ${step > s ? "bg-emerald-500" : "bg-[#1F2937]"
                      }`}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Form Card */}
        <motion.div
          layout
          className="bg-[#0F1623]/80 backdrop-blur-2xl rounded-3xl border border-white/10 p-8 shadow-2xl relative overflow-hidden"
        >
          {/* Decor */}
          <div className="absolute top-0 right-0 p-8 opacity-20 pointer-events-none">
            <div className="w-32 h-32 bg-indigo-500/30 rounded-full blur-3xl" />
          </div>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3"
              >
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                <span className="text-red-300 text-sm font-medium">{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Step 1: Email */}
          {step === 1 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">{t("auth.signup.title")}</h2>
                <p className="text-gray-400">{t("auth.signup.subtitle")}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">
                  {t("auth.signup.emailLabel")}
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t("auth.signup.emailPlaceholder")}
                    autoFocus
                    className="w-full pl-11 pr-4 py-3.5 bg-[#131B2D] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-medium"
                  />
                </div>
              </div>

              <button
                onClick={() => setStep(2)}
                disabled={!canProceed()}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20 group relative overflow-hidden"
              >
                <span className="relative z-10 flex items-center gap-2">
                  {t("auth.signup.continue")}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </span>
                <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
              </button>

              {/* Free Features */}
              <div className="pt-6 border-t border-white/5">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">{t("auth.signup.freeFeatures")}</p>
                <div className="space-y-3">
                  {["Canlı NASDAQ & XAUUSD Verisi", "30 Saniyelik AI Sinyalleri", "Temel Formasyon Tespiti"].map((feature, i) => (
                    <div key={i} className="flex items-center gap-3 text-sm text-gray-400 group/item">
                      <div className="w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center group-hover/item:bg-emerald-500/20 transition-colors">
                        <Check className="w-3 h-3 text-emerald-500" />
                      </div>
                      {/* Using hardcoded here but ideally map from translation array if consistent */}
                      {i === 0 ? t("auth.signup.features.0") : i === 1 ? t("auth.signup.features.1") : t("auth.signup.features.2")}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Step 2: Password */}
          {step === 2 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">{t("auth.signup.passwordTitle")}</h2>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Shield className="w-4 h-4 text-emerald-500" />
                  <p>{t("auth.signup.passwordSubtitle")}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">
                  {t("auth.signup.passwordLabel")}
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t("auth.signup.passwordPlaceholder")}
                    autoFocus
                    className="w-full pl-11 pr-12 py-3.5 bg-[#131B2D] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-medium"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>

                {/* Password Strength */}
                {password && (
                  <div className="mt-3 px-1">
                    <div className="flex gap-1 mb-2 h-1 bg-gray-800 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${((passwordStrength + 1) / 4) * 100}%` }}
                        className={`h-full rounded-full transition-colors duration-500 ${strengthColors[passwordStrength]}`}
                      />
                    </div>
                    <p className={`text-xs font-medium ${passwordStrength >= 2 ? "text-emerald-400" : "text-gray-500"}`}>
                      {strengthLabels[passwordStrength]}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">
                  {t("auth.signup.passwordRepeatLabel")}
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-11 pr-12 py-3.5 bg-[#131B2D] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-medium"
                  />
                  {confirmPassword && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      {password === confirmPassword ? (
                        <Check className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setStep(1)}
                  className="px-6 py-3.5 rounded-xl bg-[#131B2D] hover:bg-[#1F2937] text-gray-300 font-semibold transition-all border border-white/5"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setStep(3)}
                  disabled={!canProceed()}
                  className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20"
                >
                  {t("auth.signup.continue")}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* Step 3: Profile & Referral */}
          {step === 3 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">{t("auth.signup.profileTitle")}</h2>
                <p className="text-gray-400">{t("auth.signup.profileSubtitle")}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">
                  {t("auth.signup.nameLabel")}
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                  </div>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder={t("auth.signup.namePlaceholder")}
                    className="w-full pl-11 pr-4 py-3.5 bg-[#131B2D] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2 ml-1">
                  {t("auth.signup.referralLabel")}
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Gift className="h-5 w-5 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
                  </div>
                  <input
                    type="text"
                    value={referralCode}
                    onChange={(e) => {
                      setReferralCode(e.target.value.toUpperCase());
                      validateReferralCode(e.target.value);
                    }}
                    placeholder="ABCD1234"
                    className="w-full pl-11 pr-12 py-3.5 bg-[#131B2D] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all uppercase font-mono tracking-wide"
                  />
                  {referralValid !== null && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      {referralValid ? (
                        <Check className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                {referralValid && referrerName && (
                  <motion.p
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-2 text-sm text-emerald-400 flex items-center gap-1"
                  >
                    <Sparkles className="w-3 h-3" /> {referrerName} sizi davet etti!
                  </motion.p>
                )}
              </div>

              {/* Referral Bonus Info */}
              <div className="p-4 rounded-xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center shrink-0">
                    <Crown className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-indigo-300 font-bold text-sm mb-0.5">Pro Bonus</p>
                    <p className="text-xs text-gray-400 leading-tight">
                      {t("auth.signup.referralInfo")}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setStep(2)}
                  className="px-6 py-3.5 rounded-xl bg-[#131B2D] hover:bg-[#1F2937] text-gray-300 font-semibold transition-all border border-white/5"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <button
                  onClick={handleSignup}
                  disabled={loading}
                  className="flex-1 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      {t("auth.signup.complete")}
                      <Sparkles className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          )}

          {/* Step 4: Success */}
          {step === 4 && success && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center space-y-8 py-4"
            >
              <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-xl shadow-emerald-500/30">
                <Check className="w-12 h-12 text-white" />
              </div>

              <div>
                <h2 className="text-3xl font-bold text-white mb-3">{t("auth.signup.successTitle")}</h2>
                <p className="text-gray-400 text-lg">
                  {t("auth.signup.successText")} <br />
                  <span className="text-white font-medium bg-white/5 px-2 py-0.5 rounded">{email}</span>
                </p>
              </div>

              {newReferralCode && (
                <div className="p-6 rounded-2xl bg-[#131B2D] border border-white/10 relative group">
                  <p className="text-sm text-gray-400 mb-3">{t("auth.signup.yourReferral")}</p>
                  <div className="flex items-center justify-center gap-3 mb-6">
                    <code className="text-4xl font-mono font-bold text-indigo-400 tracking-wider">
                      {newReferralCode}
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(newReferralCode);
                      }}
                      className="p-3 rounded-xl bg-white/5 hover:bg-white/10 text-white transition-all active:scale-95"
                      title={t("auth.signup.copyLink")}
                    >
                      <span className="text-xl">📋</span>
                    </button>
                  </div>

                  {/* Share Buttons */}
                  <div className="flex flex-col gap-3">
                    <button
                      onClick={() => {
                        const shareUrl = `https://forexsai.com/signup?ref=${newReferralCode}`;
                        const message = `🚀 ForexSAI: ${shareUrl}`;
                        // Simplified message for demo purposes, assume t() keys exist in real app for message
                        window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
                      }}
                      className="w-full py-3 rounded-xl bg-[#25D366]/10 hover:bg-[#25D366]/20 text-[#25D366] font-bold border border-[#25D366]/20 transition-all flex items-center justify-center gap-2"
                    >
                      {t("auth.signup.shareWhatsApp")}
                    </button>

                    <button
                      onClick={() => {
                        const shareUrl = `https://forexsai.com/signup?ref=${newReferralCode}`;
                        navigator.clipboard.writeText(shareUrl);
                      }}
                      className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 font-medium transition-all flex items-center justify-center gap-2"
                    >
                      {t("auth.signup.copyLink")}
                    </button>
                  </div>
                </div>
              )}

              <div className="pt-4">
                <Link
                  href="/login"
                  className="block w-full py-4 rounded-xl bg-white text-black font-bold text-center hover:bg-gray-200 transition-colors shadow-lg"
                >
                  {t("nav.login")}
                </Link>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Login Link */}
        {!success && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { delay: 0.2 } }}
            className="text-center text-gray-500 mt-8 font-medium"
          >
            {t("auth.signup.haveAccount")} {" "}
            <Link
              href="/login"
              className="text-indigo-400 hover:text-indigo-300 underline underline-offset-4 transition-colors"
            >
              {t("nav.login")}
            </Link>
          </motion.p>
        )}
      </motion.div>
    </main>
  );
}

function SignupLoading() {
  return (
    <div className="min-h-screen bg-[#0B1220] flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-10 h-10 animate-spin text-indigo-500 mx-auto mb-4" />
        <p className="text-gray-400 font-medium">ForexsAi...</p>
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
