"use client";

import React, { useState } from "react";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Check, X, RotateCcw, Settings2 } from "lucide-react";
import { useDashboardEdit } from "../contexts/DashboardEditContext";

interface SortableItemProps {
  id: string;
  children: React.ReactNode;
  isEditMode: boolean;
}

function SortableItem({ id, children, isEditMode }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id, disabled: !isEditMode });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    position: "relative" as const,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${isEditMode ? "wobble-animation cursor-move" : ""} ${
        isDragging ? "z-50 scale-105" : ""
      }`}
    >
      {isEditMode && (
        <div
          {...attributes}
          {...listeners}
          className="absolute -left-2 top-1/2 -translate-y-1/2 z-10 p-2 rounded-lg bg-primary/80 text-white cursor-grab active:cursor-grabbing shadow-lg hover:bg-primary transition-colors"
          title="Sürükle"
        >
          <GripVertical className="w-4 h-4" />
        </div>
      )}
      {isEditMode && (
        <div className="absolute inset-0 border-2 border-dashed border-primary/50 rounded-xl pointer-events-none z-0" />
      )}
      {children}
    </div>
  );
}

interface DraggableColumnProps {
  columnId: string;
  items: string[];
  children: React.ReactNode;
  onReorder: (items: string[]) => void;
  isEditMode: boolean;
}

export function DraggableColumn({
  columnId,
  items,
  children,
  onReorder,
  isEditMode,
}: DraggableColumnProps) {
  const childrenArray = React.Children.toArray(children);

  return (
    <SortableContext items={items} strategy={verticalListSortingStrategy}>
      <div className="flex flex-col gap-6">
        {items.map((itemId, index) => {
          const child = childrenArray.find((c: any) => c.props?.["data-card-id"] === itemId);
          if (!child) return null;
          return (
            <SortableItem key={itemId} id={itemId} isEditMode={isEditMode}>
              {child}
            </SortableItem>
          );
        })}
      </div>
    </SortableContext>
  );
}

interface DraggableDashboardProps {
  children: React.ReactNode;
}

export function DraggableDashboard({ children }: DraggableDashboardProps) {
  const { isEditMode, saveLayout, resetLayout, setEditMode } = useDashboardEdit();
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveId(null);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      {children}
      
      {/* Edit Mode Floating Controls */}
      {isEditMode && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-6 py-3 rounded-2xl bg-background/95 backdrop-blur-xl border border-white/10 shadow-2xl">
          <span className="text-sm text-textSecondary mr-2">Düzenleme Modu</span>
          <button
            onClick={saveLayout}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-success/20 text-success hover:bg-success/30 transition-colors"
          >
            <Check className="w-4 h-4" />
            <span className="text-sm font-medium">Kaydet</span>
          </button>
          <button
            onClick={resetLayout}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 text-textSecondary hover:bg-white/20 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="text-sm font-medium">Sıfırla</span>
          </button>
          <button
            onClick={() => setEditMode(false)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-danger/20 text-danger hover:bg-danger/30 transition-colors"
          >
            <X className="w-4 h-4" />
            <span className="text-sm font-medium">İptal</span>
          </button>
        </div>
      )}
    </DndContext>
  );
}

// Edit Mode Toggle Button Component
export function EditModeButton() {
  const { isEditMode, toggleEditMode } = useDashboardEdit();

  return (
    <button
      onClick={toggleEditMode}
      className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-300 ${
        isEditMode
          ? "bg-primary text-white shadow-lg shadow-primary/30"
          : "bg-white/10 text-textSecondary hover:bg-white/20"
      }`}
      title={isEditMode ? "Düzenleme modunu kapat" : "Dashboard'u düzenle"}
    >
      <Settings2 className={`w-4 h-4 ${isEditMode ? "animate-spin-slow" : ""}`} />
      <span className="text-sm font-medium hidden md:inline">
        {isEditMode ? "Düzenleniyor..." : "Düzenle"}
      </span>
    </button>
  );
}
