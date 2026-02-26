"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useNavigationStore } from "../lib/store/navigation";
import {
    DashboardIcon,
    ChartsIcon,
    TradingIcon,
    AnalysisIcon,
    SignalsIcon,
    ForexsAILogoIcon,
    ChevronIcon,
    SupportMailIcon,
    WebsiteIcon,
    SecurityShieldIcon,
    GlobeIcon,
    TermsIcon,
    LogoutIcon,
    UserProfileIcon,
} from "./ui/CustomIcons";
import { useUser, useAuthStore } from "../lib/auth/store";
import { useI18nStore } from "../lib/i18n/store";

interface NavItem {
    href: string;
    key: string;
    label: string;
    icon: React.ElementType;
    accentColor: string;
    glowColor: string;
}

const NAV_ITEMS: NavItem[] = [
    { href: "/", key: "dashboard", label: "Dashboard", icon: DashboardIcon, accentColor: "var(--accent-info)", glowColor: "0 0 12px var(--accent-info-50)" },
    { href: "/charts", key: "charts", label: "Charts", icon: ChartsIcon, accentColor: "var(--accent-info)", glowColor: "0 0 12px var(--accent-info-50)" },
    { href: "/trading", key: "trading", label: "AI Trading", icon: TradingIcon, accentColor: "var(--accent-purple)", glowColor: "0 0 12px var(--accent-purple-50)" },
    { href: "/analysis", key: "analysis", label: "Analysis", icon: AnalysisIcon, accentColor: "var(--accent-warning)", glowColor: "0 0 12px var(--accent-warning-50)" },
    { href: "/signals", key: "signals", label: "Detailed Signals", icon: SignalsIcon, accentColor: "var(--accent-negative)", glowColor: "0 0 12px var(--accent-negative-50)" },
];

const LEGAL_LINKS = [
    { href: "https://www.forexsai.com", label: "Website", icon: WebsiteIcon },
    { href: "/risk", label: "Disclaimer", icon: SecurityShieldIcon },
    { href: "/privacy", label: "Privacy", icon: TermsIcon },
    { href: "/terms", label: "Terms", icon: TermsIcon },
];

export default function Sidebar() {
    const { activeView, setActiveView } = useNavigationStore();
    const { locale, setLocale } = useI18nStore();
    const user = useUser();
    const { logout } = useAuthStore();

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

    const firstName = user?.full_name?.split(" ")[0] || user?.email?.split("@")[0] || "Trader";

    if (!mounted) return null;

    return (
        <aside
            className={`fixed left-0 top-0 h-screen z-[999] pointer-events-auto flex flex-col transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${collapsed ? "w-[72px]" : "w-[240px]"}`}
            style={{
                background: "linear-gradient(180deg, #080d1a 0%, #060a14 50%, #0a0f1e 100%)",
                borderRight: "1px solid rgba(0,224,198,0.08)",
                boxShadow: "4px 0 30px rgba(0,0,0,0.6), 1px 0 1px rgba(0,224,198,0.04)",
            }}
        >
            {/* Animated neon line on right edge */}
            <div className="absolute right-0 top-0 bottom-0 w-[1px]" style={{
                background: "linear-gradient(180deg, transparent 0%, rgba(0,224,198,0.2) 30%, rgba(59,130,246,0.15) 70%, transparent 100%)",
            }} />

            {/* ── Logo Section ── */}
            <div className="px-4 pt-5 pb-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                <div className="flex items-center justify-between">
                    <Link href="/" className="group flex items-center gap-2.5 min-w-0">
                        <div className="relative flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-lg transition-all duration-300 group-hover:scale-110"
                            style={{
                                background: "linear-gradient(135deg, var(--accent-info) 0%, var(--accent-info) 100%)",
                                boxShadow: "0 0 20px var(--accent-info-35), inset 0 1px 0 rgba(255,255,255,0.15)",
                            }}>
                            <ForexsAILogoIcon className="text-white" size={18} />
                        </div>
                        {!collapsed && (
                            <div className="min-w-0 sidebar-fade-in">
                                <h1 className="text-[15px] font-black tracking-tight text-white leading-none">
                                    FOREXS<span style={{ color: "var(--accent-info)" }}>AI</span>
                                </h1>
                                <p className="text-[8px] font-bold tracking-[0.25em] uppercase leading-none mt-0.5" style={{ color: "var(--accent-info-50)" }}>
                                    Intelligence
                                </p>
                            </div>
                        )}
                    </Link>
                    <button onClick={toggleCollapse}
                        className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-md transition-all duration-200 hover:scale-110"
                        style={{ background: "rgba(0,224,198,0.06)", color: "rgba(0,224,198,0.6)" }}>
                        <ChevronIcon size={14} style={{ transform: collapsed ? "rotate(0deg)" : "rotate(180deg)" }} />
                    </button>
                </div>

                {/* Welcome */}
                {!collapsed && (
                    <p className="mt-2.5 mb-1 text-[11px] font-semibold sidebar-fade-in" style={{ color: "rgba(0,224,198,0.7)" }}>
                        Welcome, <span className="text-white/90">{firstName}</span>
                    </p>
                )}
            </div>

            {/* ── Nav Items ── */}
            <nav className="flex-1 px-2.5 py-3 space-y-0.5 overflow-y-auto">
                {NAV_ITEMS.map((item) => {
                    const isActive = item.key === activeView;
                    const Icon = item.icon;

                    return (
                        <button key={item.key} onClick={() => setActiveView(item.key as any)}
                            className={`w-full group relative flex items-center gap-2.5 rounded-lg transition-all duration-200 ${collapsed ? "justify-center px-0 py-2.5" : "px-3 py-2"}`}
                            style={{
                                color: isActive ? item.accentColor : "rgba(255,255,255,0.4)",
                                background: isActive ? `${item.accentColor}0a` : "transparent",
                            }}
                            title={collapsed ? item.label : undefined}
                            onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; e.currentTarget.style.color = isActive ? item.accentColor : "rgba(255,255,255,0.8)"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.background = isActive ? `${item.accentColor}0a` : "transparent"; e.currentTarget.style.color = isActive ? item.accentColor : "rgba(255,255,255,0.4)"; }}
                        >
                            {/* Neon left bar */}
                            {isActive && (
                                <div className="absolute left-0 top-[15%] bottom-[15%] w-[2.5px] rounded-r-full"
                                    style={{ background: item.accentColor, boxShadow: item.glowColor }} />
                            )}

                            <Icon className={`w-[18px] h-[18px] flex-shrink-0 transition-transform duration-200 ${!isActive ? "group-hover:scale-110" : ""}`}
                                style={isActive ? { filter: `drop-shadow(${item.glowColor})` } : undefined} />

                            {!collapsed && (
                                <span className={`text-[13px] truncate whitespace-nowrap sidebar-fade-in ${isActive ? "font-semibold" : "font-medium"}`}>
                                    {item.label}
                                </span>
                            )}
                        </button>
                    );
                })}
            </nav>

            {/* ── Bottom Section ── */}
            <div className="px-2.5 pb-3 space-y-0.5" style={{ borderTop: "1px solid rgba(255,255,255,0.04)", paddingTop: "8px" }}>
                {/* Support */}
                <Link href="mailto:support@forexsai.com"
                    className={`group flex items-center gap-2.5 rounded-lg transition-all duration-200 ${collapsed ? "justify-center px-0 py-2" : "px-3 py-1.5"}`}
                    style={{ color: "rgba(255,255,255,0.3)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "var(--accent-info)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.3)"; }}
                    title={collapsed ? "Support" : undefined}
                >
                    <SupportMailIcon size={16} className="flex-shrink-0" />
                    {!collapsed && <span className="text-[11px] font-medium sidebar-fade-in">Support / İletişim</span>}
                </Link>

                {/* Language (Globe) */}
                <button
                    onClick={() => {
                        const nextLang = locale === "tr" ? "en" : "tr";
                        setLocale(nextLang);
                    }}
                    className={`group flex items-center gap-2.5 rounded-lg transition-all duration-200 ${collapsed ? "justify-center px-0 py-2" : "px-3 py-1.5"}`}
                    style={{ color: "rgba(255,255,255,0.3)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "var(--accent-info)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.3)"; }}
                    title={collapsed ? "Language" : undefined}
                >
                    <GlobeIcon size={16} className="flex-shrink-0" />
                    {!collapsed && <span className="text-[11px] font-medium sidebar-fade-in">{locale === 'tr' ? 'Türkçe' : 'English'}</span>}
                </button>

                {/* Legal */}
                <div>
                    <button onClick={() => !collapsed && setLegalOpen(!legalOpen)}
                        className={`w-full group flex items-center gap-2.5 rounded-lg transition-all duration-200 ${collapsed ? "justify-center px-0 py-2" : "px-3 py-1.5"}`}
                        style={{ color: "rgba(255,255,255,0.3)" }}
                        onMouseEnter={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.6)"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.3)"; }}
                        title={collapsed ? "Legal / Website" : undefined}
                    >
                        <WebsiteIcon size={16} className="flex-shrink-0" />
                        {!collapsed && (
                            <>
                                <span className="text-[11px] font-medium flex-1 text-left sidebar-fade-in">Legal / Website</span>
                                <ChevronIcon size={12} style={{ transform: legalOpen ? "rotate(-90deg)" : "rotate(90deg)" }} className="transition-transform duration-200" />
                            </>
                        )}
                    </button>
                    {!collapsed && legalOpen && (
                        <div className="ml-3 mt-0.5 space-y-0 sidebar-slide-down">
                            {LEGAL_LINKS.map((link) => {
                                const LinkIcon = link.icon;
                                const isExternal = link.href.startsWith("http");
                                const Tag: any = isExternal ? "a" : Link;
                                const extraProps = isExternal ? { target: "_blank", rel: "noopener noreferrer" } : {};
                                return (
                                    <Tag key={link.href} href={link.href} {...extraProps}
                                        className="flex items-center gap-2 px-3 py-1 rounded-md transition-all duration-150 text-[11px]"
                                        style={{ color: "rgba(255,255,255,0.3)" }}
                                        onMouseEnter={(e: any) => { e.currentTarget.style.color = "rgba(255,255,255,0.7)"; e.currentTarget.style.background = "rgba(255,255,255,0.02)"; }}
                                        onMouseLeave={(e: any) => { e.currentTarget.style.color = "rgba(255,255,255,0.3)"; e.currentTarget.style.background = "transparent"; }}
                                    >
                                        <LinkIcon className="w-3 h-3" />
                                        <span>{link.label}</span>
                                    </Tag>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Divider */}
                <div className="h-px my-1" style={{ background: "rgba(255,255,255,0.04)" }} />

                {/* Account */}
                <Link href="/account"
                    className={`group flex items-center gap-2.5 rounded-lg transition-all duration-200 ${collapsed ? "justify-center px-0 py-2" : "px-3 py-1.5"}`}
                    style={{ color: "rgba(255,255,255,0.4)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "white"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.4)"; }}
                    title={collapsed ? "Account" : undefined}
                >
                    <div className="w-6 h-6 flex-shrink-0 rounded-full flex items-center justify-center"
                        style={{ background: "linear-gradient(135deg, rgba(0,224,198,0.15), rgba(59,130,246,0.15))", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <UserProfileIcon size={12} />
                    </div>
                    {!collapsed && (
                        <div className="min-w-0 sidebar-fade-in">
                            <p className="text-[11px] font-medium text-white/80 truncate">{user?.full_name || user?.email || "Account"}</p>
                            <p className="text-[9px] truncate" style={{ color: "rgba(0,224,198,0.5)" }}>{user?.membership_tier || "free"}</p>
                        </div>
                    )}
                </Link>

                {/* Logout */}
                <button onClick={() => logout()}
                    className={`w-full group flex items-center gap-2.5 rounded-lg transition-all duration-200 ${collapsed ? "justify-center px-0 py-2" : "px-3 py-1.5"}`}
                    style={{ color: "rgba(255,255,255,0.2)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.2)"; }}
                    title={collapsed ? "Logout" : undefined}
                >
                    <LogoutIcon size={16} className="flex-shrink-0" />
                    {!collapsed && <span className="text-[11px] font-medium sidebar-fade-in">Logout</span>}
                </button>
            </div>

            {/* Inline CSS animations */}
            <style jsx>{`
        @keyframes sidebarFadeIn { from { opacity: 0; transform: translateX(-6px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes sidebarSlideDown { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        .sidebar-fade-in { animation: sidebarFadeIn 0.18s ease-out; }
        .sidebar-slide-down { animation: sidebarSlideDown 0.18s ease-out; }
      `}</style>
        </aside>
    );
}
