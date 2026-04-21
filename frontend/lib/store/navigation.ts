import { create } from "zustand";

type ViewType = "dashboard" | "trading" | "analysis" | "signals" | "news-correlation";

interface NavigationState {
    activeView: ViewType;
    setActiveView: (view: ViewType) => void;
    // Mobile drawer state — only meaningful at < tablet (768px).
    // The Sidebar is ALWAYS mounted but uses CSS transforms to slide off-canvas
    // on mobile; this flag drives that transform.
    mobileSidebarOpen: boolean;
    setMobileSidebarOpen: (open: boolean) => void;
    toggleMobileSidebar: () => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
    activeView: "dashboard",
    setActiveView: (view) => set({ activeView: view, mobileSidebarOpen: false }),
    mobileSidebarOpen: false,
    setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),
    toggleMobileSidebar: () => set((state) => ({ mobileSidebarOpen: !state.mobileSidebarOpen })),
}));
