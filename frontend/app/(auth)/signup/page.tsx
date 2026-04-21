"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { getApiBase } from "@/lib/api/base";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import Turnstile from "react-turnstile";

const API_BASE = getApiBase();

// Confetti effect using canvas
function triggerConfetti() {
  if (typeof window === "undefined") return;
  
  const duration = 3000;
  const animationEnd = Date.now() + duration;
  const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

  function random(min: number, max: number) {
    return Math.random() * (max - min) + min;
  }

  const interval = setInterval(function() {
    const timeLeft = animationEnd - Date.now();

    if (timeLeft <= 0) {
      return clearInterval(interval);
    }

    const particleCount = 50 * (timeLeft / duration);
    
    // Create confetti particles
    for (let i = 0; i < particleCount; i++) {
      createParticle(random(0, window.innerWidth), random(0, window.innerHeight));
    }
  }, 250);

  function createParticle(x: number, y: number) {
    const particle = document.createElement('div');
    particle.style.position = 'fixed';
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';
    particle.style.width = '10px';
    particle.style.height = '10px';
    particle.style.backgroundColor = ['#00E0C6', '#3B82F6', '#F59E0B', '#EF4444', '#10B981'][Math.floor(Math.random() * 5)];
    particle.style.borderRadius = '50%';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '9999';
    document.body.appendChild(particle);

    const animation = particle.animate([
      { transform: 'translate(0, 0) rotate(0deg)', opacity: 1 },
      { transform: `translate(${random(-200, 200)}px, ${random(-200, 500)}px) rotate(${random(0, 360)}deg)`, opacity: 0 }
    ], {
      duration: random(1000, 3000),
      easing: 'cubic-bezier(0, .9, .57, 1)',
      delay: random(0, 200)
    });

    animation.onfinish = () => particle.remove();
  }
}

function SignupForm() {
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Form state
  const [step, setStep] = useState<"form" | "otp" | "success">("form");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [referralCode, setReferralCode] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [otpCode, setOtpCode] = useState(["", "", "", "", "", ""]);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newReferralCode, setNewReferralCode] = useState<string | null>(null);

  useEffect(() => {
    const ref = searchParams.get("ref");
    if (ref) setReferralCode(ref);
  }, [searchParams]);

  // Handle OTP input
  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) value = value[0];
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otpCode];
    newOtp[index] = value;
    setOtpCode(newOtp);
    
    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otpCode[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  // Step 1: Submit registration
  const handleSignup = async () => {
    setLoading(true);
    setError(null);
    
    if (!email.includes("@")) {
      setError(t("auth.signup.invalidEmail") || "Please enter a valid email");
      setLoading(false);
      return;
    }
    if (password.length < 5) {
      setError(t("auth.signup.passwordTooShort") || "Password must be at least 5 characters");
      setLoading(false);
      return;
    }
    if (!turnstileToken) {
      setError(t("auth.signup.turnstileRequired"));
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
          turnstile_token: turnstileToken 
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");
      
      setNewReferralCode(data.referral_code);
      setStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally { 
      setLoading(false); 
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async () => {
    setLoading(true);
    setError(null);
    
    const code = otpCode.join("");
    if (code.length !== 6) {
      setError(t("auth.signup.enter6Digits"));
      setLoading(false);
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE}/api/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp_code: code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Verification failed");
      
      setStep("success");
      setTimeout(triggerConfetti, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResendOTP = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        setError(null);
        alert(t("auth.signup.resendSuccess"));
      }
    } catch {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-20 sm:p-8 relative overflow-hidden">
      {/* Starry Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        {/* Gradient background */}
        <div className="absolute inset-0" style={{ background: 'linear-gradient(135deg, #0a0f1e 0%, #080d1a 50%, #060a14 100%)' }} />
        
        {/* Animated stars */}
        <div className="stars-container">
          {[...Array(100)].map((_, i) => (
            <div
              key={i}
              className="star"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                width: `${Math.random() * 2 + 1}px`,
                height: `${Math.random() * 2 + 1}px`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${Math.random() * 3 + 2}s`,
              }}
            />
          ))}
        </div>
        
        {/* Gradient orbs */}
        <div className="absolute -top-40 -left-40 w-[800px] h-[800px] rounded-full opacity-30"
          style={{ background: 'radial-gradient(circle, rgba(0,224,198,0.15) 0%, transparent 70%)' }} />
        <div className="absolute top-1/3 -right-20 w-[600px] h-[600px] rounded-full opacity-25"
          style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)' }} />
        <div className="absolute -bottom-40 left-1/3 w-[700px] h-[700px] rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)' }} />
        
        {/* Vignette */}
        <div className="absolute inset-0"
          style={{ background: 'radial-gradient(ellipse at center, transparent 0%, rgba(11,18,32,0.6) 100%)' }} />
      </div>
      
      <style jsx>{`
        .stars-container {
          position: absolute;
          inset: 0;
        }
        .star {
          position: absolute;
          background: white;
          border-radius: 50%;
          opacity: 0;
          animation: twinkle ease-in-out infinite;
        }
        @keyframes twinkle {
          0%, 100% { opacity: 0; transform: scale(0.5); }
          50% { opacity: 0.8; transform: scale(1); }
        }
      `}</style>
      {/* Language */}
      <div className="absolute top-4 right-4 sm:top-6 sm:right-6 z-50">
        <LanguageSwitcher />
      </div>
      
      {/* Back */}
      <div className="absolute top-4 left-4 sm:top-6 sm:left-6 z-50">
        <Link href="/welcome" className="flex items-center gap-2 text-xs uppercase tracking-widest text-gray-500 hover:text-white transition-colors">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
          Back
        </Link>
      </div>

      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-1 justify-center mb-10">
          <span className="text-2xl font-bold tracking-[0.15em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">FOREXS</span>
          <span className="text-2xl font-light tracking-[0.15em] text-white/90">AI</span>
        </div>

        {/* STEP 1: Registration Form */}
        {step === "form" && (
          <div className="bg-white/[0.03] backdrop-blur-2xl rounded-2xl border border-white/8 p-6 sm:p-8 shadow-2xl">
            <div className="mb-8">
              <p className="text-xs uppercase tracking-[0.3em] text-gray-500 mb-2">{t("auth.signup.start") || "Get Started"}</p>
              <h2 className="text-2xl font-light text-white">{t("auth.signup.createAccount") || "Create Account"}</h2>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-xl bg-red-500/8 border border-red-500/20">
                <span className="text-red-400 text-sm font-light">{error}</span>
              </div>
            )}

            <div className="space-y-5">
              {/* Email */}
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.email") || "Email"}</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-cyan-500/50 transition-all"
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.password") || "Password"}</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-cyan-500/50 transition-all"
                />
                <p className="mt-1 text-xs text-gray-600">{t("auth.signup.passwordHint") || "At least 5 characters"}</p>
              </div>

              {/* Full Name */}
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.fullName") || "Full Name (Optional)"}</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-light focus:outline-none focus:border-cyan-500/50 transition-all"
                />
              </div>

              {/* Referral Code */}
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.referral") || "Invite Code (Optional)"}</label>
                <input
                  type="text"
                  value={referralCode}
                  onChange={(e) => setReferralCode(e.target.value.toUpperCase())}
                  placeholder="ABCD1234"
                  className="w-full px-4 py-3.5 rounded-lg bg-white/[0.04] border border-white/8 text-white placeholder-gray-600 text-sm font-mono uppercase tracking-wider focus:outline-none focus:border-cyan-500/50 transition-all"
                />
              </div>

              {/* Turnstile */}
              <div className="flex justify-center py-2">
                <Turnstile
                  sitekey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || "1x00000000000000000000AA"}
                  onVerify={(token) => setTurnstileToken(token)}
                  onError={() => setTurnstileToken(null)}
                  theme="dark"
                />
              </div>

              {/* Submit */}
              <button
                onClick={handleSignup}
                disabled={loading}
                className="w-full py-3.5 rounded-lg bg-gradient-to-r from-cyan-600 via-cyan-500 to-cyan-600 border border-cyan-400/30 shadow-[0_0_20px_rgba(0,224,198,0.2)] hover:shadow-[0_0_30px_rgba(0,224,198,0.35)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium disabled:opacity-50"
              >
                {loading ? t("auth.signup.processing") : t("auth.signup.continue")}
              </button>
            </div>

            <p className="text-center text-gray-600 mt-6 text-xs">
              {t("auth.signup.haveAccount") || "Already have an account?"}{" "}
              <Link href="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors">
                {t("nav.login")}
              </Link>
            </p>
          </div>
        )}

        {/* STEP 2: OTP Verification */}
        {step === "otp" && (
          <div className="bg-white/[0.03] backdrop-blur-2xl rounded-2xl border border-white/8 p-6 sm:p-8 shadow-2xl text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <svg className="w-8 h-8 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M22 17H2a3 3 0 0 0 3-3V9a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v5a3 3 0 0 0 3 3z"/>
                <path d="M6 9V5a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4"/>
              </svg>
            </div>
            
            <h2 className="text-2xl font-light text-white mb-2">{t("auth.signup.verifyEmail") || "Verify Your Email"}</h2>
            <p className="text-gray-400 text-sm mb-6">
              {t("auth.signup.otpSent") || "We've sent a 6-digit code to"}<br/>
              <span className="text-white font-medium">{email}</span>
            </p>

            {error && (
              <div className="mb-6 p-3 rounded-xl bg-red-500/8 border border-red-500/20">
                <span className="text-red-400 text-sm">{error}</span>
              </div>
            )}

            {/* OTP Inputs */}
            <div className="flex justify-center gap-2 mb-6">
              {otpCode.map((digit, index) => (
                <input
                  key={index}
                  id={`otp-${index}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(index, e)}
                  className="w-12 h-14 text-center text-2xl font-bold bg-white/[0.04] border border-white/8 rounded-lg text-white focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                />
              ))}
            </div>

            <button
              onClick={handleVerifyOTP}
              disabled={loading || otpCode.join("").length !== 6}
              className="w-full py-3.5 rounded-lg bg-gradient-to-r from-cyan-600 via-cyan-500 to-cyan-600 border border-cyan-400/30 shadow-[0_0_20px_rgba(0,224,198,0.2)] hover:shadow-[0_0_30px_rgba(0,224,198,0.35)] transition-all duration-300 text-white uppercase tracking-widest text-xs font-medium disabled:opacity-50 mb-4"
            >
              {loading ? t("auth.signup.verifying") : t("auth.signup.verify")}
            </button>

            <button
              onClick={handleResendOTP}
              disabled={loading}
              className="text-xs text-gray-500 hover:text-cyan-400 transition-colors"
            >
              {t("auth.signup.resendCode") || "Didn't receive it? Resend code"}
            </button>
          </div>
        )}

        {/* STEP 3: Success */}
        {step === "success" && (
          <div className="bg-white/[0.03] backdrop-blur-2xl rounded-2xl border border-white/8 p-6 sm:p-8 shadow-2xl text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center animate-bounce">
              <svg className="w-10 h-10 text-green-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            
            <h2 className="text-3xl font-light text-white mb-2">🎉 {t("auth.signup.successTitle") || "Welcome!"}</h2>
            <p className="text-gray-400 text-sm mb-6">
              {t("auth.signup.successMessage") || "Your account has been verified successfully."}
            </p>

            {newReferralCode && (
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/8 mb-6">
                <p className="text-xs uppercase tracking-[0.2em] text-gray-500 mb-2">{t("auth.signup.yourInviteCode") || "Your Invite Code"}</p>
                <div className="flex items-center justify-center gap-3">
                  <code className="text-2xl font-mono font-bold text-white/80 tracking-wider">{newReferralCode}</code>
                  <button onClick={() => navigator.clipboard.writeText(newReferralCode!)} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 transition-all">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
                  </button>
                </div>
              </div>
            )}

            <Link
              href="/"
              className="block w-full py-4 rounded-lg bg-gradient-to-r from-cyan-600 via-cyan-500 to-cyan-600 border border-cyan-400/30 shadow-[0_0_25px_rgba(0,224,198,0.3)] hover:shadow-[0_0_40px_rgba(0,224,198,0.5)] transition-all duration-300 text-white uppercase tracking-widest text-sm font-medium animate-pulse"
            >
              {t("auth.signup.goToDashboard") || "Let's Get Started →"}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" /></div>}>
      <SignupForm />
    </Suspense>
  );
}
