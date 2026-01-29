"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  glowColor?: "purple" | "green" | "red" | "blue" | "amber";
  animate?: boolean;
  delay?: number;
  onClick?: () => void;
}

const glowColors = {
  purple: "hover:shadow-[0_0_40px_rgba(139,92,246,0.3)]",
  green: "hover:shadow-[0_0_40px_rgba(34,197,94,0.3)]",
  red: "hover:shadow-[0_0_40px_rgba(239,68,68,0.3)]",
  blue: "hover:shadow-[0_0_40px_rgba(59,130,246,0.3)]",
  amber: "hover:shadow-[0_0_40px_rgba(245,158,11,0.3)]",
};

const borderColors = {
  purple: "hover:border-purple-500/30",
  green: "hover:border-green-500/30",
  red: "hover:border-red-500/30",
  blue: "hover:border-blue-500/30",
  amber: "hover:border-amber-500/30",
};

export default function PremiumCard({
  children,
  className = "",
  glowColor = "purple",
  animate = true,
  delay = 0,
  onClick,
}: PremiumCardProps) {
  const baseClasses = `
    relative overflow-hidden rounded-2xl
    bg-gradient-to-br from-white/[0.08] via-white/[0.04] to-transparent
    backdrop-blur-xl border border-white/[0.08]
    shadow-[0_8px_32px_rgba(0,0,0,0.4)]
    transition-all duration-500 ease-out
    ${glowColors[glowColor]}
    ${borderColors[glowColor]}
    hover:translate-y-[-2px]
    ${onClick ? "cursor-pointer" : ""}
  `;

  const content = (
    <>
      {/* Top shine line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      
      {/* Radial glow */}
      <div className="absolute -top-1/2 left-1/2 -translate-x-1/2 w-3/4 h-full bg-gradient-radial from-purple-500/10 via-transparent to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      {/* Content */}
      <div className="relative z-10">{children}</div>
      
      {/* Bottom gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/5 to-transparent" />
    </>
  );

  if (animate) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ 
          duration: 0.5, 
          delay,
          ease: [0.25, 0.46, 0.45, 0.94] 
        }}
        whileHover={{ scale: 1.01 }}
        className={`group ${baseClasses} ${className}`}
        onClick={onClick}
      >
        {content}
      </motion.div>
    );
  }

  return (
    <div className={`group ${baseClasses} ${className}`} onClick={onClick}>
      {content}
    </div>
  );
}

export function PremiumCardHeader({ 
  children, 
  className = "" 
}: { 
  children: ReactNode; 
  className?: string;
}) {
  return (
    <div className={`px-5 py-4 border-b border-white/[0.06] ${className}`}>
      {children}
    </div>
  );
}

export function PremiumCardBody({ 
  children, 
  className = "" 
}: { 
  children: ReactNode; 
  className?: string;
}) {
  return (
    <div className={`px-5 py-4 ${className}`}>
      {children}
    </div>
  );
}

export function PremiumCardFooter({ 
  children, 
  className = "" 
}: { 
  children: ReactNode; 
  className?: string;
}) {
  return (
    <div className={`px-5 py-3 border-t border-white/[0.06] bg-white/[0.02] ${className}`}>
      {children}
    </div>
  );
}
