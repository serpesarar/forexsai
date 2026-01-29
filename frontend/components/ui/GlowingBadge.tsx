"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlowingBadgeProps {
  children: ReactNode;
  variant: "success" | "danger" | "warning" | "info" | "neutral";
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  className?: string;
}

const variants = {
  success: {
    bg: "bg-gradient-to-r from-green-500/20 to-emerald-500/20",
    border: "border-green-500/30",
    text: "text-green-400",
    glow: "shadow-[0_0_20px_rgba(34,197,94,0.3)]",
  },
  danger: {
    bg: "bg-gradient-to-r from-red-500/20 to-rose-500/20",
    border: "border-red-500/30",
    text: "text-red-400",
    glow: "shadow-[0_0_20px_rgba(239,68,68,0.3)]",
  },
  warning: {
    bg: "bg-gradient-to-r from-amber-500/20 to-yellow-500/20",
    border: "border-amber-500/30",
    text: "text-amber-400",
    glow: "shadow-[0_0_20px_rgba(245,158,11,0.3)]",
  },
  info: {
    bg: "bg-gradient-to-r from-blue-500/20 to-cyan-500/20",
    border: "border-blue-500/30",
    text: "text-blue-400",
    glow: "shadow-[0_0_20px_rgba(59,130,246,0.3)]",
  },
  neutral: {
    bg: "bg-gradient-to-r from-gray-500/20 to-slate-500/20",
    border: "border-gray-500/30",
    text: "text-gray-400",
    glow: "shadow-[0_0_10px_rgba(148,163,184,0.2)]",
  },
};

const sizes = {
  sm: "px-2 py-0.5 text-[10px]",
  md: "px-3 py-1 text-xs",
  lg: "px-4 py-1.5 text-sm",
};

export default function GlowingBadge({
  children,
  variant,
  size = "md",
  pulse = false,
  className = "",
}: GlowingBadgeProps) {
  const v = variants[variant];
  
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`
        inline-flex items-center gap-1.5 rounded-full font-semibold
        border backdrop-blur-sm
        ${v.bg} ${v.border} ${v.text} ${v.glow}
        ${sizes[size]}
        ${pulse ? "animate-pulse" : ""}
        ${className}
      `}
    >
      {pulse && (
        <span className={`w-1.5 h-1.5 rounded-full ${v.text.replace("text-", "bg-")} animate-ping`} />
      )}
      {children}
    </motion.span>
  );
}
