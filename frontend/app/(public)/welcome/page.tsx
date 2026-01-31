"use client";

import { TopNav } from "@/components/welcome/TopNav";
import { Hero } from "@/components/welcome/Hero";
import { ValueProps } from "@/components/welcome/ValueProps";
import { HowItWorks } from "@/components/welcome/HowItWorks";
import { FeaturesGrid } from "@/components/welcome/FeaturesGrid";
import { TrustSection } from "@/components/welcome/TrustSection";
import { Footer } from "@/components/welcome/Footer";

export default function WelcomePage() {
  return (
    <main className="min-h-screen bg-[#0B1220] text-[#E5E7EB]">
      <TopNav />
      <Hero />
      <ValueProps />
      <HowItWorks />
      <FeaturesGrid />
      <TrustSection />
      <Footer />
    </main>
  );
}
