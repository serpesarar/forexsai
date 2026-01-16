"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

interface DashboardItem {
  id: string;
  order: number;
}

interface DashboardLayout {
  [columnId: string]: DashboardItem[];
}

interface DashboardEditContextType {
  isEditMode: boolean;
  toggleEditMode: () => void;
  setEditMode: (value: boolean) => void;
  layout: DashboardLayout;
  updateLayout: (columnId: string, items: DashboardItem[]) => void;
  saveLayout: () => void;
  resetLayout: () => void;
}

const DEFAULT_LAYOUT: DashboardLayout = {
  left: [
    { id: "signal-nasdaq", order: 0 },
    { id: "signal-xauusd", order: 1 },
  ],
  center: [
    { id: "pattern-engine", order: 0 },
    { id: "claude-patterns", order: 1 },
  ],
  right: [
    { id: "market-news", order: 0 },
    { id: "claude-sentiment", order: 1 },
  ],
};

const LAYOUT_STORAGE_KEY = "dashboard-layout-v1";

const DashboardEditContext = createContext<DashboardEditContextType | undefined>(undefined);

export function DashboardEditProvider({ children }: { children: React.ReactNode }) {
  const [isEditMode, setIsEditMode] = useState(false);
  const [layout, setLayout] = useState<DashboardLayout>(DEFAULT_LAYOUT);

  // Load layout from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LAYOUT_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setLayout(parsed);
      }
    } catch (e) {
      console.warn("Failed to load dashboard layout:", e);
    }
  }, []);

  const toggleEditMode = useCallback(() => {
    setIsEditMode((prev) => !prev);
  }, []);

  const updateLayout = useCallback((columnId: string, items: DashboardItem[]) => {
    setLayout((prev) => ({
      ...prev,
      [columnId]: items,
    }));
  }, []);

  const saveLayout = useCallback(() => {
    try {
      localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout));
    } catch (e) {
      console.warn("Failed to save dashboard layout:", e);
    }
    setIsEditMode(false);
  }, [layout]);

  const resetLayout = useCallback(() => {
    setLayout(DEFAULT_LAYOUT);
    localStorage.removeItem(LAYOUT_STORAGE_KEY);
  }, []);

  return (
    <DashboardEditContext.Provider
      value={{
        isEditMode,
        toggleEditMode,
        setEditMode: setIsEditMode,
        layout,
        updateLayout,
        saveLayout,
        resetLayout,
      }}
    >
      {children}
    </DashboardEditContext.Provider>
  );
}

export function useDashboardEdit() {
  const context = useContext(DashboardEditContext);
  if (context === undefined) {
    throw new Error("useDashboardEdit must be used within a DashboardEditProvider");
  }
  return context;
}
