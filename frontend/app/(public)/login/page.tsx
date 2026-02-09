"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, EyeOff, ArrowLeft } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { useAuthStore } from "@/lib/auth/store";
import { fetcher } from "@/lib/api";

export default function LoginPage() {
  const { t } = useI18n();
  const router = useRouter();
  const { login } = useAuthStore();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetcher("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (response.success && response.token) {
        await login(response.token, response.user);
        router.push("/");
      } else {
        setError(response.message || "Login failed");
      }
    } catch (err: any) {
      setError(err.message || "Network error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B1220] text-[#E5E7EB] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Back Button */}
        <Link
          href="/welcome"
          className="inline-flex items-center gap-2 text-[#E5E7EB]/60 hover:text-white transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Welcome
        </Link>

        {/* Login Card */}
        <div className="bg-white/[0.05] backdrop-blur-lg border border-white/[0.10] rounded-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
            <p className="text-[#E5E7EB]/60">Sign in to your ForexsAi account</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#E5E7EB]/80 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-white/[0.05] border border-white/[0.10] rounded-xl text-white placeholder-[#E5E7EB]/40 focus:outline-none focus:ring-2 focus:ring-[#00E0C6]/50 focus:border-[#00E0C6]/50 transition-colors"
                placeholder="Enter your email"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#E5E7EB]/80 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-white/[0.05] border border-white/[0.10] rounded-xl text-white placeholder-[#E5E7EB]/40 focus:outline-none focus:ring-2 focus:ring-[#00E0C6]/50 focus:border-[#00E0C6]/50 transition-colors"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#E5E7EB]/60 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-[#00E0C6] to-[#3B82F6] text-[#0B1220] font-semibold rounded-xl hover:shadow-xl hover:shadow-[#00E0C6]/30 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-[#E5E7EB]/60">
              Don't have an account?{" "}
              <Link href="/signup" className="text-[#00E0C6] hover:text-[#00E0C6]/80 transition-colors font-medium">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
