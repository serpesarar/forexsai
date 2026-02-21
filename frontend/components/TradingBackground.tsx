"use client";

/**
 * TradingBackground - CSS-only animated background.
 * No particles library, no JS animation, zero memory cost.
 * Previously used @tsparticles (~2MB JS + continuous canvas animation).
 */
export function TradingBackground() {
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
      <div
        className="absolute -bottom-40 left-1/3 w-[700px] h-[700px] rounded-full opacity-20 hidden md:block"
        style={{
          background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)',
        }}
      />

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
