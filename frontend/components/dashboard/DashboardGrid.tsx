"use client";

import React from "react";
import { useDashboardEdit, DashboardCard } from "../../contexts/DashboardEditContext";
import { DraggableDashboard, SortableCard } from "../DraggableDashboard";

interface DashboardGridProps {
  renderCard: (cardId: string, card: DashboardCard) => React.ReactNode;
}

export function DashboardGrid({ renderCard }: DashboardGridProps) {
  const { layout, isEditMode } = useDashboardEdit();

  // Get cards for each column, sorted by order
  const getColumnCards = (column: "left" | "center" | "right") => {
    return layout.cards
      .filter(c => c.column === column && c.visible)
      .sort((a, b) => a.order - b.order);
  };

  const leftCards = getColumnCards("left");
  const centerCards = getColumnCards("center");
  const rightCards = getColumnCards("right");

  // Separate full-width cards (they go after the 3-column grid)
  const fullWidthCards = layout.cards
    .filter(c => c.size === "full" && c.visible)
    .sort((a, b) => a.order - b.order);

  // Regular cards (not full-width)
  const regularLeftCards = leftCards.filter(c => c.size !== "full");
  const regularCenterCards = centerCards.filter(c => c.size !== "full");
  const regularRightCards = rightCards.filter(c => c.size !== "full");

  return (
    <DraggableDashboard>
      {/* 3-Column Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Left Column */}
        <div className="flex flex-col gap-6">
          {regularLeftCards.map(card => (
            <SortableCard key={card.id} card={card}>
              {renderCard(card.id, card)}
            </SortableCard>
          ))}
        </div>

        {/* Center Column */}
        <div className="flex flex-col gap-6">
          {regularCenterCards.map(card => (
            <SortableCard key={card.id} card={card}>
              {renderCard(card.id, card)}
            </SortableCard>
          ))}
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-6">
          {regularRightCards.map(card => (
            <SortableCard key={card.id} card={card}>
              {renderCard(card.id, card)}
            </SortableCard>
          ))}
        </div>
      </div>

      {/* Full-Width Cards */}
      <div className="mt-6 space-y-6">
        {fullWidthCards.map(card => (
          <SortableCard key={card.id} card={card}>
            <div className="md:col-span-2 lg:col-span-3">
              {renderCard(card.id, card)}
            </div>
          </SortableCard>
        ))}
      </div>
    </DraggableDashboard>
  );
}

export default DashboardGrid;
