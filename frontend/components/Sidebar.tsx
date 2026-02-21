"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    LineChart,
    Brain,
    BarChart3,
    Activity,
    ChevronLeft,
    ChevronRight,
    Settings,
    Moon,
    Sun,
    Mail,
    ChevronDown,
    Globe,
    Shield,
    FileText,
    LogOut,
    User as UserIcon,
} from "lucide-react";
import { useUser, useAuthStore } from "../lib/auth/store";
import { useI18nStore } from "../lib/i18n/store";

interface NavItem {
    href: string;
    key: string;
    label: string;
    labelEn: string;
    icon: React.ElementType;
    accentColor: string;
    glowColor: string;
}

const NAV_ITEMS: NavItem[] = [
    {
        href: "/",
        key: "dashboard",
        label: "Dashboard",
        labelEn: "Dashboard",
        icon: LayoutDashboard,
        accentColor: "#3b82f6",
        glowColor: "rgba(59,130,246,0.3)",
    },
    {
        href: "/charts",
        key: "charts",
        label: "Charts",
        labelEn: "Charts",
        icon: LineChart,
        accentColor: "#10b981",
        glowColor: "rgba(16,185,129,0.3)",
    },
    {
        href: "/trading",
        key: "trading",
        label: "AI Trading",
        labelEn: "AI Trading",
        icon: Brain,
        accentColor: "#8b5cf6",
        glowColor: "rgba(139,92,246,0.3)",
    },
    {
        href: "/analysis",
        key: "analysis",
        label: "Analysis",
        labelEn: "Analysis",
        icon: BarChart3,
        accentColor: "#f59e0b",
        glowColor: "rgba(245,158,11,0.3)",
    },
    {
        href: "/signals",
        key: "signals",
        label: "Detailed Signals",
        labelEn: "Detailed Signals",
        icon: Activity,
        accentColor: "#ef4444",
        glowColor: "rgba(239,68,68,0.3)",
    },
];

const LEGAL_LINKS = [
    { href: "https://www.forexsai.com", label: "Website", labelEn: "Website", icon: Globe },
    { href: "/risk", label: "Disclaimer", labelEn: "Disclaimer", icon: Shield },
    { href: "/privacy", label: "Privacy", labelEn: "Privacy", icon: FileText },
    { href: "/terms", label: "Terms", labelEn: "Terms", icon: FileText },
];

export default function Sidebar() {
    const pathname = usePathname();
    const user = useUser();
    const { logout } = useAuthStore();
    const { locale } = useI18nStore();

    // Persist sidebar state in localStorage
    const [collapsed, setCollapsed] = useState(false);
    const [legalOpen, setLegalOpen] = useState(false);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const saved = localStorage.getItem("sidebar-collapsed");
        if (saved === "true") setCollapsed(true);
    }, []);

    const toggleCollapse = () => {
        const next = !collapsed;
        setCollapsed(next);
        localStorage.setItem("sidebar-collapsed", String(next));
        if (next) setLegalOpen(false);
    };

    const getActiveKey = () => {
        if (pathname === "/") return "dashboard";
        const segment = pathname.split("/")[1];
        return segment || "dashboard";
    };

    const activeKey = getActiveKey();
    const firstName = user?.full_name?.split(" ")[0] || user?.email?.split("@")[0] || "Trader";

    if (!mounted) return null;

    return (
        <aside
            className={`
        fixed left-0 top-0 h-screen z-50 flex flex-col
        transition-all duration-300 ease-in-out
        ${collapsed ? "w-[72px]" : "w-[260px]"}
      `}
            style={{
                background: "linear-gradient(180deg, rgba(10,14,26,0.97) 0%, rgba(8,12,24,0.99) 100%)",
                borderRight: "1px solid rgba(59,130,246,0.08)",
                boxShadow: "4px 0 24px rgba(0,0,0,0.4), 1px 0 0 rgba(59,130,246,0.06)",
            }}
        >
            {/* ── Top: Logo + Welcome ── */}
            <div className="px-4 pt-5 pb-3 border-b border-white/5">
                <div className="flex items-center justify-between">
                    <Link href="/" className="group flex items-center gap-3 min-w-0">
                        {/* Logo Icon */}
                        <div
                            className="relative flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-105"
                            style={{
                                background: "linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)",
                                boxShadow: "0 0 18px rgba(37,99,235,0.4)",
                            }}
                        >
                            <Activity className="text-white w-5 h-5" />
                            <div className="absolute inset-0 rounded-xl bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>

                        {/* Logo Text */}
                        {!collapsed && (
                            <div className="min-w-0 animate-fadeIn">
                                <h1 className="text-lg font-black tracking-tight text-white leading-none">
                                    FOREXS<span className="text-blue-500">AI</span>
                                </h1>
                                <p className="text-[9px] font-bold text-slate-500 tracking-[0.2em] uppercase leading-none mt-0.5">
                                    Intelligence
                                </p>
                            </div>
                        )}
                    </Link>

                    {/* Collapse Toggle */}
                    <button
                        onClick={toggleCollapse}
                        className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-md bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all duration-200 hover:scale-110"
                        title={collapsed ? "Expand" : "Collapse"}
                    >
                        {collapsed ? (
                            <ChevronRight className="w-4 h-4" />
                        ) : (
                            <ChevronLeft className="w-4 h-4" />
                        )}
                    </button>
                </div>

                {/* Welcome User */}
                {!collapsed && (
                    <p className="mt-3 text-xs font-semibold text-blue-400/80 truncate animate-fadeIn">
                        Welcome, <span className="text-blue-300">{firstName}</span>
                    </p>
                )}
            </div>

            {/* ── Navigation Items ── */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
                {NAV_ITEMS.map((item) => {
                    const isActive = item.key === activeKey;
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.key}
                            href={item.href}
                            className={`
                group relative flex items-center gap-3 rounded-lg transition-all duration-200 overflow-hidden
                ${collapsed ? "justify-center px-0 py-3" : "px-3 py-2.5"}
                ${isActive
                                    ? "text-white"
                                    : "text-slate-400 hover:text-white hover:bg-white/[0.04]"
                                }
              `}
                            title={collapsed ? item.label : undefined}
                        >
                            {/* Active indicator — neon left border */}
                            {isActive && (
                                <div
                                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] rounded-r-full transition-all"
                                    style={{
                                        height: "60%",
                                        background: item.accentColor,
                                        boxShadow: `0 0 8px ${item.glowColor}, 0 0 20px ${item.glowColor}`,
                                    }}
                                />
                            )}

                            {/* Active background glow */}
                            {isActive && (
                                <div
                                    className="absolute inset-0 rounded-lg opacity-[0.06]"
                                    style={{ background: item.accentColor }}
                                />
                            )}

                            {/* Icon */}
                            <div className="relative flex-shrink-0">
                                <Icon
                                    className={`w-5 h-5 transition-all duration-200 ${isActive ? "" : "group-hover:scale-110"
                                        }`}
                                    style={isActive ? { color: item.accentColor } : undefined}
                                />
                                {/* Icon glow on active */}
                                {isActive && (
                                    <div
                                        className="absolute inset-0 blur-md opacity-40"
                                        style={{ background: item.accentColor }}
                                    />
                                )}
                            </div>

                            {/* Label */}
                            {!collapsed && (
                                <span
                                    className={`text-sm font-medium truncate animate-fadeIn ${isActive ? "font-semibold" : ""
                                        }`}
                                >
                                    {item.label}
                                </span>
                            )}

                            {/* Hover shimmer on non-active */}
                            {!isActive && (
                                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* ── Bottom Section: Legal + Contact + Settings ── */}
            <div className="px-3 pb-4 space-y-1 border-t border-white/5 pt-3">
                {/* Support / Contact */}
                <Link
                    href="mailto:support@forexsai.com"
                    className={`
            group flex items-center gap-3 rounded-lg text-slate-500 hover:text-blue-400 transition-all duration-200
            ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2"}
          `}
                    title={collapsed ? "Contact" : undefined}
                >
                    <Mail className="w-4 h-4 flex-shrink-0 group-hover:scale-110 transition-transform" />
                    {!collapsed && <span className="text-xs font-medium animate-fadeIn">Support / İletişim</span>}
                </Link>

                {/* Legal Dropdown */}
                <div>
                    <button
                        onClick={() => !collapsed && setLegalOpen(!legalOpen)}
                        className={`
              w-full group flex items-center gap-3 rounded-lg text-slate-500 hover:text-slate-300 transition-all duration-200
              ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2"}
            `}
                        title={collapsed ? "Legal / Website" : undefined}
                    >
                        <Globe className="w-4 h-4 flex-shrink-0 group-hover:scale-110 transition-transform" />
                        {!collapsed && (
                            <>
                                <span className="text-xs font-medium flex-1 text-left animate-fadeIn">Legal / Website</span>
                                <ChevronDown
                                    className={`w-3 h-3 transition-transform duration-200 ${legalOpen ? "rotate-180" : ""}`}
                                />
                            </>
                        )}
                    </button>

                    {/* Dropdown Items */}
                    {!collapsed && legalOpen && (
                        <div className="ml-4 mt-1 space-y-0.5 animate-slideDown">
                            {LEGAL_LINKS.map((link) => {
                                const LinkIcon = link.icon;
                                const isExternal = link.href.startsWith("http");
                                const LinkComponent = isExternal ? "a" : Link;
                                const extraProps = isExternal ? { target: "_blank", rel: "noopener noreferrer" } : {};

                                return (
                                    <LinkComponent
                                        key={link.href}
                                        href={link.href}
                                        {...extraProps}
                                        className="flex items-center gap-2.5 px-3 py-1.5 rounded-md text-slate-500 hover:text-slate-300 hover:bg-white/[0.03] transition-all duration-150 text-xs"
                                    >
                                        <LinkIcon className="w-3.5 h-3.5" />
                                        <span>{link.label}</span>
                                    </LinkComponent>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Divider */}
                <div className="h-px bg-white/5 my-2" />

                {/* Account */}
                <Link
                    href="/account"
                    className={`
            group flex items-center gap-3 rounded-lg text-slate-500 hover:text-white transition-all duration-200
            ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2"}
          `}
                    title={collapsed ? "Account" : undefined}
                >
                    <div className="relative w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-br from-blue-600/30 to-purple-600/30 border border-white/10 flex items-center justify-center group-hover:border-blue-500/30 transition-all">
                        <UserIcon className="w-3.5 h-3.5 text-slate-400 group-hover:text-white transition-colors" />
                    </div>
                    {!collapsed && (
                        <div className="min-w-0 animate-fadeIn">
                            <p className="text-xs font-medium text-slate-300 truncate">{user?.full_name || user?.email || "Account"}</p>
                            <p className="text-[10px] text-slate-600 truncate">{user?.membership_tier || "free"}</p>
                        </div>
                    )}
                </Link>

                {/* Logout */}
                <button
                    onClick={() => logout()}
                    className={`
            w-full group flex items-center gap-3 rounded-lg text-slate-600 hover:text-red-400 transition-all duration-200
            ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2"}
          `}
                    title={collapsed ? "Logout" : undefined}
                >
                    <LogOut className="w-4 h-4 flex-shrink-0 group-hover:scale-110 transition-transform" />
                    {!collapsed && <span className="text-xs font-medium animate-fadeIn">Logout</span>}
                </button>
            </div>

            {/* ── Inline Animations ── */}
            <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateX(-8px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.2s ease-out; }
        .animate-slideDown { animation: slideDown 0.2s ease-out; }
      `}</style>
        </aside>
    );
}
