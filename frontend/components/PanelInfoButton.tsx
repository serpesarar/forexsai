"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import { PanelInfoModal } from "./PanelInfoModal";
import { PANEL_INFO_REGISTRY } from "../lib/panelInfoData";

interface PanelInfoButtonProps {
    panelId: string;
    className?: string;
}

export function PanelInfoButton({ panelId, className = "" }: PanelInfoButtonProps) {
    const [isOpen, setIsOpen] = useState(false);

    // Don't render if panel has no info registered
    if (!PANEL_INFO_REGISTRY[panelId]) return null;

    return (
        <>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    setIsOpen(true);
                }}
                className={`inline-flex items-center justify-center w-7 h-7 rounded-lg 
          bg-white/5 hover:bg-accent/20 border border-white/10 hover:border-accent/40
          text-gray-400 hover:text-accent
          transition-all duration-200 hover:scale-110 active:scale-95
          hover:shadow-[0_0_12px_rgba(0,224,198,0.25)]
          ${className}`}
                title="Info"
            >
                <Info className="w-3.5 h-3.5" />
            </button>
            <PanelInfoModal
                isOpen={isOpen}
                onClose={() => setIsOpen(false)}
                panelId={panelId}
            />
        </>
    );
}

export default PanelInfoButton;
