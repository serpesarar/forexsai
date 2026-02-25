"use client";

import { ReactNode } from "react";

interface NeonTextProps {
    children: ReactNode;
    color?: "cyan" | "white" | "gray";
    size?: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl";
    className?: string;
    glow?: boolean;
}

const colorClasses = {
    cyan: "text-cyan-400",
    white: "bg-gradient-to-r from-gray-100 via-white to-gray-300 bg-clip-text text-transparent",
    gray: "bg-gradient-to-r from-gray-300 to-gray-500 bg-clip-text text-transparent",
};

const glowClasses = {
    cyan: "drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]",
    white: "drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]",
    gray: "drop-shadow-[0_0_8px_rgba(156,163,175,0.3)]",
};

export function NeonText({
    children,
    color = "white",
    className = "",
    glow = false,
}: NeonTextProps) {
    return (
        <span
            className={`
        ${colorClasses[color]}
        ${glow ? glowClasses[color] : ""}
        ${className}
      `}
        >
            {children}
        </span>
    );
}

/** Metal gradient heading - büyük başlıklar için */
export function MetalHeading({
    children,
    className = "",
}: {
    children: ReactNode;
    className?: string;
}) {
    return (
        <span
            className={`
        bg-gradient-to-br from-gray-100 via-gray-300 to-gray-500 
        bg-clip-text text-transparent 
        drop-shadow-lg
        ${className}
      `}
        >
            {children}
        </span>
    );
}
