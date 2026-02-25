"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

function SignupForm() {
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [referralCode, setReferralCode] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [referralValid, setReferralValid] = useState<boolean | null>(null);
  const [referrerName, setReferrerName] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [newReferralCode, setNewReferralCode] = useState<string | null>(null);

  useEffect(() => {
    const ref = searchParams.get("ref");
    if (ref) {
      setReferralCode(ref);
      validateReferralCode(ref);
    }
  }, [searchParams]);

  const getPasswordStrength = (pw: string) => {
    if (pw.length < 5) return 0;
    if (pw.length < 8) return 1;
    if (pw.length < 12) return 2;
    return 3;
  };

  const passwordStrength = getPasswordStrength(password);
  const strengthLabels = [t("auth.signup.weak"), t("auth.signup.medium"), t("auth.signup.strong"), t("auth.signup.secure")];
  const strengthColors = ["bg-red-500", "bg-yellow-500", "bg-emerald-500", "bg-emerald-400"];

  const validateReferralCode = async (code: string) => {
    if (!code || code.length < 4) { setReferralValid(null); setReferrerName(null); return; }
    try {
      const res = await fetch(`${API_BASE}/api/auth/validate-referral/${code}`);
      const data = await res.json();
      setReferralValid(data.valid);
      setReferrerName(data.valid ? data.referrer_name : null);
    } catch { setReferralValid(null); }
  };

  const handleSignup = async () => {
    setLoading(true);
    setError(null);
    if (password !== confirmPassword) { setError(t("auth.signup.passwordMismatch") || "Şifreler eşleşmiyor"); setLoading(false); return; }
    if (password.length < 5) { setError(t("auth.signup.passwordTooShort") || "En az 5 karakter"); setLoading(false); return; }
    try {
      const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName || null, referral_code: referralCode || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kayıt başarısız");
      setNewReferralCode(data.referral_code);
      setSuccess(true);
      setStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bir hata oluştu");
    } finally { setLoading(false); }
  };

  const canProceed = () => {
    if (step === 1) return email.includes("@") && email.includes(".");
    if (step === 2) return password.length >= 5 && password === confirmPassword;
    if (step === 3) return true;
    return false;
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-8 relative">
      {/* Language */}
      <div className="absolute top-6 right-6 z-50">
        <LanguageSwitcher />
      </div>
      <div className="absolute top-6 left-6 z-50">
        <Link href="/welcome" className="flex items-center gap-2 text-xs uppercase tracking-widest text-gray-500 hover:text-white transition-colors">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Back
        </Link>
      </div>

      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex items-center gap-1 justify-center mb-10">
          <span className="text-2xl font-bold tracking-[0.15em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">FOREXS</span>
          <span className="text-2xl font-light tracking-[0.15em] text-white/90">AI</span>
        </div>

        {/* Step dots */}
        {!success && (
          <div className="flex items-center justify-center gap-3 mb-10">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-all duration-300 border ${step > s ? "bg-cyan-500/20 border-cyan-500/50 text-cyan-400" :
                    step === s ? "bg-white/10 border-white/20 text-white" :
                      "bg-white/[0.03] border-white/8 text-gray-600"
                  }`}>
                  {step > s ? (
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
                  ) : s}
                </div>
                {s < 3 && (
                  <div className={`w-10 h-px rounded-full transition-all duration-500 ${step > s ? "bg-cyan-500/40" : "bg-white/8"}`} />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Card */}
        <div className="bg-white/[0.03] backdrop-blur-2xl rounded-2xl border border-white/8 p-8 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/3 blur-3xl pointer-events-none" />

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/8 border border-red-500/20 flex items-center gap-3">
              <svg className="w-4 h-4 text-red-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
              <span className="text-red-400 text-sm font-light">{error}</span>
            </div>
          )}

          {/* Step 1: Email */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">Create Account</p>
                <h2 className="text-xl font-light text-white">{t("auth.signup.title")}</h2>
                <p className="text-sm text-gray-600 mt-1 font-light">{t("auth.signup.subtitle")}</p>
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.emailLabel")}</label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t("auth.signup.emailPlaceholder")} autoFocus
                    className="w-full pl-11 pr-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-white/20 transition-all" />
                </div>
              </div>
              <button onClick={() => setStep(2)} disabled={!canProceed()}
                className="w-full py-3.5 rounded-sm bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.1)] hover:shadow-[0_0_25px_rgba(192,192,192,0.25)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                {t("auth.signup.continue")}
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
              </button>
              <div className="pt-4 border-t border-white/5 space-y-3">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-600">{t("auth.signup.freeFeatures")}</p>
                {[t("auth.signup.features.0"), t("auth.signup.features.1"), t("auth.signup.features.2")].map((f, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="text-cyan-500/50 text-[8px]">◆</span>
                    {f as string}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Password */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">Security</p>
                <h2 className="text-xl font-light text-white">{t("auth.signup.passwordTitle")}</h2>
                <p className="text-sm text-gray-600 mt-1 font-light">{t("auth.signup.passwordSubtitle")}</p>
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.passwordLabel")}</label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t("auth.signup.passwordPlaceholder") as string} autoFocus
                    className="w-full pl-11 pr-12 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-white/20 transition-all" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
                    {showPassword ? (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
                    ) : (
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                    )}
                  </button>
                </div>
                {password && (
                  <div className="mt-3">
                    <div className="h-0.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all duration-500 ${strengthColors[passwordStrength]}`} style={{ width: `${((passwordStrength + 1) / 4) * 100}%` }} />
                    </div>
                    <p className={`text-xs mt-1.5 ${passwordStrength >= 2 ? "text-emerald-400" : "text-gray-600"}`}>{strengthLabels[passwordStrength]}</p>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.passwordRepeatLabel")}</label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                  <input type={showPassword ? "text" : "password"} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••"
                    className="w-full pl-11 pr-12 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-white/20 transition-all" />
                  {confirmPassword && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      {password === confirmPassword ? (
                        <svg className="w-4 h-4 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                      ) : (
                        <svg className="w-4 h-4 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                      )}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex gap-3">
                <button onClick={() => setStep(1)} className="px-4 py-3.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] border border-white/8 text-gray-400 transition-all">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
                </button>
                <button onClick={() => setStep(3)} disabled={!canProceed()}
                  className="flex-1 py-3.5 rounded-sm bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.1)] hover:shadow-[0_0_25px_rgba(192,192,192,0.25)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                  {t("auth.signup.continue")}
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Profile */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-1">Profile</p>
                <h2 className="text-xl font-light text-white">{t("auth.signup.profileTitle")}</h2>
                <p className="text-sm text-gray-600 mt-1 font-light">{t("auth.signup.profileSubtitle")}</p>
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.nameLabel")}</label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                  <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder={t("auth.signup.namePlaceholder") as string}
                    className="w-full pl-11 pr-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-white/20 transition-all" />
                </div>
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.referralLabel")}</label>
                <div className="relative">
                  <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="20 12 20 22 4 22 4 12" /><rect x="2" y="7" width="20" height="5" /><path d="M12 22V7" /><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z" /><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z" /></svg>
                  <input type="text" value={referralCode} onChange={(e) => { setReferralCode(e.target.value.toUpperCase()); validateReferralCode(e.target.value); }} placeholder="ABCD1234"
                    className="w-full pl-11 pr-12 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-mono uppercase tracking-wider focus:outline-none focus:border-white/20 transition-all" />
                  {referralValid !== null && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                      {referralValid ? (
                        <svg className="w-4 h-4 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                      ) : (
                        <svg className="w-4 h-4 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                      )}
                    </div>
                  )}
                </div>
                {referralValid && referrerName && (
                  <p className="mt-2 text-xs text-cyan-400 font-light">✦ {referrerName} invited you</p>
                )}
              </div>
              <div className="p-4 rounded-lg bg-white/[0.03] border border-white/8">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-1">Referral Bonus</p>
                <p className="text-xs text-gray-600 font-light">{t("auth.signup.referralInfo")}</p>
              </div>
              <div className="flex gap-3">
                <button onClick={() => setStep(2)} className="px-4 py-3.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] border border-white/8 text-gray-400 transition-all">
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
                </button>
                <button onClick={handleSignup} disabled={loading}
                  className="flex-1 py-3.5 rounded-sm bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.1)] hover:shadow-[0_0_25px_rgba(192,192,192,0.25)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                  {loading ? (
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
                  ) : t("auth.signup.complete")}
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Success */}
          {step === 4 && success && (
            <div className="text-center space-y-8 py-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div>
                <h2 className="text-2xl font-light text-white mb-2">{t("auth.signup.successTitle")}</h2>
                <p className="text-gray-500 font-light">
                  {t("auth.signup.successText")} <span className="text-gray-300 font-medium">{email}</span>
                </p>
              </div>
              {newReferralCode && (
                <div className="p-6 rounded-xl bg-white/[0.03] border border-white/8">
                  <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-3">{t("auth.signup.yourReferral")}</p>
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <code className="text-3xl font-mono font-bold text-white/80 tracking-wider">{newReferralCode}</code>
                    <button onClick={() => navigator.clipboard.writeText(newReferralCode)} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 transition-all">
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
                    </button>
                  </div>
                  <div className="flex flex-col gap-2">
                    <button onClick={() => { const url = `https://forexsai.com/signup?ref=${newReferralCode}`; window.open(`https://wa.me/?text=${encodeURIComponent(`🚀 ForexSAI: ${url}`)}`, "_blank"); }}
                      className="w-full py-2.5 rounded-lg bg-white/[0.03] border border-white/8 text-green-400/70 text-xs uppercase tracking-widest hover:bg-white/[0.06] transition-all">
                      {t("auth.signup.shareWhatsApp")}
                    </button>
                    <button onClick={() => navigator.clipboard.writeText(`https://forexsai.com/signup?ref=${newReferralCode}`)}
                      className="w-full py-2.5 rounded-lg bg-white/[0.03] border border-white/8 text-gray-500 text-xs uppercase tracking-widest hover:bg-white/[0.06] transition-all">
                      {t("auth.signup.copyLink")}
                    </button>
                  </div>
                </div>
              )}
              <Link href="/login" className="block w-full py-3.5 rounded-sm bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.1)] hover:shadow-[0_0_25px_rgba(192,192,192,0.25)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium text-center">
                {t("nav.login")}
              </Link>
            </div>
          )}
        </div>

        {!success && (
          <p className="text-center text-gray-600 mt-6 text-xs tracking-wide">
            {t("auth.signup.haveAccount")}{" "}
            <Link href="/login" className="text-gray-400 hover:text-white transition-colors">
              {t("nav.login")}
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
      <svg className="w-8 h-8 animate-spin text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
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
