"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, useIsAuthenticated } from "../lib/auth/store";
import { Activity, Loader2 } from "lucide-react";

const waitForHydration = (): Promise<void> => {
  return new Promise((resolve) => {
    const check = () => {
      if (useAuthStore.getState()._hasHydrated) {
        resolve();
      } else {
        setTimeout(check, 50);
      }
    };
    check();
  });
};

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const { checkAuth } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const check = async () => {
      await waitForHydration();
      const authed = await checkAuth();
      setIsChecking(false);
      if (!authed) {
        router.push("/welcome");
      }
    };
    check();
  }, []);

  if (isChecking) {
    return (
      <div className="min-h-screen bg-[#0B1220] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#00E0C6] via-purple-500 to-cyan-500 flex items-center justify-center animate-pulse">
              <Activity className="w-8 h-8 text-white" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-[#00E0C6]" />
            <span className="text-gray-400">Yükleniyor...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
