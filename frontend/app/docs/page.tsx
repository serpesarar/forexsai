"use client";

import { BookOpen, Search, ChevronRight, FileText, Video, HelpCircle, ExternalLink, Code, Terminal, BookMarked, Zap, Shield, BarChart3, MessageSquare } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const docSections = [
  {
    title: "Getting Started",
    icon: Zap,
    items: [
      { title: "Quick Start Guide", description: "Get up and running in 5 minutes", href: "#" },
      { title: "Platform Overview", description: "Learn about ForexSAI features", href: "#" },
      { title: "Account Setup", description: "Configure your trading profile", href: "#" },
    ]
  },
  {
    title: "Trading Features",
    icon: BarChart3,
    items: [
      { title: "Smart Trades", description: "AI-powered trade recommendations", href: "#" },
      { title: "News Analysis", description: "Real-time news impact on markets", href: "#" },
      { title: "Technical Indicators", description: "Available chart indicators", href: "#" },
      { title: "Risk Management", description: "Set stop-loss and take-profit", href: "#" },
    ]
  },
  {
    title: "AI & Machine Learning",
    icon: MessageSquare,
    items: [
      { title: "AI Analysis Engine", description: "How our AI analyzes markets", href: "#" },
      { title: "Chat AI Assistant", description: "Get help from our AI assistant", href: "#" },
      { title: "Prediction Models", description: "Understanding ML predictions", href: "#" },
      { title: "Sentiment Analysis", description: "Market sentiment indicators", href: "#" },
    ]
  },
  {
    title: "API Reference",
    icon: Code,
    items: [
      { title: "REST API", description: "Access market data via API", href: "#" },
      { title: "WebSocket API", description: "Real-time data streaming", href: "#" },
      { title: "Authentication", description: "API key management", href: "#" },
      { title: "Rate Limits", description: "API usage limits", href: "#" },
    ]
  },
  {
    title: "Security",
    icon: Shield,
    items: [
      { title: "Two-Factor Auth", description: "Secure your account", href: "#" },
      { title: "API Security", description: "Best practices for API keys", href: "#" },
      { title: "Data Privacy", description: "How we handle your data", href: "#" },
    ]
  },
];

const quickLinks = [
  { title: "Video Tutorials", icon: Video, href: "#" },
  { title: "FAQ", icon: HelpCircle, href: "#" },
  { title: "Changelog", icon: FileText, href: "#" },
  { title: "Support", icon: MessageSquare, href: "#" },
];

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedSection, setExpandedSection] = useState<string | null>("Getting Started");

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold flex items-center justify-center gap-3 mb-4">
            <BookOpen className="w-8 h-8 text-purple-400" />
            Documentation
          </h1>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Everything you need to know about using ForexSAI. Search our docs, watch tutorials, or get support.
          </p>
        </div>

        {/* Search */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-gray-900 border border-gray-800 rounded-xl text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-4 gap-4 mb-12">
          {quickLinks.map((link) => (
            <a
              key={link.title}
              href={link.href}
              className="flex items-center gap-3 p-4 bg-gray-900/50 border border-gray-800 rounded-xl hover:border-purple-500/50 hover:bg-gray-900 transition-all group"
            >
              <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
                <link.icon className="w-5 h-5 text-purple-400" />
              </div>
              <span className="font-medium">{link.title}</span>
            </a>
          ))}
        </div>

        {/* Documentation Sections */}
        <div className="grid grid-cols-2 gap-6">
          {docSections.map((section) => {
            const Icon = section.icon;
            const isExpanded = expandedSection === section.title;
            
            return (
              <div
                key={section.title}
                className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedSection(isExpanded ? null : section.title)}
                  className="w-full flex items-center justify-between p-5 hover:bg-gray-900 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
                      <Icon className="w-5 h-5 text-purple-400" />
                    </div>
                    <span className="font-semibold text-lg">{section.title}</span>
                  </div>
                  <ChevronRight className={cn("w-5 h-5 text-gray-500 transition-transform", isExpanded && "rotate-90")} />
                </button>
                
                {isExpanded && (
                  <div className="border-t border-gray-800">
                    {section.items.map((item) => (
                      <a
                        key={item.title}
                        href={item.href}
                        className="flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors group"
                      >
                        <div>
                          <p className="font-medium text-white group-hover:text-purple-400 transition-colors">
                            {item.title}
                          </p>
                          <p className="text-sm text-gray-500 mt-0.5">{item.description}</p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-600 group-hover:text-purple-400 transition-colors" />
                      </a>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Help CTA */}
        <div className="mt-12 p-6 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-xl">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-1">Need help?</h3>
              <p className="text-gray-400">Can't find what you're looking for? Contact our support team.</p>
            </div>
            <button className="px-6 py-3 bg-purple-500 hover:bg-purple-600 rounded-lg font-medium transition-colors">
              Contact Support
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
