"use client";

import React, { useState, useCallback } from "react";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  DragOverEvent,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { 
  GripVertical, 
  Check, 
  X, 
  RotateCcw, 
  Settings2, 
  Eye, 
  EyeOff,
  Maximize2,
  Minimize2,
  ChevronUp,
  ChevronDown,
  Undo2,
  Redo2,
  Layers,
  Move,
} from "lucide-react";
import { useDashboardEdit, useColumnCards, DashboardCard, CardSize } from "../contexts/DashboardEditContext";

// ============================================
// SORTABLE CARD WRAPPER
// ============================================
interface SortableCardProps {
  card: DashboardCard;
  children: React.ReactNode;
}

export function SortableCard({ card, children }: SortableCardProps) {
  const { isEditMode, activeCardId, setActiveCardId, toggleCardCollapsed, setCardSize, dragOverCardId } = useDashboardEdit();
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: card.id, 
    disabled: !isEditMode,
    data: { card },
  });
  
  const isDropTarget = dragOverCardId === card.id && !isDragging;

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition || "transform 200ms cubic-bezier(0.25, 1, 0.5, 1)",
    opacity: isDragging ? 0.4 : 1,
    zIndex: isDragging ? 100 : activeCardId === card.id ? 50 : 1,
  };

  const isActive = activeCardId === card.id;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`relative group transition-all duration-300 ${
        isEditMode ? "wobble-animation" : ""
      } ${isDragging ? "scale-[1.02] shadow-2xl shadow-primary/20" : ""} ${
        isActive && isEditMode ? "ring-2 ring-primary ring-offset-2 ring-offset-background" : ""
      }`}
      onClick={() => isEditMode && setActiveCardId(isActive ? null : card.id)}
    >
      {/* Drag Handle */}
      {isEditMode && (
        <div
          {...attributes}
          {...listeners}
          className="absolute -left-3 top-1/2 -translate-y-1/2 z-20 p-2.5 rounded-xl bg-gradient-to-br from-primary to-purple-600 text-white cursor-grab active:cursor-grabbing shadow-lg shadow-primary/30 hover:scale-110 transition-transform"
          title="Sürükleyerek taşı"
          onClick={(e) => e.stopPropagation()}
        >
          <Move className="w-4 h-4" />
        </div>
      )}

      {/* Edit Mode Overlay */}
      {isEditMode && (
        <>
          <div className={`absolute inset-0 rounded-2xl pointer-events-none z-10 transition-all duration-300 ${
            isDragging 
              ? "border-2 border-primary bg-primary/5" 
              : "border-2 border-dashed border-primary/40 hover:border-primary/60"
          }`} />
          
          {/* Card Controls - Top Right */}
          <div className="absolute -top-2 -right-2 z-30 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => { e.stopPropagation(); toggleCardCollapsed(card.id); }}
              className="p-1.5 rounded-lg bg-background/90 border border-white/10 text-textSecondary hover:text-white hover:bg-white/20 transition-all"
              title={card.collapsed ? "Genişlet" : "Daralt"}
            >
              {card.collapsed ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
            </button>
            <button
              onClick={(e) => { 
                e.stopPropagation(); 
                const nextSize: CardSize = card.size === "large" ? "medium" : card.size === "medium" ? "small" : "large";
                setCardSize(card.id, nextSize); 
              }}
              className="p-1.5 rounded-lg bg-background/90 border border-white/10 text-textSecondary hover:text-white hover:bg-white/20 transition-all"
              title="Boyut değiştir"
            >
              {card.size === "large" ? <Minimize2 className="w-3 h-3" /> : <Maximize2 className="w-3 h-3" />}
            </button>
          </div>

          {/* Card Label */}
          <div className="absolute -top-3 left-8 z-20 px-2 py-0.5 rounded-md bg-primary/90 text-white text-[10px] font-medium uppercase tracking-wider">
            {card.title}
          </div>
        </>
      )}

      {/* Collapsed State */}
      {card.collapsed ? (
        <div className="glass-card p-4 flex items-center justify-between">
          <span className="text-sm font-medium text-textSecondary">{card.title}</span>
          <ChevronDown className="w-4 h-4 text-textSecondary" />
        </div>
      ) : (
        children
      )}
    </div>
  );
}

// ============================================
// DROPPABLE COLUMN
// ============================================
interface DroppableColumnProps {
  columnId: "left" | "center" | "right";
  children: React.ReactNode;
}

export function DroppableColumn({ columnId, children }: DroppableColumnProps) {
  const { isEditMode, getCardsByColumn } = useDashboardEdit();
  const { setNodeRef, isOver } = useDroppable({ id: columnId });
  const cards = getCardsByColumn(columnId);

  const isHighlighted = isOver;

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col gap-6 min-h-[200px] transition-all duration-300 rounded-2xl ${
        isEditMode && isHighlighted
          ? "bg-primary/5 ring-2 ring-primary/30 ring-dashed p-2 -m-2"
          : ""
      }`}
    >
      <SortableContext items={cards.map(c => c.id)} strategy={verticalListSortingStrategy}>
        {children}
      </SortableContext>
      
      {/* Empty Column Placeholder */}
      {isEditMode && cards.length === 0 && (
        <div className="flex-1 flex items-center justify-center border-2 border-dashed border-white/20 rounded-xl p-8 text-textSecondary text-sm">
          <Layers className="w-5 h-5 mr-2 opacity-50" />
          Kartları buraya sürükle
        </div>
      )}
    </div>
  );
}

// ============================================
// MAIN DASHBOARD WRAPPER
// ============================================
interface DraggableDashboardProps {
  children: React.ReactNode;
}

export function DraggableDashboard({ children }: DraggableDashboardProps) {
  const { 
    isEditMode, 
    saveLayout, 
    resetLayout, 
    setEditMode,
    moveCard,
    swapCards,
    setActiveCardId,
    setDragOverCardId,
    layout,
  } = useDashboardEdit();
  
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activeCard, setActiveCard] = useState<DashboardCard | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const id = event.active.id as string;
    setActiveId(id);
    setActiveCardId(id);
    const card = layout.cards.find(c => c.id === id);
    setActiveCard(card || null);
  }, [layout.cards, setActiveCardId]);

  const handleDragOver = useCallback((event: DragOverEvent) => {
    const overId = event.over?.id as string | undefined;
    if (overId && !["left", "center", "right"].includes(overId)) {
      // Hovering over another card
      setDragOverCardId(overId);
    } else {
      setDragOverCardId(null);
    }
  }, [setDragOverCardId]);

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    
    setActiveId(null);
    setActiveCard(null);
    setActiveCardId(null);
    setDragOverCardId(null);

    if (!over) return;

    const activeCardId = active.id as string;
    const overId = over.id as string;

    // Skip if dropped on itself
    if (activeCardId === overId) return;

    // Dropped on a column
    if (["left", "center", "right"].includes(overId)) {
      const targetColumn = overId as "left" | "center" | "right";
      const columnCards = layout.cards.filter(c => c.column === targetColumn && c.visible);
      moveCard(activeCardId, targetColumn, columnCards.length);
    } else {
      // Dropped on another card - SWAP them
      swapCards(activeCardId, overId);
    }
  }, [layout.cards, moveCard, swapCards, setActiveCardId, setDragOverCardId]);

  // Get all card IDs for SortableContext
  const cardIds = layout.cards.filter(c => c.visible).map(c => c.id);

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
        {children}
      </SortableContext>

      {/* Drag Overlay - Ghost of dragged item */}
      <DragOverlay dropAnimation={{
        duration: 300,
        easing: "cubic-bezier(0.18, 0.67, 0.6, 1.22)",
      }}>
        {activeCard && (
          <div className="glass-card p-4 rounded-2xl shadow-2xl shadow-primary/30 border-2 border-primary/50 opacity-90 scale-105">
            <div className="flex items-center gap-3">
              <Move className="w-5 h-5 text-primary" />
              <span className="font-medium">{activeCard.title}</span>
            </div>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}

// ============================================
// EDIT MODE FLOATING CONTROLS
// ============================================
export function EditModeControls() {
  const { 
    isEditMode, 
    saveLayout, 
    resetLayout, 
    setEditMode,
    undo,
    redo,
    canUndo,
    canRedo,
    layout,
    toggleCardVisibility,
  } = useDashboardEdit();

  const [showCardManager, setShowCardManager] = useState(false);

  if (!isEditMode) return null;

  return (
    <>
      {/* Main Controls */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-3 rounded-2xl bg-background/95 backdrop-blur-xl border border-white/10 shadow-2xl animate-slide-in-right">
        {/* Status */}
        <div className="flex items-center gap-2 pr-3 border-r border-white/10">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-primary animate-ping" />
          </div>
          <span className="text-xs text-textSecondary font-medium">Düzenleme Modu</span>
        </div>

        {/* Undo/Redo */}
        <div className="flex items-center gap-1 pr-3 border-r border-white/10">
          <button
            onClick={undo}
            disabled={!canUndo}
            className={`p-2 rounded-lg transition-all ${
              canUndo 
                ? "text-textSecondary hover:text-white hover:bg-white/10" 
                : "text-white/20 cursor-not-allowed"
            }`}
            title="Geri Al (Ctrl+Z)"
          >
            <Undo2 className="w-4 h-4" />
          </button>
          <button
            onClick={redo}
            disabled={!canRedo}
            className={`p-2 rounded-lg transition-all ${
              canRedo 
                ? "text-textSecondary hover:text-white hover:bg-white/10" 
                : "text-white/20 cursor-not-allowed"
            }`}
            title="İleri Al (Ctrl+Y)"
          >
            <Redo2 className="w-4 h-4" />
          </button>
        </div>

        {/* Card Manager Toggle */}
        <button
          onClick={() => setShowCardManager(!showCardManager)}
          className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-all ${
            showCardManager 
              ? "bg-primary/20 text-primary" 
              : "text-textSecondary hover:bg-white/10"
          }`}
          title="Kart Yöneticisi"
        >
          <Layers className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">Kartlar</span>
        </button>

        {/* Actions */}
        <button
          onClick={resetLayout}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 text-textSecondary hover:bg-white/10 transition-all"
          title="Varsayılana Sıfırla"
        >
          <RotateCcw className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">Sıfırla</span>
        </button>
        <button
          onClick={() => setEditMode(false)}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-danger/10 text-danger hover:bg-danger/20 transition-all"
          title="İptal Et"
        >
          <X className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">İptal</span>
        </button>
        <button
          onClick={saveLayout}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-success to-emerald-600 text-white font-medium shadow-lg shadow-success/30 hover:shadow-success/50 transition-all"
          title="Değişiklikleri Kaydet"
        >
          <Check className="w-4 h-4" />
          <span className="text-xs font-medium">Kaydet</span>
        </button>
      </div>

      {/* Card Manager Panel */}
      {showCardManager && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 w-[400px] max-w-[90vw] p-4 rounded-2xl bg-background/95 backdrop-blur-xl border border-white/10 shadow-2xl animate-slide-in-right">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Kart Yöneticisi</h3>
            <button 
              onClick={() => setShowCardManager(false)}
              className="p-1 rounded-lg hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4 text-textSecondary" />
            </button>
          </div>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {layout.cards.map((card) => (
              <div
                key={card.id}
                className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                  card.visible 
                    ? "border-white/10 bg-white/5" 
                    : "border-white/5 bg-white/[0.02] opacity-50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    card.column === "left" ? "bg-blue-500" :
                    card.column === "center" ? "bg-purple-500" : "bg-orange-500"
                  }`} />
                  <span className="text-sm">{card.title}</span>
                </div>
                <button
                  onClick={() => toggleCardVisibility(card.id)}
                  className={`p-2 rounded-lg transition-all ${
                    card.visible 
                      ? "text-success hover:bg-success/10" 
                      : "text-textSecondary hover:bg-white/10"
                  }`}
                  title={card.visible ? "Gizle" : "Göster"}
                >
                  {card.visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </button>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-white/10 flex items-center justify-center gap-4 text-[10px] text-textSecondary">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-blue-500" /> Sol
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-purple-500" /> Orta
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-orange-500" /> Sağ
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ============================================
// EDIT MODE TOGGLE BUTTON
// ============================================
export function EditModeButton() {
  const { isEditMode, toggleEditMode } = useDashboardEdit();

  return (
    <button
      onClick={toggleEditMode}
      className={`relative flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-300 overflow-hidden ${
        isEditMode
          ? "bg-gradient-to-r from-primary to-purple-600 text-white shadow-lg shadow-primary/30"
          : "bg-white/10 text-textSecondary hover:bg-white/20 hover:text-white"
      }`}
      title={isEditMode ? "Düzenleme modunu kapat" : "Dashboard'u düzenle"}
    >
      {isEditMode && (
        <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-white/20 to-primary/0 animate-shimmer" />
      )}
      <Settings2 className={`w-4 h-4 relative z-10 ${isEditMode ? "animate-spin-slow" : ""}`} />
      <span className="text-sm font-medium hidden md:inline relative z-10">
        {isEditMode ? "Düzenleniyor..." : "Düzenle"}
      </span>
    </button>
  );
}
