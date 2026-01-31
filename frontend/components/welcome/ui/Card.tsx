"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface CardProps {
  children?: ReactNode;
  className?: string;
  icon?: ReactNode;
  title?: string;
  description?: string;
}

export function AnimatedCard({
  children,
  className,
  icon,
  title,
  description,
}: CardProps) {
  return (
    <motion.div
      className={cn(
        "relative group rounded-2xl p-6 md:p-8",
        "bg-white/[0.03] border border-white/[0.08]",
        "hover:border-[#00E0C6]/30",
        "transition-all duration-500",
        "overflow-hidden",
        className
      )}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
    >
      {/* Shimmer effect */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
      </div>

      {/* Glow effect */}
      <div className="absolute -inset-px rounded-2xl bg-gradient-to-r from-[#00E0C6]/0 via-[#00E0C6]/20 to-[#00E0C6]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm" />

      {/* Content */}
      <div className="relative z-10">
        {icon && (
          <div className="mb-4 inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#00E0C6]/20 to-[#3B82F6]/20 text-[#00E0C6]">
            {icon}
          </div>
        )}
        {title && (
          <h3 className="text-lg md:text-xl font-semibold text-white mb-2">
            {title}
          </h3>
        )}
        {description && (
          <p className="text-[#E5E7EB]/70 text-sm md:text-base leading-relaxed">
            {description}
          </p>
        )}
        {children}
      </div>
    </motion.div>
  );
}
