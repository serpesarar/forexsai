"use client";

import { Building2, Star, CheckCircle2, ExternalLink, Shield, DollarSign, Globe, BarChart3 } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Broker {
  id: string;
  name: string;
  logo: string;
  rating: number;
  spreads: string;
  leverage: string;
  regulation: string;
  features: string[];
  recommended?: boolean;
}

const brokers: Broker[] = [
  {
    id: "1",
    name: "Interactive Brokers",
    logo: "IB",
    rating: 4.9,
    spreads: "0.1 pips",
    leverage: "1:50",
    regulation: "FCA, SEC",
    features: ["Low spreads", "Advanced platform", "Global markets"],
    recommended: true,
  },
  {
    id: "2",
    name: "OANDA",
    logo: "OA",
    rating: 4.7,
    spreads: "0.6 pips",
    leverage: "1:50",
    regulation: "FCA, ASIC",
    features: ["Easy to use", "Good for beginners", "Strong regulation"],
  },
  {
    id: "3",
    name: "Saxo Bank",
    logo: "SB",
    rating: 4.8,
    spreads: "0.4 pips",
    leverage: "1:30",
    regulation: "FCA, Danish FSA",
    features: ["Professional tools", "Research", "VIP service"],
  },
];

export default function BrokersPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-2xl font-bold flex items-center justify-center gap-3 mb-4">
            <Building2 className="w-6 h-6 text-green-400" />
            Recommended Brokers
          </h1>
          <p className="text-gray-500 max-w-2xl mx-auto">
            Connect with trusted brokers that offer competitive spreads, strong regulation, and reliable execution.
          </p>
        </div>

        {/* Brokers List */}
        <div className="space-y-4">
          {brokers.map((broker, idx) => (
            <div
              key={broker.id}
              className={cn(
                "bg-gray-900/50 border rounded-xl p-6 flex items-center gap-6",
                broker.recommended 
                  ? "border-purple-500/30 bg-purple-500/5" 
                  : "border-gray-800 hover:border-gray-700"
              )}
            >
              {/* Logo */}
              <div className="w-16 h-16 bg-gray-800 rounded-xl flex items-center justify-center text-lg font-bold">
                {broker.logo}
              </div>

              {/* Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold">{broker.name}</h3>
                  {broker.recommended && (
                    <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded-full border border-purple-500/30">
                      Recommended
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-6 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                    {broker.rating}
                  </span>
                  <span className="flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    Spreads from {broker.spreads}
                  </span>
                  <span className="flex items-center gap-1">
                    <BarChart3 className="w-4 h-4" />
                    Leverage up to {broker.leverage}
                  </span>
                  <span className="flex items-center gap-1">
                    <Shield className="w-4 h-4" />
                    {broker.regulation}
                  </span>
                </div>
              </div>

              {/* Features */}
              <div className="hidden lg:flex gap-2">
                {broker.features.map((feature) => (
                  <span key={feature} className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                    {feature}
                  </span>
                ))}
              </div>

              {/* CTA */}
              <button className="px-6 py-2 bg-green-500 hover:bg-green-600 rounded-lg font-medium transition-colors flex items-center gap-2">
                Open Account
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Disclaimer */}
        <p className="text-center text-xs text-gray-600 mt-8">
          Trading involves risk. Please ensure you understand the risks before opening an account.
        </p>
      </div>
    </div>
  );
}
