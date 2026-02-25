"use client";

import { ReactNode } from "react";
import Link from "next/link";

interface MetalButtonProps {
    children: ReactNode;
    onClick?: () => void;
    href?: string;
    variant?: "primary" | "ghost" | "outline";
    size?: "sm" | "md" | "lg";
    className?: string;
    disabled?: boolean;
    type?: "button" | "submit" | "reset";
}

const sizeClasses = {
    sm: "px-5 py-2 text-xs",
    md: "px-8 py-3 text-sm",
    lg: "px-10 py-4 text-sm",
};

const variantClasses = {
    primary: `
    bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 
    border border-gray-500/50 
    shadow-[0_0_15px_rgba(192,192,192,0.15)]
    hover:shadow-[0_0_25px_rgba(192,192,192,0.3)]
    hover:from-gray-600 hover:via-gray-300 hover:to-gray-600
  `,
    ghost: `
    bg-white/5 hover:bg-white/10 
    border border-white/10 hover:border-white/20
  `,
    outline: `
    bg-transparent 
    border border-white/20 hover:border-white/40 
    hover:bg-white/5
  `,
};

export function MetalButton({
    children,
    onClick,
    href,
    variant = "primary",
    size = "md",
    className = "",
    disabled = false,
    type = "button",
}: MetalButtonProps) {
    const baseClasses = `
    relative overflow-hidden
    text-white font-light tracking-widest uppercase
    rounded-sm transition-all duration-300
    flex items-center justify-center gap-2
    disabled:opacity-50 disabled:cursor-not-allowed
    active:scale-95
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${className}
  `;

    if (href) {
        return (
            <Link href={href} className={baseClasses}>
                {children}
            </Link>
        );
    }

    return (
        <button onClick={onClick} className={baseClasses} disabled={disabled} type={type}>
            {children}
        </button>
    );
}
