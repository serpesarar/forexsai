"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuthStore } from "@/lib/auth/store";
import { 
  Eye, EyeOff, Mail, Lock, ArrowRight, 
  TrendingUp, Shield, Zap, AlertCircle, Loader2,
  BarChart3, Brain
} from "lucide-react";
import { AnimatedBackground } from "@/components/welcome/AnimatedBackground";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await login(email, password);
      if (!result.success) {
        throw new Error(result.error || "Login failed");
      }
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E5E7EB] flex relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <AnimatedBackground />
      </div>

      <motion.div 
        initial={{ opacity: 0, x: -30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="hidden lg:flex lg:w-1/2 flex-col justify-center px-12 xl:px-24 relative z-10"
      >
        <div className="max-w-lg">
          <Link href="/welcome" className="flex items-center gap-3 mb-8 group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] flex items-center justify-center shadow-lg shadow-[#00E0C6]/20">
              <TrendingUp className="w-7 h-7 text-[#0B1220]" />
            </div>
            <span className="text-2xl font-bold text-white">ForexsAi</span>
          </Link>

          <h1 className="text-4xl xl:text-5xl font-bold text-white mb-6 leading-tight">
            AI-Powered
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00E0C6] to-[#3B82F6]">
              {" "}Market Analysis
            </span>
          </h1>

          <p className="text-lg text-[#E5E7EB]/60 mb-10 leading-relaxed">
            30M+ data-trained ML model, 350+ pattern recognition, and 
            real-time market analysis to optimize your trading decisions.
          </p>

          <div className="space-y-4">
            {[
              { icon: Brain, text: "Claude AI News & Sentiment Analysis" },
              { icon: BarChart3, text: "350+ Technical Pattern Recognition" },
              { icon: Zap, text: "Real-time Signal Generation" },
            ].map((feature, i) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.3 + i * 0.1 }}
                className="flex items-center gap-3 text-[#E5E7EB]/80"
              >
                <div className="w-10 h-10 rounded-lg bg-[#00E0C6]/10 border border-[#00E0C6]/20 flex items-center justify-center">
                  <feature.icon className="w-5 h-5 text-[#00E0C6]" />
                </div>
                <span>{feature.text}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00E0C6] to-[#3B82F6] flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-[#0B1220]" />
            </div>
            <span className="text-xl font-bold text-white">ForexsAi</span>
          </div>

          <div className="bg-[#0B1220]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-8 shadow-2xl shadow-black/50">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-[#00E0C6]/10 flex items-center justify-center">
                <Shield className="w-4 h-4 text-[#00E0C6]" />
              </div>
              <h2 className="text-2xl font-bold text-white">Welcome Back</h2>
            </div>
            <p className="text-[#E5E7EB]/50 mb-8">Sign in to your account</p>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3"
              >
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                <span className="text-red-400 text-sm">{error}</span>
              </motion.div>
            )}

            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-[#E5E7EB]/80 mb-2">
                  Email Address
                </label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#E5E7EB]/40 group-focus-within:text-[#00E0C6] transition-colors" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                    className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-[#E5E7EB]/30 focus:outline-none focus:border-[#00E0C6]/50 focus:ring-1 focus:ring-[#00E0C6]/50 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#E5E7EB]/80 mb-2">
                  Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#E5E7EB]/40 group-focus-within:text-[#00E0C6] transition-colors" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full pl-12 pr-12 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-[#E5E7EB]/30 focus:outline-none focus:border-[#00E0C6]/50 focus:ring-1 focus:ring-[#00E0C6]/50 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#E5E7EB]/40 hover:text-[#E5E7EB]/70 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex justify-end">
                <Link href="/forgot-password" className="text-sm text-[#00E0C6] hover:text-[#00E0C6]/80 transition-colors">
                  Forgot Password?
                </Link>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] hover:from-[#00E0C6]/90 hover:to-[#3B82F6]/90 text-[#0B1220] font-semibold flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group shadow-lg shadow-[#00E0C6]/20"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Sign In
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </motion.button>
            </form>

            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10" />
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 bg-[#0B1220] text-[#E5E7EB]/40 text-sm">or</span>
              </div>
            </div>

            <p className="text-center text-[#E5E7EB]/60">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="text-[#00E0C6] hover:text-[#00E0C6]/80 font-medium transition-colors">
                Create Free Account
              </Link>
            </p>
          </div>

          <p className="text-center text-[#E5E7EB]/30 text-sm mt-8">
            By signing in, you agree to our{" "}
            <Link href="/terms" className="text-[#E5E7EB]/50 hover:text-[#E5E7EB]/70">Terms of Service</Link>
            {" "}and{" "}
            <Link href="/privacy" className="text-[#E5E7EB]/50 hover:text-[#E5E7EB]/70">Privacy Policy</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
