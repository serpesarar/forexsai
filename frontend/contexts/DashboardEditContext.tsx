"use client";

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";

export interface DashboardCard {
  id: string;
  title: string;
  column: "left" | "center" | "right";
  order: number;
  visible: boolean;
  size: "normal" | "large" | "compact";
  collapsed: boolean;
}

export interface DashboardLayout {
  cards: DashboardCard[];
  version: number;
}

interface HistoryState {
  past: DashboardLayout[];
  future: DashboardLayout[];
}

interface DashboardEditContextType {
  isEditMode: boolean;
  toggleEditMode: () => void;
  setEditMode: (value: boolean) => void;
  layout: DashboardLayout;
  setLayout: React.Dispatch<React.SetStateAction<DashboardLayout>>;
  moveCard: (cardId: string, toColumn: "left" | "center" | "right", toIndex: number) => void;
  toggleCardVisibility: (cardId: string) => void;
  toggleCardCollapsed: (cardId: string) => void;
  setCardSize: (cardId: string, size: "normal" | "large" | "compact") => void;
  saveLayout: () => void;
  resetLayout: () => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  activeCardId: string | null;
  setActiveCardId: (id: string | null) => void;
  dragOverColumn: string | null;
  setDragOverColumn: (column: string | null) => void;
}

const DEFAULT_LAYOUT: DashboardLayout = {
  cards: [
    { id: "signal-nasdaq", title: "NASDAQ Trend", column: "left", order: 0, visible: true, size: "normal", collapsed: false },
    { id: "signal-xauusd", title: "XAUUSD Trend", column: "left", order: 1, visible: true, size: "normal", collapsed: false },
    { id: "pattern-engine", title: "Pattern Engine V2", column: "center", order: 0, visible: true, size: "large", collapsed: false },
    { id: "claude-patterns", title: "Claude Patterns", column: "center", order: 1, visible: true, size: "normal", collapsed: false },
    { id: "sentiment", title: "AI Sentiment", column: "right", order: 0, visible: true, size: "normal", collapsed: false },
    { id: "news", title: "Market News", column: "right", order: 1, visible: true, size: "normal", collapsed: false },
    { id: "ai-panels", title: "AI Prediction Panels", column: "center", order: 2, visible: true, size: "large", collapsed: false },
  ],
  version: 2,
};

const LAYOUT_STORAGE_KEY = "dashboard-layout-v2";
const MAX_HISTORY = 50;

const DashboardEditContext = createContext<DashboardEditContextType | undefined>(undefined);

export function DashboardEditProvider({ children }: { children: React.ReactNode }) {
  const [isEditMode, setIsEditMode] = useState(false);
  const [layout, setLayout] = useState<DashboardLayout>(DEFAULT_LAYOUT);
  const [history, setHistory] = useState<HistoryState>({ past: [], future: [] });
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  const isUndoRedo = useRef(false);

  // Load layout from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LAYOUT_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.version === 2) {
          setLayout(parsed);
        }
      }
    } catch (e) {
      console.warn("Failed to load dashboard layout:", e);
    }
  }, []);

  // Track history for undo/redo
  useEffect(() => {
    if (isUndoRedo.current) {
      isUndoRedo.current = false;
      return;
    }
    // Only track when in edit mode
    if (!isEditMode) return;
    
    setHistory((prev) => ({
      past: [...prev.past.slice(-MAX_HISTORY), layout],
      future: [],
    }));
  }, [layout, isEditMode]);

  const toggleEditMode = useCallback(() => {
    setIsEditMode((prev) => !prev);
    if (!isEditMode) {
      setHistory({ past: [], future: [] });
    }
  }, [isEditMode]);

  const moveCard = useCallback((cardId: string, toColumn: "left" | "center" | "right", toIndex: number) => {
    setLayout((prev) => {
      const cards = [...prev.cards];
      const cardIndex = cards.findIndex((c) => c.id === cardId);
      if (cardIndex === -1) return prev;

      const card = { ...cards[cardIndex] };
      const oldColumn = card.column;
      card.column = toColumn;

      // Remove from old position
      cards.splice(cardIndex, 1);

      // Get cards in target column and recalculate orders
      const columnCards = cards.filter((c) => c.column === toColumn);
      const otherCards = cards.filter((c) => c.column !== toColumn);

      // Insert at new position
      columnCards.splice(toIndex, 0, card);

      // Recalculate orders
      columnCards.forEach((c, i) => {
        c.order = i;
      });

      // Also recalculate old column if different
      if (oldColumn !== toColumn) {
        const oldColumnCards = otherCards.filter((c) => c.column === oldColumn);
        oldColumnCards.forEach((c, i) => {
          c.order = i;
        });
      }

      return {
        ...prev,
        cards: [...otherCards.filter((c) => c.column !== oldColumn), ...cards.filter((c) => c.column === oldColumn && c.id !== cardId), ...columnCards],
      };
    });
  }, []);

  const toggleCardVisibility = useCallback((cardId: string) => {
    setLayout((prev) => ({
      ...prev,
      cards: prev.cards.map((c) =>
        c.id === cardId ? { ...c, visible: !c.visible } : c
      ),
    }));
  }, []);

  const toggleCardCollapsed = useCallback((cardId: string) => {
    setLayout((prev) => ({
      ...prev,
      cards: prev.cards.map((c) =>
        c.id === cardId ? { ...c, collapsed: !c.collapsed } : c
      ),
    }));
  }, []);

  const setCardSize = useCallback((cardId: string, size: "normal" | "large" | "compact") => {
    setLayout((prev) => ({
      ...prev,
      cards: prev.cards.map((c) =>
        c.id === cardId ? { ...c, size } : c
      ),
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

  const undo = useCallback(() => {
    setHistory((prev) => {
      if (prev.past.length <= 1) return prev;
      const newPast = [...prev.past];
      const current = newPast.pop()!;
      const previous = newPast[newPast.length - 1];
      
      isUndoRedo.current = true;
      setLayout(previous);
      
      return {
        past: newPast,
        future: [current, ...prev.future],
      };
    });
  }, []);

  const redo = useCallback(() => {
    setHistory((prev) => {
      if (prev.future.length === 0) return prev;
      const [next, ...newFuture] = prev.future;
      
      isUndoRedo.current = true;
      setLayout(next);
      
      return {
        past: [...prev.past, next],
        future: newFuture,
      };
    });
  }, []);

  return (
    <DashboardEditContext.Provider
      value={{
        isEditMode,
        toggleEditMode,
        setEditMode: setIsEditMode,
        layout,
        setLayout,
        moveCard,
        toggleCardVisibility,
        toggleCardCollapsed,
        setCardSize,
        saveLayout,
        resetLayout,
        undo,
        redo,
        canUndo: history.past.length > 1,
        canRedo: history.future.length > 0,
        activeCardId,
        setActiveCardId,
        dragOverColumn,
        setDragOverColumn,
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

// Helper to get cards by column, sorted by order
export function useColumnCards(column: "left" | "center" | "right") {
  const { layout } = useDashboardEdit();
  return layout.cards
    .filter((c) => c.column === column && c.visible)
    .sort((a, b) => a.order - b.order);
}
