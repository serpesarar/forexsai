"use client";

import { useEffect, useMemo, useState } from "react";
import type { ISourceOptions, Engine } from "@tsparticles/engine";

/**
 * TradingBackground - Performance-optimized animated background.
 * - Mobile: Only static CSS gradients (no particles, no JS animation)
 * - Desktop: Reduced particle count (30 vs 80), 30fps cap, no hover interaction
 * - Tab hidden: Particles engine not loaded
 */
export function TradingBackground() {
  const [init, setInit] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [ParticlesComponent, setParticlesComponent] = useState<any>(null);

  // Detect mobile once on mount
  useEffect(() => {
    const mobile = window.innerWidth < 768 || /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    setIsMobile(mobile);

    // Only load particles engine on desktop
    if (!mobile) {
      Promise.all([
        import("@tsparticles/react"),
        import("@tsparticles/slim"),
      ]).then(([{ default: Particles, initParticlesEngine }, { loadSlim }]) => {
        initParticlesEngine(async (engine: Engine) => {
          await loadSlim(engine);
        }).then(() => {
          setParticlesComponent(() => Particles);
          setInit(true);
        });
      });
    }
  }, []);

  const options: ISourceOptions = useMemo(
    () => ({
      fullScreen: false,
      fpsLimit: 30,
      interactivity: { events: {} },
      particles: {
        color: {
          value: ["#00E0C6", "#3B82F6", "#8B5CF6"],
        },
        links: {
          color: "#00E0C6",
          distance: 200,
          enable: true,
          opacity: 0.06,
          width: 1,
        },
        move: {
          direction: "none",
          enable: true,
          outModes: { default: "out" },
          random: true,
          speed: 0.2,
          straight: false,
        },
        number: {
          density: { enable: true, area: 1600 },
          value: 30,
        },
        opacity: {
          value: { min: 0.1, max: 0.4 },
        },
        shape: { type: "circle" },
        size: {
          value: { min: 0.5, max: 2 },
        },
      },
      detectRetina: true,
    }),
    []
  );

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {/* Static gradient orbs - lightweight CSS only */}
      <div 
        className="absolute -top-40 -left-40 w-[800px] h-[800px] rounded-full opacity-30"
        style={{
          background: 'radial-gradient(circle, rgba(0,224,198,0.15) 0%, transparent 70%)',
        }}
      />
      <div 
        className="absolute top-1/3 -right-20 w-[600px] h-[600px] rounded-full opacity-25"
        style={{
          background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)',
        }}
      />
      {!isMobile && (
        <div 
          className="absolute -bottom-40 left-1/3 w-[700px] h-[700px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)',
          }}
        />
      )}
      
      {/* Particles - desktop only */}
      {init && ParticlesComponent && (
        <ParticlesComponent
          id="trading-particles"
          options={options}
          className="absolute inset-0"
        />
      )}
      
      {/* Subtle grid overlay */}
      <div 
        className="absolute inset-0 opacity-[0.015] hidden md:block"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0,224,198,0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,224,198,0.3) 1px, transparent 1px)
          `,
          backgroundSize: '80px 80px',
        }}
      />
      
      {/* Vignette effect */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(11,18,32,0.4) 100%)',
        }}
      />
    </div>
  );
}
