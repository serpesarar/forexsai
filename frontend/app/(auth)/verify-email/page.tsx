"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [message, setMessage] = useState("Email adresiniz doğrulanıyor...");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Geçersiz doğrulama bağlantısı.");
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await apiClient.post("/api/auth/verify-email", { token });
        
        if (response.data.success) {
          setStatus("success");
          setMessage("Email adresiniz başarıyla doğrulandı!");
          // Redirect to login after 3 seconds
          setTimeout(() => {
            router.push("/login");
          }, 3000);
        } else {
          setStatus("error");
          setMessage(response.data.error || "Doğrulama başarısız oldu.");
        }
      } catch (error: any) {
        setStatus("error");
        setMessage(error.response?.data?.error || "Doğrulama sırasında bir hata oluştu.");
      }
    };

    verifyEmail();
  }, [token, router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        {/* Logo */}
        <div className="flex items-center gap-1 justify-center mb-12">
          <span className="text-2xl font-bold tracking-[0.15em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">
            FOREXS
          </span>
          <span className="text-2xl font-light tracking-[0.15em] text-white/90">AI</span>
        </div>

        {/* Status Card */}
        <div className="bg-white/[0.03] backdrop-blur-2xl rounded-2xl border border-white/8 p-10 shadow-2xl">
          {status === "verifying" && (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-full border-2 border-cyan-500/30 border-t-cyan-500 animate-spin mb-6" />
              <h2 className="text-xl font-light text-white tracking-wide mb-2">Doğrulanıyor</h2>
              <p className="text-gray-500 text-sm font-light">{message}</p>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center mb-6">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <h2 className="text-xl font-light text-white tracking-wide mb-2">Doğrulama Başarılı!</h2>
              <p className="text-gray-500 text-sm font-light mb-6">{message}</p>
              <p className="text-gray-600 text-xs">Giriş sayfasına yönlendiriliyorsunuz...</p>
            </div>
          )}

          {status === "error" && (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mb-6">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="15" y1="9" x2="9" y2="15" />
                  <line x1="9" y1="9" x2="15" y2="15" />
                </svg>
              </div>
              <h2 className="text-xl font-light text-white tracking-wide mb-2">Doğrulama Başarısız</h2>
              <p className="text-gray-500 text-sm font-light mb-6">{message}</p>
              <Link
                href="/login"
                className="text-cyan-400 hover:text-cyan-300 text-sm transition-colors"
              >
                Giriş sayfasına dön →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-16 h-16 rounded-full border-2 border-cyan-500/30 border-t-cyan-500 animate-spin" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
