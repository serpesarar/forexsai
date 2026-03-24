import { create } from "zustand";
import { persist } from "zustand/middleware";
import { buildApiUrl } from "../api/base";

// Track hydration state
let hasHydrated = false;

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  membership_tier: "free" | "pro" | "enterprise" | "admin";
  tier_expires_at: string | null;
  referral_code: string;
  referral_count: number;
  email_verified: boolean;
  is_pro: boolean;
  can_use_claude: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  _hasHydrated: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setHasHydrated: (state: boolean) => void;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string; error_code?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
      _hasHydrated: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token }),
      setHasHydrated: (state) => set({ _hasHydrated: state }),

      login: async (emailOrToken: string, passwordOrUser?: string | any) => {
        // Check if this is a direct login with token and user
        if (typeof emailOrToken === "string" && typeof passwordOrUser === "object" && passwordOrUser !== null) {
          // Direct login with token and user
          const token = emailOrToken;
          const user = passwordOrUser;
          
          const formattedUser: User = {
            ...user,
            is_pro: ["pro", "enterprise", "admin"].includes(user.membership_tier),
            can_use_claude: ["pro", "enterprise", "admin"].includes(user.membership_tier),
          };

          set({
            user: formattedUser,
            token,
            isAuthenticated: true,
            isLoading: false,
          });

          return { success: true };
        }
        
        // Regular login with email and password
        const email = emailOrToken;
        const password = passwordOrUser as string;
        
        set({ isLoading: true });
        try {
          console.log("[Auth] Login request starting...");
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 20000);
          
          const res = await fetch(buildApiUrl("/api/auth/login"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
            signal: controller.signal,
          });
          clearTimeout(timeoutId);

          console.log("[Auth] Login response:", res.status);
          const data = await res.json();

          if (!res.ok) {
            set({ isLoading: false });
            // Handle specific error codes
            const errorCode = data.error_code;
            let errorMessage = data.detail || data.error || "Giriş başarısız";
            
            if (errorCode === "EMAIL_NOT_VERIFIED") {
              errorMessage = "Email adresiniz doğrulanmamış. Lütfen email kutunuzu kontrol edin.";
            }
            
            return { success: false, error: errorMessage, error_code: errorCode };
          }

          const user: User = {
            ...data.user,
            is_pro: ["pro", "enterprise", "admin"].includes(data.user.membership_tier),
            can_use_claude: ["pro", "enterprise", "admin"].includes(data.user.membership_tier),
          };

          set({
            user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
          });

          console.log("[Auth] Login success, token set");
          return { success: true };
        } catch (error: any) {
          console.error("[Auth] Login error:", error?.name, error?.message);
          set({ isLoading: false });
          if (error?.name === "AbortError") {
            return { success: false, error: "Sunucu yanıt vermedi. Lütfen tekrar deneyin." };
          }
          return { success: false, error: "Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin." };
        }
      },

      logout: async () => {
        const { token } = get();
        
        if (token) {
          try {
            await fetch(buildApiUrl("/api/auth/logout"), {
              method: "POST",
              headers: { Authorization: `Bearer ${token}` },
            });
          } catch {
            // Ignore logout errors
          }
        }

        set({ user: null, token: null, isAuthenticated: false });
      },

      refreshUser: async () => {
        const { token } = get();
        if (!token) return;

        try {
          const res = await fetch(buildApiUrl("/api/auth/me"), {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (res.ok) {
            const data = await res.json();
            const user: User = {
              ...data,
              is_pro: ["pro", "enterprise", "admin"].includes(data.membership_tier),
              can_use_claude: ["pro", "enterprise", "admin"].includes(data.membership_tier),
            };
            set({ user, isAuthenticated: true });
          } else {
            // Token invalid, logout
            set({ user: null, token: null, isAuthenticated: false });
          }
        } catch {
          // Network error, keep current state
        }
      },

      checkAuth: async () => {
        const { token, user } = get();
        
        // If we have token and user from persist, consider authenticated
        if (token && user) {
          set({ isAuthenticated: true });
          return true;
        }
        
        if (!token) {
          set({ isAuthenticated: false });
          return false;
        }

        // Token exists but no user - try to refresh
        await get().refreshUser();
        return get().isAuthenticated;
      },
    }),
    {
      name: "xauusd-auth",
      partialize: (state) => ({ token: state.token, user: state.user }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.setHasHydrated(true);
          // If token and user exist after hydration, set authenticated
          if (state.token && state.user) {
            state.isAuthenticated = true;
          }
        }
        hasHydrated = true;
      },
    }
  )
);

// Export hydration check
export const waitForHydration = () => {
  return new Promise<void>((resolve) => {
    if (hasHydrated || useAuthStore.getState()._hasHydrated) {
      resolve();
    } else {
      const unsub = useAuthStore.subscribe((state) => {
        if (state._hasHydrated) {
          unsub();
          resolve();
        }
      });
    }
  });
};

// Helper hooks
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsPro = () => useAuthStore((state) => state.user?.is_pro ?? false);
export const useCanUseClaude = () => useAuthStore((state) => state.user?.can_use_claude ?? false);
export const useMembershipTier = () => useAuthStore((state) => state.user?.membership_tier ?? "free");
