"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth/store";
import { useI18n } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const { t } = useI18n();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [resendingEmail, setResendingEmail] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setErrorCode(null);
    setResendSuccess(false);

    try {
      const loginPromise = login(email, password);
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("Bağlantı zaman aşımına uğradı. Lütfen tekrar deneyin.")), 15000)
      );
      const result = await Promise.race([loginPromise, timeoutPromise]);
      if (!result.success) {
        setErrorCode(result.error_code || null);
        throw new Error(result.error || t("auth.login.failed") || "Login failed");
      }
      await new Promise(resolve => setTimeout(resolve, 100));
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  const handleResendVerification = async () => {
    if (!email) return;
    setResendingEmail(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "https://upbeat-flow-production.up.railway.app"}/api/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setResendSuccess(true);
      } else {
        setError(data.error || "Email gönderilemedi.");
      }
    } catch {
      setError("Bağlantı hatası. Lütfen tekrar deneyin.");
    } finally {
      setResendingEmail(false);
    }
  };

  return (
    <div className="min-h-screen flex relative">
      {/* Language & Back */}
      <div className="absolute top-6 right-6 z-50">
        <LanguageSwitcher />
      </div>
      <div className="absolute top-6 left-6 z-50">
        <Link
          href="/welcome"
          className="flex items-center gap-2 text-xs uppercase tracking-widest text-gray-500 hover:text-white transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Back
        </Link>
      </div>

      {/* LEFT PANEL — Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center px-16 xl:px-24 relative border-r border-white/5">
        {/* Ambient glow */}
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-cyan-500/5 blur-3xl rounded-full pointer-events-none" />

        <div className="relative max-w-md">
          {/* Logo */}
          <div className="flex items-center gap-1 mb-16">
            <span className="text-2xl font-bold tracking-[0.15em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">
              FOREXS
            </span>
            <span className="text-2xl font-light tracking-[0.15em] text-white/90">AI</span>
          </div>

          <h1 className="text-5xl xl:text-6xl font-sans leading-tight mb-6">
            <span className="font-bold tracking-[0.1em] bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 bg-clip-text text-transparent block">
              ADVANCED
            </span>
            <span className="font-light tracking-[0.1em] text-white/70 block mt-1">
              TRADING INTELLIGENCE
            </span>
          </h1>

          <p className="text-gray-500 font-light text-base leading-relaxed mb-12 border-l-2 border-cyan-500/40 pl-4">
            Neural network-powered market analysis for NASDAQ, XAUUSD, DAX and US OIL.
          </p>

          {/* Feature list */}
          <div className="space-y-5">
            {[
              { icon: "◆", label: "30M+ data-trained ML models" },
              { icon: "◆", label: "350+ technical pattern recognition" },
              { icon: "◆", label: "Real-time signal generation" },
              { icon: "◆", label: "Claude AI news & sentiment" },
            ].map((f) => (
              <div key={f.label} className="flex items-center gap-4">
                <span className="text-cyan-500/60 text-[8px]">{f.icon}</span>
                <span className="text-gray-400 text-sm font-light tracking-wide">{f.label}</span>
              </div>
            ))}
          </div>

          {/* Sub tagline */}
          <div className="mt-16 pt-8 border-t border-white/5">
            <p className="text-xs uppercase tracking-[0.3em] text-gray-600">
              Algorithmic · Neural · Autonomous
            </p>
          </div>
        </div>
      </div>

      {/* RIGHT PANEL — Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-1 justify-center mb-10">
            <span className="text-2xl font-bold tracking-[0.15em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">
              FOREXS
            </span>
            <span className="text-2xl font-light tracking-[0.15em] text-white/90">AI</span>
          </div>

          {/* Card */}
          <div className="bg-white/[0.03] backdrop-blur-2xl rounded-2xl border border-white/8 p-8 shadow-2xl">
            <div className="mb-8">
              <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-2">Welcome back</p>
              <h2 className="text-2xl font-light text-white tracking-wide">
                {t("nav.login") || "Sign In"}
              </h2>
            </div>

            {/* Error */}
            {error && (
              <div className={`mb-6 p-4 rounded-xl border ${errorCode === "EMAIL_NOT_VERIFIED" ? "bg-amber-500/8 border-amber-500/20" : "bg-red-500/8 border-red-500/20"}`}>
                <div className="flex items-center gap-3 mb-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={errorCode === "EMAIL_NOT_VERIFIED" ? "#f59e0b" : "#f87171"} strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                  <span className={`text-sm font-light ${errorCode === "EMAIL_NOT_VERIFIED" ? "text-amber-400" : "text-red-400"}`}>{error}</span>
                </div>
                {errorCode === "EMAIL_NOT_VERIFIED" && (
                  <div className="mt-3 pt-3 border-t border-amber-500/20">
                    {resendSuccess ? (
                      <p className="text-xs text-emerald-400">✓ Doğrulama linki gönderildi!</p>
                    ) : (
                      <button
                        type="button"
                        onClick={async () => {
                          setResendingEmail(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/auth/resend-verification`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ email }),
                            });
                            if (res.ok) {
                              setResendSuccess(true);
                            }
                          } catch {
                            // Ignore errors
                          } finally {
                            setResendingEmail(false);
                          }
                        }}
                        disabled={resendingEmail}
                        className="text-xs text-amber-400 hover:text-amber-300 transition-colors disabled:opacity-50"
                      >
                        {resendingEmail ? "Gönderiliyor..." : "Doğrulama linkini tekrar gönder →"}
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-5">
              {/* Email */}
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">
                  {t("auth.signup.emailLabel") || "Email"}
                </label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t("auth.signup.emailPlaceholder") || "you@example.com"}
                    required
                    className="w-full pl-11 pr-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-white/20 focus:bg-white/[0.06] transition-all"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">
                  {t("auth.signup.passwordLabel") || "Password"}
                </label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full pl-11 pr-12 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-white/20 focus:bg-white/[0.06] transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 transition-colors"
                  >
                    {showPassword ? (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
                    ) : (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <Link href="/forgot-password" className="text-xs text-gray-500 hover:text-cyan-400 transition-colors tracking-wide">
                  {t("auth.login.forgotPassword") || "Forgot Password?"}
                </Link>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-sm bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.1)] hover:shadow-[0_0_25px_rgba(192,192,192,0.25)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
                ) : (
                  t("auth.signup.loginLink") || "Sign In"
                )}
              </button>
            </form>

            {/* Demo Mode - only in dev */}
            {process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_DEMO_MODE === "true" && (
              <>
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-white/5" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-4 bg-transparent text-gray-600 text-xs uppercase tracking-widest">or</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={async () => {
                    setLoading(true);
                    const { setUser, setToken } = useAuthStore.getState();
                    const demoUser = {
                      id: "999",
                      email: "demo@forexsai.com",
                      full_name: "Demo Trader",
                      membership_tier: "pro" as const,
                      tier_expires_at: null,
                      referral_code: "DEMO999",
                      referral_count: 0,
                      email_verified: true,
                      is_pro: true,
                      can_use_claude: true,
                    };
                    setUser(demoUser);
                    setToken("demo-token-localhost-only");
                    await new Promise(resolve => setTimeout(resolve, 200));
                    router.push("/");
                  }}
                  className="w-full py-3 rounded-lg bg-white/5 border border-white/8 hover:bg-white/8 transition-all text-amber-400/70 text-xs uppercase tracking-widest font-light"
                >
                  🧪 Demo Mode
                </button>
              </>
            )}

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/5" />
              </div>
            </div>

            <p className="text-center text-xs text-gray-600 tracking-wide">
              {t("auth.signup.dontHaveAccount") || "No account?"}{" "}
              <Link href="/signup" className="text-gray-400 hover:text-white transition-colors">
                {t("nav.startFree") || "Create Account"}
              </Link>
            </p>
          </div>

          <p className="text-center text-gray-700 text-xs mt-6 tracking-wide">
            By signing in, you agree to our{" "}
            <Link href="/terms" className="hover:text-gray-500 transition-colors">Terms</Link>
            {" "}and{" "}
            <Link href="/privacy" className="hover:text-gray-500 transition-colors">Privacy Policy</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
