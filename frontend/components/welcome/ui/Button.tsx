"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  className?: string;
  onClick?: () => void;
  href?: string;
  disabled?: boolean;
}

export function AnimatedButton({
  children,
  variant = "primary",
  size = "md",
  className,
  onClick,
  href,
  disabled,
}: ButtonProps) {
  const baseStyles =
    "relative inline-flex items-center justify-center font-semibold transition-all duration-300 overflow-hidden group";

  const variants = {
    primary: [
      "bg-gradient-to-r from-[#00E0C6] to-[#3B82F6]",
      "text-[#0B1220]",
      "hover:shadow-[0_0_30px_rgba(0,224,198,0.4)]",
      "hover:scale-[1.02]",
      "before:absolute before:inset-0",
      "before:bg-gradient-to-r before:from-transparent before:via-white/30 before:to-transparent",
      "before:-translate-x-full before:group-hover:translate-x-full",
      "before:transition-transform before:duration-700",
    ],
    secondary: [
      "bg-white/10",
      "text-white",
      "border border-white/20",
      "hover:bg-white/15",
      "hover:border-white/30",
      "hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]",
    ],
    outline: [
      "bg-transparent",
      "text-white",
      "border border-white/30",
      "hover:bg-white/5",
      "hover:border-[#00E0C6]/50",
    ],
    ghost: [
      "bg-transparent",
      "text-white/70",
      "hover:text-white",
      "hover:bg-white/5",
    ],
  };

  const sizes = {
    sm: "px-4 py-2 text-sm rounded-lg",
    md: "px-6 py-3 text-base rounded-xl",
    lg: "px-8 py-4 text-lg rounded-2xl",
  };

  const combinedClassName = cn(
    baseStyles,
    variants[variant],
    sizes[size],
    disabled && "opacity-50 cursor-not-allowed",
    className
  );

  const content = (
    <>
      <span className="relative z-10">{children}</span>
      {variant === "primary" && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-[#00E0C6] via-[#3B82F6] to-[#00E0C6] opacity-0 group-hover:opacity-100"
          transition={{ duration: 0.3 }}
        />
      )}
    </>
  );

  if (href) {
    return (
      <motion.a
        href={href}
        className={combinedClassName}
        whileHover={{ scale: disabled ? 1 : 1.02 }}
        whileTap={{ scale: disabled ? 1 : 0.98 }}
        onClick={onClick}
      >
        {content}
      </motion.a>
    );
  }

  return (
    <motion.button
      className={combinedClassName}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      onClick={onClick}
      disabled={disabled}
    >
      {content}
    </motion.button>
  );
}
