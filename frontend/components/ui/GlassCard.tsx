"use client";

import { ReactNode } from "react";

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    hover?: boolean;
    glow?: "cyan" | "gray" | "none";
}

export function GlassCard({ children, className = "", hover = false, glow = "none" }: GlassCardProps) {
    const glowClass = {
        cyan: "hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]",
        gray: "hover:shadow-[0_0_30px_rgba(255,255,255,0.05)]",
        none: "",
    }[glow];

    return (
        <div
            className={`
        bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl
        ${hover ? "transition-all duration-300 hover:bg-white/8 hover:scale-[1.01] cursor-pointer" : ""}
        ${glowClass}
        ${className}
      `}
        >
            {children}
        </div>
    );
}
