import { create } from "zustand";
import { persist } from "zustand/middleware";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

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
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
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

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          });

          const data = await res.json();

          if (!res.ok) {
            set({ isLoading: false });
            return { success: false, error: data.detail || "Giriş başarısız" };
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

          return { success: true };
        } catch (error) {
          set({ isLoading: false });
          return { success: false, error: "Bağlantı hatası" };
        }
      },

      logout: async () => {
        const { token } = get();
        
        if (token) {
          try {
            await fetch(`${API_BASE}/api/auth/logout`, {
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
          const res = await fetch(`${API_BASE}/api/auth/me`, {
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
