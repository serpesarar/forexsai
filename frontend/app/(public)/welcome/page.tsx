"use client";

import Link from "next/link";
import dynamic from "next/dynamic";

const SplineViewerClientNoSSR = dynamic(
  () => import("../../../components/welcome/SplineViewerClient"),
  { ssr: false }
);

export default function WelcomePage() {
  return (
    <div className="relative w-full h-screen overflow-hidden bg-black text-white font-sans">

      {/* 3D Spline Arka Plan - Client-Side Only */}
      <SplineViewerClientNoSSR />

      {/* Grain Texture Overlay */}
      <div className="pointer-events-none absolute inset-0 z-10 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay"></div>

      {/* Subtle Vignette */}
      <div className="pointer-events-none absolute inset-0 z-10 bg-[radial-gradient(circle_at_center,_transparent_0%,_black_100%)] opacity-70"></div>

      {/* UI Content Layer */}
      <div className="relative z-20 flex flex-col h-full mx-auto max-w-[1400px]">

        {/* Glass Navbar */}
        <nav className="flex items-center justify-between px-8 py-5 backdrop-blur-md border-b border-white/10">
          <div className="flex items-center gap-1">
            <span className="text-xl font-bold tracking-[0.1em] bg-gradient-to-br from-gray-100 to-gray-400 bg-clip-text text-transparent">FOREXS</span>
            <span className="text-xl font-light tracking-[0.1em] text-white/90">AI</span>
          </div>

          <div className="hidden md:flex gap-10">
            {['MARKETS', 'ANALYSIS', 'ABOUT'].map((label) => (
              <span key={label} className="uppercase tracking-widest text-xs text-gray-400 hover:text-white transition-colors cursor-pointer">
                {label}
              </span>
            ))}
          </div>

          <div>
            <Link
              href="/login"
              className="uppercase tracking-widest text-xs text-gray-300 hover:text-white transition-colors border border-white/20 px-5 py-2.5 rounded hover:bg-white/5"
            >
              LOGIN
            </Link>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="flex-1 flex flex-col items-end justify-center px-12 pb-32">
          <div className="max-w-xl text-right">
            <h1 className="text-6xl md:text-8xl font-sans mb-4 flex flex-col items-end leading-tight">
              <span className="font-bold tracking-[0.2em] bg-gradient-to-r from-gray-100 via-gray-400 to-gray-100 bg-clip-text text-transparent drop-shadow-lg">
                FOREXS
              </span>
              <span className="font-light tracking-[0.2em] text-white/90">
                AI
              </span>
            </h1>

            <p className="text-gray-400 font-light text-xl mb-10 max-w-lg mt-6 ml-auto leading-relaxed border-r-2 border-cyan-500/50 pr-4">
              Advanced algorithmic trading powered by neural networks
            </p>

            <Link href="/demo">
              <button className="bg-gradient-to-r from-gray-700 via-gray-400 to-gray-700 border border-gray-500/50 shadow-[0_0_15px_rgba(192,192,192,0.3)] hover:shadow-[0_0_25px_rgba(192,192,192,0.5)] transition-all duration-300 text-white uppercase tracking-widest text-sm px-10 py-4 rounded-sm font-medium">
                START TRADING
              </button>
            </Link>
          </div>
        </div>

        {/* Glass Cards (Bottom) */}
        <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 w-full max-w-5xl px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Card 1 */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-300 cursor-pointer group">
              <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center mb-4 group-hover:bg-cyan-500/40 transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
              </div>
              <h3 className="uppercase tracking-widest text-sm mb-2 text-gray-200">Live Markets</h3>
              <p className="font-light text-gray-500 text-sm">Real-time AI analysis</p>
            </div>

            {/* Card 2 */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-300 cursor-pointer group">
              <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center mb-4 group-hover:bg-purple-500/40 transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-purple-400"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
              </div>
              <h3 className="uppercase tracking-widest text-sm mb-2 text-gray-200">AI Analysis</h3>
              <p className="font-light text-gray-500 text-sm">Deep pattern recognition</p>
            </div>

            {/* Card 3 */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-xl hover:bg-white/10 hover:scale-105 transition-all duration-300 cursor-pointer group">
              <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center mb-4 group-hover:bg-blue-500/40 transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
              </div>
              <h3 className="uppercase tracking-widest text-sm mb-2 text-gray-200">Portfolio</h3>
              <p className="font-light text-gray-500 text-sm">Intelligent risk management</p>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
