"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useNavigationStore } from "../lib/store/navigation";
import {
    DashboardIcon,
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
    NewspaperIcon,
} from "./ui/CustomIcons";
import { useUser, useAuthStore } from "../lib/auth/store";
import { useI18nStore } from "../lib/i18n/store";

interface NavItem {
    href: string;
    key: string;
    label: string;
    icon: React.ElementType;
    gradient: string;
}

const NAV_ITEMS: NavItem[] = [
    { 
        href: "/", 
        key: "dashboard", 
        label: "Dashboard", 
        icon: DashboardIcon, 
        gradient: "from-cyan-500 to-blue-500" 
    },
    { 
        href: "/trading", 
        key: "trading", 
        label: "AI Trading", 
        icon: TradingIcon, 
        gradient: "from-purple-500 to-pink-500" 
    },
    { 
        href: "/analysis", 
        key: "analysis", 
        label: "Analysis", 
        icon: AnalysisIcon, 
        gradient: "from-amber-500 to-orange-500" 
    },
    { 
        href: "/signals", 
        key: "signals", 
        label: "Signals", 
        icon: SignalsIcon, 
        gradient: "from-rose-500 to-red-500" 
    },
    { 
        href: "/news-correlation", 
        key: "news-correlation", 
        label: "News AI", 
        icon: NewspaperIcon, 
        gradient: "from-emerald-500 to-teal-500" 
    },
];

const LEGAL_LINKS = [
    { href: "https://www.forexsai.com", label: "Website", icon: WebsiteIcon },
    { href: "/risk", label: "Disclaimer", icon: SecurityShieldIcon },
    { href: "/privacy", label: "Privacy", icon: TermsIcon },
    { href: "/terms", label: "Terms", icon: TermsIcon },
];

export default function Sidebar() {
    const router = useRouter();
    const { activeView, setActiveView } = useNavigationStore();
    const { locale, setLocale } = useI18nStore();
    const user = useUser();
    const { logout } = useAuthStore();

    const [collapsed, setCollapsed] = useState(false);
    const [legalOpen, setLegalOpen] = useState(false);
    const [mounted, setMounted] = useState(false);
    const legalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setMounted(true);
        const saved = localStorage.getItem("sidebar-collapsed");
        if (saved === "true") setCollapsed(true);
    }, []);

    // Close legal dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (legalRef.current && !legalRef.current.contains(event.target as Node)) {
                setLegalOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const toggleCollapse = () => {
        const next = !collapsed;
        setCollapsed(next);
        localStorage.setItem("sidebar-collapsed", String(next));
        if (next) setLegalOpen(false);
    };

    const handleLogout = async () => {
        await logout();
        router.push("/welcome");
    };

    const firstName = user?.full_name?.split(" ")[0] || user?.email?.split("@")[0] || "Trader";

    if (!mounted) return null;

    return (
        <aside
            className={`fixed left-0 top-0 h-screen z-[999] pointer-events-auto flex flex-col transition-all duration-500 ease-out ${collapsed ? "w-[80px]" : "w-[260px]"}`}
            style={{
                background: "linear-gradient(180deg, rgba(8,13,26,0.98) 0%, rgba(6,10,20,0.99) 50%, rgba(10,15,30,0.98) 100%)",
                borderRight: "1px solid rgba(0,224,198,0.12)",
                boxShadow: "4px 0 40px rgba(0,0,0,0.5), inset -1px 0 0 rgba(255,255,255,0.03)",
            }}
        >
            {/* Animated neon line on right edge */}
            <div className="absolute right-0 top-0 bottom-0 w-[2px] opacity-60" style={{
                background: "linear-gradient(180deg, transparent 0%, rgba(0,224,198,0.4) 20%, rgba(59,130,246,0.3) 50%, rgba(0,224,198,0.4) 80%, transparent 100%)",
            }} />

            {/* ── Logo Section ── */}
            <div className="px-5 pt-6 pb-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                <div className="flex items-center justify-between">
                    <Link href="/" className="group flex items-center gap-3 min-w-0">
                        <div className="relative flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-110 group-hover:rotate-3"
                            style={{
                                background: "linear-gradient(135deg, #00E0C6 0%, #3B82F6 100%)",
                                boxShadow: "0 4px 20px rgba(0,224,198,0.4), inset 0 1px 0 rgba(255,255,255,0.2)",
                            }}>
                            <ForexsAILogoIcon className="text-white" size={20} />
                            {/* Shine effect */}
                            <div className="absolute inset-0 rounded-xl overflow-hidden">
                                <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                            </div>
                        </div>
                        {!collapsed && (
                            <div className="min-w-0 sidebar-fade-in">
                                <h1 className="text-[17px] font-black tracking-tight text-white leading-none">
                                    FOREXS<span className="text-cyan-400">AI</span>
                                </h1>
                                <p className="text-[9px] font-bold tracking-[0.3em] uppercase leading-none mt-1 text-cyan-500/60">
                                    Intelligence
                                </p>
                            </div>
                        )}
                    </Link>
                    <button onClick={toggleCollapse}
                        className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg transition-all duration-300 hover:scale-110 hover:bg-cyan-500/10"
                        style={{ color: "rgba(0,224,198,0.6)" }}>
                        <ChevronIcon size={16} style={{ transform: collapsed ? "rotate(0deg)" : "rotate(180deg)", transition: "transform 0.3s" }} />
                    </button>
                </div>

                {/* Welcome */}
                {!collapsed && (
                    <div className="mt-4 flex items-center gap-2 sidebar-fade-in">
                        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        <p className="text-[12px] font-semibold text-cyan-400/80">
                            Welcome, <span className="text-white font-bold">{firstName}</span>
                        </p>
                    </div>
                )}
            </div>

            {/* ── Nav Items ── */}
            <nav className="flex-1 px-3 py-4 space-y-2 overflow-y-auto">
                {NAV_ITEMS.map((item) => {
                    const isActive = item.key === activeView;
                    const Icon = item.icon;

                    return (
                        <button 
                            key={item.key} 
                            onClick={() => setActiveView(item.key as any)}
                            className={`w-full group relative flex items-center gap-4 rounded-xl transition-all duration-300 overflow-hidden ${collapsed ? "justify-center px-0 py-3" : "px-4 py-3.5"} ${isActive ? "bg-gradient-to-r from-cyan-500/10 to-transparent" : "hover:bg-white/[0.03]"}`}
                            style={{
                                color: isActive ? "#00E0C6" : "rgba(255,255,255,0.5)",
                            }}
                            title={collapsed ? item.label : undefined}
                        >
                            {/* Active indicator line */}
                            {isActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-8 rounded-r-full bg-gradient-to-b from-cyan-400 to-blue-500 shadow-[0_0_10px_rgba(0,224,198,0.5)]" />
                            )}

                            {/* Icon container */}
                            <div className={`relative flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-300 ${isActive ? "bg-gradient-to-br " + item.gradient + " shadow-lg" : "bg-white/[0.03] group-hover:bg-white/[0.06] group-hover:scale-110"}`}>
                                <Icon 
                                    className={`w-5 h-5 flex-shrink-0 transition-all duration-300 ${isActive ? "text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]" : "group-hover:text-white"}`}
                                />
                                {/* Hover glow effect */}
                                {!isActive && (
                                    <div className={`absolute inset-0 rounded-lg bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-20 transition-opacity duration-300`} />
                                )}
                            </div>

                            {!collapsed && (
                                <div className="flex-1 text-left sidebar-fade-in">
                                    <span className={`text-[15px] block truncate whitespace-nowrap transition-all duration-200 ${isActive ? "font-bold text-white" : "font-medium group-hover:text-white group-hover:translate-x-1"}`}>
                                        {item.label}
                                    </span>
                                </div>
                            )}
                            
                            {/* Hover arrow */}
                            {!collapsed && !isActive && (
                                <div className="opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
                                    <ChevronIcon size={14} style={{ transform: "rotate(-90deg)" }} className="text-white/30" />
                                </div>
                            )}
                        </button>
                    );
                })}
            </nav>

            {/* ── Bottom Section ── */}
            <div className="px-3 pb-4 space-y-2" style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px" }}>
                
                {/* Support */}
                <Link href="mailto:support@forexsai.com"
                    className={`group flex items-center gap-3 rounded-xl transition-all duration-300 hover:bg-white/[0.03] ${collapsed ? "justify-center px-0 py-3" : "px-4 py-2.5"}`}
                    style={{ color: "rgba(255,255,255,0.4)" }}
                    title={collapsed ? "Support" : undefined}
                >
                    <div className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/[0.03] group-hover:bg-cyan-500/10 group-hover:scale-110 transition-all duration-300">
                        <SupportMailIcon size={18} className="flex-shrink-0 group-hover:text-cyan-400 transition-colors" />
                    </div>
                    {!collapsed && <span className="text-[13px] font-medium group-hover:text-white transition-colors sidebar-fade-in">Support</span>}
                </Link>

                {/* Language (Globe) */}
                <button
                    onClick={() => {
                        const nextLang = locale === "tr" ? "en" : "tr";
                        setLocale(nextLang);
                    }}
                    className={`w-full group flex items-center gap-3 rounded-xl transition-all duration-300 hover:bg-white/[0.03] ${collapsed ? "justify-center px-0 py-3" : "px-4 py-2.5"}`}
                    style={{ color: "rgba(255,255,255,0.4)" }}
                    title={collapsed ? "Language" : undefined}
                >
                    <div className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/[0.03] group-hover:bg-blue-500/10 group-hover:scale-110 transition-all duration-300">
                        <GlobeIcon size={18} className="flex-shrink-0 group-hover:text-blue-400 transition-colors" />
                    </div>
                    {!collapsed && <span className="text-[13px] font-medium group-hover:text-white transition-colors sidebar-fade-in">{locale === 'tr' ? 'Türkçe' : 'English'}</span>}
                </button>

                {/* Legal Dropdown */}
                <div ref={legalRef}>
                    <button 
                        onClick={() => !collapsed && setLegalOpen(!legalOpen)}
                        className={`w-full group flex items-center gap-3 rounded-xl transition-all duration-300 hover:bg-white/[0.03] ${collapsed ? "justify-center px-0 py-3" : "px-4 py-2.5"}`}
                        style={{ color: "rgba(255,255,255,0.4)" }}
                        title={collapsed ? "Legal / Website" : undefined}
                    >
                        <div className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/[0.03] group-hover:bg-purple-500/10 group-hover:scale-110 transition-all duration-300">
                            <WebsiteIcon size={18} className="flex-shrink-0 group-hover:text-purple-400 transition-colors" />
                        </div>
                        {!collapsed && (
                            <>
                                <span className="text-[13px] font-medium flex-1 text-left group-hover:text-white transition-colors sidebar-fade-in">Legal</span>
                                <ChevronIcon size={14} style={{ transform: legalOpen ? "rotate(0deg)" : "rotate(-90deg)", transition: "transform 0.3s" }} className="text-white/30" />
                            </>
                        )}
                    </button>
                    
                    {/* Dropdown Content */}
                    {!collapsed && legalOpen && (
                        <div className="mt-2 ml-4 space-y-1 sidebar-slide-down overflow-hidden">
                            {LEGAL_LINKS.map((link, index) => {
                                const LinkIcon = link.icon;
                                const isExternal = link.href.startsWith("http");
                                const Tag: any = isExternal ? "a" : Link;
                                const extraProps = isExternal ? { target: "_blank", rel: "noopener noreferrer" } : {};
                                return (
                                    <Tag 
                                        key={link.href} 
                                        href={link.href} 
                                        {...extraProps}
                                        className="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 text-[13px] hover:bg-white/[0.03] group/item"
                                        style={{ color: "rgba(255,255,255,0.35)" }}
                                    >
                                        <LinkIcon className="w-4 h-4 group-hover/item:text-purple-400 transition-colors" />
                                        <span className="group-hover/item:text-white transition-colors">{link.label}</span>
                                    </Tag>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Divider */}
                <div className="h-px my-2 mx-2" style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)" }} />

                {/* Account */}
                <Link href="/account"
                    className={`group flex items-center gap-3 rounded-xl transition-all duration-300 hover:bg-white/[0.03] ${collapsed ? "justify-center px-0 py-3" : "px-4 py-2.5"}`}
                    style={{ color: "rgba(255,255,255,0.5)" }}
                    title={collapsed ? "Account" : undefined}
                >
                    <div className="w-10 h-10 flex-shrink-0 rounded-full flex items-center justify-center bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-white/10 group-hover:border-cyan-500/30 group-hover:scale-110 transition-all duration-300">
                        <UserProfileIcon size={18} className="text-cyan-400" />
                    </div>
                    {!collapsed && (
                        <div className="min-w-0 flex-1 sidebar-fade-in">
                            <p className="text-[13px] font-semibold text-white/90 truncate">{user?.full_name || user?.email || "Account"}</p>
                            <p className="text-[11px] truncate text-cyan-500/70 font-medium uppercase tracking-wider">{user?.membership_tier || "free"}</p>
                        </div>
                    )}
                </Link>

                {/* Logout */}
                <button 
                    onClick={handleLogout}
                    className={`w-full group flex items-center gap-3 rounded-xl transition-all duration-300 hover:bg-red-500/10 ${collapsed ? "justify-center px-0 py-3" : "px-4 py-2.5"}`}
                    style={{ color: "rgba(255,255,255,0.3)" }}
                    title={collapsed ? "Logout" : undefined}
                >
                    <div className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/[0.03] group-hover:bg-red-500/20 group-hover:scale-110 transition-all duration-300">
                        <LogoutIcon size={18} className="flex-shrink-0 group-hover:text-red-400 transition-colors" />
                    </div>
                    {!collapsed && <span className="text-[13px] font-medium group-hover:text-red-400 transition-colors sidebar-fade-in">Logout</span>}
                </button>
            </div>

            {/* Inline CSS animations */}
            <style jsx>{`
                @keyframes sidebarFadeIn { 
                    from { opacity: 0; transform: translateX(-10px); } 
                    to { opacity: 1; transform: translateX(0); } 
                }
                @keyframes sidebarSlideDown { 
                    from { opacity: 0; transform: translateY(-10px); max-height: 0; } 
                    to { opacity: 1; transform: translateY(0); max-height: 200px; } 
                }
                .sidebar-fade-in { 
                    animation: sidebarFadeIn 0.25s cubic-bezier(0.4, 0, 0.2, 1) forwards; 
                }
                .sidebar-slide-down { 
                    animation: sidebarSlideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards; 
                }
            `}</style>
        </aside>
    );
}
