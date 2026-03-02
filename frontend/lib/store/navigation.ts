import { create } from "zustand";

type ViewType = "dashboard" | "charts" | "trading" | "analysis" | "signals" | "news-correlation";

interface NavigationState {
    activeView: ViewType;
    setActiveView: (view: ViewType) => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
    activeView: "dashboard",
    setActiveView: (view) => set({ activeView: view }),
}));
